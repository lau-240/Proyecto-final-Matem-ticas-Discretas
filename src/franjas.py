"""Franjas horarias como bits (álgebra booleana).

La semana se divide en franjas de una hora: 6 días (lun-sáb) x 16 horas (6:00-22:00).
La franja número f = dia * N_HORAS + (hora - H_INI). Un conjunto de franjas es un
entero cuyo bit f vale 1 si la franja f pertenece al conjunto.
"""
DIAS = ["lun", "mar", "mie", "jue", "vie", "sab"]
H_INI = 6
H_FIN = 22
N_HORAS = H_FIN - H_INI
N_FRANJAS = len(DIAS) * N_HORAS
TODAS = (1 << N_FRANJAS) - 1


def franja(dia, hora):
    """Número de franja para un día (0=lun) y una hora de inicio (ej. 8)."""
    return dia * N_HORAS + (hora - H_INI)


def rango(dia, h_ini, h_fin):
    """Máscara con las franjas de h_ini a h_fin (h_fin no incluida) de un día."""
    mascara = 0
    for h in range(h_ini, h_fin):
        mascara |= 1 << franja(dia, h)
    return mascara


def desde(f, n):
    """Máscara de n franjas consecutivas empezando en la franja f."""
    return ((1 << n) - 1) << f


def contar(mascara):
    """Cuántas franjas hay en la máscara (bits en 1)."""
    return bin(mascara).count("1")


def describir(f):
    """Texto legible de una franja, ej. 'lun 8:00'."""
    dia, h = divmod(f, N_HORAS)
    return f"{DIAS[dia]} {h + H_INI}:00"


def rangos_texto(mascara):
    """Texto legible de una máscara, ej. 'lun 10:00-12:00, mar 8:00-9:00'."""
    partes = []
    f = 0
    while f < N_FRANJAS:
        if (mascara >> f) & 1:
            ini = f
            while (f + 1 < N_FRANJAS and (mascara >> (f + 1)) & 1
                   and (f + 1) // N_HORAS == ini // N_HORAS):
                f += 1
            dia, h = divmod(ini, N_HORAS)
            _, h2 = divmod(f, N_HORAS)
            partes.append(f"{DIAS[dia]} {h + H_INI}:00-{h2 + H_INI + 1}:00")
        f += 1
    return ", ".join(partes)