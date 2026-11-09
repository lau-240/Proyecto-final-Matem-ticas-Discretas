"""Carga de horarios desde un CSV.

Columnas:  dia, hora_inicio, hora_fin, salon, materia   (materia es opcional)
Ejemplo:   Martes,9,11,26J,Calculo II
Acepta coma o punto y coma (Excel en español). Días: Lunes ... Sábado.
"""
import csv
import io
import unicodedata

from .campus import misma_materia
from .codigos import asegurar_espacio, normalizar, parsear_codigo
from .franjas import H_FIN, H_INI, franja, rango

PLANTILLA = ("dia,hora_inicio,hora_fin,salon,materia\n"
             "Martes,9,11,26J,Calculo II\n"
             "Jueves,12,14,SDU9,Fisica\n")

NOMBRES_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
_DIAS = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4,
         "sabado": 5, "lun": 0, "mar": 1, "mie": 2, "jue": 3, "vie": 4, "sab": 5}


def _norm(texto):
    """minúsculas y sin tildes: 'Miércoles' -> 'miercoles'."""
    texto = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


def _hora(texto):
    """'9' o '9:00' -> 9. Lanza ValueError si no es un número."""
    return int(str(texto).strip().split(":")[0])


def espacio_deportivo(texto):
    """Si el texto nombra un deporte, devuelve la cancha del bloque M donde se practica.

    tenis -> M-tenis, fútbol/futsal -> M-futbol, natación/piscina -> M-piscina.
    ('tenis de mesa' no cuenta: no se juega en la cancha de tenis.)
    """
    t = _norm(texto)
    if "tenis" in t and "mesa" not in t:
        return "M-tenis"
    if "futbol" in t or "futsal" in t:
        return "M-futbol"
    if "piscina" in t or "natacion" in t or "acuatic" in t:
        return "M-piscina"
    return None


def codigo_conocido(codigo, campus=None):
    if campus is not None and asegurar_espacio_sin_crear(campus, codigo):
        return True
    return parsear_codigo(codigo) is not None


def asegurar_espacio_sin_crear(campus, codigo):
    c = normalizar(codigo)
    return any(e.upper() == c for e in campus.espacios)


def leer_horario(texto, campus=None):
    """Devuelve (clases, errores). clases = [(dia, h_ini, h_fin, codigo, materia)]."""
    texto = texto.strip()
    if not texto:
        return [], ["El archivo está vacío."]
    primera = texto.splitlines()[0]
    delimitador = ";" if primera.count(";") > primera.count(",") else ","
    lector = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
    campos = {_norm(c): c for c in (lector.fieldnames or [])}
    faltan = [c for c in ("dia", "hora_inicio", "hora_fin", "salon") if c not in campos]
    if faltan:
        return [], [f"Faltan columnas: {', '.join(faltan)}. "
                    "Debe empezar con: dia,hora_inicio,hora_fin,salon,materia"]

    def valor(fila, clave):
        return (fila.get(campos[clave]) or "").strip() if clave in campos else ""

    clases, errores = [], []
    for n, fila in enumerate(lector, start=2):
        if not any((v or "").strip() for v in fila.values() if not isinstance(v, list)):
            continue                                    # fila en blanco
        dia = _DIAS.get(_norm(valor(fila, "dia")))
        if dia is None:
            errores.append(f"Fila {n}: día no válido ('{valor(fila, 'dia')}').")
            continue
        try:
            h_ini, h_fin = _hora(valor(fila, "hora_inicio")), _hora(valor(fila, "hora_fin"))
        except ValueError:
            errores.append(f"Fila {n}: las horas deben ser números (ej. 9 y 11).")
            continue
        if not (H_INI <= h_ini < h_fin <= H_FIN):
            errores.append(f"Fila {n}: la franja {h_ini}-{h_fin} no es válida "
                           f"(debe estar entre {H_INI} y {H_FIN}).")
            continue
        texto_salon = valor(fila, "salon")
        materia = valor(fila, "materia") or valor(fila, "detalle")
        codigo = normalizar(texto_salon)
        if not codigo_conocido(codigo, campus):
            # un deporte sin código de salón se asume en su cancha (bloque M)
            cancha = espacio_deportivo(materia) or espacio_deportivo(texto_salon)
            if cancha is None:
                errores.append(f"Fila {n}: salón '{codigo}' no reconocido. Si es un código "
                               "especial, agréguenlo en ESPECIALES de src/codigos.py.")
                continue
            codigo = cancha
            materia = materia or texto_salon
        materia = materia or f"Clase en {codigo}"
        clases.append((dia, h_ini, h_fin, codigo, materia))
    return clases, errores


