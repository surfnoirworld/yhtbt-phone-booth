import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

for model in client.models.list():
    if "bidiGenerateContent" in model.supported_generation_methods:
        print(model.name)
