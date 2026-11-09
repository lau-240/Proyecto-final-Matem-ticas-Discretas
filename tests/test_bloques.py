"""Catálogo de salones por bloque y consulta del estado de un salón."""
from src.codigos import SALONES_CATALOGO, parsear_codigo
from src.consultas import estado_en_ventana, ids_de_bloque
from src.datos import campus_base
from src.franjas import rango

SALONES_C = ["13C", "14C", "22C", "23C", "24C", "25C", "26C",
             "31C", "32C", "33C", "34C", "35C", "36C", "37C", "38C", "A1C"]


def test_bloque_c_tiene_exactamente_sus_salones():
    for codigo in SALONES_C:
        assert parsear_codigo(codigo).bloque == "C"
    assert parsear_codigo("a1c").bloque == "C"               # minúscula también
    assert sum(1 for b in SALONES_CATALOGO.values() if b == "C") == 16


def test_un_salon_que_no_esta_en_el_bloque_c_se_rechaza():
    for codigo in ("27C", "21C", "39C", "12C", "B1C"):
        assert parsear_codigo(codigo) is None


def test_bloque_b_no_esta_completo_acepta_otros_salones():
    assert parsear_codigo("32B").bloque == "B" and parsear_codigo("33B").bloque == "B"
    assert parsear_codigo("35B").bloque == "B"               # B aún tiene salones por confirmar


def test_lista_de_salones_por_bloque_en_orden_natural():
    campus = campus_base()
    assert ids_de_bloque(campus, "C") == SALONES_C + ["SDU1"]
    assert ids_de_bloque(campus, "B") == ["32B", "33B", "SDU2", "SDU3", "SDU5"]
    assert ids_de_bloque(campus, "A") == []                  # aún no hay salones confirmados
    assert ids_de_bloque(campus, "LAB") == ["L1-3", "L1-4", "L1-5"]
    assert "M-tenis" in ids_de_bloque(campus, "M") and "M-piscina" in ids_de_bloque(campus, "M")


def test_estado_de_un_salon_en_una_ventana():
    campus = campus_base()
    ventana = rango(0, 10, 12)
    assert estado_en_ventana(campus, "36C", ventana) == ("desconocido", [])   # nadie lo ha cargado
    campus.confirmar("36C", rango(0, 10, 11))
    assert estado_en_ventana(campus, "36C", ventana)[0] == "parcial"          # solo una hora conocida
    campus.confirmar("36C", ventana)
    assert estado_en_ventana(campus, "36C", ventana) == ("libre", [])
    campus.ocupar("36C", rango(0, 11, 12), "tutoria", "Algebra Lineal")
    estado, registros = estado_en_ventana(campus, "36C", ventana)
    assert estado == "ocupado" and registros[0].detalle == "Algebra Lineal"