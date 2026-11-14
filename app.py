"""Interfaz (Streamlit) de espacios del campus.

Uso:  python -m streamlit run app.py
"""
import datetime as dt
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src import almacen
from src.campus import TIPOS
from src.codigos import BLOQUE_LABORATORIOS, LABORATORIOS, asegurar_espacio
from src.consultas import (cobertura, ranking_cercanos, ubicacion_inferida,
                           ver_tutorias)
from src.datos import BLOQUES
from src.franjas import (DIAS, H_FIN, H_INI, TODAS, franja, rango,
                         rangos_texto)
from src.horario_csv import PLANTILLA, aplicar_horario, leer_horario
from src.lector_imagen import imagen_a_csv


BASE = os.environ.get("DATOS_DIR", "datos")
CLAVE_ADMIN = os.environ.get("CLAVE_ADMIN", "cambiar-esta-clave")

NOMBRES_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
ETIQ_TIPO = {"salon": "Salón", "laboratorio": "Laboratorio", "cancha_tenis": "Cancha de tenis",
             "cancha_futbol": "Cancha de fútbol", "piscina": "Piscina",
             "sala_musica": "Sala de música"}
ETIQ_MOTIVO = {"clase": "Clase", "tutoria": "Tutoría", "estudio": "Estudio",
               "reunion": "Reunión", "practica": "Práctica"}
ESTADOS = {"ocupado": "🔴 Ocupado", "libre": "🟢 Libre",
           "desconocido": "⚪ Sin información"}

st.set_page_config(page_title="Espacios del campus", page_icon="🏫")
campus, horarios, semestre = almacen.cargar_o_crear(BASE)
hoy = dt.date.today()
esta_vencido = almacen.vencido(semestre, hoy)


def guardar():
    almacen.guardar_estado(BASE, campus, horarios, semestre)


def etiqueta(espacio):
    piso = f" · Piso {espacio.piso}" if espacio.piso else ""
    nombre = LABORATORIOS.get(espacio.id, ETIQ_TIPO[espacio.tipo])
    return f"{espacio.id} · Bloque {espacio.bloque}{piso} · {nombre}"


def selector_espacio(clave):
    return st.selectbox("Espacio", sorted(campus.espacios),
                        format_func=lambda i: etiqueta(campus.espacios[i]), key=clave)


def selector_franjas(pref):
    c1, c2, c3 = st.columns(3)
    dia = c1.selectbox("Día", range(len(DIAS)), key=f"{pref}_dia",
                       format_func=lambda i: NOMBRES_DIAS[i])
    h_ini = c2.selectbox("Desde", range(H_INI, H_FIN), key=f"{pref}_ini",
                         format_func=lambda h: f"{h}:00")
    h_fin = c3.selectbox("Hasta", range(h_ini + 1, H_FIN + 1), key=f"{pref}_fin",
                         format_func=lambda h: f"{h}:00")
    return dia, h_ini, h_fin


# ---------------------------------------------------------------- buscar
def vista_buscar():
    st.subheader("Buscar un espacio libre")
    st.caption("Solo aparecen espacios que alguien ya registró o cargó en su horario.")
    c1, c2 = st.columns(2)
    dia = c1.selectbox("Día", range(len(DIAS)), key="b_dia",
                       format_func=lambda i: NOMBRES_DIAS[i])
    hora = c2.selectbox("Hora de inicio", range(H_INI, H_FIN), key="b_hora",
                        format_func=lambda h: f"{h}:00")
    duracion = st.slider("Duración (horas)", 1, 4, 2, key="b_dur")
    tipo = st.selectbox("Tipo de espacio", ["cualquiera"] + list(TIPOS), key="b_tipo",
                        format_func=lambda t: "Cualquiera" if t == "cualquiera"
                        else ETIQ_TIPO[t])
    modo = st.radio("¿Dónde estás?", ["Inferir de mi horario", "Elegir bloque"],
                    key="b_modo", horizontal=True)
    origen = None
    if modo == "Elegir bloque":
        origen = st.selectbox("Mi bloque", BLOQUES + [BLOQUE_LABORATORIOS],
                              key="b_bloque")
    elif horarios:
        alias = st.selectbox("Mi código de horario", list(horarios), key="b_alias")
        origen = ubicacion_inferida(campus, almacen.estudiante_de(alias, horarios),
                                    franja(dia, hora))
        if origen:
            st.caption(f"Según tu horario, estás cerca del bloque {origen}.")
        else:
            st.warning("Tu horario no permite saber dónde estás. Elige un bloque.")
    else:
        st.info("Aún no hay horarios cargados. Elige un bloque o carga el tuyo.")
    desconocidos = st.checkbox("Incluir espacios sin información (pueden estar ocupados)",
                               key="b_desc")
    if st.button("Buscar", key="b_buscar", disabled=origen is None):
        if hora + duracion > H_FIN:
            st.error(f"La franja se pasa de las {H_FIN}:00.")
            return
        mascara = rango(dia, hora, hora + duracion)
        tipo_f = None if tipo == "cualquiera" else tipo
        ranking = ranking_cercanos(campus, origen, mascara, tipo_f, desconocidos)[:8]
        if ranking:
            mejor, minutos = ranking[0]
            st.success(f"Más cercano: {mejor.id} (bloque {mejor.bloque}), "
                       f"a {minutos} min caminando.")
            st.table([{"Espacio": e.id, "Bloque": e.bloque, "Tipo": ETIQ_TIPO[e.tipo],
                       "Minutos": m,
                       "Datos": "confirmado" if campus.info[e.id] & mascara == mascara
                       else "sin información"} for e, m in ranking])
        else:
            st.warning("No hay espacios libres confirmados para esa franja. "
                       "Prueba incluyendo los que no tienen información.")
        st.caption(f"Cobertura de datos en esa franja: "
                   f"{cobertura(campus, mascara):.0%}. Con poca cobertura, "
                   "'sin información' no significa libre.")


