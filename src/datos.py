"""Datos: campus de ejemplo, caso de resultado conocido y simulación."""
import random

from .campus import Campus, Espacio, crear_grafo
from .codigos import BLOQUE_LABORATORIOS, LABORATORIOS, SDU
from .consultas import Estudiante
from .franjas import TODAS, N_FRANJAS, N_HORAS, DIAS, rango, franja

BLOQUES = list("ABCDEFGHIJKLM")

# TIEMPOS DE EJEMPLO (minutos). Deben MEDIRSE en el campus real.
ARISTAS_CAMPUS = [
    ("A", "B", 2), ("B", "C", 2), ("C", "D", 3), ("D", "E", 2), ("E", "F", 2),
    ("F", "G", 3), ("G", "H", 2), ("H", "I", 2), ("I", "J", 3), ("J", "K", 2),
    ("K", "L", 2), ("L", "M", 6), ("L", "LAB", 3),
    ("B", "E", 4), ("C", "F", 5), ("F", "I", 5), ("H", "K", 4),
]


def campus_base():
    """Campus REAL para la app: bloque M, salones SDU y el grafo. Los demás salones
    se crean solos cuando alguien carga un horario que los usa (ver codigos.py)."""
    campus = Campus(crear_grafo(ARISTAS_CAMPUS))
    campus.agregar_espacio(Espacio("M-tenis", "M", "cancha_tenis"))
    campus.agregar_espacio(Espacio("M-futbol", "M", "cancha_futbol"))
    campus.agregar_espacio(Espacio("M-piscina", "M", "piscina"))
    for i in range(1, 4):
        campus.agregar_espacio(Espacio(f"M-musica{i}", "M", "sala_musica"))
    for codigo, (bloque, piso) in SDU.items():
        campus.agregar_espacio(Espacio(codigo, bloque, "salon", piso))
    for codigo in LABORATORIOS:
        campus.agregar_espacio(Espacio(codigo, BLOQUE_LABORATORIOS, "laboratorio"))
    return campus


def campus_completo(salones_por_bloque=3):
    """Salones en los bloques A-L; en M: tenis, fútbol, piscina y 3 salas de música."""
    campus = Campus(crear_grafo(ARISTAS_CAMPUS))
    for b in BLOQUES[:-1]:
        for i in range(1, salones_por_bloque + 1):
            campus.agregar_espacio(Espacio(f"{b}{i}", b, "salon"))
    campus.agregar_espacio(Espacio("M-tenis", "M", "cancha_tenis"))
    campus.agregar_espacio(Espacio("M-futbol", "M", "cancha_futbol"))
    campus.agregar_espacio(Espacio("M-piscina", "M", "piscina"))
    for i in range(1, 4):
        campus.agregar_espacio(Espacio(f"M-musica{i}", "M", "sala_musica"))
    return campus


def caso_conocido():
    """Campus pequeño (3 bloques, 4 salones) con respuesta conocida.

    Lunes. Una estudiante tiene clase 8-10 en A1, así que a las 10:00 está en A.
    Quiere un salón libre de 10 a 12.
      - A1: ocupado 10-12 por una tutoría
      - A2: SIN información en 10-12  (desconocido)
      - B1: libre y confirmado (2 min desde A)
      - C1: libre y confirmado (5 min desde A, pasando por B)
    Esperado: B1 a 2 min. Si se permite 'desconocido': A2 a 0 min.
    """
    campus = Campus(crear_grafo([("A", "B", 2), ("B", "C", 3)]))
    for id_, bloque in [("A1", "A"), ("A2", "A"), ("B1", "B"), ("C1", "C")]:
        campus.agregar_espacio(Espacio(id_, bloque, "salon"))
    manana = rango(0, 7, 21)
    campus.confirmar("A1", manana)
    campus.confirmar("B1", manana)
    campus.confirmar("C1", manana)
    campus.confirmar("A2", rango(0, 7, 10) | rango(0, 12, 21))  # hueco 10-12
    campus.ocupar("A1", rango(0, 10, 12), "tutoria", "Calculo II")
    ana = Estudiante("ana", [(franja(0, 8), franja(0, 10), "A1")])
    return campus, ana


def ocupacion_verdadera(campus, semilla=42, prob=0.45):
    """Ocupación 'real' simulada: bloques de 2 horas ocupados al azar."""
    rng = random.Random(semilla)
    verdad = {}
    for e in campus.espacios:
        m = 0
        for dia in range(len(DIAS)):
            for h in range(7, 21, 2):
                if rng.random() < prob:
                    m |= rango(dia, h, min(h + 2, 21))
        verdad[e] = m
    return verdad


def revelar(campus_vacio, verdad, cobertura, semilla=7):
    """Cada (espacio, franja) es conocido con probabilidad `cobertura`.
    Solo se conoce la ocupación real de las franjas conocidas."""
    rng = random.Random(semilla)
    for e in campus_vacio.espacios:
        info = 0
        for f in range(N_FRANJAS):
            if rng.random() < cobertura:
                info |= 1 << f
        campus_vacio.info[e] = info
        campus_vacio.ocupado[e] = verdad[e] & info
    return campus_vacio