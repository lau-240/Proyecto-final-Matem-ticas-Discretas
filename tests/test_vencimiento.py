"""Los usos de una sola vez (estudio, reunión, práctica) vencen; clases y tutorías no."""
import datetime as dt
import json
import os

from src import almacen
from src.datos import campus_base
from src.franjas import franja, rango
from src.tiempo import fin_de_la_proxima_vez

MARTES_1415 = rango(1, 14, 16)                       # martes 14:00-16:00
LUNES = dt.datetime(2026, 11, 9, 8, 0)               # lunes 9 de noviembre de 2026
MARTES = dt.date(2026, 11, 10)


def _a(dia, hora, minuto=0):
    return dt.datetime.combine(dia, dt.time(hora, minuto))


def test_fin_de_la_proxima_vez():
    assert fin_de_la_proxima_vez(MARTES_1415, LUNES) == _a(MARTES, 16)                      # mañana
    assert fin_de_la_proxima_vez(MARTES_1415, _a(MARTES, 15)) == _a(MARTES, 16)             # está pasando ahora
    assert fin_de_la_proxima_vez(MARTES_1415, _a(MARTES, 17)) == _a(MARTES + dt.timedelta(7), 16)
    assert fin_de_la_proxima_vez(MARTES_1415, _a(MARTES, 16)) == _a(MARTES + dt.timedelta(7), 16)
    assert fin_de_la_proxima_vez(MARTES_1415, _a(dt.date(2026, 11, 11), 9)) == \
        _a(MARTES + dt.timedelta(7), 16)                                                    # miércoles


def test_solo_los_usos_de_una_vez_llevan_vencimiento():
    campus = campus_base()
    assert campus.ocupar("36C", MARTES_1415, "estudio", "Grupo de Fisica", ahora=LUNES)
    assert campus.ocupar("32C", MARTES_1415, "reunion", "Proyecto", ahora=LUNES)
    assert campus.ocupar("33C", MARTES_1415, "practica", "Coro", ahora=LUNES)
    assert campus.ocupar("34C", MARTES_1415, "tutoria", "Algebra", ahora=LUNES)
    assert campus.ocupar("35C", MARTES_1415, "clase", "Calculo", ahora=LUNES)
    vence = {r.espacio_id: r.vence for r in campus.registros}
    assert vence["36C"] == vence["32C"] == vence["33C"] == "2026-11-10T16:00:00"
    assert vence["34C"] == "" and vence["35C"] == ""


def test_al_vencer_el_espacio_queda_sin_informacion_no_libre():
    campus = campus_base()
    campus.ocupar("36C", MARTES_1415, "estudio", "Grupo de Fisica", ahora=LUNES)
    assert campus.purgar_vencidos(_a(MARTES, 15, 59)) == 0
    assert campus.estado("36C", franja(1, 14)) == "ocupado"
    assert campus.purgar_vencidos(_a(MARTES, 16)) == 1
    assert campus.estado("36C", franja(1, 14)) == "desconocido"
    assert campus.registros == []


def test_las_clases_y_tutorias_nunca_se_purgan():
    campus = campus_base()
    campus.ocupar("35C", MARTES_1415, "clase", "Calculo", ahora=LUNES)
    campus.ocupar("34C", MARTES_1415, "tutoria", "Algebra", ahora=LUNES)
    assert campus.purgar_vencidos(dt.datetime(2030, 1, 1)) == 0
    assert len(campus.registros) == 2


def test_se_puede_volver_a_ocupar_despues_de_que_vence():
    campus = campus_base()
    campus.ocupar("36C", MARTES_1415, "estudio", "Grupo A", ahora=LUNES)
    assert not campus.ocupar("36C", MARTES_1415, "estudio", "Grupo B", ahora=LUNES)   # aún está ocupado
    campus.purgar_vencidos(_a(MARTES, 16))
    assert campus.ocupar("36C", MARTES_1415, "estudio", "Grupo B", ahora=_a(MARTES, 16))


def _guardar_con_estudio(tmp_path):
    base = str(tmp_path)
    campus, horarios, sem = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 9), ahora=LUNES)
    campus.ocupar("36C", MARTES_1415, "estudio", "Grupo de Fisica", ahora=LUNES)
    campus.ocupar("35C", MARTES_1415, "clase", "Calculo", ahora=LUNES)
    almacen.guardar_estado(base, campus, horarios, sem)
    return base


def test_al_cargar_se_borran_los_vencidos_y_se_conservan_los_vigentes(tmp_path):
    base = _guardar_con_estudio(tmp_path)
    antes, _, _ = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 9), ahora=_a(MARTES, 15))
    assert {r.espacio_id for r in antes.registros} == {"36C", "35C"}
    despues, _, _ = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 9), ahora=_a(MARTES, 17))
    assert {r.espacio_id for r in despues.registros} == {"35C"}
    assert despues.estado("36C", franja(1, 14)) == "desconocido"


def test_datos_guardados_antes_de_este_cambio_se_cargan_igual(tmp_path):
    base = _guardar_con_estudio(tmp_path)
    ruta = os.path.join(base, "semestres", "2026-2.json")
    estado = json.load(open(ruta, encoding="utf-8"))
    for r in estado["registros"]:
        r.pop("vence")                                  # como se guardaba antes
    json.dump(estado, open(ruta, "w", encoding="utf-8"))
    campus, _, _ = almacen.cargar_o_crear(base, hoy=dt.date(2026, 11, 9), ahora=_a(MARTES, 17))
    assert len(campus.registros) == 2                    # sin vencimiento: se conservan