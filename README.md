# Disponibilidad y uso de espacios del campus (MAT 4021)

Modelo con álgebra booleana (ocupación por franja), grafo ponderado de bloques
(espacio libre más cercano con Dijkstra) y análisis de redes. Incluye una interfaz
web (Streamlit) donde cada estudiante carga su horario y consulta qué espacios
están libres u ocupados.

## Cómo ejecutarlo

### Primera vez (instalación)

```
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
python -m pip install -r requirements.txt
```

### Cada vez que quieras usarlo

- **Windows, lo más fácil:** doble clic en `iniciar.bat` (activa el entorno y abre la app).
- **A mano:**

```
venv\Scripts\activate
python -m streamlit run app.py # interfaz web local (se abre en el navegador)
```

Otros comandos:

```
python main.py                 # caso conocido, conflictos, tutorías, simulación, red
python -m pytest               # pruebas
```

### Configuración

- **Clave de administrador** (para cerrar el semestre): variable de entorno `CLAVE_ADMIN`.
  Si no se define, la clave es `cambiar-esta-clave`: **cámbienla**.
- **Leer el horario desde una foto** es OPCIONAL y usa la IA de Google Gemini. Requiere una
  clave de API gratis (https://aistudio.google.com/apikey). Sin ella, se puede cargar el
  horario a mano, clase por clase. La clave se puede dar de dos formas:

  1. Archivo `.streamlit/secrets.toml` (recomendada; ya está en `.gitignore`, así que no se
     sube a GitHub):

     ```toml
     GEMINI_API_KEY = "tu-clave"
     ```

  2. Variable de entorno. En PowerShell:

     ```
     $env:CLAVE_ADMIN="mi-clave"
     $env:GEMINI_API_KEY="tu-clave"
     python -m streamlit run app.py
     ```

  Si se definen las dos, gana la variable de entorno. Nunca suban la clave a GitHub ni
  compartan el proyecto comprimido con `secrets.toml` adentro.
- **Modelos de IA:** `src/lector_imagen.py` prueba en orden los modelos de
  `MODELOS_POR_DEFECTO`. Para ver cuáles tiene disponibles tu clave, ejecuten
  `python listar_modelos.py` (necesita `GEMINI_API_KEY` como variable de entorno). Para usar
  otros, definan `MODELO_GEMINI` (uno o varios separados por coma).

## Estructura

| Archivo | Qué hace |
|---|---|
| `app.py` | Interfaz Streamlit: buscar libre, qué hay, tutorías, registrar, mi horario, semestre |
| `iniciar.bat` | Atajo de Windows: activa el entorno y abre la app |
| `listar_modelos.py` | Lista los modelos de Gemini disponibles para tu clave |
| `main.py` | Caso conocido, conflictos, tutorías, simulación y análisis de red |
| `src/franjas.py` | Franjas horarias como bits (6 días x 16 horas, 6:00-22:00) |
| `src/tiempo.py` | Hora de Colombia y vencimiento de los usos de una sola vez |
| `src/campus.py` | Espacios, ocupación/información, estados y grafo de bloques |
| `src/codigos.py` | Códigos de salón (26J, 37G2, SDU9, L1-5) -> bloque |
| `src/horario_csv.py` | Lectura y validación de horarios en CSV |
| `src/lector_imagen.py` | Lectura de la foto del horario con IA (opcional) |
| `src/consultas.py` | Libres, más cercano, tutorías, ubicación inferida, cobertura |
| `src/almacen.py` | Guardado en disco (JSON), candado de guardado y ciclo de vida por semestre |
| `src/datos.py` | Campus real, campus de simulación, caso conocido |
| `src/metricas.py` | Modelo de 3 estados vs. ingenuo de 2 estados |
| `tests/` | Pruebas, incluido el caso con resultado conocido |

## Modelo en una línea

Por espacio: `ocupado` e `info` (vectores de bits). Ocupado = bit en `ocupado`;
libre = `info` y no `ocupado`; desconocido = sin `info`. Conflicto al reservar =
`ocupado AND máscara != 0`.

## Usos que se repiten y usos de una sola vez

Los horarios son semanales (no tienen fecha), así que cada uso se trata según su motivo:

- **Clase y tutoría:** se repiten cada semana hasta que termina el semestre.
- **Estudio, reunión y práctica:** ocupan la franja solo la próxima vez que ocurre y se
  borran solos al terminar. El espacio queda *sin información*, no *libre*.

## Códigos de salón

- `26J`, `93K`: número + letra del bloque. `37G2`: el bloque G tiene dos lados (G1, G2).
- `SDU1`-`SDU10`: tabla fija en `src/codigos.py` (bloque y piso).
- `L1-5`, `L1-4`, `L1-3`: laboratorios de física, todos en el bloque `LAB`.

## Semestres: los horarios vencen

- Los datos se guardan en `datos/semestres/<semestre>.json` (no se suben a GitHub).
- Cada semestre tiene fecha de fin. Pasada esa fecha la app deja de mostrar datos y solo
  permite al administrador cerrar el semestre (borrar o archivar) y empezar uno vacío.
- **La fecha de fin por defecto es de ejemplo: ajustarla al calendario académico real.**
- Al cargar su horario, el estudiante usa un código inventado, no su nombre.

## Limitaciones conocidas

- Un espacio solo se asegura como libre u ocupado si alguien lo registró o cargó un horario
  que lo usa; "sin información" no significa libre.
- Los tiempos de caminata entre bloques (`ARISTAS_CAMPUS` en `src/datos.py`) son valores de
  ejemplo y deben medirse en el campus. El tiempo del bloque `LAB` también.
- El código estudiantil no es secreto y no hay contraseña: quien conozca el código de otra
  persona puede ver, corregir o borrar su horario.
- El candado de guardado funciona dentro de un solo proceso de Streamlit (como se ejecuta
  aquí). Si se corrieran varios procesos sobre la misma carpeta `datos/`, harían falta
  otras garantías (por ejemplo, una base de datos).
- La lectura por foto depende de un servicio externo, puede equivocarse y por eso siempre
  se revisa antes de guardar.

## Pendiente para el grupo

- [ ] Medir en el campus los tiempos de caminata reales.
- [ ] Cargar horarios reales y hacer la encuesta de tiempo de búsqueda (manual vs. modelo).
- [ ] Agregar los salones de los demás bloques a `SALONES_BLOQUE` en `src/codigos.py`.
- [ ] Poner la fecha de fin real del semestre.