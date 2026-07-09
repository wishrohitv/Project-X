from google import genai
from settings import Settings

client = genai.Client()


def generate_bot_response(query: str) -> str | None:
    response = client.models.generate_content(
        model=Settings.GEMINI_MODEL_NAME or "gemini-3.5-flash",
        contents=str(query),
    )
    return response.text
