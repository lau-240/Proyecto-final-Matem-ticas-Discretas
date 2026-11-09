from src.consultas import (mas_cercano_libre, ubicacion_inferida, ver_tutorias,
                           libres)
from src.datos import (caso_conocido, campus_completo, ocupacion_verdadera,
                       revelar)
from src.franjas import rango, franja, TODAS
from src.metricas import evaluar


def test_conflicto_con_and():
    campus, _ = caso_conocido()
    assert campus.ocupar("B1", rango(0, 14, 16), "estudio", "Fisica") is True
    assert campus.ocupar("B1", rango(0, 15, 17), "reunion", "Proyecto") is False
    assert campus.ocupar("B1", rango(0, 16, 18), "reunion", "Proyecto") is True


def test_registro_identico_es_confirmacion():
    campus, _ = caso_conocido()
    m = rango(1, 8, 10)
    assert campus.ocupar("B1", m, "clase", "Calculo I")
    assert campus.ocupar("B1", m, "clase", "Calculo I")
    assert len(campus.registros) == 2          # la tutoría + este registro (sin duplicar)
    assert campus.registros[-1].confirmaciones == 2


def test_ubicacion_inferida():
    campus, ana = caso_conocido()
    assert ubicacion_inferida(campus, ana, franja(0, 9)) == "A"   # en clase
    assert ubicacion_inferida(campus, ana, franja(0, 12)) == "A"  # clase que terminó


def test_mas_cercano_libre_conocido():
    campus, ana = caso_conocido()
    pedido = rango(0, 10, 12)
    espacio, minutos = mas_cercano_libre(campus, "A", pedido)
    assert (espacio.id, minutos) == ("B1", 2)


def test_desconocido_se_excluye_salvo_que_se_permita():
    campus, _ = caso_conocido()
    pedido = rango(0, 10, 12)
    espacio, minutos = mas_cercano_libre(campus, "A", pedido, permitir_desconocido=True)
    assert (espacio.id, minutos) == ("A2", 0)


def test_vista_tutorias():
    campus, _ = caso_conocido()
    tut = ver_tutorias(campus)
    assert [t.detalle for t in tut] == ["Calculo II"]


def test_bloque_m_por_tipo():
    campus = campus_completo()
    campus.confirmar("M-piscina", TODAS)
    pedido = rango(0, 10, 12)
    assert [e.id for e in libres(campus, pedido, tipo="piscina")] == ["M-piscina"]
    assert libres(campus, pedido, tipo="cancha_tenis") == []


def test_modelo_3_estados_mejor_que_ingenuo():
    campus = campus_completo()
    verdad = ocupacion_verdadera(campus)
    revelar(campus, verdad, 0.5)
    r = evaluar(campus, verdad)
    assert r["precision_modelo"] == 1.0
    assert r["precision_ingenuo"] < r["precision_modelo"]