# ---------------------------------------------------------------- qué hay
def vista_que_hay():
    st.subheader("¿Qué hay en un espacio?")
    esp = selector_espacio("q_esp")
    dia = st.selectbox("Día", range(len(DIAS)), key="q_dia",
                       format_func=lambda i: NOMBRES_DIAS[i])
    filas = []
    for h in range(H_INI, H_FIN):
        f = franja(dia, h)
        r = campus.que_hay(esp, f)
        filas.append({"Hora": f"{h}:00", "Estado": ESTADOS[campus.estado(esp, f)],
                      "Detalle": f"{ETIQ_MOTIVO[r.motivo]}: {r.detalle}" if r else ""})
    st.table(filas)


# ---------------------------------------------------------------- tutorías
def vista_tutorias():
    st.subheader("Espacios ocupados por tutorías")
    tutorias = ver_tutorias(campus)
    if not tutorias:
        st.info("No hay tutorías registradas.")
        return
    st.table([{"Espacio": t.espacio_id, "Bloque": campus.espacios[t.espacio_id].bloque,
               "Cuándo": rangos_texto(t.mascara), "Materia": t.detalle,
               "Confirmaciones": t.confirmaciones} for t in tutorias])


# ---------------------------------------------------------------- registrar
def panel_confirmar(texto, alias, clave):
    """Valida un horario en formato CSV, lo muestra y deja guardarlo."""
    clases, errores = leer_horario(texto, campus)
    for e in errores:
        st.error(e)
    if not clases:
        return
    st.write("Esto es lo que se va a guardar. Revísalo con tu horario al lado:")
    st.table([{"Día": NOMBRES_DIAS[d], "Hora": f"{a}:00-{b}:00", "Salón": c,
               "Materia": m} for d, a, b, c, m in clases])
    if errores:
        st.warning("Las filas con error no se guardarán.")
    if st.button("Guardar este horario", key=f"{clave}_guardar"):
        if not alias:
            st.error("Escribe primero tu código.")
            return
        agregadas, conflictos = aplicar_horario(campus, horarios, alias, clases)
        guardar()
        st.success(f"Se guardaron {agregadas} clases nuevas.")
        for c in conflictos:
            st.error(f"Conflicto: {c}.")


