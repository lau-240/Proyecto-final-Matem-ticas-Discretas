"""Métricas: modelo de 3 estados vs. modelo ingenuo de 2 estados."""
from .franjas import contar, TODAS


def evaluar(campus, verdad):
    """Compara las respuestas 'libre' de ambos modelos con la verdad simulada.

    modelo   : libre = info AND NOT ocupado          (3 estados)
    ingenuo  : libre = NOT ocupado  (sin info = libre) (2 estados)
    precisión = de lo que marca libre, cuánto lo está realmente.
    OJO: la precisión del modelo es 1.0 por construcción (se asume que lo
    confirmado es correcto); el riesgo real son las confirmaciones falsas.
    """
    n = len(campus.espacios) * contar(TODAS)
    info_total = decl_m = ok_m = decl_n = ok_n = 0
    for e in campus.espacios:
        info = campus.info[e]
        ocu = campus.ocupado[e]
        v = verdad[e]
        libre_m = info & ~ocu & TODAS
        libre_n = ~ocu & TODAS
        info_total += contar(info)
        decl_m += contar(libre_m)
        ok_m += contar(libre_m & ~v)
        decl_n += contar(libre_n)
        ok_n += contar(libre_n & ~v)
    return {
        "cobertura": info_total / n,
        "precision_modelo": ok_m / decl_m if decl_m else 1.0,
        "precision_ingenuo": ok_n / decl_n if decl_n else 1.0,
    }
