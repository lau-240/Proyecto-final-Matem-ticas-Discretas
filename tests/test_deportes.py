"""Si el horario dice un deporte, se asume que es en las canchas del bloque M."""
from src.codigos import parsear_codigo
from src.datos import campus_base
from src.horario_csv import aplicar_horario, espacio_deportivo, leer_horario
from src.lector_imagen import construir_prompt

ENC = "dia,hora_inicio,hora_fin,salon,materia\n"


def test_espacio_deportivo():
    assert espacio_deportivo("Tenis") == "M-tenis"
    assert espacio_deportivo("FÚTBOL sala") == "M-futbol"
    assert espacio_deportivo("Microfútbol") == "M-futbol"
    assert espacio_deportivo("Natación") == "M-piscina"
    assert espacio_deportivo("Tenis de mesa") is None
    assert espacio_deportivo("Calculo II") is None


def test_deporte_sin_codigo_de_salon_va_a_su_cancha():
    clases, errores = leer_horario(ENC + "Lunes,16,18,,Tenis\n"
                                         "Martes,10,12,CANCHA,Fútbol\n"
                                         "Jueves,8,10,,Natación\n")
    assert errores == []
    assert [(c[3], c[4]) for c in clases] == [("M-tenis", "Tenis"), ("M-futbol", "Fútbol"),
                                              ("M-piscina", "Natación")]


def test_si_el_deporte_viene_en_la_columna_del_salon():
    clases, errores = leer_horario(ENC + "Lunes,16,18,TENIS,\n")
    assert errores == [] and clases == [(0, 16, 18, "M-tenis", "TENIS")]


def test_si_hay_codigo_valido_se_respeta():
    clases, errores = leer_horario(ENC + "Lunes,16,18,26J,Tenis\n")
    assert errores == [] and clases[0][3] == "26J"


def test_sin_deporte_un_codigo_raro_sigue_siendo_error():
    _, errores = leer_horario(ENC + "Lunes,9,11,ZZ9,Calculo\nLunes,12,14,,Tenis de mesa\n")
    assert len(errores) == 2


def test_se_guarda_en_la_cancha_del_campus():
    campus, horarios = campus_base(), {}
    clases, _ = leer_horario(ENC + "Lunes,16,18,,Tenis\n")
    assert aplicar_horario(campus, horarios, "ana", clases) == (1, [])
    assert campus.espacios["M-tenis"].tipo == "cancha_tenis"
    assert campus.registros[0].espacio_id == "M-tenis"


def test_codigos_del_bloque_m_se_reconocen():
    assert parsear_codigo("m-tenis").id == "M-tenis"
    assert parsear_codigo("M-piscina").tipo == "piscina"


def test_la_instruccion_de_la_ia_menciona_los_deportes():
    assert "deportiva" in construir_prompt()