"""Códigos de salón de Uninorte -> bloque.

Reglas (según cómo los nombra la universidad):
  26J, 93K, 22D  -> número + letra del bloque (J, K, D)
  37G2, 13G2     -> bloque G tiene dos lados: G1 y G2 (mismo bloque, lado distinto)
  SDU1 ... SDU10 -> tabla fija abajo (bloque y piso)
  L1-5, L1-4, L1-3 -> laboratorios de física (ver LABORATORIOS)
  M-tenis, M-futbol, M-piscina, M-musica1..3 -> bloque M (ver BLOQUE_M)
  Salones confirmados de los bloques B y C (ver SALONES_BLOQUE), incluido A1C
Un código que no cumpla ninguna regla devuelve None: agréguenlo en ESPECIALES.
"""
import re

from .campus import Espacio

# SDU -> (bloque, piso)
SDU = {"SDU1": ("C", 1), "SDU2": ("B", 2), "SDU3": ("B", 2), "SDU4": ("D", 3),
       "SDU5": ("B", 3), "SDU6": ("G", 5), "SDU7": ("G", 5), "SDU8": ("K", 5),
       "SDU9": ("K", 5), "SDU10": ("K", 5)}

# Salones CONFIRMADOS por bloque (sin contar los SDU, que van en su tabla de arriba).
# Para agregar salones: añádanlos a la lista de su bloque (o creen el bloque).
SALONES_BLOQUE = {
    "B": ["32B", "33B"],
    "C": ["13C", "14C", "22C", "23C", "24C", "25C", "26C",
          "31C", "32C", "33C", "34C", "35C", "36C", "37C", "38C", "A1C"],
}
# Bloques cuya lista de arriba está COMPLETA: un código de ese bloque que no esté
# en la lista se rechaza (suele ser un error de escritura o de lectura de la IA).
# Para un bloque que aún no tienen completo, no lo pongan aquí.
BLOQUES_COMPLETOS = {"C"}
SALONES_CATALOGO = {s: b for b, lista in SALONES_BLOQUE.items() for s in lista}

# Los laboratorios de física están todos en el "bloque" de Laboratorios (sin letra).
BLOQUE_LABORATORIOS = "LAB"
LABORATORIOS = {"L1-5": "Laboratorio de física (electricidad)",
                "L1-4": "Laboratorio de física (mecánica)",
                "L1-3": "Laboratorio de física (calor y ondas)"}

# Bloque M: deportes y música. Código -> tipo de espacio.
BLOQUE_M = {"M-tenis": "cancha_tenis", "M-futbol": "cancha_futbol",
            "M-piscina": "piscina", "M-musica1": "sala_musica",
            "M-musica2": "sala_musica", "M-musica3": "sala_musica"}

# Otros códigos raros: "CODIGO": (bloque, piso). Ej.:  "X9": ("B", 0)
# S1-8L: laboratorio en el sótano del bloque K (piso -1).
ESPECIALES = {"S1-8L": ("K", -1)}

_PATRON = re.compile(r"^(\d+)([A-M])(\d?)$")


def normalizar(codigo):
    """Quita espacios y pasa a mayúsculas: ' 37g2 ' -> '37G2'."""
    return re.sub(r"\s+", "", str(codigo)).upper()


def parsear_codigo(codigo):
    """Devuelve el Espacio que corresponde al código, o None si no se reconoce."""
    c = normalizar(codigo)
    if c in SDU:
        bloque, piso = SDU[c]
        return Espacio(c, bloque, "salon", piso)
    if c in LABORATORIOS:
        return Espacio(c, BLOQUE_LABORATORIOS, "laboratorio")
    if c in ESPECIALES:
        bloque, piso = ESPECIALES[c]
        return Espacio(c, bloque, "salon", piso)
    for id_m, tipo in BLOQUE_M.items():
        if c == id_m.upper():
            return Espacio(id_m, "M", tipo)
    if c in SALONES_CATALOGO:
        return Espacio(c, SALONES_CATALOGO[c], "salon")
    m = _PATRON.match(c)
    if not m:
        return None
    _, letra, lado = m.groups()
    if lado and (letra != "G" or lado not in "12"):
        return None          # solo el bloque G tiene lados (1 y 2)
    if letra in BLOQUES_COMPLETOS:
        return None          # ese bloque tiene su lista completa y este código no está
    return Espacio(c, letra, "salon")


def asegurar_espacio(campus, codigo):
    """Devuelve el espacio del campus; si no existe pero el código es válido, lo crea.
    Devuelve None si el código no se reconoce."""
    if codigo in campus.espacios:
        return campus.espacios[codigo]
    c = normalizar(codigo)
    for existente in campus.espacios:          # ej. 'm-tenis' -> 'M-tenis'
        if existente.upper() == c:
            return campus.espacios[existente]
    espacio = parsear_codigo(c)
    if espacio is None:
        return None
    campus.agregar_espacio(espacio)
    return espacio