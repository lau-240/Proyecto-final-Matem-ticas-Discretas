"""Piezas visuales (HTML/CSS) de la interfaz: cabecera, pasos, tira de horas y horario semanal.

Solo presentación: no toca el modelo. Estilo de portal universitario con la paleta
institucional de la Universidad del Norte (rojo, negro y amarillo roble).
"""
from html import escape

ROJO = "#C8102E"        # Rojo Uninorte (Pantone 1797C, aprox.)
NEGRO = "#1A1A1A"
AMARILLO = "#FFC72C"    # Amarillo roble (Pantone 116C, aprox.)
VERDE = "#2E8540"       # solo para "libre"

CSS = f"""
<style>
.block-container {{max-width: 1100px; padding-top: 3.2rem;}}

/* ---------- cabecera tipo portal ---------- */
.un-barra {{
  background: {NEGRO}; color: #fff; font-size: .78rem; padding: .45rem 1.2rem;
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: .4rem;
  letter-spacing: .02em;
}}
.un-barra span:last-child {{opacity: .75;}}
.un-cabecera {{
  background: #fff; border: 1px solid #E2E2E2; border-top: 0;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
  gap: 1rem; padding: 1.2rem 1.4rem 1.2rem 1.2rem; border-left: 6px solid {ROJO};
}}
.un-titulo {{font-size: 1.85rem; font-weight: 800; color: {NEGRO}; line-height: 1.1;}}
.un-sub {{color: #5A5A5A; margin-top: .3rem; font-size: .95rem;}}
.un-ahora {{display: flex; gap: .5rem; align-items: stretch;}}
.un-ahora .un-cuando {{font-size: .75rem; color: #5A5A5A; text-transform: uppercase;
                      letter-spacing: .05em; align-self: center; margin-right: .4rem;
                      text-align: right; line-height: 1.3;}}
.un-dato {{border: 1px solid #E2E2E2; padding: .35rem .8rem; min-width: 5.2rem;
          text-align: center; background: #FAFAFA;}}
.un-dato b {{display: block; font-size: 1.45rem; color: {NEGRO}; line-height: 1.1;}}
.un-dato small {{font-size: .72rem; color: #5A5A5A;}}
.un-dato.ocupado {{border-top: 3px solid {ROJO};}}
.un-dato.libre {{border-top: 3px solid {VERDE};}}
.un-dato.sin {{border-top: 3px solid #BDBDBD;}}

/* ---------- menú principal: barra roja ---------- */
.stTabs [role="tablist"] {{
  background: {ROJO}; gap: 0; padding: 0 .4rem; margin-bottom: 1.2rem; border: 0;
}}
.stTabs [role="tab"] {{
  color: #fff; padding: .8rem 1.1rem .7rem; border-bottom: 4px solid transparent;
  border-radius: 0; margin: 0;
}}
.stTabs [role="tab"] p {{font-weight: 600; font-size: .95rem; color: inherit;}}
.stTabs [role="tab"]:hover {{background: rgba(0,0,0,.12); color: #fff;}}
.stTabs [role="tab"][aria-selected="true"] {{
  background: rgba(0,0,0,.2); border-bottom-color: {AMARILLO}; color: #fff;
}}
.stTabs .react-aria-SelectionIndicator {{display: none;}}

/* pestañas internas (dentro de una sección): estilo simple */
.stTabs .stTabs [role="tablist"] {{
  background: transparent; padding: 0; border-bottom: 1px solid #E2E2E2; margin-bottom: .6rem;
}}
.stTabs .stTabs [role="tab"] {{color: {NEGRO}; padding: .5rem .9rem;}}
.stTabs .stTabs [role="tab"]:hover {{background: #F2F2F2; color: {NEGRO};}}
.stTabs .stTabs [role="tab"][aria-selected="true"] {{
  background: transparent; color: {ROJO}; border-bottom-color: {ROJO};
}}

/* ---------- títulos de sección: línea amarilla ---------- */
.stMainBlockContainer h3 {{font-weight: 800; padding-bottom: .2rem;}}
.stMainBlockContainer h3::after {{
  content: ""; display: block; width: 56px; height: 4px; background: {AMARILLO};
  margin-top: .45rem;
}}

/* ---------- pasos ---------- */
.un-paso {{display: flex; align-items: center; gap: .6rem; margin: .1rem 0 .6rem;}}
.un-paso span {{
  background: {ROJO}; color: #fff; font-weight: 700; font-size: .85rem;
  width: 1.55rem; height: 1.55rem; display: inline-flex; align-items: center;
  justify-content: center;
}}
.un-paso b {{font-size: 1rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: .03em; color: {NEGRO};}}

/* ---------- tira de horas de un día ---------- */
.un-dia {{display: grid; grid-template-columns: repeat(16, 1fr); gap: 2px; margin: .5rem 0 .2rem;}}
.un-hora {{text-align: center;}}
.un-celda {{height: 28px;}}
.un-hora small {{display: block; margin-top: 3px; font-size: .75rem; color: #6A6A6A;}}
.un-libre {{background: {VERDE};}}
.un-ocupado {{background: {ROJO};}}
.un-desconocido {{background: #E6E6E6;}}
.un-marcada {{box-shadow: 0 0 0 2px {NEGRO}; position: relative; z-index: 1;}}
.un-leyenda {{display: flex; gap: 1.2rem; flex-wrap: wrap; font-size: .82rem; color: #4A4A4A;
             margin: .35rem 0 .8rem;}}
.un-leyenda i {{display: inline-block; width: .8rem; height: .8rem; margin-right: .35rem;
               vertical-align: -1px;}}

/* ---------- horario semanal ---------- */
.un-semana {{display: grid; grid-template-columns: 3.2rem repeat(6, 1fr); gap: 1px;
            font-size: .8rem; margin: .5rem 0 1rem; background: #E2E2E2;
            border: 1px solid #E2E2E2;}}
.un-semana > div {{background: #fff;}}
.un-semana .un-cab {{text-align: center; font-weight: 700; padding: .45rem 0; color: #fff;
                    background: {NEGRO};}}
.un-semana .un-esq {{background: {NEGRO};}}
.un-semana .un-h {{text-align: right; padding-right: .45rem; color: #6A6A6A; line-height: 28px;
                  font-size: .75rem; background: #FAFAFA;}}
.un-semana .un-v {{min-height: 28px;}}
.un-semana .un-clase {{padding: .3rem .45rem; overflow: hidden; line-height: 1.25;
                      margin: 1px;}}
.un-clase b {{display: block; font-weight: 700;}}
.un-clase small {{opacity: .85;}}
</style>
"""

