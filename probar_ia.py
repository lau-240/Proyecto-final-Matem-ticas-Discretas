"""Prueba la conexion con Gemini y cada modelo del lector, con limite de tiempo.

Uso (con el entorno activado, dentro de la carpeta del proyecto):
    python probar_ia.py
Lee la clave de GEMINI_API_KEY o, si no existe, de .streamlit/secrets.toml.
Nunca imprime la clave.
"""
import os
import time
import tomllib


def leer_clave():
    clave = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if clave:
        return clave, "variable de entorno"
    ruta = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(ruta):
        return None, f"no hay variable de entorno ni existe {ruta}"
    try:
        with open(ruta, "rb") as f:
            datos = tomllib.load(f)
    except tomllib.TOMLDecodeError as error:
        return None, (f"{ruta} tiene un error de formato ({error}). Debe ser una sola "
                      'linea:  GEMINI_API_KEY = "tu-clave"')
    if not datos.get("GEMINI_API_KEY"):
        return None, f"{ruta} no tiene GEMINI_API_KEY"
    return datos["GEMINI_API_KEY"], ruta


def main():
    clave, origen = leer_clave()
    if not clave:
        print("PROBLEMA con la clave:", origen)
        return
    print(f"Clave encontrada en: {origen} ({len(clave)} caracteres)")

    from google import genai
    from google.genai import types
    from src import lector_imagen

    cliente = genai.Client(api_key=clave, http_options=types.HttpOptions(timeout=20_000))
    try:
        disponibles = sorted(m.name.replace("models/", "") for m in cliente.models.list())
    except Exception as error:
        print("NO se pudo conectar con Gemini (clave invalida, sin internet o bloqueado):")
        print("  ", str(error)[:300])
        return
    print(f"Conexion OK: tu clave ve {len(disponibles)} modelos.\n")

    for modelo in lector_imagen.MODELOS:
        existe = "existe" if modelo in disponibles else "NO aparece en tu lista"
        print(f"Modelo {modelo} ({existe}):")
        try:
            lector_imagen._llamar(cliente, modelo, ["Responde solo con la palabra: ok"])
            print("   -> RESPONDE\n")
        except Exception as error:
            print("   -> FALLA:", str(error)[:200], "\n")

    sugeridos = [m for m in disponibles if "flash" in m and "gemini" in m][:10]
    print("Modelos 'flash' disponibles (puedes ponerlos en MODELO_GEMINI, separados por coma):")
    print("  " + ", ".join(sugeridos))


if __name__ == "__main__":
    main()