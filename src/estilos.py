"""Piezas visuales (HTML/CSS) de la interfaz: cabecera, pasos, tira de horas y horario semanal.

Solo presentación: no toca el modelo. Los colores de la tira y del horario usan
transparencias para verse bien con el tema claro y con el oscuro (ver
`.streamlit/config.toml`).
"""
from html import escape

CSS = """
<style>
.block-container {max-width: 1080px; padding-top: 1.6rem;}

/* ---------- cabecera ---------- */
.ec-cabecera {
  background: #1B2B44; color: #F6F1E7; border-radius: 14px;
  padding: 1.6rem 1.8rem 1.4rem; margin-bottom: 1rem; position: relative; overflow: hidden;
}
.ec-cabecera::after {            /* tira de horas decorativa, abajo */
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 6px;
  background: repeating-linear-gradient(90deg,
    #2E9E6A 0 9%, transparent 9% 10%, #E4572E 10% 16%, transparent 16% 17%,
    rgba(246,241,231,.25) 17% 30%, transparent 30% 31%);
}
.ec-sello {font-size: .75rem; letter-spacing: .12em; text-transform: uppercase;
           color: #F2A07B; font-weight: 600;}
.ec-titulo {font-family: "Fraunces", Georgia, serif; font-size: 2.3rem; font-weight: 600;
            line-height: 1.1; margin: .35rem 0 .45rem;}
.ec-cabecera p {margin: 0; max-width: 46rem; opacity: .85; font-size: 1rem;}
.ec-ahora {margin-top: 1rem; font-size: .92rem; display: flex; flex-wrap: wrap; gap: .3rem 1.4rem;}
.ec-ahora b {font-family: "Fraunces", Georgia, serif; font-size: 1.35rem; margin-right: .25rem;}
.ec-ahora .ec-p {display: inline-block; width: .6rem; height: .6rem; border-radius: 2px;
                 margin-right: .4rem; vertical-align: 2px;}

/* ---------- pestañas ---------- */
.stTabs [data-baseweb="tab-list"] {gap: 1.2rem;}
.stTabs [data-baseweb="tab"] p {font-size: 1rem; font-weight: 500;}

/* ---------- pasos ---------- */
.ec-paso {display: flex; align-items: baseline; gap: .55rem; margin: .1rem 0 .5rem;}
.ec-paso span {font-family: "Fraunces", Georgia, serif; font-size: 1.05rem; font-weight: 600;
               color: #E4572E;}
.ec-paso b {font-size: 1.02rem; font-weight: 600;}

/* ---------- tira de horas de un día ---------- */
.ec-dia {display: grid; grid-template-columns: repeat(16, 1fr); gap: 3px; margin: .5rem 0 .2rem;}
.ec-hora {text-align: center;}
.ec-celda {height: 30px; border-radius: 4px;}
.ec-hora small {display: block; margin-top: 3px; font-size: .75rem; opacity: .65;}
.ec-libre {background: #2E9E6A;}
.ec-ocupado {background: #E4572E;}
.ec-desconocido {background: rgba(127,127,127,.16);}
.ec-marcada {box-shadow: 0 0 0 2px currentColor;}
.ec-leyenda {display: flex; gap: 1.2rem; flex-wrap: wrap; font-size: .82rem; opacity: .8;
             margin: .3rem 0 .7rem;}
.ec-leyenda i {display: inline-block; width: .75rem; height: .75rem; border-radius: 2px;
               margin-right: .35rem; vertical-align: -1px;}

/* ---------- horario semanal ---------- */
.ec-semana {display: grid; grid-template-columns: 3rem repeat(6, 1fr); gap: 2px;
            font-size: .8rem; margin: .5rem 0 1rem;}
.ec-semana .ec-cab {text-align: center; font-weight: 600; padding: .3rem 0 .4rem;}
.ec-semana .ec-h {text-align: right; padding-right: .45rem; opacity: .55; line-height: 28px;
                  font-size: .75rem;}
.ec-semana .ec-v {min-height: 28px; background: rgba(127,127,127,.06);}
.ec-clase {padding: .3rem .45rem; overflow: hidden; line-height: 1.25; border-radius: 5px;}
.ec-clase b {display: block; font-weight: 600;}
.ec-clase small {opacity: .8;}
</style>
"""

# Colores por materia (r, g, b): tonos de la misma paleta de la app
COLOR_CLASE = ["52,96,160", "228,87,46", "46,158,106", "196,140,40", "92,107,192",
               "170,70,110"]


def cabecera(semestre, fin, ahora_txt, ocupados, libres, sin_info):
    """Cabecera con el estado del campus en este momento."""
    if ahora_txt is None:
        ahora = ('<div class="ec-ahora"><span>Ahora el campus está fuera del horario '
                 'registrado (lunes a sábado, 6:00-22:00).</span></div>')
    else:
        ahora = (
            f'<div class="ec-ahora"><span style="opacity:.75">{escape(ahora_txt)}</span>'
            f'<span><i class="ec-p" style="background:#E4572E"></i><b>{ocupados}</b>ocupados</span>'
            f'<span><i class="ec-p" style="background:#2E9E6A"></i><b>{libres}</b>libres '
            f'confirmados</span>'
            f'<span><i class="ec-p" style="background:rgba(246,241,231,.35)"></i>'
            f'<b>{sin_info}</b>sin información</span></div>')
    return f"""
<div class="ec-cabecera">
  <div class="ec-sello">Espacios del campus · semestre {escape(str(semestre))}</div>
  <div class="ec-titulo">¿Dónde hay un salón libre?</div>
  <p>Revisa cada espacio hora por hora con lo que los estudiantes han registrado, o deja
     registrado el tuyo para que los demás lo sepan. Datos válidos hasta
     {escape(str(fin))}.</p>
  {ahora}
</div>"""


def paso(numero, texto):
    """Título de una sección con su número ('01  Cuándo')."""
    return f'<div class="ec-paso"><span>{numero:02d}</span><b>{escape(texto)}</b></div>'


def leyenda():
    return ('<div class="ec-leyenda">'
            '<span><i class="ec-libre"></i>Libre</span>'
            '<span><i class="ec-ocupado"></i>Ocupado</span>'
            '<span><i class="ec-desconocido"></i>Sin información</span>'
            '<span><i style="box-shadow:0 0 0 2px currentColor"></i>Franja consultada</span>'
            '</div>')


def franja_dia(horas, marcadas=()):
    """Tira con el estado de cada hora de un día.

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
    celdas = ['<div></div>'] + [f'<div class="ec-cab">{escape(d)}</div>'
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
            f'grid-column:{d + 2};background:rgba({rgb},.22);'
            f'box-shadow:inset 0 0 0 1px rgba({rgb},.35)"'
            f' title="{escape(f"{materia} · {espacio} · {a}:00-{b}:00")}">'
            f'<b>{escape(materia)}</b><small>{escape(espacio)} · {a}:00-{b}:00</small></div>')
    return f'<div class="ec-semana">{"".join(celdas)}</div>'
