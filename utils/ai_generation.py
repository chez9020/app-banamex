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
    'look_a': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px. 
    La persona está delante de un Fondo neón rosa intenso. En un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestido rosa brillante con hombreras grandes y falda con mucho vuelo, chaqueta corta a juego, cinturón ancho. 
    Tacones altos rosas. Peinado recogido con volumen ochentero. Maquillaje llamativo con labios rojos. 
    Elementos decorativos: stickers de zapatos de tacón, íconos de los 80, teléfono retro, diadema ochentero, revistas de moda estilizadas. 
    Estética teatral publicitaria, vibrante y colorida. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_b': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px. 
    La persona está delante de un Fondo azul eléctrico. En un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: leggins negros ajustados con saco largo azul con hombreras, blusa blanca, cinturón ancho dorado. Botines negros. 
    Peinado largo y voluminoso con estilo rockero ochentero. Maquillaje fuerte con delineado marcado y sombras oscuras.
    Elementos decorativos: maletín, cassetes, rayos en estilo pop-art, casetes, rayos neón estilizados, portafolio ochentero. 
    Estética teatral vibrante, alta resolución. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_c': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px. 
    La persona está enfrente de un Fondo naranja brillante. En un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: chamarra con animal print con hombreras, chaqueta ligera, tacones a juego. 
    Accesorios grandes (aretes circulares, collares llamativos). Peinado rubio voluminoso con rizos exagerados ochenteros. 
    Maquillaje intenso con sombras lilas y labios brillantes. Elementos decorativos: máquina de escribir, papeles, gafas neón. 
    Estética teatral pop ochentera, encuadre vertical. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_d': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px. 
    La persona está delante de un Fondo verde neón. en un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Debe tener Camisón largo verde con hombreras, zapatos discretos ochenteros. 
    Peinado corto y rizado con volumen. Maquillaje en tonos cálidos, natural pero con acento ochentero. Elementos decorativos: gafas grandes estilo ochentas, libros escolares, 
    regla gigante pop-art, debe estar un osito de peluche ochentero. 
    Estética teatral kitsch, vibrante y colorida. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_e': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px.
    La persona esta de frente a un Fondo rojo neón, en un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: saco rojo con hombreras, camisa negra, corbata roja, pantalones negros rectos, cinturón elegante. 
    Debe tener Tennis blancos de bota. Peinado engominado con volumen típico de los 80. Elementos decorativos: lentes de sol neón, micrófono retro, corazones pop-art.
    Estética teatral publicitaria vibrante, encuadre vertical. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_f': """Genera una imagen: Retrato estilo cartel promocional con dimensiones 610x930px. 
    La persona está posando frente a un fondo azul eléctrico, en un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: saco azul con hombreras, camisa negra, corbata azul, pantalones negros rectos, cinturón elegante.
    Debe tener tenis blancos de bota. Peinado engominado con volumen típico de los 80.
    Elementos decorativos: maletín, cassettes, rayos en estilo pop-art, rayos neón estilizados, portafolio ochentero.
    No incluyas ningún texto ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_g': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px. 
    La persona esta posando de frente a un Fondo naranja neón, en un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: saco naranja con hombreras debe incluir animal print, camisa negra, corbata naranja, pantalones negros rectos, cinturón elegante.
    Debe tener Tennis blancos de bota. Peinado engominado con volumen típico de los 80. Elementos decorativos: máquina de escribir, papeles, gafas neón.
    Estética teatral pop ochentera, encuadre vertical. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """,
    'look_h': """Genera una imagen: Retrato estilo cartel promocional con estas dimensiones 610x 930px con profundidad de campo 50mm.
    La persona esta posando de frente a un Fondo verde neón, en un encuadre más amplio (plano general o full-body shot) que muestre la figura completa con espacio libre arriba y a los lados. 
    Perspectiva con ligera profundidad de campo (efecto de cámara real), manteniendo el enfoque en el sujeto.
    Vestuario: saco verde con hombreras, camisa negra, corbata verde, pantalones negros rectos, cinturón elegante. 
    Debe tener Tennis blancos de bota. Peinado engominado con volumen típico de los 80.
    Elementos decorativos: gafas grandes estilo ochentas, libros escolares, regla gigante pop-art, debe estar un osito de peluche ochentero.
    Estética teatral kitsch, vibrante y colorida. No incluyas ningun texto, ni marcos. Mantén la estética y la iluminación tipo póster publicitario.
    """
}


def generate_with_gemini(image_path: str, character: str) -> Image.Image:
    user_img = Image.open(image_path).convert("RGB")
    base = PROMPTS.get(character, PROMPTS['look_a'])
    full_prompt = f"{base}"

    resp = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=[full_prompt, user_img],  # ← texto (str) + PIL.Image
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="2:3",
            )
        )
    )
    
    # Devuelve la primera imagen encontrada, sin cambios de tamaño ni avisos
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            return Image.open(BytesIO(part.inline_data.data)).convert("RGB")

    # si el modelo devolvió solo texto
    raise RuntimeError("La respuesta no incluyó imagen generada.")