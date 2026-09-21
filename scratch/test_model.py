import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

def test_inference(model_name="gemini-3.1-pro-preview"):
    print(f"Testing {model_name} with thinking_level=HIGH...")
    try:
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH),
            temperature=0.1
        )
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'OK 3.1 Pro en HIGH funcionando'",
            config=config
        )
        print("Success:", response.text)
        return True
    except Exception as e:
        print("Failed:", e)
        return False

test_inference("gemini-3.1-pro-preview")
