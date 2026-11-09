"""Lee una foto del horario con un modelo de IA con visión (API de Google Gemini).

La IA devuelve el horario en el MISMO formato CSV que ya sabe leer `horario_csv`,
así todo pasa por la misma validación (días, horas y códigos de salón).

Para equivocarse menos:
  1. La instrucción explica cómo leer la cuadrícula y lista los códigos válidos.
  2. Si la validación encuentra filas con problemas (por ejemplo un código que no
     existe), se le pide a la IA que mire de nuevo SOLO esas filas y las corrija.
  3. Antes de gastar una segunda llamada, se intentan arreglar EN LOCAL las confusiones
     típicas de caracteres en los códigos (0/O, 1/I/L, 5/S, 8/B, 2/Z), pero solo si
     existe una única corrección válida.
  4. Si un modelo está saturado (503) o no disponible, se prueba el siguiente.
Para que sea más rápido: la imagen se reduce antes de enviarla y a los modelos Gemini 3
se les pide poco "pensamiento" (thinking_level LOW). En la terminal se imprime cuánto
tarda cada llamada y con qué modelo.
Aun así puede fallar: el estudiante siempre revisa y corrige antes de guardar.
La imagen NO se guarda en el programa.

Requisitos:  pip install google-genai
             y la variable de entorno GEMINI_API_KEY (clave gratis en
             https://aistudio.google.com/apikey).

Modelos: por defecto se prueban en orden los de MODELOS_POR_DEFECTO. Se pueden
cambiar con la variable MODELO_GEMINI (uno o varios separados por coma).
"""
import csv
import io
import itertools
import os
import time

from .codigos import ESPECIALES, normalizar
from .horario_csv import codigo_conocido, espacio_deportivo, leer_horario

# gemini-3.8-flash va al final: suele estar saturado (503) y hacerlo esperar primero es lento
MODELOS_POR_DEFECTO = "gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.8-flash"
MODELOS = [m.strip() for m in
           os.environ.get("MODELO_GEMINI", MODELOS_POR_DEFECTO).split(",") if m.strip()]
MAX_BYTES = 5 * 1024 * 1024          # límite de tamaño de imagen que aceptamos
FORMATOS = ("image/png", "image/jpeg", "image/webp")
TIMEOUT_S = int(os.environ.get("LECTOR_TIMEOUT", "45"))   # espera máxima por llamada
LADO_MAXIMO = 1600                   # px: más grande que esto no mejora la lectura

# errores que justifican reintentar o pasar al siguiente modelo
_TRANSITORIOS = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND",
                 "500", "INTERNAL", "504", "DEADLINE")


def construir_prompt():
    """Instrucción para la IA. Incluye los códigos especiales que conoce el programa."""
    extras = sorted(ESPECIALES)
    extras_txt = (", " + ", ".join(extras)) if extras else ""
    return (
        "Eres un lector cuidadoso de horarios universitarios. La imagen es un horario "
        "semanal de clases. Cada celda de color contiene el CÓDIGO del salón y, a veces, "
        "el nombre de la materia.\n\n"
        "Cómo leerlo (lo más importante es no equivocarse):\n"
        "1. Mira el encabezado para saber qué columna es cada día (Lunes a Sábado) y el "
        "eje izquierdo para saber qué fila es cada hora. Una celda pertenece SOLO al día "
        "de su columna y a la hora de su fila.\n"
        "2. Lee cada celda con color. Copia el código del salón carácter por carácter.\n"
        "3. Si la misma materia y el mismo código ocupan celdas consecutivas de la misma "
        "columna, es UNA sola clase: hora_inicio es el inicio de la primera celda y "
        "hora_fin es el FINAL de la última (ej. 9:00-10:00 y 10:00-11:00 => 9 a 11).\n"
        "4. Códigos válidos: un número seguido de la letra del bloque (A a M), por "
        "ejemplo 26J, 93K, 22D, 21K; el bloque G puede llevar 1 o 2 al final (13G2, "
        "37G1); SDU1 a SDU10; laboratorios L1-3, L1-4, L1-5" + extras_txt + ". "
        "Si dudas entre caracteres parecidos (0/O, 1/I/L, 5/S, 8/B, 2/Z), elige el que "
        "forme un código válido de esta lista.\n"
        "5. materia: copia el nombre tal como aparece en la celda o en la leyenda de "
        "colores, completo y sin abreviar. Si la imagen no lo muestra, déjala vacía.\n"
        "6. Si una celda es una actividad deportiva (tenis, fútbol, natación...) y no "
        "muestra código de salón, escribe en salon el nombre del deporte (ej. TENIS) y "
        "en materia el mismo nombre.\n"
        "7. Ignora las celdas vacías. No inventes clases ni repitas la misma dos veces.\n\n"
        "Formato: devuelve SOLO un CSV, sin explicaciones ni bloques de código, con esta "
        "primera línea exacta:\n"
        "dia,hora_inicio,hora_fin,salon,materia\n"
        "dia: Lunes, Martes, Miércoles, Jueves, Viernes o Sábado. Las horas son números "
        "enteros de 24 horas (ej. 7, 14). Si un campo (por ejemplo la materia) lleva "
        "comas, ponlo entre comillas dobles."
    )


