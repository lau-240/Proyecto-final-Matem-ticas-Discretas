"""Comparación flexible de materias: la misma clase escrita distinto NO es conflicto."""
from src.campus import misma_materia
from src.datos import campus_base
from src.franjas import franja
from src.horario_csv import aplicar_horario, borrar_clase, borrar_horario


def test_misma_materia_escrita_distinto():
    assert misma_materia("ENERGIA MEDIO AMBIENTE Y SOC", "Energía Medio Ambiente y Sociedad")
    assert misma_materia("Calculo II", "calculo ii")
    assert misma_materia("Estructura de Datos II", "ESTRUCTURA DATOS II")
    assert misma_materia("", "")


def test_materias_distintas_no_se_confunden():
    assert not misma_materia("Estructura de Datos I", "Estructura de Datos II")
    assert not misma_materia("Fisica 1", "Fisica 2")
    assert not misma_materia("Fisica Electricidad", "Fisica Mecanica")
    assert not misma_materia("Grupo de Fisica", "Otro grupo")
    assert not misma_materia("", "Calculo")
    assert not misma_materia("Grupo A", "Grupo B")
    assert not misma_materia("Fisica A", "Fisica B")


def test_misma_clase_de_otro_estudiante_es_confirmacion_no_conflicto():
    campus, horarios = campus_base(), {}
    a = [(1, 17, 18, "13G2", "ENERGIA MEDIO AMBIENTE Y SOC")]
    b = [(1, 17, 18, "13G2", "Energía Medio Ambiente y Sociedad")]
    assert aplicar_horario(campus, horarios, "ana", a) == (1, [])
    assert aplicar_horario(campus, horarios, "luis", b) == (1, [])
    assert len(campus.registros) == 1 and campus.registros[0].confirmaciones == 2
    # luis queda guardado con el nombre que ya tenía el registro
    assert horarios["luis"][0][3] == "ENERGIA MEDIO AMBIENTE Y SOC"


def test_el_mismo_estudiante_no_duplica_si_la_ia_escribe_distinto():
    campus, horarios = campus_base(), {}
    aplicar_horario(campus, horarios, "ana", [(2, 11, 12, "25E", "FISICA ELECTRICIDAD")])
    assert aplicar_horario(campus, horarios, "ana", [(2, 11, 12, "25E", "Fisica electricidad")]) == (0, [])
    assert campus.registros[0].confirmaciones == 1


def test_otra_materia_en_el_mismo_salon_y_hora_si_es_conflicto_y_lo_explica():
    campus, horarios = campus_base(), {}
    aplicar_horario(campus, horarios, "ana", [(2, 11, 12, "25E", "FISICA ELECTRICIDAD")])
    agregadas, conflictos = aplicar_horario(
        campus, horarios, "luis", [(2, 11, 12, "25E", "ECUACIONES DIFERENCIALES")])
    assert agregadas == 0 and len(conflictos) == 1
    assert "FISICA ELECTRICIDAD" in conflictos[0] and "ECUACIONES DIFERENCIALES" in conflictos[0]


def test_borrar_funciona_con_nombres_escritos_distinto():
    campus, horarios = campus_base(), {}
    aplicar_horario(campus, horarios, "ana", [(1, 17, 18, "13G2", "ENERGIA MEDIO AMBIENTE Y SOC")])
    aplicar_horario(campus, horarios, "luis", [(1, 17, 18, "13G2", "Energía Medio Ambiente y Sociedad")])
    borrar_horario(campus, horarios, "ana")
    assert campus.estado("13G2", franja(1, 17)) == "ocupado"      # luis sigue ahí
    borrar_clase(campus, horarios, "luis", 0)
    assert campus.estado("13G2", franja(1, 17)) == "desconocido"