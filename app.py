"""Interfaz (Streamlit) de espacios del campus.

Uso:  python -m streamlit run app.py
"""
import datetime as dt
import os

import streamlit as st

from src import almacen
from src.campus import TIPOS
from src.codigos import BLOQUE_LABORATORIOS, LABORATORIOS, asegurar_espacio
from src.consultas import (cobertura, estado_en_ventana, ids_de_bloque,
                           ranking_cercanos, ubicacion_inferida, ver_tutorias)
from src.datos import BLOQUES
from src.franjas import (DIAS, H_FIN, H_INI, TODAS, franja, rango,
                         rangos_texto)
from src.horario_csv import (aplicar_horario, borrar_clase, borrar_horario,
                             leer_horario)
from src.lector_imagen import imagen_a_csv

# Pasa la clave de .streamlit/secrets.toml a una variable de entorno,
# que es donde la busca src/lector_imagen.py
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ.setdefault("GEMINI_API_KEY", st.secrets["GEMINI_API_KEY"])
except Exception:
    pass  # si no hay secrets.toml, se usa la variable de entorno normal

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

OTRO = "__otro__"                      # opción "escribir un código" del selector de salón
OPCIONES_BLOQUE = BLOQUES + [BLOQUE_LABORATORIOS]
REVISAR = "Revisar un salón (elige bloque y salón)"
CERCANO = "Encontrar el espacio libre más cercano a mí"

st.set_page_config(page_title="Espacios del campus", page_icon="🏫")
campus, horarios, semestre = almacen.cargar_o_crear(BASE)
hoy = dt.date.today()
esta_vencido = almacen.vencido(semestre, hoy)


def guardar():
    almacen.guardar_estado(BASE, campus, horarios, semestre)


def etiqueta_salon(espacio):
    """Texto corto para la lista de salones de un bloque."""
    piso = f" · piso {espacio.piso}" if espacio.piso else ""
    nombre = LABORATORIOS.get(espacio.id)
    if nombre is None and espacio.tipo != "salon":
        nombre = ETIQ_TIPO[espacio.tipo]
    return f"{espacio.id}{piso}" + (f" · {nombre}" if nombre else "")


def selector_salon(pref):
    """Primero el bloque y después el salón exacto. Devuelve el id o None."""
    c1, c2 = st.columns(2)
    bloque = c1.selectbox(
        "Bloque", OPCIONES_BLOQUE, key=f"{pref}_bloque",
        format_func=lambda b: f"Bloque {b} · {len(ids_de_bloque(campus, b))} espacios")
    ids = ids_de_bloque(campus, bloque)
    elegido = c2.selectbox(
        "Salón", ids + [OTRO], key=f"{pref}_salon",
        format_func=lambda i: "Otro (escribir código)" if i == OTRO
        else etiqueta_salon(campus.espacios[i]))
    if not ids:
        st.caption("Aún no hay salones confirmados en este bloque: escribe el código.")
    if elegido != OTRO:
        return elegido
    codigo = st.text_input("Código del salón (ej. 25E, 37G2)", key=f"{pref}_codigo")
    if not codigo.strip():
        return None
    espacio = asegurar_espacio(campus, codigo)
    if espacio is None:
        st.error("Código no reconocido (o no existe en ese bloque). Revisa cómo lo escribiste.")
        return None
    if espacio.bloque != bloque:
        st.error(f"El código {espacio.id} es del bloque {espacio.bloque}, no del {bloque}.")
        return None
    return espacio.id


