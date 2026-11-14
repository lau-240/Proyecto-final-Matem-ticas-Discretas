# Disponibilidad y uso de espacios del campus (MAT 4021)

Modelo con álgebra booleana (ocupación por franja), grafo ponderado de bloques
(espacio libre más cercano con Dijkstra) y análisis de redes. Incluye una interfaz
web (Streamlit) donde cada estudiante carga su horario y consulta qué espacios
están libres u ocupados.

## Cómo ejecutarlo

```
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
python -m pip install -r requirements.txt
python main.py                 # caso conocido, conflictos, tutorías, simulación, red
python -m streamlit run app.py # interfaz web local (se abre en el navegador)
python -m pytest               # pruebas
```

- Clave de administrador (para cerrar el semestre): variable de entorno `CLAVE_ADMIN`.
  Si no se define, la clave es `cambiar-esta-clave`: **cámbienla**.
- Leer el horario desde una foto es OPCIONAL y requiere una clave de API:
  variable de entorno `ANTHROPIC_API_KEY`. Sin ella, se puede cargar el horario por CSV
  o a mano. Nunca guarden la clave en un archivo del proyecto ni la suban a GitHub.

En PowerShell:
```
$env:CLAVE_ADMIN="mi-clave"
$env:ANTHROPIC_API_KEY="tu-clave"
python -m streamlit run app.py
```

## Estructura

| Archivo | Qué hace |
|---|---|
| `app.py` | Interfaz Streamlit: buscar libre, qué hay, tutorías, registrar, semestre |
| `main.py` | Caso conocido, conflictos, tutorías, simulación y análisis de red |
| `src/franjas.py` | Franjas horarias como bits (6 días x 16 horas, 6:00-22:00) |
| `src/campus.py` | Espacios, ocupación/información, estados y grafo de bloques |
| `src/codigos.py` | Códigos de salón (26J, 37G2, SDU9, L1-5) -> bloque |
| `src/horario_csv.py` | Lectura y validación de horarios en CSV |
| `src/lector_imagen.py` | Lectura de la foto del horario con IA (opcional) |
| `src/consultas.py` | Libres, más cercano, tutorías, ubicación inferida, cobertura |
| `src/almacen.py` | Guardado en disco (JSON) y ciclo de vida por semestre |
| `src/datos.py` | Campus real, campus de simulación, caso conocido |
| `src/metricas.py` | Modelo de 3 estados vs. ingenuo de 2 estados |
| `tests/` | Pruebas, incluido el caso con resultado conocido |

## Modelo en una línea

Por espacio: `ocupado` e `info` (vectores de bits). Ocupado = bit en `ocupado`;
libre = `info` y no `ocupado`; desconocido = sin `info`. Conflicto al reservar =
`ocupado AND máscara != 0`.

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

- Un espacio solo aparece en la app cuando alguien lo registra o carga un horario que lo usa;
  "sin información" no significa libre.
- Los tiempos de caminata entre bloques (`ARISTAS_CAMPUS` en `src/datos.py`) son valores de
  ejemplo y deben medirse en el campus. El tiempo del bloque `LAB` también.
- Borrar un horario no deshace las confirmaciones ya sumadas a clases compartidas.
- La lectura por foto depende de un servicio externo, puede equivocarse y por eso siempre
  se revisa antes de guardar.

## Pendiente para el grupo

- [ ] Medir en el campus los tiempos de caminata reales.
- [ ] Cargar horarios reales y hacer la encuesta de tiempo de búsqueda (manual vs. modelo).
- [ ] Decidir cuándo expira una ocupación declarada sin confirmar (`Campus.liberar`).