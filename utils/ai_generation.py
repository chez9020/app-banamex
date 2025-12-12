# ai_generation.py
import os
from io import BytesIO  # Aquí importas BytesIO directamente
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Falta GOOGLE_API_KEY. Ponla en tu entorno o en un archivo .env"
    )

# Crea el cliente una sola vez
client = genai.Client(api_key=API_KEY)

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


def generate_with_gemini(image_path: str, character: str, output_video_path: str) -> str:
    """
    Genera un video a partir de la imagen dada usando Veo 3.1.
    """
    # 1. Abrir la imagen con PIL
    user_img = Image.open(image_path).convert("RGB")
    
    # 2. CONVERSIÓN CRÍTICA: Convertir PIL a Bytes
    # Corrección: Usamos BytesIO() directamente porque ya lo importaste arriba
    bytes_buffer = BytesIO() 
    user_img.save(bytes_buffer, format="JPEG") # Forzamos formato JPEG
    image_bytes = bytes_buffer.getvalue()

    base_prompt = PROMPTS.get(character, PROMPTS['look_man'])
    video_prompt = f"Cinematic slow motion shot. {base_prompt}"

    print("Iniciando generación de video con Veo 3.1...")
    
    # 3. Preparar el objeto Image correcto para el SDK
    image_input = types.Image(
        image_bytes=image_bytes,
        mime_type="image/jpeg"
    )

    # Llamada a Veo 3.1
    operation = client.models.generate_videos(
        model="veo-3.1-fast-generate-preview",
        prompt=video_prompt,
        image=image_input,
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16"
        ),
    )

    # Polling hasta que termine
    while not operation.done:
        print("Esperando generación de video...")
        time.sleep(5)
        operation = client.operations.get(operation)

    # Descargar y guardar
    if operation.response and operation.response.generated_videos:
        video_result = operation.response.generated_videos[0]
        
        # Descargar el contenido del video remoto antes de guardar
        print("Descargando video generado...")
        client.files.download(file=video_result.video)
        
        video_result.video.save(output_video_path)
        print(f"Video guardado en {output_video_path}")
        return output_video_path
    
    raise RuntimeError("La operación terminó pero no se generó video.")