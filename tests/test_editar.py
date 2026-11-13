"""Corregir una clase ya cargada, sin volver a subir todo el horario."""
from src.datos import campus_base
from src.franjas import franja, rango
from src.horario_csv import actualizar_clase, aplicar_horario


def _ana():
    campus, horarios = campus_base(), {}
    aplicar_horario(campus, horarios, "ana", [
        (1, 9, 11, "26J", "Calculo II"),          # martes 9-11
        (3, 14, 16, "SDU9", "Fisica")])           # jueves 14-16
    return campus, horarios


def test_cambiar_de_salon_libera_el_viejo_y_ocupa_el_nuevo():
    campus, horarios = _ana()
    assert actualizar_clase(campus, horarios, "ana", 0, 1, 9, 11, "25J", "Calculo II") == (True, "")
    assert campus.estado("25J", franja(1, 9)) == "ocupado"
    assert campus.estado("26J", franja(1, 9)) == "desconocido"      # no se afirma que esté libre
    assert horarios["ana"][0] == [franja(1, 9), franja(1, 11), "25J", "Calculo II"]


def test_cambiar_dia_y_horas():
    campus, horarios = _ana()
    ok, _ = actualizar_clase(campus, horarios, "ana", 1, 4, 8, 10, "SDU9", "Fisica")
    assert ok
    assert campus.estado("SDU9", franja(4, 8)) == "ocupado"
    assert campus.estado("SDU9", franja(3, 14)) == "desconocido"
    assert horarios["ana"][1] == [franja(4, 8), franja(4, 10), "SDU9", "Fisica"]


def test_corregir_el_nombre_de_la_materia():
    campus, horarios = _ana()
    ok, _ = actualizar_clase(campus, horarios, "ana", 0, 1, 9, 11, "26J", "Cálculo Diferencial")
    assert ok
    assert horarios["ana"][0][3] == "Cálculo Diferencial"
    assert campus.que_hay("26J", franja(1, 9)).detalle == "Cálculo Diferencial"
    assert len(campus.registros) == 2                               # no quedó un registro viejo


def test_sin_cambios_no_toca_nada():
    campus, horarios = _ana()
    antes = [list(c) for c in horarios["ana"]]
    assert actualizar_clase(campus, horarios, "ana", 0, 1, 9, 11, "26J", "Calculo II") == (True, "")
    assert horarios["ana"] == antes and len(campus.registros) == 2


def test_conflicto_con_otra_materia_deja_la_clase_original_intacta():
    campus, horarios = _ana()
    aplicar_horario(campus, horarios, "luis", [(1, 9, 11, "25J", "Ecuaciones Diferenciales")])
    ok, motivo = actualizar_clase(campus, horarios, "ana", 0, 1, 9, 11, "25J", "Calculo II")
    assert not ok and "Ecuaciones Diferenciales" in motivo
    assert horarios["ana"][0] == [franja(1, 9), franja(1, 11), "26J", "Calculo II"]   # misma posición
    assert campus.estado("26J", franja(1, 9)) == "ocupado"
    assert campus.estado("25J", franja(1, 9)) == "ocupado"          # sigue siendo de luis
    assert campus.que_hay("25J", franja(1, 9)).detalle == "Ecuaciones Diferenciales"


def test_no_se_puede_dejar_dos_clases_iguales():
    campus, horarios = _ana()
    ok, motivo = actualizar_clase(campus, horarios, "ana", 0, 3, 14, 16, "SDU9", "Fisica")
    assert not ok and "igual" in motivo
    assert len(horarios["ana"]) == 2
    assert horarios["ana"][0] == [franja(1, 9), franja(1, 11), "26J", "Calculo II"]


def test_codigo_o_horas_invalidos_no_cambian_nada():
    campus, horarios = _ana()
    antes = [list(c) for c in horarios["ana"]]
    assert not actualizar_clase(campus, horarios, "ana", 0, 1, 9, 11, "ZZ9", "x")[0]
    assert not actualizar_clase(campus, horarios, "ana", 0, 1, 11, 9, "26J", "x")[0]
    assert not actualizar_clase(campus, horarios, "ana", 0, 1, 5, 7, "26J", "x")[0]
    assert not actualizar_clase(campus, horarios, "ana", 9, 1, 9, 11, "26J", "x")[0]   # no existe la clase 9
    assert not actualizar_clase(campus, horarios, "nadie", 0, 1, 9, 11, "26J", "x")[0]
    assert horarios["ana"] == antes and len(campus.registros) == 2


def test_clase_compartida_el_otro_estudiante_no_pierde_la_suya():
    campus, horarios = campus_base(), {}
    aplicar_horario(campus, horarios, "ana", [(1, 9, 11, "26J", "Calculo II")])
    aplicar_horario(campus, horarios, "luis", [(1, 9, 11, "26J", "Calculo II")])
    assert campus.registros[0].confirmaciones == 2
    assert actualizar_clase(campus, horarios, "ana", 0, 1, 9, 11, "25J", "Calculo II")[0]
    assert campus.estado("26J", franja(1, 9)) == "ocupado"          # luis sigue ahí
    assert campus.registros[0].confirmaciones == 1
    assert campus.estado("25J", franja(1, 9)) == "ocupado"