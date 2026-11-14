"""Lee una foto del horario con un modelo de IA con visión (API de Anthropic).

La IA devuelve el horario en el MISMO formato CSV que ya sabe leer `horario_csv`,
así todo pasa por la misma validación (días, horas y códigos de salón). Si la IA
se equivoca o inventa algo, la validación lo rechaza o el estudiante lo corrige en
pantalla antes de guardar. La imagen NO se guarda en el programa.

Requisitos:  pip install anthropic   y la variable de entorno ANTHROPIC_API_KEY.
"""
import base64
import os

MODELO = os.environ.get("MODELO_IA", "claude-sonnet-5-5")
MAX_BYTES = 5 * 1024 * 1024          # límite de tamaño de imagen de la API

PROMPT = """Esta imagen es un horario semanal de clases de una universidad. \
Cada celda de color muestra el CÓDIGO del salón (por ejemplo 26J, 37G2, SDU9, L1-5).

Devuelve SOLO un CSV, sin explicaciones ni bloques de código, con esta primera línea exacta:
dia,hora_inicio,hora_fin,salon,materia

Reglas:
- Una fila por clase. Si el mismo código aparece en celdas consecutivas de la misma \
columna (mismo día), únelas en una sola fila: hora_inicio es el inicio de la primera \
celda y hora_fin es el FINAL de la última celda (ej. celdas 9:00-10:00 y 10:00-11:00 \
=> hora_inicio 9, hora_fin 11).
- dia: Lunes, Martes, Miércoles, Jueves, Viernes o Sábado.
- Horas como números enteros de 24 horas (ej. 9, 14).
- salon: copia el código EXACTAMENTE como se ve en la celda.
- materia: déjala vacía, salvo que la imagen muestre una leyenda que relacione el \
color con el nombre de la materia; en ese caso escribe el nombre.
- Ignora las celdas vacías. No inventes clases que no se vean."""


def limpiar_csv(texto):
    """Quita ``` y espacios sobrantes por si el modelo envolvió la respuesta."""
    lineas = [l for l in texto.strip().splitlines() if not l.strip().startswith("```")]
    return "\n".join(lineas).strip()


def _crear_cliente():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta la clave de la IA: define la variable de entorno "
                           "ANTHROPIC_API_KEY antes de ejecutar la app.")
    import anthropic                      # se importa aquí para no exigirlo si no se usa
    return anthropic.Anthropic()


def imagen_a_csv(datos, tipo_mime, cliente=None):
    """Envía la imagen a la IA y devuelve el horario como texto CSV."""
    if len(datos) > MAX_BYTES:
        raise ValueError("La imagen pesa más de 5 MB. Redúcela o recórtala.")
    if tipo_mime not in ("image/png", "image/jpeg", "image/webp", "image/gif"):
        raise ValueError(f"Formato de imagen no soportado: {tipo_mime}")
    cliente = cliente or _crear_cliente()
    respuesta = cliente.messages.create(
        model=MODELO,
        max_tokens=2000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": tipo_mime,
                                         "data": base64.b64encode(datos).decode()}},
            {"type": "text", "text": PROMPT}]}],
    )
    texto = "".join(b.text for b in respuesta.content if b.type == "text")
    return limpiar_csv(texto)