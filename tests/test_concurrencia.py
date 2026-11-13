"""Dos sesiones guardando al mismo tiempo no deben pisarse."""
import datetime as dt
import threading

from src import almacen
from src.horario_csv import aplicar_horario

HOY = dt.date(2026, 11, 9)


def _estudiante(i):
    dia, hora = divmod(i, 14)
    return f"2002{i:05d}", [(dia % 6, 6 + hora, 7 + hora, f"{20 + i % 9}J", f"Materia {i}")]


def test_muchas_sesiones_guardando_a_la_vez_no_pierden_cambios(tmp_path):
    base = str(tmp_path)
    almacen.cargar_o_crear(base, hoy=HOY)                 # crea el semestre vacío
    n = 24
    errores = []

    def sesion(i):
        alias, clases = _estudiante(i)
        try:
            almacen.modificar(base, lambda c, h: aplicar_horario(c, h, alias, clases), hoy=HOY)
        except Exception as e:                            # pragma: no cover
            errores.append(e)

    hilos = [threading.Thread(target=sesion, args=(i,)) for i in range(n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert errores == []
    _, horarios, _ = almacen.cargar_o_crear(base, hoy=HOY)
    assert len(horarios) == n                             # ningún estudiante se perdió


def test_modificar_devuelve_el_estado_actualizado_y_el_resultado(tmp_path):
    base = str(tmp_path)
    campus, horarios, sem, resultado = almacen.modificar(
        base, lambda c, h: aplicar_horario(c, h, "ana", [(1, 9, 11, "26J", "Calculo II")]), hoy=HOY)
    assert resultado == (1, [])
    assert "ana" in horarios and "26J" in campus.espacios
    _, horarios2, _ = almacen.cargar_o_crear(base, hoy=HOY)
    assert "ana" in horarios2