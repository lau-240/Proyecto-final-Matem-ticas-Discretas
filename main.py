"""Punto de entrada: caso conocido, conflictos, tutorías, simulación y red.

Uso:  python main.py
"""
import matplotlib
matplotlib.use("Agg")  # sin ventana; guarda la imagen en resultados/
import matplotlib.pyplot as plt
import networkx as nx

from src.consultas import (mas_cercano_libre, ubicacion_inferida, ver_tutorias,
                           libres, cobertura)
from src.datos import (caso_conocido, campus_completo, ocupacion_verdadera,
                       revelar)
from src.franjas import rango, franja, describir, TODAS
from src.metricas import evaluar


def parte_1_caso_conocido():
    print("=== 1. Caso de resultado conocido ===")
    campus, ana = caso_conocido()
    f = franja(0, 10)
    origen = ubicacion_inferida(campus, ana, f)
    pedido = rango(0, 10, 12)
    print(f"Ubicación inferida de Ana a las {describir(f)}: bloque {origen}")
    estricto = mas_cercano_libre(campus, origen, pedido)
    print("Más cercano (solo confirmados):", estricto[0].id, f"a {estricto[1]} min")
    flexible = mas_cercano_libre(campus, origen, pedido, permitir_desconocido=True)
    print("Más cercano (permitiendo desconocidos):", flexible[0].id,
          f"a {flexible[1]} min")
    print("Estado de A2 a las 10:00:", campus.estado("A2", f))
    r = campus.que_hay("A1", f)
    print(f"Qué hay en A1 a las 10:00: {r.motivo} - {r.detalle}")


def parte_2_conflictos_y_tutorias():
    print("\n=== 2. Conflictos (AND) y vista de tutorías ===")
    campus, _ = caso_conocido()
    ok = campus.ocupar("B1", rango(0, 14, 16), "estudio", "Grupo de Fisica")
    print("Ocupar B1 14-16 (estudio):", "aceptado" if ok else "conflicto")
    ok = campus.ocupar("B1", rango(0, 15, 17), "reunion", "Proyecto")
    print("Ocupar B1 15-17 (reunión):", "aceptado" if ok else "conflicto (se cruza 15-16)")
    campus.ocupar("C1", rango(1, 9, 11), "tutoria", "Algebra Lineal")
    print("Tutorías registradas:")
    for t in ver_tutorias(campus):
        print(f"  {t.espacio_id}: {t.detalle}")


def parte_3_simulacion():
    print("\n=== 3. Simulación: modelo de 3 estados vs. ingenuo ===")
    print(f"{'cobertura':>10}{'prec. modelo':>15}{'prec. ingenuo':>16}")
    for c in (0.2, 0.4, 0.6, 0.8, 0.95):
        campus = campus_completo()
        verdad = ocupacion_verdadera(campus)
        revelar(campus, verdad, c)
        r = evaluar(campus, verdad)
        print(f"{r['cobertura']:>10.2f}{r['precision_modelo']:>15.2f}"
              f"{r['precision_ingenuo']:>16.2f}")
    campus = campus_completo()
    print("\nEjemplo bloque M, tipo piscina libre el lunes 10-12 (todo sin info):",
          len(libres(campus, rango(0, 10, 12), tipo="piscina")),
          "con datos estrictos /",
          len(libres(campus, rango(0, 10, 12), tipo="piscina",
                     permitir_desconocido=True)), "permitiendo desconocidos")
    return campus


def parte_4_red(campus):
    print("\n=== 4. Análisis de red del campus ===")
    g = campus.grafo
    cerca = nx.closeness_centrality(g, distance="weight")
    inter = nx.betweenness_centrality(g, weight="weight")
    top_c = sorted(cerca.items(), key=lambda kv: kv[1], reverse=True)[:3]
    top_i = sorted(inter.items(), key=lambda kv: kv[1], reverse=True)[:3]
    print("Bloques más accesibles (cercanía):", [(b, round(v, 3)) for b, v in top_c])
    print("Bloques de paso (intermediación):", [(b, round(v, 3)) for b, v in top_i])
    plt.figure(figsize=(8, 5))
    pos = nx.spring_layout(g, seed=3, weight=None)
    nx.draw(g, pos, with_labels=True, node_color="#cfe3ff", node_size=700)
    nx.draw_networkx_edge_labels(g, pos, nx.get_edge_attributes(g, "weight"))
    plt.savefig("resultados/campus.png", dpi=150)
    print("Gráfico guardado en resultados/campus.png")


if __name__ == "__main__":
    parte_1_caso_conocido()
    parte_2_conflictos_y_tutorias()
    c = parte_3_simulacion()
    parte_4_red(c)
