"""Campus: espacios, ocupación (álgebra booleana) y grafo de bloques.

Por cada espacio se guardan DOS vectores de bits:
  ocupado[e] : 1 = hay una clase/tutoría/uso registrado en esa franja
  info[e]    : 1 = el estado de esa franja es CONOCIDO
Estados:  ocupado  -> ocupado = 1
          libre    -> info = 1 y ocupado = 0
          desconocido -> info = 0   (sin información NO significa libre)
"""
import difflib
import re
import unicodedata
from dataclasses import dataclass, asdict

import networkx as nx

TIPOS = ("salon", "laboratorio", "cancha_tenis", "cancha_futbol", "piscina",
         "sala_musica")
MOTIVOS = ("clase", "tutoria", "estudio", "reunion", "practica")


_ROMANOS = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}


def _normalizar_materia(texto):
    """minúsculas, sin tildes ni signos: 'Energía Medio-Ambiente' -> 'energia medio ambiente'."""
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def misma_materia(a, b):
    """True si dos textos nombran la misma materia aunque se hayan escrito distinto.

    Ignora mayúsculas, tildes y signos, acepta nombres cortados ("... Y SOC" vs
    "... Y SOCIEDAD") y diferencias pequeñas de lectura. Si el nivel final es
    distinto (Cálculo I vs Cálculo II, Física 1 vs Física 2) son materias distintas.
    """
    na, nb = _normalizar_materia(a), _normalizar_materia(b)
    if na == nb:
        return True
    if not na or not nb:
        return False
    ta, tb = na.split(), nb.split()

    def nivel(tokens):
        return tokens[-1] if tokens[-1] in _ROMANOS or tokens[-1].isdigit() else None

    if nivel(ta) != nivel(tb):
        return False
    corto, largo = sorted((na, nb), key=len)
    if len(corto) >= 10 and largo.startswith(corto):
        return True
    return difflib.SequenceMatcher(None, na, nb).ratio() >= 0.85


@dataclass(frozen=True)
class Espacio:
    id: str
    bloque: str
    tipo: str = "salon"
    piso: int = 0          # 0 = no se sabe


@dataclass
class Registro:
    espacio_id: str
    mascara: int
    motivo: str
    detalle: str = ""
    confirmaciones: int = 1   # cuántos estudiantes reportaron lo mismo


class Campus:
    def __init__(self, grafo):
        self.grafo = grafo          # nx.Graph: bloques con peso = minutos caminando
        self.espacios = {}
        self.ocupado = {}
        self.info = {}
        self.registros = []

    # ---------- construcción ----------
    def agregar_espacio(self, espacio):
        self.espacios[espacio.id] = espacio
        self.ocupado[espacio.id] = 0
        self.info[espacio.id] = 0

    def confirmar(self, espacio_id, mascara):
        """Marca franjas como conocidas (ej. horario oficial del espacio)."""
        self.info[espacio_id] |= mascara

    # ---------- ocupar / liberar ----------
    def registro_de(self, espacio_id, mascara, motivo, detalle):
        """Registro equivalente (mismo espacio, franjas, motivo y misma materia) o None."""
        for r in self.registros:
            if (r.espacio_id == espacio_id and r.mascara == mascara
                    and r.motivo == motivo and misma_materia(r.detalle, detalle)):
                return r
        return None

    def ocupar(self, espacio_id, mascara, motivo, detalle=""):
        """Registra un uso. Devuelve True si se aceptó, False si hay conflicto.

        Conflicto = (ocupado AND mascara) != 0. Si ya existe un registro equivalente
        (mismo motivo y franjas, y la misma materia aunque esté escrita distinto)
        se toma como confirmación, no conflicto.
        """
        r = self.registro_de(espacio_id, mascara, motivo, detalle)
        if r is not None:
            r.confirmaciones += 1
            return True
        if self.ocupado[espacio_id] & mascara:
            return False
        self.ocupado[espacio_id] |= mascara
        self.info[espacio_id] |= mascara
        self.registros.append(Registro(espacio_id, mascara, motivo, detalle))
        return True

    def liberar(self, espacio_id, mascara):
        """Quita ocupación (ej. una ocupación declarada que expiró)."""
        self.ocupado[espacio_id] &= ~mascara
        self.registros = [r for r in self.registros
                          if not (r.espacio_id == espacio_id and r.mascara & mascara)]

    # ---------- consultas básicas ----------
    def estado(self, espacio_id, franja):
        bit = 1 << franja
        if self.ocupado[espacio_id] & bit:
            return "ocupado"
        if self.info[espacio_id] & bit:
            return "libre"
        return "desconocido"

    def que_hay(self, espacio_id, franja):
        """Registro que ocupa el espacio en esa franja (o None)."""
        bit = 1 << franja
        for r in self.registros:
            if r.espacio_id == espacio_id and r.mascara & bit:
                return r
        return None

    # ---------- guardar / restaurar ----------
    def exportar(self):
        """Estado a guardar: franjas conocidas y registros (lo demás es fijo)."""
        return {"espacios": [asdict(e) for e in self.espacios.values()],
                "info": dict(self.info),
                "registros": [asdict(r) for r in self.registros]}

    def importar(self, estado):
        """Restaura lo guardado. El campus (espacios y grafo) ya viene construido."""
        for e in estado.get("espacios", []):
            if e["id"] not in self.espacios:
                self.agregar_espacio(Espacio(**e))
        for espacio_id, mascara in estado.get("info", {}).items():
            if espacio_id in self.info:
                self.info[espacio_id] = mascara
        for r in estado.get("registros", []):
            if r["espacio_id"] in self.espacios:
                self.ocupado[r["espacio_id"]] |= r["mascara"]
                self.registros.append(Registro(**r))

    def distancias_desde(self, bloque):
        """Minutos de caminata desde un bloque a todos los demás (Dijkstra)."""
        return nx.single_source_dijkstra_path_length(self.grafo, bloque, weight="weight")


def crear_grafo(aristas):
    """aristas: lista de (bloque_a, bloque_b, minutos)."""
    g = nx.Graph()
    for a, b, minutos in aristas:
        g.add_edge(a, b, weight=minutos)
    return g