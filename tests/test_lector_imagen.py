from types import SimpleNamespace

import pytest

from src import lector_imagen
from src.horario_csv import leer_horario

ENCABEZADO = "dia,hora_inicio,hora_fin,salon,materia\n"
RESPUESTA = """```csv
dia,hora_inicio,hora_fin,salon,materia
Martes,9,11,L1-5,
Martes,12,14,SDU9,
Jueves,9,11,37G2,
```"""
MALO = ENCABEZADO + "Martes,9,11,ZZ9,\nMartes,12,14,SDU9,\n"
BUENO = ENCABEZADO + "Martes,9,11,L1-5,\nMartes,12,14,SDU9,\n"


class ClienteFalso:
    """Imita al cliente de Gemini: devuelve respuestas fijas (una por llamada)."""
    def __init__(self, *textos):
        self.llamadas = []
        self.models = SimpleNamespace(generate_content=self._generar)
        self._textos = list(textos)

    def _generar(self, **kwargs):
        self.llamadas.append(kwargs)
        i = min(len(self.llamadas) - 1, len(self._textos) - 1)
        return SimpleNamespace(text=self._textos[i])


def test_limpiar_csv_quita_las_comillas_de_codigo():
    limpio = lector_imagen.limpiar_csv(RESPUESTA)
    assert limpio.startswith("dia,hora_inicio") and "```" not in limpio


def test_imagen_a_csv_y_validacion():
    cliente = ClienteFalso(RESPUESTA)
    texto = lector_imagen.imagen_a_csv(b"bytes-de-imagen", "image/png", cliente)
    clases, errores = leer_horario(texto)
    assert len(clases) == 3 and errores == []
    assert len(cliente.llamadas) == 1             # sin errores: no hace falta corregir
    llamada = cliente.llamadas[0]
    assert llamada["model"] in lector_imagen.MODELOS
    assert len(llamada["contents"]) == 2          # la imagen y la instrucción


def test_la_instruccion_lista_los_codigos_validos():
    prompt = lector_imagen.construir_prompt()
    assert "SDU1 a SDU10" in prompt and "L1-5" in prompt and "dia,hora_inicio" in prompt


def test_si_hay_errores_se_pide_una_correccion():
    cliente = ClienteFalso(MALO, BUENO)
    texto = lector_imagen.imagen_a_csv(b"x", "image/png", cliente)
    clases, errores = leer_horario(texto)
    assert len(clases) == 2 and errores == []
    assert len(cliente.llamadas) == 2
    assert "ZZ9" in cliente.llamadas[1]["contents"][1]   # le dice qué fila falló


def test_si_la_correccion_no_mejora_se_conserva_la_primera():
    peor = ENCABEZADO + "Martes,9,11,ZZ9,\nMartes,12,14,YY8,\n"
    texto = lector_imagen.imagen_a_csv(b"x", "image/jpeg", ClienteFalso(MALO, peor))
    clases, errores = leer_horario(texto)
    assert len(clases) == 1 and "ZZ9" in errores[0]


def test_imagen_muy_grande_o_formato_raro():
    with pytest.raises(ValueError):
        lector_imagen.imagen_a_csv(b"x" * (lector_imagen.MAX_BYTES + 1), "image/png", ClienteFalso(""))
    with pytest.raises(ValueError):
        lector_imagen.imagen_a_csv(b"x", "application/pdf", ClienteFalso(""))


def test_respuesta_vacia_da_un_error_claro():
    with pytest.raises(ValueError, match="no devolvió texto"):
        lector_imagen.imagen_a_csv(b"x", "image/png", ClienteFalso(None))


def test_si_un_modelo_esta_saturado_prueba_el_siguiente(monkeypatch):
    monkeypatch.setattr(lector_imagen, "MODELOS", ["modelo-a", "modelo-b"])
    monkeypatch.setattr(lector_imagen.time, "sleep", lambda s: None)
    usados = []

    def generar(**kwargs):
        usados.append(kwargs["model"])
        if kwargs["model"] == "modelo-a":
            raise Exception("503 UNAVAILABLE. This model is currently experiencing high demand")
        return SimpleNamespace(text=BUENO)

    cliente = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
    texto = lector_imagen.imagen_a_csv(b"x", "image/png", cliente)
    assert len(leer_horario(texto)[0]) == 2
    assert usados == ["modelo-a", "modelo-b"]   # saturado: pasa al siguiente sin esperar


def test_un_error_que_no_es_transitorio_se_propaga(monkeypatch):
    def generar(**kwargs):
        raise Exception("400 INVALID_ARGUMENT")
    cliente = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
    with pytest.raises(Exception, match="INVALID_ARGUMENT"):
        lector_imagen.imagen_a_csv(b"x", "image/png", cliente)


