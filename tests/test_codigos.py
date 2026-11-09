from src import codigos
from src.codigos import parsear_codigo
from src.datos import campus_base
from src.franjas import franja
from src.horario_csv import leer_horario, aplicar_horario
from src.almacen import estudiante_de
from src.consultas import ubicacion_inferida

CSV = """dia,hora_inicio,hora_fin,salon,materia
Martes,9,11,L1-5,
Martes,12,14,SDU9,
Martes,14,16,11J,
Martes,17,18,13G2,
Miércoles,10,12,26J,
Miércoles,14,15,23J,
Miércoles,15,16,17J,
Jueves,9,11,37G2,
Jueves,11,12,22D,
Jueves,12,14,93K,
Viernes,9,11,22J,
Viernes,11,12,36C,
"""


def test_codigos_normales():
    assert parsear_codigo("26J").bloque == "J"
    assert parsear_codigo("93k").bloque == "K"          # minúscula también
    assert parsear_codigo(" 36C ").id == "36C"


def test_bloque_g_tiene_dos_lados():
    assert parsear_codigo("37G2").bloque == "G"
    assert parsear_codigo("13G1").bloque == "G"
    assert parsear_codigo("37G3") is None               # solo lados 1 y 2
    assert parsear_codigo("26J2") is None               # otros bloques no tienen lados


def test_sdu_usa_la_tabla():
    e = parsear_codigo("SDU9")
    assert (e.bloque, e.piso) == ("K", 5)
    assert parsear_codigo("sdu1").bloque == "C"
    assert parsear_codigo("SDU10").piso == 5


def test_laboratorios_de_fisica():
    for codigo in ("L1-5", "L1-4", "L1-3"):
        e = parsear_codigo(codigo)
        assert e.tipo == "laboratorio" and e.bloque == codigos.BLOQUE_LABORATORIOS
    assert parsear_codigo("l1-5").id == "L1-5"          # minúscula también


def test_codigo_raro_se_rechaza_hasta_agregarlo(monkeypatch):
    assert parsear_codigo("X9") is None
    monkeypatch.setitem(codigos.ESPECIALES, "X9", ("B", 0))
    assert parsear_codigo("X9").bloque == "B"


def test_csv_del_horario_real():
    clases, errores = leer_horario(CSV)
    assert len(clases) == 12 and errores == []


def test_csv_con_codigo_desconocido():
    clases, errores = leer_horario(CSV + "Lunes,8,10,ZZ9,\n")
    assert len(clases) == 12
    assert len(errores) == 1 and "ZZ9" in errores[0]


def test_csv_con_punto_y_coma_y_errores():
    texto = "dia;hora_inicio;hora_fin;salon\nLunes;9:00;11:00;26J\nDomingo;9;10;26J\nLunes;11;9;26J\n"
    clases, errores = leer_horario(texto)
    assert len(clases) == 1
    assert len(errores) == 2


def test_csv_sin_columnas():
    clases, errores = leer_horario("a,b\n1,2\n")
    assert clases == [] and "Faltan columnas" in errores[0]


def test_aplicar_horario_sin_duplicar_y_con_conflicto():
    campus, horarios = campus_base(), {}
    clases, _ = leer_horario(CSV)
    agregadas, conflictos = aplicar_horario(campus, horarios, "ana", clases)
    assert agregadas == 12 and conflictos == []
    assert aplicar_horario(campus, horarios, "ana", clases) == (0, [])   # no duplica
    otra = [(2, 10, 12, "26J", "Otra materia")]                          # mismo salón y hora
    agregadas, conflictos = aplicar_horario(campus, horarios, "luis", otra)
    assert agregadas == 0 and len(conflictos) == 1


def test_ubicacion_con_horario_real():
    campus, horarios = campus_base(), {}
    clases, _ = leer_horario(CSV)
    aplicar_horario(campus, horarios, "ana", clases)
    ana = estudiante_de("ana", horarios)
    assert ubicacion_inferida(campus, ana, franja(1, 14)) == "J"   # martes 14:00, en 11J
    assert ubicacion_inferida(campus, ana, franja(1, 12)) == "K"   # martes 12:00, en SDU9


def test_laboratorios_son_un_bloque_propio_dentro_del_grafo():
    campus = campus_base()
    assert campus.espacios["L1-5"].bloque == "LAB"
    assert "K" in campus.distancias_desde("LAB")          # el grafo conecta LAB con el resto


def test_ubicacion_en_laboratorio():
    campus, horarios = campus_base(), {}
    clases, _ = leer_horario(CSV)
    aplicar_horario(campus, horarios, "ana", clases)
    ana = estudiante_de("ana", horarios)
    assert ubicacion_inferida(campus, ana, franja(1, 10)) == "LAB"   # martes 10:00, en L1-5