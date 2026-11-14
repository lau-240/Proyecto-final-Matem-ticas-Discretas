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

from .consultas import Estudiante
from .datos import campus_base
from .codigos import asegurar_espacio

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


def cargar_o_crear(base, hoy=None):
    """Devuelve (campus, horarios, semestre). Crea un semestre vacío si no hay."""
    hoy = hoy or dt.date.today()
    os.makedirs(base, exist_ok=True)
    if not os.path.exists(_ruta(base, "activo.json")):
        nombre, fin = semestre_por_defecto(hoy)
        crear_semestre(base, nombre, fin)
    with open(_ruta(base, "activo.json"), encoding="utf-8") as f:
        nombre = json.load(f)["nombre"]
    with open(_ruta(base, "semestres", f"{nombre}.json"), encoding="utf-8") as f:
        estado = json.load(f)
        campus = campus_base()
    for id_espacio in estado.get("espacios_extra", []):
        asegurar_espacio(campus, id_espacio)
    campus.importar(estado)
    return campus, estado["horarios"], estado["semestre"]


def guardar_estado(base, campus, horarios, semestre):
    estado = campus.exportar()
    estado["semestre"] = semestre
    estado["horarios"] = horarios
    base_ids = set(campus_base().espacios)
    estado["espacios_extra"] = [i for i in campus.espacios if i not in base_ids]
    _escribir(base, estado)


def vencido(semestre, hoy=None):
    """True si ya pasó la fecha de fin del semestre."""
    hoy = hoy or dt.date.today()
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