def vista_registrar():
    st.subheader("Ocupar un espacio")
    st.caption("Declara en qué lo vas a usar: así aparecerá ocupado para los demás.")
    codigo = st.text_input("Código del espacio (ej. 26J, 37G2, SDU9, M-tenis)",
                           key="o_esp")
    dia, h_ini, h_fin = selector_franjas("o")
    motivo = st.selectbox("Motivo", [m for m in ETIQ_MOTIVO if m != "clase"],
                          key="o_motivo", format_func=lambda m: ETIQ_MOTIVO[m])
    detalle = st.text_input("¿De qué? (materia, grupo, actividad)", key="o_detalle")
    if st.button("Ocupar", key="o_boton"):
        espacio = asegurar_espacio(campus, codigo) if codigo.strip() else None
        if espacio is None:
            st.error("Código no reconocido. Ejemplos: 26J, 37G2, SDU9, M-tenis.")
        elif not detalle.strip():
            st.error("Escribe en qué lo vas a usar.")
        elif campus.ocupar(espacio.id, rango(dia, h_ini, h_fin), motivo, detalle.strip()):
            guardar()
            st.success("Listo: el espacio quedó ocupado en ese horario.")
        else:
            st.error("Conflicto: ese espacio ya está ocupado en parte de ese horario.")

    st.divider()
    st.subheader("Cargar mi horario")
    st.caption("Usa un código inventado (no tu nombre). Se guarda solo hasta el final "
               "del semestre y se usa para saber en qué bloque estás.")
    alias = st.text_input("Mi código", key="h_alias").strip()

    st.markdown("**Opción 1: subir una foto o captura de tu horario** (la lee una IA)")
    st.caption("La imagen se envía a un servicio de IA externo (Anthropic) solo para "
               "leerla y no se guarda. Recórtala para que no salgan tu nombre ni tu código.")
    imagen = st.file_uploader("Foto del horario", type=["png", "jpg", "jpeg", "webp"],
                              key="h_img")
    if imagen is not None:
        st.image(imagen, caption="Tu horario", width=420)
        if st.button("Leer horario de la imagen", key="h_leer"):
            try:
                with st.spinner("Leyendo la imagen..."):
                    st.session_state["h_img_texto"] = imagen_a_csv(
                        imagen.getvalue(), imagen.type)
            except Exception as error:
                st.error(f"No se pudo leer la imagen: {error}")
    if "h_img_texto" in st.session_state and imagen is not None:
        texto = st.text_area("Lo que leyó la IA (puedes corregirlo antes de guardar)",
                             key="h_img_texto", height=220)
        panel_confirmar(texto, alias, "img")

    st.markdown("**Opción 2: subir un CSV** (una fila por clase)")
    st.download_button("Descargar plantilla CSV", PLANTILLA, file_name="plantilla_horario.csv",
                       mime="text/csv", key="h_plantilla")
    archivo = st.file_uploader("Sube tu horario en CSV", type=["csv"], key="h_csv")
    if archivo is not None:
        panel_confirmar(archivo.getvalue().decode("utf-8-sig", errors="replace"),
                        alias, "csv")

    st.markdown("**Opción 3: agregar una clase a mano**")
    codigo_h = st.text_input("Código del salón (ej. 26J)", key="h_esp")
    dia_h, ini_h, fin_h = selector_franjas("h")
    materia = st.text_input("Materia", key="h_materia")
    if st.button("Agregar clase", key="h_boton"):
        if not alias or not materia.strip():
            st.error("Escribe tu código y la materia.")
        else:
            agregadas, conflictos = aplicar_horario(
                campus, horarios, alias, [(dia_h, ini_h, fin_h, codigo_h, materia.strip())])
            if agregadas:
                guardar()
                st.success("Clase agregada.")
            else:
                st.error("No se pudo agregar: " + (conflictos[0] if conflictos
                                                    else "ya estaba cargada."))
    if alias in horarios:
        st.write("Tus clases cargadas:")
        st.table([{"Cuándo": rangos_texto(((1 << (b - a)) - 1) << a),
                   "Espacio": e, "Materia": m} for a, b, e, m in horarios[alias]])


# ---------------------------------------------------------------- semestre
def vista_semestre():
    st.subheader("Semestre")
    st.write(f"**Semestre vigente:** {semestre['nombre']} · "
             f"**datos válidos hasta:** {semestre['fin']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Registros de uso", len(campus.registros))
    c2.metric("Horarios cargados", len(horarios))
    c3.metric("Cobertura de datos", f"{cobertura(campus, TODAS):.0%}")
    st.caption("Los horarios vencen al terminar el semestre. Cerrar el semestre "
               "borra (o archiva) los datos y empieza uno nuevo vacío.")
    clave = st.text_input("Clave de administrador", type="password", key="s_clave")
    if not clave:
        return
    if clave != CLAVE_ADMIN:
        st.error("Clave incorrecta.")
        return
    nuevo = st.text_input("Nombre del semestre nuevo (ej. 2027-1)", key="s_nuevo")
    fin = st.date_input("Fecha de fin del semestre nuevo", key="s_fin",
                        value=hoy + dt.timedelta(days=120))
    borrar = st.checkbox("Borrar definitivamente los datos del semestre anterior "
                         "(recomendado por privacidad)", value=True, key="s_borrar")
    conf = st.text_input(f"Para confirmar escribe: {semestre['nombre']}", key="s_conf")
    if st.button("Cerrar semestre y empezar uno nuevo", key="s_cerrar"):
        if conf != semestre["nombre"]:
            st.error("La confirmación no coincide.")
        elif not nuevo.strip() or nuevo.strip() == semestre["nombre"]:
            st.error("Escribe un nombre nuevo distinto al actual.")
        else:
            almacen.cerrar_semestre(BASE, semestre, nuevo.strip(), fin, borrar)
            st.success("Semestre cerrado. Empezó uno nuevo vacío.")
            st.rerun()


# ---------------------------------------------------------------- principal
st.title("🏫 Espacios del campus")
st.caption(f"Semestre {semestre['nombre']} · datos válidos hasta {semestre['fin']}")

if esta_vencido:
    st.error(f"El semestre {semestre['nombre']} terminó el {semestre['fin']}. "
             "Sus horarios ya no son válidos: el administrador debe cerrar el semestre.")
    vista_semestre()
    st.stop()

pestanas = st.tabs(["Buscar libre", "¿Qué hay?", "Tutorías", "Registrar", "Semestre"])
for pestana, vista in zip(pestanas, [vista_buscar, vista_que_hay, vista_tutorias,
                                     vista_registrar, vista_semestre]):
    with pestana:
        vista()