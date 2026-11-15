"""Pruebas de la interfaz con el simulador de Streamlit (AppTest)."""
import datetime as dt
import json
import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
OTRO = "__otro__"


def _lunes_6_30():
    """Lunes de esta semana a las 6:30: hora fija para que las pruebas no dependan del reloj."""
    hoy = dt.date.today()
    return dt.datetime.combine(hoy - dt.timedelta(days=hoy.weekday()), dt.time(6, 30))


def _app(tmp_path, monkeypatch, fin=None, ahora=None):
    ahora = ahora or _lunes_6_30()
    monkeypatch.setattr("src.tiempo.ahora", lambda: ahora)
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


def test_sin_clave_admin_no_se_puede_cerrar_semestre(tmp_path, monkeypatch):
    monkeypatch.delenv("CLAVE_ADMIN", raising=False)
    at = _app(tmp_path, monkeypatch, fin="2020-01-01")
    at.run()
    assert not at.exception
    assert any("No hay clave de administrador" in w.value for w in at.warning)
    assert not [t for t in at.text_input if t.key == "s_clave"]


def test_clave_admin_incorrecta_y_correcta(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAVE_ADMIN", "clave-de-prueba")
    at = _app(tmp_path, monkeypatch, fin="2020-01-01")
    at.run()
    at.text_input(key="s_clave").set_value("otra").run()
    assert any("Clave incorrecta" in e.value for e in at.error)
    assert not [t for t in at.text_input if t.key == "s_nuevo"]
    at.text_input(key="s_clave").set_value("clave-de-prueba").run()
    assert not at.exception
    assert [t for t in at.text_input if t.key == "s_nuevo"]


def _app_con_horario(tmp_path, monkeypatch):
    """App con un semestre vigente y el horario de 'ana1' ya guardado."""
    from src import almacen
    from src.horario_csv import aplicar_horario
    _app(tmp_path, monkeypatch, fin=_futuro())
    campus, horarios, sem = almacen.cargar_o_crear(str(tmp_path))
    aplicar_horario(campus, horarios, "ana1", [(1, 9, 11, "26J", "Calculo II"),
                                               (3, 14, 16, "SDU9", "Fisica")])
    almacen.guardar_estado(str(tmp_path), campus, horarios, sem)
    return AppTest.from_file(APP, default_timeout=30)


def _guardado(tmp_path):
    return json.loads((tmp_path / "semestres" / "2026-2.json").read_text())


def test_mi_horario_codigo_que_no_existe_avisa(tmp_path, monkeypatch):
    at = _app_con_horario(tmp_path, monkeypatch)
    at.run()
    at.text_input(key="m_alias").set_value("nadie").run()
    assert any("No hay un horario cargado" in w.value for w in at.warning)


def test_mi_horario_corregir_el_nombre_de_una_clase(tmp_path, monkeypatch):
    at = _app_con_horario(tmp_path, monkeypatch)
    at.run()
    at.text_input(key="m_alias").set_value("ana1").run()
    assert not at.exception
    assert at.text_input(key="m_materia").value == "Calculo II"      # muestra los datos actuales
    at.text_input(key="m_materia").set_value("Calculo Diferencial")
    at.button(key="m_guardar").click().run()
    assert not at.exception
    assert any("actualizada" in s.value for s in at.success)
    assert _guardado(tmp_path)["horarios"]["ana1"][0][3] == "Calculo Diferencial"


def test_mi_horario_cambiar_una_clase_de_salon(tmp_path, monkeypatch):
    at = _app_con_horario(tmp_path, monkeypatch)
    at.run()
    at.text_input(key="m_alias").set_value("ana1").run()
    _elegir_otro_codigo(at, "m", "E", "25E")                          # bloque E, salón 25E
    at.button(key="m_guardar").click().run()
    assert not at.exception
    guardado = _guardado(tmp_path)
    assert guardado["horarios"]["ana1"][0][2] == "25E"
    assert [r["espacio_id"] for r in guardado["registros"]].count("26J") == 0


def test_mi_horario_borrar_una_clase_y_luego_todo(tmp_path, monkeypatch):
    at = _app_con_horario(tmp_path, monkeypatch)
    at.run()
    at.text_input(key="m_alias").set_value("ana1").run()
    at.radio(key="m_accion").set_value("Borrar esta clase").run()
    at.button(key="m_borrar_uno").click().run()
    assert not at.exception
    assert len(_guardado(tmp_path)["horarios"]["ana1"]) == 1

    at.text_input(key="m_alias").set_value("ana1").run()
    at.checkbox(key="m_borrar_conf").set_value(True).run()
    at.button(key="m_borrar_todo").click().run()
    assert not at.exception
    guardado = _guardado(tmp_path)
    assert guardado["horarios"] == {} and guardado["registros"] == []


def test_mi_horario_un_cambio_que_choca_se_rechaza_y_no_pierde_la_clase(tmp_path, monkeypatch):
    from src import almacen
    from src.horario_csv import aplicar_horario
    at = _app_con_horario(tmp_path, monkeypatch)
    campus, horarios, sem = almacen.cargar_o_crear(str(tmp_path))
    aplicar_horario(campus, horarios, "luis1", [(1, 9, 11, "25E", "Ecuaciones")])
    almacen.guardar_estado(str(tmp_path), campus, horarios, sem)
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.text_input(key="m_alias").set_value("ana1").run()
    _elegir_otro_codigo(at, "m", "E", "25E")                          # ya lo ocupa Luis
    at.button(key="m_guardar").click().run()
    assert any("tu clase sigue igual" in e.value for e in at.error)
    assert _guardado(tmp_path)["horarios"]["ana1"][0][2] == "26J"


def test_buscar_y_ocupar_abren_con_el_dia_y_la_hora_de_ahora(tmp_path, monkeypatch):
    miercoles = _lunes_6_30() + dt.timedelta(days=2, hours=8, minutes=50)       # miércoles 15:20
    at = _app(tmp_path, monkeypatch, fin=_futuro(), ahora=miercoles)
    at.run()
    assert (at.selectbox(key="b_dia").value, at.selectbox(key="b_hora").value) == (2, 15)
    assert (at.selectbox(key="o_dia").value, at.selectbox(key="o_ini").value) == (2, 15)


def test_domingo_y_horas_fuera_de_rango_se_ajustan(tmp_path, monkeypatch):
    domingo_noche = _lunes_6_30() + dt.timedelta(days=6, hours=17)              # domingo 23:30
    at = _app(tmp_path, monkeypatch, fin=_futuro(), ahora=domingo_noche)
    at.run()
    assert not at.exception
    assert (at.selectbox(key="b_dia").value, at.selectbox(key="b_hora").value) == (0, 21)


def test_un_estudio_avisa_cuando_deja_de_valer(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())            # lunes 6:30; franja por defecto 6-7
    at.run()
    at.selectbox(key="o_bloque").set_value("C").run()
    at.selectbox(key="o_salon").set_value("36C").run()
    at.text_input(key="o_detalle").set_value("Grupo de Fisica")
    at.button(key="o_boton").click().run()
    assert any("Dejará de valer" in s.value and "07:00" in s.value for s in at.success)
    registro = json.loads((tmp_path / "semestres" / "2026-2.json").read_text())["registros"][0]
    assert registro["motivo"] == "estudio" and registro["vence"].endswith("T07:00:00")


def test_una_tutoria_se_repite_cada_semana(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    at.run()
    at.selectbox(key="o_bloque").set_value("C").run()
    at.selectbox(key="o_salon").set_value("36C").run()
    at.selectbox(key="o_motivo").set_value("tutoria").run()
    at.text_input(key="o_detalle").set_value("Algebra Lineal")
    at.button(key="o_boton").click().run()
    assert any("Se repite cada semana" in s.value for s in at.success)
    registro = json.loads((tmp_path / "semestres" / "2026-2.json").read_text())["registros"][0]
    assert registro["vence"] == ""


def test_un_uso_de_una_vez_ya_vencido_no_aparece_como_ocupado(tmp_path, monkeypatch):
    from src.franjas import rango
    at = _app(tmp_path, monkeypatch, fin=_futuro())
    ruta = tmp_path / "semestres" / "2026-2.json"
    estado = json.loads(ruta.read_text())
    mascara = rango(0, 6, 8)
    estado["info"] = {"36C": mascara}
    estado["registros"] = [{"espacio_id": "36C", "mascara": mascara, "motivo": "estudio",
                            "detalle": "Grupo viejo", "confirmaciones": 1,
                            "vence": "2020-01-01T08:00:00"}]
    ruta.write_text(json.dumps(estado))
    at.run()
    at.selectbox(key="b_bloque").set_value("C").run()
    at.selectbox(key="b_salon").set_value("36C").run()
    assert not at.exception
    assert not any("está ocupado" in e.value for e in at.error)
    assert any("Sin información" in w.value for w in at.warning)