def construir_prompt_correccion(csv_previo, errores):
    problemas = "\n".join("- " + e.split(" Si es un código")[0] for e in errores)
    return (
        "Antes leíste este horario de la imagen:\n\n" + csv_previo + "\n\n"
        "Al validarlo se encontraron estos problemas:\n" + problemas + "\n\n"
        "Vuelve a mirar la imagen con mucho cuidado, sobre todo esas filas, y corrige "
        "lo que esté mal leído (código del salón, día u hora). Si después de mirar "
        "estás seguro de que lo leído es correcto, déjalo igual. Devuelve el CSV "
        "COMPLETO (todas las filas) con el mismo formato y sin explicaciones."
    )


# caracteres que la IA suele confundir al leer un código (y por cuáles se cambian)
_CONFUNDIBLES = {"0": "O", "O": "0", "1": "IL", "I": "1", "L": "1",
                 "5": "S", "S": "5", "8": "B", "B": "8", "2": "Z", "Z": "2"}


def _variantes(codigo, cambios):
    """Códigos que resultan de cambiar EXACTAMENTE `cambios` caracteres confundibles."""
    posiciones = [i for i, ch in enumerate(codigo) if ch in _CONFUNDIBLES]
    for pos in itertools.combinations(posiciones, cambios):
        for reemplazos in itertools.product(*(_CONFUNDIBLES[codigo[i]] for i in pos)):
            letras = list(codigo)
            for i, r in zip(pos, reemplazos):
                letras[i] = r
            yield "".join(letras)


def corregir_codigo(codigo):
    """Si `codigo` no es válido pero hay UNA sola forma válida de arreglarlo cambiando
    caracteres parecidos (1 cambio y, si no sirve, 2), la devuelve. Si no hay ninguna
    o hay varias (ambiguo), devuelve None para no adivinar."""
    c = normalizar(codigo)
    if not c or codigo_conocido(c):
        return None
    for cambios in (1, 2):
        validos = {v for v in _variantes(c, cambios) if codigo_conocido(v)}
        if len(validos) == 1:
            return validos.pop()
        if validos:
            return None                    # ambiguo
    return None


def corregir_codigos_local(texto):
    """Arregla los códigos de salón mal leídos sin volver a llamar a la IA.

    Devuelve (csv_nuevo, cambios) con cambios = [(leído, corregido), ...].
    Si no hay nada que corregir devuelve el texto tal cual.
    """
    texto = texto.strip()
    if not texto:
        return texto, []
    primera = texto.splitlines()[0]
    delimitador = ";" if primera.count(";") > primera.count(",") else ","
    filas = list(csv.reader(io.StringIO(texto), delimiter=delimitador))
    encabezado = [c.strip().lower() for c in filas[0]]
    if "salon" not in encabezado:
        return texto, []
    i_salon = encabezado.index("salon")
    i_materia = encabezado.index("materia") if "materia" in encabezado else None
    cambios = []
    for fila in filas[1:]:
        if len(fila) <= i_salon:
            continue
        materia = fila[i_materia] if i_materia is not None and len(fila) > i_materia else ""
        if espacio_deportivo(fila[i_salon]) or espacio_deportivo(materia):
            continue                       # un deporte no lleva código de salón
        nuevo = corregir_codigo(fila[i_salon])
        if nuevo:
            cambios.append((fila[i_salon].strip(), nuevo))
            fila[i_salon] = nuevo
    if not cambios:
        return texto, []
    salida = io.StringIO()
    csv.writer(salida, delimiter=delimitador, lineterminator="\n").writerows(filas)
    return salida.getvalue().strip(), cambios


def limpiar_csv(texto):
    """Quita ``` y espacios sobrantes por si el modelo envolvió la respuesta."""
    lineas = [l for l in texto.strip().splitlines() if not l.strip().startswith("```")]
    return "\n".join(lineas).strip()


def _crear_cliente():
    clave = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not clave:
        raise RuntimeError("Falta la clave de la IA: define la variable de entorno "
                           "GEMINI_API_KEY antes de ejecutar la app "
                           "(se saca gratis en https://aistudio.google.com/apikey).")
    from google import genai              # se importa aquí para no exigirlo si no se usa
    from google.genai import types
    # sin límite de tiempo la app puede quedarse "Leyendo la imagen..." para siempre
    return genai.Client(api_key=clave,
                        http_options=types.HttpOptions(timeout=TIMEOUT_S * 1000))


