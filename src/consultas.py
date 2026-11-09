"""Consultas: espacios libres, más cercano, tutorías y ubicación inferida."""
import re
from dataclasses import dataclass, field

from .franjas import contar


@dataclass
class Estudiante:
    id: str
    # lista de (franja_inicio, franja_fin_excluida, espacio_id)
    clases: list = field(default_factory=list)


def esta_libre(campus, espacio_id, mascara, permitir_desconocido=False):
    """True si el espacio está libre en TODAS las franjas de la máscara.

    - sin choque con lo ocupado:  ocupado AND mascara == 0
    - con información suficiente: info AND mascara == mascara
    """
    if campus.ocupado[espacio_id] & mascara:
        return False
    if permitir_desconocido:
        return True
    return (campus.info[espacio_id] & mascara) == mascara


def _clave_natural(texto):
    """Orden natural: 13C, 14C, 22C ... 38C, A1C (números primero, bien ordenados)."""
    return [(0, int(p), "") if p.isdigit() else (1, 0, p.lower())
            for p in re.split(r"(\d+)", texto) if p]


def ids_de_bloque(campus, bloque):
    """Ids de todos los espacios de un bloque, en orden natural."""
    return sorted((e.id for e in campus.espacios.values() if e.bloque == bloque),
                  key=_clave_natural)


def estado_en_ventana(campus, espacio_id, mascara):
    """Estado de un espacio durante TODAS las franjas de `mascara`.

    Devuelve (estado, registros):
      'ocupado'     -> alguna franja está ocupada; registros = lo que la ocupa
      'libre'       -> todas las franjas tienen información y ninguna está ocupada
      'parcial'     -> ninguna ocupada, pero hay franjas sin información
      'desconocido' -> no hay información de ninguna de las franjas
    """
    if campus.ocupado[espacio_id] & mascara:
        registros = [r for r in campus.registros
                     if r.espacio_id == espacio_id and r.mascara & mascara]
        return "ocupado", registros
    conocido = campus.info[espacio_id] & mascara
    if conocido == mascara:
        return "libre", []
    return ("parcial" if conocido else "desconocido"), []


def libres(campus, mascara, tipo=None, bloque=None, permitir_desconocido=False):
    """Espacios libres durante todas las franjas de `mascara`."""
    resultado = []
    for e in campus.espacios.values():
        if tipo and e.tipo != tipo:
            continue
        if bloque and e.bloque != bloque:
            continue
        if esta_libre(campus, e.id, mascara, permitir_desconocido):
            resultado.append(e)
    return resultado


def ranking_cercanos(campus, origen, mascara, tipo=None, permitir_desconocido=False):
    """Espacios libres ordenados por minutos de caminata desde el bloque origen."""
    dist = campus.distancias_desde(origen)
    lista = []
    for e in libres(campus, mascara, tipo, None, permitir_desconocido):
        if e.bloque in dist:
            lista.append((dist[e.bloque], e.id, e))
    lista.sort(key=lambda t: (t[0], t[1]))
    return [(e, minutos) for minutos, _, e in lista]


def mas_cercano_libre(campus, origen, mascara, tipo=None, permitir_desconocido=False):
    """(espacio, minutos) del espacio libre más cercano, o None si no hay."""
    ranking = ranking_cercanos(campus, origen, mascara, tipo, permitir_desconocido)
    return ranking[0] if ranking else None


def ver_tutorias(campus, mascara=None):
    """Registros de tutorías (opcionalmente solo los que tocan `mascara`)."""
    return [r for r in campus.registros
            if r.motivo == "tutoria" and (mascara is None or r.mascara & mascara)]


def ubicacion_inferida(campus, estudiante, franja):
    """Bloque donde probablemente está el estudiante en `franja`.

    1) si está en clase -> bloque de esa clase
    2) si no, bloque de la última clase que terminó antes
    3) si no, bloque de la próxima clase
    4) si no hay horario -> None (la persona debe indicarlo a mano)
    """
    ini_fin = estudiante.clases
    for f_ini, f_fin, esp in ini_fin:
        if f_ini <= franja < f_fin:
            return campus.espacios[esp].bloque
    anteriores = [(f_fin, esp) for f_ini, f_fin, esp in ini_fin if f_fin <= franja]
    if anteriores:
        return campus.espacios[max(anteriores)[1]].bloque
    siguientes = [(f_ini, esp) for f_ini, f_fin, esp in ini_fin if f_ini > franja]
    if siguientes:
        return campus.espacios[min(siguientes)[1]].bloque
    return None


def cargar_horario(campus, estudiante, detalles=None):
    """Registra las clases de un estudiante. `detalles` mapea espacio->texto."""
    for f_ini, f_fin, esp in estudiante.clases:
        mascara = ((1 << (f_fin - f_ini)) - 1) << f_ini
        detalle = (detalles or {}).get((f_ini, esp), "clase")
        campus.ocupar(esp, mascara, "clase", detalle)


def cobertura(campus, mascara):
    """Fracción de pares (espacio, franja) con información, dentro de `mascara`."""
    total = len(campus.espacios) * contar(mascara)
    if total == 0:
        return 0.0
    conocidos = sum(contar(campus.info[e] & mascara) for e in campus.espacios)
    return conocidos / total