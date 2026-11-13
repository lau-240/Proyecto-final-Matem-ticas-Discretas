"""Hora y fecha de Colombia, y cuándo termina la próxima vez que ocurre una franja.

Se usa la hora de Colombia aunque el computador o el servidor estén en otra zona,
para que "ahora" y los vencimientos no se corran varias horas.
"""
import datetime as dt

from .franjas import H_INI, N_HORAS

try:
    from zoneinfo import ZoneInfo
    _ZONA = ZoneInfo("America/Bogota")
except Exception:          # en Windows hace falta `pip install tzdata`; si no, hora local
    _ZONA = None


def ahora():
    """Fecha y hora actuales en Colombia (sin zona horaria)."""
    if _ZONA is None:
        return dt.datetime.now()
    return dt.datetime.now(_ZONA).replace(tzinfo=None, microsecond=0)


def fin_de_la_proxima_vez(mascara, desde):
    """Fecha y hora en que termina la PRÓXIMA vez que ocurre la franja (la última de la
    máscara), contando desde `desde`. Ej.: franja martes 14-16 declarada el martes a las
    15:00 -> hoy a las 16:00; declarada el martes a las 17:00 -> el martes siguiente."""
    dia, h = divmod(mascara.bit_length() - 1, N_HORAS)
    hora_fin = h + H_INI + 1
    fecha = desde.date() + dt.timedelta(days=(dia - desde.weekday()) % 7)
    fin = dt.datetime.combine(fecha, dt.time(hora_fin))
    if fin <= desde:
        fin += dt.timedelta(days=7)
    return fin