def reducir_imagen(datos, tipo_mime):
    """Reduce una imagen grande (lado mayor > LADO_MAXIMO) y la pasa a JPEG: se sube y se
    procesa más rápido. Si no hace falta o algo falla, devuelve la imagen original."""
    try:
        from PIL import Image
        imagen = Image.open(io.BytesIO(datos))
        if max(imagen.size) <= LADO_MAXIMO:
            return datos, tipo_mime
        imagen = imagen.convert("RGB")
        imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
        salida = io.BytesIO()
        imagen.save(salida, format="JPEG", quality=90)
        if salida.tell() >= len(datos):
            return datos, tipo_mime            # no se ganó nada
        return salida.getvalue(), "image/jpeg"
    except Exception:
        return datos, tipo_mime


def _config_para(modelo):
    """Gemini 3 piensa mucho por defecto (lento). Leer una cuadrícula no lo necesita."""
    if "gemini-3" not in modelo:
        return None
    from google.genai import types
    return types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="LOW"))


def _llamar(cliente, modelo, contenido):
    """Una llamada a un modelo. Si rechaza la configuración, se repite sin ella."""
    args = {"model": modelo, "contents": contenido}
    config = _config_para(modelo)
    if config is not None:
        args["config"] = config
    inicio = time.perf_counter()
    print(f"[lector] enviando a {modelo}...", flush=True)
    try:
        respuesta = cliente.models.generate_content(**args)
    except Exception as error:
        if config is None or "INVALID_ARGUMENT" not in str(error):
            print(f"[lector] {modelo}: falló tras {time.perf_counter() - inicio:.1f} s",
                  flush=True)
            raise
        del args["config"]                     # ese modelo no acepta thinking_level
        respuesta = cliente.models.generate_content(**args)
    print(f"[lector] {modelo}: {time.perf_counter() - inicio:.1f} s", flush=True)
    return respuesta


def _es_timeout(texto):
    t = texto.lower()
    return "timed out" in t or "timeout" in t


def _generar(cliente, contenido):
    """Llama al modelo. Si falla, prueba el siguiente de inmediato. Solo el último modelo
    de la lista se reintenta una vez cuando está saturado (503)."""
    ultimo = None
    for modelo in MODELOS:
        for intento in range(2):
            try:
                return _llamar(cliente, modelo, contenido)
            except Exception as error:
                ultimo = error
                texto = str(error)
                if not (any(c in texto for c in _TRANSITORIOS) or _es_timeout(texto)):
                    raise
                print(f"[lector] {modelo} falló ({texto[:90]}); se prueba otro modelo",
                      flush=True)
                saturado = "503" in texto or "UNAVAILABLE" in texto
                if saturado and intento == 0 and modelo == MODELOS[-1]:
                    time.sleep(2)             # último modelo saturado: un segundo intento
                    continue
                break                         # si hay otro modelo, se pasa al siguiente ya
    raise ultimo


def _texto_de(respuesta):
    texto = respuesta.text or ""
    if not texto.strip():
        raise ValueError("La IA no devolvió texto (puede haber bloqueado la imagen). "
                         "Prueba con otra captura.")
    return limpiar_csv(texto)


def imagen_a_csv(datos, tipo_mime, cliente=None, corregir=True):
    """Envía la imagen a la IA y devuelve el horario como texto CSV."""
    if len(datos) > MAX_BYTES:
        raise ValueError("La imagen pesa más de 5 MB. Redúcela o recórtala.")
    if tipo_mime not in FORMATOS:
        raise ValueError(f"Formato de imagen no soportado: {tipo_mime}")
    cliente = cliente or _crear_cliente()
    from google.genai import types
    datos, tipo_mime = reducir_imagen(datos, tipo_mime)
    imagen = types.Part.from_bytes(data=datos, mime_type=tipo_mime)

    horario = _texto_de(_generar(cliente, [imagen, construir_prompt()]))
    horario, _ = corregir_codigos_local(horario)    # primero lo barato: arreglo local
    if not corregir:
        return horario

    clases, errores = leer_horario(horario)
    if errores:                                # segunda pasada solo si siguen los problemas
        try:
            horario2 = _texto_de(_generar(
                cliente, [imagen, construir_prompt_correccion(horario, errores)]))
        except Exception:
            return horario                     # la corrección es opcional
        horario2, _ = corregir_codigos_local(horario2)
        clases2, errores2 = leer_horario(horario2)
        if len(errores2) < len(errores) and len(clases2) >= len(clases):
            return horario2
    return horario