"""Pruebas de la interfaz con el simulador de Streamlit (AppTest)."""
import datetime as dt
import json
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
OTRO = "__otro__"


def _app(tmp_path, monkeypatch, fin=None):
    monkeypatch.setenv("DATOS_DIR", str(tmp_path))
    if fin:  # forzar un semestre con fecha de fin conocida
        os.makedirs(tmp_path / "semestres", exist_ok=True)
        estado = {"semestre": {"nombre": "2026-2", "fin": fin},
                  "info": {}, "registros": [], "horarios": {}}
        (tmp_path / "semestres" / "2026-2.json").write_text(json.dumps(estado))
        (tmp_path / "activo.json").write_text(json.dumps({"nombre": "2026-2"}))
    return AppTest.from_file(APP, default_timeout=30)


def _futuro():
    return (dt.date.today() + dt.timedelta(days=30)).isoformat()


def _elegir_otro_codigo(at, pref, bloque, codigo):
    """Bloque -> 'Otro (escribir código)' -> código."""
    at.selectbox(key=f"{pref}_bloque").set_value(bloque).run()
    at.selectbox(key=f"{pref}_salon").set_value(OTRO).run()
    at.text_input(key=f"{pref}_codigo").set_value(codigo)


def test_la_app_abre_sin_errores(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    assert not at.exception


def test_ocupar_un_salon_de_la_lista_guarda_y_detecta_conflicto(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    at.selectbox(key="o_bloque").set_value("C").run()
    at.selectbox(key="o_salon").set_value("36C").run()          # salón exacto del bloque C
    at.text_input(key="o_detalle").set_value("Grupo de Fisica")
    at.button(key="o_boton").click().run()
    assert not at.exception
    assert any("quedó ocupado" in s.value for s in at.success)
    guardado = json.loads((tmp_path / "semestres" / "2026-2.json").read_text())
    assert guardado["registros"][0]["espacio_id"] == "36C"
    assert guardado["registros"][0]["detalle"] == "Grupo de Fisica"

    at.text_input(key="o_detalle").set_value("Otro grupo")   # mismo horario -> conflicto
    at.button(key="o_boton").click().run()
    assert any("Conflicto" in e.value for e in at.error)


def test_ocupar_un_salon_que_no_esta_en_la_lista_escribiendo_el_codigo(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    _elegir_otro_codigo(at, "o", "E", "25E")
    at.text_input(key="o_detalle").set_value("Estudio")
    at.button(key="o_boton").click().run()
    assert not at.exception
    guardado = json.loads((tmp_path / "semestres" / "2026-2.json").read_text())
    assert any(e["id"] == "25E" and e["bloque"] == "E" for e in guardado["espacios"])


def test_codigo_desconocido_da_error(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    _elegir_otro_codigo(at, "o", "E", "ZZ9")
    at.text_input(key="o_detalle").set_value("algo")
    at.button(key="o_boton").click().run()
    assert any("no reconocido" in e.value.lower() for e in at.error)


def test_codigo_de_otro_bloque_da_error(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    _elegir_otro_codigo(at, "o", "E", "25J")        # elegí el bloque E pero escribí uno de J
    at.run()
    assert any("es del bloque J" in e.value for e in at.error)


def test_salon_del_bloque_c_que_no_existe_se_rechaza(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    _elegir_otro_codigo(at, "o", "C", "27C")        # el bloque C tiene su lista completa
    at.run()
    assert any("no reconocido" in e.value.lower() for e in at.error)


def test_revisar_un_salon_sin_informacion_no_dice_libre(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    at.selectbox(key="b_bloque").set_value("C").run()
    at.selectbox(key="b_salon").set_value("36C").run()
    assert not at.exception
    assert any("Sin información" in w.value for w in at.warning)
    assert not any("está libre" in s.value for s in at.success)


def test_revisar_un_salon_ocupado_dice_por_que(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    # lunes a las 6:00 (valores por defecto de las dos pantallas): se ocupa 36C 6-7
    at.selectbox(key="o_bloque").set_value("C").run()
    at.selectbox(key="o_salon").set_value("36C").run()
    at.selectbox(key="o_ini").set_value(6).run()
    at.selectbox(key="o_fin").set_value(8).run()
    at.text_input(key="o_detalle").set_value("Calculo II")
    at.button(key="o_boton").click().run()
    at.selectbox(key="b_bloque").set_value("C").run()
    at.selectbox(key="b_salon").set_value("36C").run()
    at.selectbox(key="b_hora").set_value(6).run()
    assert any("está ocupado" in e.value for e in at.error)


def test_semestre_vencido_bloquea_la_app(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin="2020-01-01")
    at.run()
    assert not at.exception
    assert any("terminó" in e.value for e in at.error)
    assert len(at.tabs) == 0          # no se muestran las pestañas normales