def _quien_ocupa(campus, espacio_id, dia, h_ini, h_fin):
    """Texto de lo que ya ocupa el espacio en esa franja (para explicar el conflicto)."""
    for f in range(franja(dia, h_ini), franja(dia, h_fin)):
        r = campus.que_hay(espacio_id, f)
        if r is not None:
            return r.detalle or r.motivo
    return "otra cosa"


def aplicar_horario(campus, horarios, alias, clases):
    """Registra las clases. Devuelve (agregadas, conflictos).

    Si el espacio ya tiene esa misma clase en esas franjas (aunque la materia esté
    escrita un poco distinto: mayúsculas, tildes, nombre cortado) cuenta como una
    confirmación más, no como conflicto. Una clase que `alias` ya tenía cargada se
    omite. Solo es conflicto si el espacio está ocupado por OTRA materia.
    """
    agregadas, conflictos = 0, []
    for dia, h_ini, h_fin, codigo, materia in clases:
        espacio = asegurar_espacio(campus, codigo)
        if espacio is None:
            conflictos.append(f"{codigo}: código no reconocido")
            continue
        f_ini, f_fin = franja(dia, h_ini), franja(dia, h_fin)
        if any(e[0] == f_ini and e[1] == f_fin and e[2] == espacio.id
               and misma_materia(e[3], materia) for e in horarios.get(alias, [])):
            continue                                   # ya la tenía cargada
        mascara = rango(dia, h_ini, h_fin)
        if campus.ocupar(espacio.id, mascara, "clase", materia):
            registro = campus.registro_de(espacio.id, mascara, "clase", materia)
            nombre = registro.detalle if registro else materia   # nombre ya guardado
            horarios.setdefault(alias, []).append([f_ini, f_fin, espacio.id, nombre])
            agregadas += 1
        else:
            choque = _quien_ocupa(campus, espacio.id, dia, h_ini, h_fin)
            conflictos.append(f"{codigo} {NOMBRES_DIAS[dia]} {h_ini}:00-{h_fin}:00 "
                              f"ya está ocupado con «{choque}» y tú cargaste «{materia}»")
    return agregadas, conflictos


def borrar_clase(campus, horarios, alias, indice):
    """Quita la clase número `indice` (0, 1, ...) del horario de `alias`.

    Deshace lo que hizo `aplicar_horario`: si la clase la habían confirmado varias
    personas solo baja el contador; si era la única, el espacio vuelve a quedar
    SIN INFORMACIÓN (no "libre": borrar un horario no demuestra que esté libre).
    Devuelve True si la clase existía.
    """
    clases = horarios.get(alias, [])
    if not 0 <= indice < len(clases):
        return False
    f_ini, f_fin, espacio_id, materia = clases.pop(indice)
    mascara = ((1 << (f_fin - f_ini)) - 1) << f_ini
    r = campus.registro_de(espacio_id, mascara, "clase", materia)
    if r is not None:
        if r.confirmaciones > 1:
            r.confirmaciones -= 1
        else:
            campus.liberar(espacio_id, mascara)
            campus.info[espacio_id] &= ~mascara
    if not clases:
        horarios.pop(alias, None)
    return True


def borrar_horario(campus, horarios, alias):
    """Borra TODAS las clases de `alias`. Devuelve cuántas se borraron."""
    borradas = 0
    while horarios.get(alias):
        borrar_clase(campus, horarios, alias, 0)
        borradas += 1
    return borradas