"""Estilos y piezas visuales (HTML) de la interfaz.

Solo presentación: no toca el modelo. Los colores usan transparencias para que se vean
bien con el tema claro y con el oscuro (ver `.streamlit/config.toml`).
"""
from html import escape

CSS = """
<style>
/* Ancho cómodo de lectura aunque la página use layout="wide" */
.block-container {max-width: 1120px; padding-top: 2.2rem;}

/* ---------- encabezado ---------- */
.ec-hero {
  border-radius: 18px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
  background: linear-gradient(135deg, rgba(13,148,136,.18), rgba(37,99,235,.12));
  border: 1px solid rgba(13,148,136,.30);
}
.ec-hero h1 {font-size: 1.9rem; margin: 0; padding: 0; line-height: 1.2;}
.ec-hero p {margin: .35rem 0 0; opacity: .8;}
.ec-badges {display: flex; flex-wrap: wrap; gap: .45rem; margin-top: .8rem;}
.ec-badge {
  font-size: .82rem; padding: .2rem .65rem; border-radius: 999px;
  background: rgba(127,127,127,.14); border: 1px solid rgba(127,127,127,.25);
}
.ec-badge b {font-weight: 600;}

/* ---------- pestañas ---------- */
.stTabs [data-baseweb="tab-list"] {gap: .25rem; flex-wrap: wrap;}
.stTabs [data-baseweb="tab"] {
  padding: .45rem .9rem; border-radius: 10px 10px 0 0; font-weight: 600;
}

/* ---------- títulos de sección ---------- */
.ec-paso {display: flex; align-items: center; gap: .6rem; margin: .2rem 0 .6rem;}
.ec-paso span {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.6rem; height: 1.6rem; border-radius: 50%; font-size: .85rem; font-weight: 700;
  background: rgba(13,148,136,.20); border: 1px solid rgba(13,148,136,.45);
}
.ec-paso b {font-size: 1.05rem;}

/* ---------- leyenda y franja del día ---------- */
.ec-leyenda {display: flex; gap: 1rem; flex-wrap: wrap; font-size: .85rem; opacity: .9;}
.ec-leyenda i {
  display: inline-block; width: .8rem; height: .8rem; border-radius: 3px;
  margin-right: .35rem; vertical-align: -1px; border: 1px solid rgba(127,127,127,.45);
}
.ec-dia {display: grid; grid-template-columns: repeat(16, 1fr); gap: 3px; margin: .5rem 0 .3rem;}
.ec-hora {text-align: center;}
.ec-celda {height: 34px; border-radius: 6px; border: 1px solid rgba(127,127,127,.25);}
.ec-hora small {display: block; margin-top: 3px; font-size: .75rem; opacity: .75;}
.ec-libre {background: rgba(34,197,94,.55); border-color: rgba(34,197,94,.9);}
.ec-ocupado {background: rgba(239,68,68,.55); border-color: rgba(239,68,68,.9);}
.ec-desconocido {
  background: repeating-linear-gradient(45deg, rgba(127,127,127,.12) 0 5px,
                                        rgba(127,127,127,.22) 5px 10px);
}
.ec-marcada {outline: 2px solid rgba(37,99,235,.95); outline-offset: 1px;}

/* ---------- horario semanal ---------- */
.ec-semana {
  display: grid; grid-template-columns: 3.2rem repeat(6, 1fr); gap: 3px;
  font-size: .78rem; margin: .4rem 0 1rem;
}
.ec-semana .ec-cab {text-align: center; font-weight: 700; padding: .3rem 0;}
.ec-semana .ec-h {text-align: right; padding-right: .4rem; opacity: .65; line-height: 28px;}
.ec-semana .ec-v {min-height: 28px; border-radius: 4px; background: rgba(127,127,127,.07);}
.ec-clase {
  border-radius: 6px; padding: .25rem .4rem; overflow: hidden; line-height: 1.25;
  background: rgba(13,148,136,.28); border-left: 4px solid rgba(13,148,136,1);
}
.ec-clase b {display: block; font-size: .78rem;}
.ec-clase small {opacity: .8;}

div[data-testid="stMetric"] {padding: .2rem .4rem;}
</style>
"""