def tabla_dia(espacio_id, dia):
    """Estado hora por hora de un espacio en un día."""
    filas = []
    for h in range(H_INI, H_FIN):
        f = franja(dia, h)
        r = campus.que_hay(espacio_id, f)
        filas.append({"Hora": f"{h}:00", "Estado": ESTADOS[campus.estado(espacio_id, f)],
                      "Detalle": f"{ETIQ_MOTIVO[r.motivo]}: {r.detalle}" if r else ""})
    st.table(filas)


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
def revisar_salon(dia, hora, duracion):
    """El estudiante elige bloque y salón exacto y se le dice si está libre."""
    espacio_id = selector_salon("b")
    if hora + duracion > H_FIN:
        st.error(f"La franja se pasa de las {H_FIN}:00.")
        return
    if espacio_id is None:
        st.info("Elige un bloque y un salón.")
        return
    mascara = rango(dia, hora, hora + duracion)
    estado, registros = estado_en_ventana(campus, espacio_id, mascara)
    ventana = f"{NOMBRES_DIAS[dia]} de {hora}:00 a {hora + duracion}:00"
    if estado == "libre":
        st.success(f"🟢 {espacio_id} está libre el {ventana}.")
    elif estado == "ocupado":
        st.error(f"🔴 {espacio_id} está ocupado el {ventana}.")
        for r in registros:
            st.write(f"- {rangos_texto(r.mascara & mascara)}: "
                     f"{ETIQ_MOTIVO[r.motivo]} · {r.detalle}")
    elif estado == "parcial":
        st.warning(f"⚪ No hay ocupaciones registradas en {espacio_id} el {ventana}, pero "
                   "faltan datos de algunas horas: no se puede asegurar que esté libre.")
    else:
        st.warning(f"⚪ Sin información de {espacio_id} el {ventana}. "
                   "Sin información no significa libre.")
    st.write(f"Estado de {espacio_id} hora por hora ({NOMBRES_DIAS[dia]}):")
    tabla_dia(espacio_id, dia)


def buscar_cercano(dia, hora, duracion):
    """Lista los espacios libres ordenados por cercanía a donde está el estudiante."""
    tipo = st.selectbox("Tipo de espacio", ["cualquiera"] + list(TIPOS), key="b_tipo",
                        format_func=lambda t: "Cualquiera" if t == "cualquiera"
                        else ETIQ_TIPO[t])
    modo = st.radio("¿Dónde estás?", ["Inferir de mi horario", "Elegir bloque"],
                    key="b_modo", horizontal=True)
    origen = None
    if modo == "Elegir bloque":
        origen = st.selectbox("Mi bloque", OPCIONES_BLOQUE, key="bc_bloque")
    elif horarios:
        alias = st.text_input("Mi código estudiantil", key="b_alias").strip()
        if alias in horarios:
            origen = ubicacion_inferida(campus, almacen.estudiante_de(alias, horarios),
                                        franja(dia, hora))
            if origen:
                st.caption(f"Según tu horario, estás cerca del bloque {origen}.")
            else:
                st.warning("Tu horario no permite saber dónde estás. Elige un bloque.")
        elif alias:
            st.warning("No hay un horario cargado con ese código. "
                       "Cárgalo en Registrar o elige un bloque.")
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


def vista_buscar():
    st.subheader("Buscar un espacio libre")
    st.caption("Un salón sin información no se considera libre: solo se asegura lo que "
               "alguien ya registró o cargó en su horario.")
    c1, c2 = st.columns(2)
    dia = c1.selectbox("Día", range(len(DIAS)), key="b_dia",
                       format_func=lambda i: NOMBRES_DIAS[i])
    hora = c2.selectbox("Hora de inicio", range(H_INI, H_FIN), key="b_hora",
                        format_func=lambda h: f"{h}:00")
    duracion = st.slider("Duración (horas)", 1, 4, 2, key="b_dur")
    objetivo = st.radio("¿Qué quieres hacer?", [REVISAR, CERCANO], key="b_objetivo")
    if objetivo == REVISAR:
        revisar_salon(dia, hora, duracion)
    else:
        buscar_cercano(dia, hora, duracion)


