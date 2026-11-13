"""Guardado en disco y ciclo de vida por semestre.

Archivos (dentro de la carpeta base, normalmente `datos/`):
  activo.json                 -> cuál es el semestre vigente
  semestres/<nombre>.json     -> estado del semestre vigente (se reescribe al cambiar)
  archivo/<nombre>.json       -> semestres cerrados que se decidió conservar

Los horarios VENCEN: pasada la fecha de fin del semestre la app deja de mostrar
datos y pide cerrar el semestre (archivar o borrar) y empezar uno nuevo vacío.
"""
import datetime as dt
import json
import os
import shutil
import threading

from .consultas import Estudiante
from . import tiempo
from .datos import campus_base


def _ruta(base, *partes):
    return os.path.join(base, *partes)


def semestre_por_defecto(hoy):
    """Nombre y fecha de fin de EJEMPLO. Ajustar al calendario académico real."""
    periodo = 1 if hoy.month <= 6 else 2
    fin = dt.date(hoy.year, 6 if periodo == 1 else 12, 15)
    return f"{hoy.year}-{periodo}", fin


def _estado_vacio(nombre, fin):
    return {"semestre": {"nombre": nombre, "fin": fin.isoformat()},
            "info": {}, "registros": [], "horarios": {}}


def _escribir(base, estado):
    os.makedirs(_ruta(base, "semestres"), exist_ok=True)
    destino = _ruta(base, "semestres", f"{estado['semestre']['nombre']}.json")
    temporal = destino + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=1)
    os.replace(temporal, destino)   # escritura atómica: no queda a medias


def _marcar_activo(base, nombre):
    with open(_ruta(base, "activo.json"), "w", encoding="utf-8") as f:
        json.dump({"nombre": nombre}, f)


def crear_semestre(base, nombre, fin):
    estado = _estado_vacio(nombre, fin)
    _escribir(base, estado)
    _marcar_activo(base, nombre)
    return estado


# Candado: evita que dos sesiones guarden a la vez y una pise el cambio de la otra.
# (Sirve dentro de un mismo proceso de Streamlit, que es como se ejecuta la app.)
BLOQUEO = threading.RLock()


def cargar_o_crear(base, hoy=None, ahora=None):
    """Devuelve (campus, horarios, semestre). Crea un semestre vacío si no hay.

    Al cargar se borran los usos de una sola vez (estudio, reunión, práctica) que ya
    terminaron. `ahora` solo se pasa en las pruebas."""
    ahora = ahora or tiempo.ahora()
    hoy = hoy or ahora.date()
    os.makedirs(base, exist_ok=True)
    if not os.path.exists(_ruta(base, "activo.json")):
        nombre, fin = semestre_por_defecto(hoy)
        crear_semestre(base, nombre, fin)
    with open(_ruta(base, "activo.json"), encoding="utf-8") as f:
        nombre = json.load(f)["nombre"]
    with open(_ruta(base, "semestres", f"{nombre}.json"), encoding="utf-8") as f:
        estado = json.load(f)
    campus = campus_base()
    campus.importar(estado)
    campus.purgar_vencidos(ahora)
    return campus, estado["horarios"], estado["semestre"]


def guardar_estado(base, campus, horarios, semestre):
    estado = campus.exportar()
    estado["semestre"] = semestre
    estado["horarios"] = horarios
    _escribir(base, estado)


def modificar(base, operacion, hoy=None, ahora=None):
    """Aplica un cambio sobre el estado MÁS RECIENTE y lo guarda, todo bajo el candado.

    `operacion(campus, horarios)` hace el cambio y puede devolver un resultado.
    Devuelve (campus, horarios, semestre, resultado) con el estado ya actualizado.
    Así, si dos estudiantes guardan al mismo tiempo, no se pierde ningún cambio.
    """
    with BLOQUEO:
        campus, horarios, semestre = cargar_o_crear(base, hoy, ahora)
        resultado = operacion(campus, horarios)
        guardar_estado(base, campus, horarios, semestre)
        return campus, horarios, semestre, resultado


def vencido(semestre, hoy=None):
    """True si ya pasó la fecha de fin del semestre."""
    hoy = hoy or tiempo.ahora().date()
    return dt.date.fromisoformat(semestre["fin"]) < hoy


def cerrar_semestre(base, semestre_actual, nuevo_nombre, nuevo_fin, borrar_anterior=True):
    """Cierra el semestre vigente y empieza uno nuevo VACÍO.

    borrar_anterior=True  -> se elimina el archivo (lo más prudente por privacidad)
    borrar_anterior=False -> se mueve a archivo/ para análisis posteriores
    """
    if nuevo_nombre == semestre_actual["nombre"]:
        raise ValueError("El semestre nuevo debe tener un nombre distinto")
    origen = _ruta(base, "semestres", f"{semestre_actual['nombre']}.json")
    if os.path.exists(origen):
        if borrar_anterior:
            os.remove(origen)
        else:
            os.makedirs(_ruta(base, "archivo"), exist_ok=True)
            shutil.move(origen, _ruta(base, "archivo", os.path.basename(origen)))
    return crear_semestre(base, nuevo_nombre, nuevo_fin)


def estudiante_de(alias, horarios):
    """Estudiante (para inferir su ubicación) a partir del horario guardado."""
    clases = [(a, b, esp) for a, b, esp, _ in horarios.get(alias, [])]
    return Estudiante(alias, clases)