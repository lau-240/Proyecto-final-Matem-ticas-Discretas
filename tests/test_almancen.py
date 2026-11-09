import datetime as dt
import os

import pytest

from src import almacen
from src.codigos import asegurar_espacio
from src.franjas import rango, franja


def test_guardar_y_cargar(tmp_path):
    base = str(tmp_path)
    campus, horarios, sem = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    assert campus.ocupar("SDU9", rango(0, 8, 10), "clase", "Calculo I")
    horarios["ana"] = [[franja(0, 8), franja(0, 10), "SDU9", "Calculo I"]]
    almacen.guardar_estado(base, campus, horarios, sem)

    campus2, horarios2, sem2 = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    assert campus2.ocupado["SDU9"] == rango(0, 8, 10)
    assert campus2.estado("SDU9", franja(0, 8)) == "ocupado"
    assert campus2.que_hay("SDU9", franja(0, 9)).detalle == "Calculo I"
    assert horarios2["ana"][0][2] == "SDU9"
    assert sem2["nombre"] == sem["nombre"]


def test_espacios_creados_por_codigo_se_guardan(tmp_path):
    base = str(tmp_path)
    campus, horarios, sem = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    espacio = asegurar_espacio(campus, "26J")
    assert espacio.bloque == "J"
    campus.ocupar("26J", rango(2, 10, 12), "clase", "Algebra")
    almacen.guardar_estado(base, campus, horarios, sem)

    campus2, _, _ = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    assert "26J" in campus2.espacios and campus2.espacios["26J"].bloque == "J"
    assert campus2.estado("26J", franja(2, 10)) == "ocupado"


def test_semestre_vence():
    sem = {"nombre": "2026-2", "fin": "2026-12-15"}
    assert not almacen.vencido(sem, dt.date(2026, 12, 15))   # último día: aún vale
    assert almacen.vencido(sem, dt.date(2026, 12, 16))


def test_cerrar_semestre_borra_y_empieza_vacio(tmp_path):
    base = str(tmp_path)
    campus, horarios, sem = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    campus.ocupar("SDU2", rango(1, 9, 11), "tutoria", "Algebra")
    almacen.guardar_estado(base, campus, horarios, sem)
    almacen.cerrar_semestre(base, sem, "2027-1", dt.date(2027, 6, 15), borrar_anterior=True)

    assert not os.path.exists(os.path.join(base, "semestres", f"{sem['nombre']}.json"))
    campus2, horarios2, sem2 = almacen.cargar_o_crear(base, hoy=dt.date(2027, 2, 1))
    assert sem2["nombre"] == "2027-1"
    assert campus2.registros == [] and horarios2 == {}


def test_cerrar_semestre_archivando(tmp_path):
    base = str(tmp_path)
    campus, horarios, sem = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    almacen.guardar_estado(base, campus, horarios, sem)
    almacen.cerrar_semestre(base, sem, "2027-1", dt.date(2027, 6, 15), borrar_anterior=False)
    assert os.path.exists(os.path.join(base, "archivo", f"{sem['nombre']}.json"))


def test_no_se_puede_reusar_el_nombre(tmp_path):
    base = str(tmp_path)
    _, _, sem = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 8))
    with pytest.raises(ValueError):
        almacen.cerrar_semestre(base, sem, sem["nombre"], dt.date(2027, 1, 1))