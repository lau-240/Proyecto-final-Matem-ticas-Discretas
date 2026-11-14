"""Carga de horarios desde un CSV.

Columnas:  dia, hora_inicio, hora_fin, salon, materia   (materia es opcional)
Ejemplo:   Martes,9,11,26J,Calculo II
Acepta coma o punto y coma (Excel en español). Días: Lunes ... Sábado.
"""
import csv
import io
import unicodedata

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
        codigo = normalizar(valor(fila, "salon"))
        if not codigo_conocido(codigo, campus):
            errores.append(f"Fila {n}: salón '{codigo}' no reconocido. Si es un código "
                           "especial, agréguenlo en ESPECIALES de src/codigos.py.")
            continue
        materia = valor(fila, "materia") or valor(fila, "detalle") or f"Clase en {codigo}"
        clases.append((dia, h_ini, h_fin, codigo, materia))
    return clases, errores


def aplicar_horario(campus, horarios, alias, clases):
    """Registra las clases. Devuelve (agregadas, conflictos).

    Una clase que ya estaba cargada por el mismo alias se omite (no duplica
    confirmaciones). Si otra persona ocupa ese espacio con otra cosa, es conflicto.
    """
    agregadas, conflictos = 0, []
    for dia, h_ini, h_fin, codigo, materia in clases:
        espacio = asegurar_espacio(campus, codigo)
        if espacio is None:
            conflictos.append(f"{codigo}: código no reconocido")
            continue
        entrada = [franja(dia, h_ini), franja(dia, h_fin), espacio.id, materia]
        if entrada in horarios.get(alias, []):
            continue
        if campus.ocupar(espacio.id, rango(dia, h_ini, h_fin), "clase", materia):
            horarios.setdefault(alias, []).append(entrada)
            agregadas += 1
        else:
            conflictos.append(f"{codigo} {NOMBRES_DIAS[dia]} {h_ini}:00-{h_fin}:00 "
                              "ya está ocupado con otra cosa")
    return agregadas, conflictos