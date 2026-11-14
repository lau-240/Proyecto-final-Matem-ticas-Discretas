"""Pruebas de la interfaz con el simulador de Streamlit (AppTest)."""
import datetime as dt
import json
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


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


def test_la_app_abre_sin_errores(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    assert not at.exception


def test_ocupar_por_codigo_guarda_y_detecta_conflicto(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    at.text_input(key="o_esp").set_value("26J")
    at.text_input(key="o_detalle").set_value("Grupo de Fisica")
    at.button(key="o_boton").click().run()
    assert not at.exception
    assert any("quedó ocupado" in s.value for s in at.success)
    guardado = json.loads((tmp_path / "semestres" / "2026-2.json").read_text())
    assert guardado["registros"][0]["detalle"] == "Grupo de Fisica"
    assert any(e["id"] == "26J" for e in guardado["espacios"])

    at.text_input(key="o_detalle").set_value("Otro grupo")   # mismo horario -> conflicto
    at.button(key="o_boton").click().run()
    assert any("Conflicto" in e.value for e in at.error)


def test_codigo_desconocido_da_error(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    at.text_input(key="o_esp").set_value("ZZ9")
    at.text_input(key="o_detalle").set_value("algo")
    at.button(key="o_boton").click().run()
    assert any("no reconocido" in e.value for e in at.error)


def test_semestre_vencido_bloquea_la_app(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin="2020-01-01")
    at.run()
    assert not at.exception
    assert any("terminó" in e.value for e in at.error)
    assert len(at.tabs) == 0          # no se muestran las pestañas normales