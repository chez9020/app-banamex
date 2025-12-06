# ai_generation.py
import os
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()
# Crea el cliente una sola vez

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Falta GOOGLE_API_KEY. Ponla en tu entorno o en un archivo .env"
    )

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Tus prompts por personaje (idénticos a los que ya tienes)
PROMPTS = {
    'look_woman': """1980s rock diva portrait, style of Tina Turner. Massive voluminous wild spiky blonde-streaked hair, explosive hair texture. 
    Bold 80s stage makeup, heavy blush, shiny red lipstick. Wearing a distressed black leather jacket over a sequined mini-dress, fishnet details. 
    Sweaty glowing skin. Dramatic concert stage lighting with colored gels (red and blue lights), gritty analog film grain, powerful confident energy.
    """,
    'look_man': """1980s male rock star portrait, channeling the grit and swagger style of Tina Turner.
    Big textured voluminous rocker hair, teased and wild (glam metal style). Wearing an open distressed denim vest with studs over bare chest, 
    lots of chunky silver chains and leather wristbands. Intense sweaty face, strong jawline, "guyliner" (smudged eyeliner). 
    Warm intense stage spotlights creating deep shadows, coarse film photograph texture, rebellious attitude.
    """
}


def generate_with_gemini(image_path: str, character: str) -> Image.Image:
    user_img = Image.open(image_path).convert("RGB")
    # Usa 'look_man' como fallback si no encuentra el character
    base = PROMPTS.get(character, PROMPTS['look_man'])
    full_prompt = f"{base}"

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[full_prompt, user_img]
    )
    
    # Manejo de respuesta actualizado según docs
    if hasattr(response, 'parts'):
        for part in response.parts:
            # Check for inline_data (image)
            if hasattr(part, 'inline_data') and part.inline_data is not None:
                try:
                    # Intenta usar .as_image() si devuelve PIL, sino busca sus bytes
                    img_candidate = part.as_image()
                    # Si devuelve un objeto de google.genai..., convertimos
                    if not isinstance(img_candidate, Image.Image):
                        # Caso: devuelve un google.genai.types.Image
                        # Intentamos extraer bytes si tiene método .save() a buffer o propiedades raw
                        # Pero lo más seguro es usar los bytes originales del part.inline_data
                        return Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                    return img_candidate
                except AttributeError:
                    # Fallback standard extraction
                    return Image.open(BytesIO(part.inline_data.data)).convert("RGB")
            # If text, we can ignore or log
            elif hasattr(part, 'text') and part.text:
                print(f"Modelo retornó texto: {part.text}")

    # Si no encontró imagen
    raise RuntimeError("La respuesta no incluyó imagen generada.")