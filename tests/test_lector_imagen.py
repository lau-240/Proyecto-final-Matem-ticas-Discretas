from types import SimpleNamespace

import pytest

from src import lector_imagen
from src.horario_csv import leer_horario

RESPUESTA = """```csv
dia,hora_inicio,hora_fin,salon,materia
Martes,9,11,L1-5,
Martes,12,14,SDU9,
Jueves,9,11,37G2,
```"""


class ClienteFalso:
    """Imita al cliente de la API: devuelve una respuesta fija y guarda la llamada."""
    def __init__(self, texto):
        self.llamadas = []
        self.messages = SimpleNamespace(create=self._crear)
        self._texto = texto

    def _crear(self, **kwargs):
        self.llamadas.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._texto)])


def test_limpiar_csv_quita_las_comillas_de_codigo():
    limpio = lector_imagen.limpiar_csv(RESPUESTA)
    assert limpio.startswith("dia,hora_inicio") and "```" not in limpio


def test_imagen_a_csv_y_validacion():
    cliente = ClienteFalso(RESPUESTA)
    texto = lector_imagen.imagen_a_csv(b"bytes-de-imagen", "image/png", cliente)
    clases, errores = leer_horario(texto)
    assert len(clases) == 3 and errores == []
    contenido = cliente.llamadas[0]["messages"][0]["content"]
    assert contenido[0]["type"] == "image" and contenido[0]["source"]["media_type"] == "image/png"


def test_si_la_ia_inventa_un_salon_la_validacion_lo_rechaza():
    texto = lector_imagen.imagen_a_csv(
        b"x", "image/jpeg",
        ClienteFalso("dia,hora_inicio,hora_fin,salon,materia\nMartes,9,11,ZZ9,\nMartes,12,14,SDU9,\n"))
    clases, errores = leer_horario(texto)
    assert len(clases) == 1 and "ZZ9" in errores[0]


def test_imagen_muy_grande_o_formato_raro():
    with pytest.raises(ValueError):
        lector_imagen.imagen_a_csv(b"x" * (lector_imagen.MAX_BYTES + 1), "image/png", ClienteFalso(""))
    with pytest.raises(ValueError):
        lector_imagen.imagen_a_csv(b"x", "application/pdf", ClienteFalso(""))


def test_sin_clave_da_un_error_claro(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        lector_imagen.imagen_a_csv(b"x", "image/png")