# Colores por materia: fondo claro y borde izquierdo del mismo tono
COLOR_CLASE = [("#FDE7EA", ROJO), ("#FFF4D6", "#C99700"), ("#E8F1FB", "#1F5FA8"),
               ("#E9F5EC", VERDE), ("#F1ECF8", "#6B4C9A"), ("#F2F2F2", "#4A4A4A")]


def cabecera(semestre, fin, ahora_txt, ocupados, libres, sin_info):
    """Barra negra superior + cabecera blanca con el estado del campus en este momento."""
    if ahora_txt is None:
        ahora = ('<div class="un-ahora"><span class="un-cuando">Fuera del horario<br>'
                 'lun-sáb, 6:00-22:00</span></div>')
    else:
        ahora = (f'<div class="un-ahora"><span class="un-cuando">Ahora<br>'
                 f'{escape(ahora_txt)}</span>'
                 f'<div class="un-dato ocupado"><b>{ocupados}</b><small>ocupados</small></div>'
                 f'<div class="un-dato libre"><b>{libres}</b><small>libres</small></div>'
                 f'<div class="un-dato sin"><b>{sin_info}</b><small>sin información</small>'
                 f'</div></div>')
    return f"""
<div class="un-barra">
  <span>MAT 4021 · Matemáticas Discretas · Proyecto final</span>
  <span>Semestre {escape(str(semestre))} · datos válidos hasta {escape(str(fin))}</span>
</div>
<div class="un-cabecera">
  <div>
    <div class="un-titulo">Espacios del campus</div>
    <div class="un-sub">Disponibilidad de salones, laboratorios y escenarios deportivos</div>
  </div>
  {ahora}
</div>"""


def paso(numero, texto):
    """Título de una sección con su número en un recuadro rojo."""
    return f'<div class="un-paso"><span>{numero}</span><b>{escape(texto)}</b></div>'


def leyenda():
    return ('<div class="un-leyenda">'
            '<span><i class="un-libre"></i>Libre</span>'
            '<span><i class="un-ocupado"></i>Ocupado</span>'
            '<span><i class="un-desconocido"></i>Sin información</span>'
            f'<span><i style="box-shadow:0 0 0 2px {NEGRO}"></i>Franja consultada</span>'
            '</div>')


def franja_dia(horas, marcadas=()):
    """Tira con el estado de cada hora de un día.

    `horas`: lista de (hora, estado, detalle) con estado en libre/ocupado/desconocido.
    `marcadas`: horas que se resaltan (la franja que el estudiante consultó).
    """
    celdas = []
    for hora, estado, detalle in horas:
        titulo = f"{hora}:00-{hora + 1}:00 · " + (detalle or estado)
        marca = " un-marcada" if hora in marcadas else ""
        celdas.append(f'<div class="un-hora" title="{escape(titulo)}">'
                      f'<div class="un-celda un-{estado}{marca}"></div>'
                      f'<small>{hora}</small></div>')
    return f'<div class="un-dia">{"".join(celdas)}</div>' + leyenda()


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
    celdas = ['<div class="un-esq"></div>'] + [f'<div class="un-cab">{escape(d)}</div>'
                                               for d in nombres_dias]
    for i, h in enumerate(range(desde, hasta)):
        fila = i + 2
        celdas.append(f'<div class="un-h" style="grid-row:{fila};grid-column:1">{h}:00</div>')
        for d in range(len(nombres_dias)):
            celdas.append(f'<div class="un-v" style="grid-row:{fila};grid-column:{d + 2}"></div>')
    for d, a, b, espacio, materia in clases:
        fondo, borde = colores[materia]
        celdas.append(
            f'<div class="un-clase" style="grid-row:{a - desde + 2}/{b - desde + 2};'
            f'grid-column:{d + 2};background:{fondo};border-left:4px solid {borde};'
            f'color:{NEGRO}" title="{escape(f"{materia} · {espacio} · {a}:00-{b}:00")}">'
            f'<b>{escape(materia)}</b><small>{escape(espacio)} · {a}:00-{b}:00</small></div>')
    return f'<div class="un-semana">{"".join(celdas)}</div>'