# ---------------------------------------------------------------- qué hay
def vista_que_hay():
    st.subheader("¿Qué hay en un espacio?")
    esp = selector_salon("q")
    dia = st.selectbox("Día", range(len(DIAS)), key="q_dia",
                       format_func=lambda i: NOMBRES_DIAS[i])
    if esp is None:
        st.info("Elige un bloque y un salón.")
        return
    tabla_dia(esp, dia)


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
    espacio_id = selector_salon("o")
    dia, h_ini, h_fin = selector_franjas("o")
    motivo = st.selectbox("Motivo", [m for m in ETIQ_MOTIVO if m != "clase"],
                          key="o_motivo", format_func=lambda m: ETIQ_MOTIVO[m])
    detalle = st.text_input("¿De qué? (materia, grupo, actividad)", key="o_detalle")
    if st.button("Ocupar", key="o_boton"):
        if espacio_id is None:
            st.error("Elige el bloque y el salón (o escribe un código válido).")
        elif not detalle.strip():
            st.error("Escribe en qué lo vas a usar.")
        elif campus.ocupar(espacio_id, rango(dia, h_ini, h_fin), motivo, detalle.strip()):
            guardar()
            st.success("Listo: el espacio quedó ocupado en ese horario.")
        else:
            st.error("Conflicto: ese espacio ya está ocupado en parte de ese horario.")

    st.divider()
    st.subheader("Cargar mi horario")
    st.caption("Escribe tu código estudiantil. Se guarda solo hasta el final del "
               "semestre y se usa para saber en qué bloque estás y para que puedas "
               "borrar tu horario.")
    alias = st.text_input("Mi código estudiantil", key="h_alias").strip()

    st.markdown("**Opción 1: subir una foto o captura de tu horario** (la lee una IA)")
    st.caption("La imagen se envía a un servicio de IA externo (Google Gemini) solo para "
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

    st.markdown("**Opción 2: agregar una clase a mano**")
    espacio_h = selector_salon("h")
    dia_h, ini_h, fin_h = selector_franjas("h")
    materia = st.text_input("Materia", key="h_materia")
    if st.button("Agregar clase", key="h_boton"):
        if not alias or not materia.strip():
            st.error("Escribe tu código y la materia.")
        elif espacio_h is None:
            st.error("Elige el bloque y el salón (o escribe un código válido).")
        else:
            agregadas, conflictos = aplicar_horario(
                campus, horarios, alias, [(dia_h, ini_h, fin_h, espacio_h, materia.strip())])
            if agregadas:
                guardar()
                st.success("Clase agregada.")
            else:
                st.error("No se pudo agregar: " + (conflictos[0] if conflictos
                                                    else "ya estaba cargada."))
    if "h_aviso" in st.session_state:
        st.success(st.session_state.pop("h_aviso"))
    if alias in horarios:
        st.write("Tus clases cargadas:")
        st.table([{"Cuándo": rangos_texto(((1 << (b - a)) - 1) << a),
                   "Espacio": e, "Materia": m} for a, b, e, m in horarios[alias]])
        st.markdown("**Borrar información de mi horario**")

        def texto_clase(i):
            a, b, e, m = horarios[alias][i]
            return f"{rangos_texto(((1 << (b - a)) - 1) << a)} · {e} · {m}"

        elegida = st.selectbox("Clase a borrar", range(len(horarios[alias])),
                               format_func=texto_clase, key="h_borrar_sel")
        if st.button("Borrar esta clase", key="h_borrar_uno"):
            borrar_clase(campus, horarios, alias, elegida)
            guardar()
            st.session_state.pop("h_borrar_sel", None)
            st.session_state["h_aviso"] = "Clase borrada."
            st.rerun()
        seguro = st.checkbox("Sí, quiero borrar TODO mi horario", key="h_borrar_conf")
        if st.button("Borrar todo mi horario", key="h_borrar_todo", disabled=not seguro):
            n = borrar_horario(campus, horarios, alias)
            guardar()
            st.session_state.pop("h_borrar_sel", None)
            st.session_state.pop("h_borrar_conf", None)
            st.session_state["h_aviso"] = f"Se borraron {n} clases de tu horario."
            st.rerun()


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