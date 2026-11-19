## Qué necesitas tener instalado

| Qué | Para qué | Notas |
|---|---|---|
| **Python 3.12 o superior** | Ejecutar el programa | Descárgalo de https://www.python.org/downloads/. **En Windows, marca la casilla «Add python.exe to PATH»** al instalar. Con versiones anteriores a 3.12 algunas librerías (como `networkx`) no se instalan. |
| **Un navegador moderno** | Ver la interfaz | Chrome, Edge o Firefox. |
| **Conexión a internet** | Instalar las librerías (solo la primera vez) y, opcionalmente, leer el horario desde una foto | El resto de la app funciona sin internet. |
| Git *(opcional)* | Descargar el proyecto con `git clone` | Si no lo tienes, se baja como ZIP desde GitHub. |
| Clave de Gemini *(opcional)* | Solo para leer el horario desde una foto | Ver «Configuración» más abajo. |
| Tectonic o XeLaTeX *(opcional)* | Solo para volver a compilar el documento y las diapositivas | Ver «Documento y diapositivas». |

Las librerías de Python (`streamlit`, `networkx`, `matplotlib`, `google-genai`, `pytest`, entre
otras) **no hay que instalarlas a mano**: el paso 3 las instala todas desde `requirements.txt`.

Para comprobar que Python quedó bien instalado, abre una terminal y escribe:

```
python --version
```

Debe mostrar `Python 3.12` o superior. Si dice que no reconoce el comando, prueba con
`py --version`. Si no lo tienes, instálalo desde python.org y marca la casilla “Add Python to PATH” durante la instalación.

## Cómo abrirlo y ejecutarlo

### 1. Descargar el proyecto

- **Con Git:**

  ```
  git clone https://github.com/lau-240/Proyecto-final-Matem-ticas-Discretas.git
  ```

- **Sin Git:** en la página del repositorio en GitHub, botón **Code → Download ZIP**, y
  extraer el ZIP.

Entra a la carpeta que contiene `app.py`. Si al extraer el ZIP quedó una carpeta dentro de
otra, entra a la de adentro.

### 2. Abrir una terminal en esa carpeta

- **Desde el Explorador de archivos:** entra a la carpeta, haz clic en la barra de
  direcciones, escribe `powershell` y pulsa Enter.
- **O desde VS Code:** *Archivo → Abrir carpeta*, elige la carpeta, y luego
  *Terminal → Nueva terminal*.

Para comprobar que estás en el sitio correcto, escribe `dir`: debes ver `app.py`, `main.py`
y `requirements.txt`.

### 3. Instalación (solo la primera vez)

```
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

- Después del segundo comando, el inicio de la línea debe mostrar `(venv)`.
- Si PowerShell dice que la ejecución de scripts está deshabilitada, escribe
  `Set-ExecutionPolicy -Scope Process Bypass` y vuelve a ejecutar `venv\Scripts\activate`.
- En Mac o Linux: `python3 -m venv venv` y `source venv/bin/activate`.

### 4. Abrir y ejecutar la app

```
python -m streamlit run app.py
```

- La app se abre sola en el navegador en **http://localhost:8501**. Si no se abre, copia esa
  dirección en el navegador.
- La primera vez Streamlit puede pedir un correo: déjalo vacío y pulsa Enter.
- **No cierres la terminal mientras uses la app.** Para detenerla, pulsa `Ctrl + C` en la
  terminal.
- Desde otro dispositivo conectado a la misma red Wi-Fi se puede abrir la «Network URL» que
  aparece en la terminal (si Windows pregunta por el firewall, permite las redes privadas).
- Los datos se guardan en la carpeta `datos/`, que se crea sola.

### 5. Las próximas veces

- **Lo más fácil (Windows):** doble clic en `iniciar.bat`. Activa el entorno y abre la app.
  Solo funciona si ya hiciste el paso 3 una vez, porque necesita la carpeta `venv`.
- **A mano:** abre la terminal en la carpeta, escribe `venv\Scripts\activate` y luego
  `python -m streamlit run app.py`.

### 6. Comprobar que todo funciona

```
python -m pytest               # debe terminar con «passed» y ningún «failed»
python main.py                 # demostración del modelo: caso conocido, simulación y red
```

`main.py` también guarda un gráfico del campus en `resultados/campus.png`.

### 7. Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `python` no se reconoce | Python quedó sin PATH: reinstálalo marcando «Add python.exe to PATH», o usa `py` en lugar de `python`. |
| `No module named streamlit` (u otra librería) | No está activado el entorno (no se ve `(venv)`) o falta el paso 3. |
| `iniciar.bat` se cierra enseguida | Falta crear el entorno: haz el paso 3 una vez. |
| `pytest` no se reconoce | Usa siempre `python -m pytest`. |
| La página no abre o el puerto está ocupado | `python -m streamlit run app.py --server.port 8502` y abre http://localhost:8502. |
| No puedo cerrar el semestre | Falta definir `CLAVE_ADMIN` (ver «Configuración»). |
| Leer el horario desde la foto da error | Falta la clave de Gemini o no hay internet. Usa «agregar una clase a mano». |

### Configuración

- **Clave de administrador** (para cerrar el semestre): `CLAVE_ADMIN`, como variable de
  entorno o en `.streamlit/secrets.toml` (igual que la clave de la IA, ver abajo). No tiene
  valor por defecto: si no se define, la app avisa y nadie puede cerrar el semestre.
- **Leer el horario desde una foto** es OPCIONAL y usa la IA de Google Gemini. Requiere una
  clave de API gratis (https://aistudio.google.com/apikey). Sin ella, se puede cargar el
  horario a mano, clase por clase. La clave se puede dar de dos formas:

  1. Archivo `.streamlit/secrets.toml` (recomendada; ya está en `.gitignore`, así que no se
     sube a GitHub):

     ```toml
     GEMINI_API_KEY = "tu-clave"
     CLAVE_ADMIN = "mi-clave"
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
  `MODELOS_POR_DEFECTO`. Para comprobar la clave, ver si cada modelo responde y listar los
  que tiene disponibles tu clave, ejecuten `python probar_ia.py` (lee la clave de la
  variable de entorno o de `secrets.toml`). Para usar otros, definan `MODELO_GEMINI` (uno o
  varios separados por coma).
