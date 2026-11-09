import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
for m in client.models.list():
    acciones = getattr(m, "supported_actions", None)
    if acciones is None or "generateContent" in acciones:
        print(m.name.replace("models/", ""))