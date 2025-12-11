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

PROMPTS = {
    'look_woman': """Full-body 1980s rock diva on stage, inspired by Tina Turner, 
	based on the reference photo (same face, same bone structure, same eyes, same mouth, same nose, same body type, same proportions, same pose and expression).
	Hair: messy, voluminous, wild 80s blonde hair with textured spiky layers.
	Makeup: bold stage makeup, heavy blush, metallic eyeshadow, glossy red lipstick.
	Wardrobe: silver sequined mini-dress with fringe details, fishnet stockings, high heels, matching bracelets.
	Pose: standing front-facing with legs apart, holding microphone in one hand, the other arm raised pointing upward (same pose as reference).
	Lighting: dramatic warm concert stage lighting with orange, gold, and red tones, backlights and spotlights behind, slight lens flare.
	Background: live band, stage risers, glowing bulbs and stage light structures.
	Photography: high-detail realism, slightly sweaty skin glow, cinematic depth, 1980s analog film grain, crisp highlights.
	Strong energetic performance vibe.
    """,
    'look_man': """Full-body photograph of a male 1980s rock icon on stage, channeling the fierce energy and style of Tina Turner.
	CRITICAL: The output must strictly be based on the reference photo provided (maintaining same facial features, bone structure, eyes, mouth, nose, body type, proportions, specific pose, and intense expression).
	Hair: Messy, voluminous, wild 80s blonde rocker hair with textured spiky layers, teased high.
	Makeup: Bold 80s stage makeup suitable for a male rocker: heavy black "guyliner" and smudged kohl, defined contoured cheekbones, metallic silver eyeshadow, stage lip color. Sweaty skin glow.
	Wardrobe (Adapted for male rocker style): Open sleeveless vest covered in silver sequins with long fringe details swinging, worn over a shredded mesh tank top. Tight distressed leather pants with fishnet cutouts showing underneath. Chunky platform rock boots with heels. Multiple chunky silver chains, studded leather wristbands matching the reference vibe.
	Pose: Standing front-facing with legs apart in a power stance, gripping a microphone intensely in one hand, the other arm raised high pointing upward (exact same pose as reference photo).
	Lighting: Dramatic warm concert stage lighting dominated by orange, gold, and deep red tones; strong backlights creating rim light and spotlights hitting the face, slight anamorphic lens flare.
	Background: Live backing band musicians in shadow, stage risers, glowing industrial bulbs and massive stage light trusses.
	Photography Style: High-detail realism, cinematic depth of field, rich 1980s analog film grain texture, crisp highlights on sweat and sequins. Strong energetic performance vibe radiating from the subject.
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