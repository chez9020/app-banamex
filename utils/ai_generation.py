# ai_generation.py
import os
from io import BytesIO  # Aquí importas BytesIO directamente
from PIL import Image
# from google import genai
# from google.genai import types
from dotenv import load_dotenv
import time
import replicate  # Nueva importación

load_dotenv()

# --- Configuración antigua de Google ---
# API_KEY = os.getenv("GOOGLE_API_KEY")
# if not API_KEY:
#     raise RuntimeError(
#         "Falta GOOGLE_API_KEY. Ponla en tu entorno o en un archivo .env"
#     )
# client = genai.Client(api_key=API_KEY)

PROMPTS = {
    'look_woman': """
    High-fidelity cinematic 1980s music video footage shot on vintage 35mm film.
    SUBJECT: The woman from the reference photo performing as a legendary 80s Powerhouse Rock Diva.
    IDENTITY LOCK: It is critical to preserve the exact facial features, bone structure, and expression of the provided reference image. Do not change the face.
    HAIR: Massive, wild, voluminous, textured "lion mane" hairstyle typical of 1980s rock icons. Spiky and layered.
    WARDROBE: A sparkling silver sequined mini-dress covered in long, dynamic fringe layers that swing and sway with movement. Fishnet stockings and high heels.
    ACTION: She stands in a wide, energetic power stance on a concert stage, holding a microphone. Strong, fierce attitude. The fringe on her dress is moving dynamically.
    LIGHTING & ATMOSPHERE: Hazy, smoky stage with dramatic warm backlighting (orange and gold spotlights) creating a rim-light silhouette. Lens flares, slightly sweaty glowing skin, cinematic grain.
    """,
    'look_man': """
    Cinematic 1980s concert footage, raw and energetic style.
    SUBJECT: The man from the reference photo performing as an 80s Glam Rock Soul Icon.
    IDENTITY LOCK: Maintain absolute facial resemblance to the reference image. Keep the user's natural skin tone and facial structure intact.
    HAIR: Wild, teased, gravity-defying 80s spiky hair with volume. Sweaty and textured.
    WARDROBE: A glittering silver open vest (sequins or chainmail) with hanging fringe details, worn over a shredded mesh tank top. Tight distressed leather pants or acid-wash denim.
    ACTION: Intense performance energy. He holds the microphone stand aggressively with legs apart in a power squat stance. Raw rock energy.
    LIGHTING & ATMOSPHERE: High-contrast stage lighting with beams of light cutting through stage fog. Golden and amber tones. Volumetric lighting, 35mm film grain, handheld camera shake for realism.
    """
}


def generate_with_gemini(image_path: str, character: str, output_video_path: str) -> str:
    """
    Genera un video a partir de la imagen dada usando Replicate (Runway Gen-4 Turbo).
    (El nombre de la función se mantiene por compatibilidad).
    """
    base_prompt = PROMPTS.get(character, PROMPTS['look_man'])
    video_prompt = f"Keep the same style and mood of the reference photo.{base_prompt}"

    print("Iniciando generación de video con Replicate (Gen-4 Turbo)...")

    # --- Lógica de Replicate (Runway Gen-4 Turbo) ---
    try:
        with open(image_path, "rb") as input_image_file:
            output = replicate.run(
                #"runwayml/gen4-turbo",
                 "google/veo-3.1-fast",
                input={
                    "image": input_image_file,
                    "prompt": video_prompt,
                    "duration": 6,
                    "aspect_ratio": "9:16",
                    "resolution": "720p",
                    "generate_audio": False
                }
            )
        
        # Guardar el resultado
        print(f"Video generado, URL: {getattr(output, 'url', 'N/A')}")
        
        # El output de Replicate para gen4-turbo es un FileOutput object que tiene método read()
        # o a veces es una URL directa. El snippet del usuario usa .read(), así que asumimos FileOutput.
        # Si fuera URL string, tendríamos que hacer requests.get()
        
        with open(output_video_path, "wb") as file:
            file.write(output.read())
            
        print(f"Video guardado en {output_video_path}")
        return output_video_path

    except Exception as e:
        print(f"Error en Replicate: {e}")
        raise e

    # --- Lógica antigua de Google (Comentada) ---
    # '''
    # # 1. Abrir la imagen con PIL
    # user_img = Image.open(image_path).convert("RGB")
    # 
    # # 2. CONVERSIÓN CRÍTICA: Convertir PIL a Bytes
    # bytes_buffer = BytesIO() 
    # user_img.save(bytes_buffer, format="JPEG") # Forzamos formato JPEG
    # image_bytes = bytes_buffer.getvalue()
    #
    # # 3. Preparar el objeto Image correcto para el SDK
    # image_input = types.Image(
    #     image_bytes=image_bytes,
    #     mime_type="image/jpeg"
    # )
    # 
    # # Llamada a Veo 3.1
    # operation = client.models.generate_videos(
    #     model="veo-3.1-fast-generate-preview",
    #     prompt=video_prompt,
    #     image=image_input,
    #     config=types.GenerateVideosConfig(
    #         aspect_ratio="9:16",
    #         resolution ="720p"
    #     ),
    # )
    # 
    # # Polling hasta que termine
    # while not operation.done:
    #     print("Esperando generación de video...")
    #     time.sleep(5)
    #     operation = client.operations.get(operation)
    # 
    # # Descargar y guardar
    # if operation.response and operation.response.generated_videos:
    #     video_result = operation.response.generated_videos[0]
    #     
    #     # Descargar el contenido del video remoto antes de guardar
    #     print("Descargando video generado...")
    #     client.files.download(file=video_result.video)
    #     
    #     video_result.video.save(output_video_path)
    #     print(f"Video guardado en {output_video_path}")
    #     return output_video_path
    # 
    # raise RuntimeError("La operación terminó pero no se generó video.")
    # '''