def test_sin_clave_da_un_error_claro(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        lector_imagen.imagen_a_csv(b"x", "image/png")


def test_corregir_codigo_arregla_confusiones_de_caracteres():
    assert lector_imagen.corregir_codigo("2OJ") == "20J"       # O leída en vez de 0
    assert lector_imagen.corregir_codigo("LI-5") == "L1-5"     # I leída en vez de 1
    assert lector_imagen.corregir_codigo("37g2") is None       # ya es válido: no se toca
    assert lector_imagen.corregir_codigo("ZZ9") is None        # sin arreglo válido: no adivina
    assert lector_imagen.corregir_codigo("") is None


def test_el_arreglo_local_evita_la_segunda_llamada_a_la_ia():
    leido = ENCABEZADO + "Martes,9,11,LI-5,\nMartes,12,14,SDU9,\n"
    cliente = ClienteFalso(leido)
    texto = lector_imagen.imagen_a_csv(b"x", "image/png", cliente)
    clases, errores = leer_horario(texto)
    assert errores == [] and clases[0][3] == "L1-5"
    assert len(cliente.llamadas) == 1                # se corrigió en local


def test_el_arreglo_local_no_toca_deportes_ni_materias_con_comas():
    leido = ENCABEZADO + 'Lunes,7,9,TENIS,TENIS\nMartes,9,11,26J,"Cálculo, grupo 2"\n'
    nuevo, cambios = lector_imagen.corregir_codigos_local(leido)
    assert cambios == [] and nuevo == leido.strip()


def test_el_prompt_pide_comillas_para_campos_con_comas():
    assert "comillas dobles" in lector_imagen.construir_prompt()


def test_reducir_imagen_achica_las_grandes_y_respeta_las_pequenas():
    import io
    import random
    from PIL import Image
    random.seed(1)
    grande = Image.effect_noise((3000, 2000), 80).convert("RGB")
    buf = io.BytesIO()
    grande.save(buf, format="PNG")
    datos, tipo = lector_imagen.reducir_imagen(buf.getvalue(), "image/png")
    assert tipo == "image/jpeg" and len(datos) < len(buf.getvalue())
    assert max(Image.open(io.BytesIO(datos)).size) <= lector_imagen.LADO_MAXIMO
    chica = io.BytesIO()
    Image.new("RGB", (400, 300), "white").save(chica, format="PNG")
    assert lector_imagen.reducir_imagen(chica.getvalue(), "image/png") == (chica.getvalue(), "image/png")
    assert lector_imagen.reducir_imagen(b"no-es-imagen", "image/png") == (b"no-es-imagen", "image/png")


def test_los_modelos_gemini_3_piden_poco_pensamiento_y_si_lo_rechazan_se_repite_sin_config(monkeypatch):
    monkeypatch.setattr(lector_imagen, "MODELOS", ["gemini-3.x-flash"])
    recibidos = []

    def generar(**kwargs):
        recibidos.append(kwargs)
        if "config" in kwargs:
            raise Exception("400 INVALID_ARGUMENT: thinking_level no soportado")
        return SimpleNamespace(text=BUENO)

    cliente = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
    texto = lector_imagen.imagen_a_csv(b"x", "image/png", cliente)
    assert len(leer_horario(texto)[0]) == 2
    assert "config" in recibidos[0] and "config" not in recibidos[1]
    assert str(recibidos[0]["config"].thinking_config.thinking_level).endswith("LOW")
    assert lector_imagen._config_para("modelo-a") is None


def test_si_un_modelo_no_responde_a_tiempo_prueba_el_siguiente(monkeypatch):
    monkeypatch.setattr(lector_imagen, "MODELOS", ["modelo-a", "modelo-b"])
    usados = []

    def generar(**kwargs):
        usados.append(kwargs["model"])
        if kwargs["model"] == "modelo-a":
            raise Exception("The read operation timed out")
        return SimpleNamespace(text=BUENO)

    cliente = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
    texto = lector_imagen.imagen_a_csv(b"x", "image/png", cliente)
    assert len(leer_horario(texto)[0]) == 2
    assert usados == ["modelo-a", "modelo-b"]          # no pierde tiempo reintentando


def test_el_cliente_real_lleva_limite_de_tiempo(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    cliente = lector_imagen._crear_cliente()
    assert cliente._api_client._http_options.timeout == lector_imagen.TIMEOUT_S * 1000


def test_si_el_unico_modelo_esta_saturado_se_reintenta_una_vez(monkeypatch):
    monkeypatch.setattr(lector_imagen, "MODELOS", ["modelo-a"])
    monkeypatch.setattr(lector_imagen.time, "sleep", lambda s: None)
    usados = []

    def generar(**kwargs):
        usados.append(kwargs["model"])
        if len(usados) == 1:
            raise Exception("503 UNAVAILABLE")
        return SimpleNamespace(text=BUENO)

    cliente = SimpleNamespace(models=SimpleNamespace(generate_content=generar))
    texto = lector_imagen.imagen_a_csv(b"x", "image/png", cliente)
    assert len(leer_horario(texto)[0]) == 2 and usados == ["modelo-a", "modelo-a"]


def test_el_modelo_saturado_por_defecto_queda_al_final():
    assert lector_imagen.MODELOS_POR_DEFECTO.split(",")[-1] == "gemini-3.8-flash"