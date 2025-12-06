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
    'look_woman': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px. 
    La persona está delante de un Fondo azul eléctrico. En un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: leggins negros ajustados con saco largo azul con hombreras, blusa blanca, cinturón ancho dorado. Botines negros. 
    Peinado largo y voluminoso con estilo rockero ochentero. Maquillaje fuerte con delineado marcado y sombras oscuras.
    Elementos decorativos: maletín, cassetes, rayos en estilo pop-art, casetes, rayos neón estilizados, portafolio ochentero. 
    Estética teatral vibrante, alta resolución. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_man': """Genera una imagen: Retrato estilo cartel promocional con dimensiones 610x930px. 
    La persona está posando frente a un fondo azul eléctrico, en un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: saco azul con hombreras, camisa negra, corbata azul, pantalones negros rectos, cinturón elegante.
    Debe tener tenis blancos de bota. Peinado engominado con volumen típico de los 80.
    Elementos decorativos: maletín, cassettes, rayos en estilo pop-art, rayos neón estilizados, portafolio ochentero.
    No incluyas ningún texto ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
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