COLOR_CLASE = ["13,148,136", "37,99,235", "147,51,234", "234,88,12", "219,39,119",
               "202,138,4", "22,163,74", "8,145,178"]


def encabezado(semestre, fin, n_registros, n_horarios, cobertura):
    """Bloque superior con el título y el estado del semestre."""
    return f"""
<div class="ec-hero">
  <h1>🏫 Espacios del campus</h1>
  <p>Encuentra salones libres, revisa qué hay en cada espacio y comparte tu horario
     para que todos sepan qué está ocupado.</p>
  <div class="ec-badges">
    <span class="ec-badge">📅 Semestre <b>{escape(str(semestre))}</b></span>
    <span class="ec-badge">⏳ Datos válidos hasta <b>{escape(str(fin))}</b></span>
    <span class="ec-badge">📝 <b>{n_registros}</b> registros</span>
    <span class="ec-badge">👥 <b>{n_horarios}</b> horarios</span>
    <span class="ec-badge">📊 Cobertura <b>{cobertura:.0%}</b></span>
  </div>
</div>"""


def paso(numero, texto):
    """Título numerado de una sección ('1 · ¿Cuándo?')."""
    return f'<div class="ec-paso"><span>{numero}</span><b>{escape(texto)}</b></div>'


def leyenda():
    return ('<div class="ec-leyenda">'
            '<span><i class="ec-libre"></i>Libre (confirmado)</span>'
            '<span><i class="ec-ocupado"></i>Ocupado</span>'
            '<span><i class="ec-desconocido"></i>Sin información</span>'
            '<span><i class="ec-marcada" style="background:transparent"></i>'
            'Franja consultada</span></div>')


def franja_dia(horas, marcadas=()):
    """Tira de colores con el estado de cada hora de un día.

    `horas`: lista de (hora, estado, detalle) con estado en libre/ocupado/desconocido.
    `marcadas`: horas que se resaltan (la franja que el estudiante consultó).
    """
    celdas = []
    for hora, estado, detalle in horas:
        titulo = f"{hora}:00-{hora + 1}:00 · " + (detalle or estado)
        marca = " ec-marcada" if hora in marcadas else ""
        celdas.append(f'<div class="ec-hora" title="{escape(titulo)}">'
                      f'<div class="ec-celda ec-{estado}{marca}"></div>'
                      f'<small>{hora}</small></div>')
    return f'<div class="ec-dia">{"".join(celdas)}</div>' + leyenda()


def horario_semanal(clases, nombres_dias, h_ini, h_fin):
    """Cuadrícula lunes-sábado con las clases de un estudiante.

    `clases`: lista de (dia, hora_ini, hora_fin, espacio, materia).
    Solo muestra las horas entre la primera y la última clase.
    """
    if not clases:
        return ""
    desde = max(h_ini, min(c[1] for c in clases))
    hasta = min(h_fin, max(c[2] for c in clases))
    colores = {}
    for c in clases:
        colores.setdefault(c[4], COLOR_CLASE[len(colores) % len(COLOR_CLASE)])
    celdas = ['<div></div>'] + [f'<div class="ec-cab">{escape(d[:3])}</div>'
                                for d in nombres_dias]
    for i, h in enumerate(range(desde, hasta)):
        fila = i + 2
        celdas.append(f'<div class="ec-h" style="grid-row:{fila};grid-column:1">{h}:00</div>')
        for d in range(len(nombres_dias)):
            celdas.append(f'<div class="ec-v" style="grid-row:{fila};grid-column:{d + 2}"></div>')
    for d, a, b, espacio, materia in clases:
        rgb = colores[materia]
        celdas.append(
            f'<div class="ec-clase" style="grid-row:{a - desde + 2}/{b - desde + 2};'
            f'grid-column:{d + 2};background:rgba({rgb},.25);border-left-color:rgb({rgb})"'
            f' title="{escape(f"{materia} · {espacio} · {a}:00-{b}:00")}">'
            f'<b>{escape(materia)}</b><small>{escape(espacio)} · {a}-{b}</small></div>')
    return f'<div class="ec-semana">{"".join(celdas)}</div>'

