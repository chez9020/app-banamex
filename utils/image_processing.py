# utils/image_processing.py
import os
from os import PathLike
from io import BytesIO
from PIL import Image

def upscale_vertical(image_path, target_height=2160):
    """
    Escala la imagen manteniendo proporción vertical.
    Ejemplo: si target_height=2160 → 1484x2160 (aprox).
    """
    img = Image.open(image_path).convert("RGB")
    aspect_ratio = img.width / img.height

    new_height = target_height
    new_width = int(new_height * aspect_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    img.save(image_path, "JPEG", quality=95)
    return image_path



#def resize_and_crop(img_or_path, target_w, target_h, *, mode="cover"):
def resize_and_crop(img_or_path, target_w, target_h, *, mode="cover"):
    # --- abrir imagen según el tipo ---
    if isinstance(img_or_path, Image.Image):
        img = img_or_path

    elif isinstance(img_or_path, (str, PathLike)):
        img = Image.open(img_or_path)

    elif isinstance(img_or_path, (bytes, bytearray, BytesIO)):
        bio = img_or_path if isinstance(img_or_path, BytesIO) else BytesIO(img_or_path)
        bio.seek(0)
        img = Image.open(bio)

    else:
        raise TypeError(f"img_or_path debe ser PIL.Image.Image, ruta (str/PathLike) o bytes/BytesIO, no {type(img_or_path)}")

    img = img.convert("RGBA")

    # --- escalar y recortar ---
    src_w, src_h = img.size
    if mode == "cover":
        scale = max(target_w/src_w, target_h/src_h)# * 0.95  # <--- factor de zoom-out
        new_w, new_h = int(src_w*scale), int(src_h*scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left   = (new_w - target_w)//2
        top    = (new_h - target_h)//2
        right  = left + target_w
        bottom = top + target_h
        return img.crop((left, top, right, bottom))

    if mode == "contain":
        scale = min(target_w/src_w, target_h/src_h)
        new_w, new_h = int(src_w*scale), int(src_h*scale)
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (target_w, target_h), (0,0,0,0))
        x = (target_w - new_w)//2
        y = (target_h - new_h)//2
        canvas.paste(resized, (x, y), resized)
        return canvas

    raise ValueError("mode debe ser 'cover' o 'contain'")

# def resize_and_crop(img_or_path, target_w, target_h, *, mode="contain"):
#     """
#     Redimensiona inteligentemente minimizando pérdida
#     """
#     if isinstance(img_or_path, Image.Image):
#         img = img_or_path
#     else:
#         img = Image.open(img_or_path)
    
#     # Primero redimensionar a 610 de ancho
#     scale = target_w / img.width
#     temp_height = int(img.height * scale)  # Sería ~1084px
    
#     img = img.resize((target_w, temp_height), Image.LANCZOS)
    
#     # Recortar inteligentemente (quitar un poco de arriba y abajo)
#     crop_amount = temp_height - target_h  # ~154px a recortar
#     top_crop = crop_amount // 3  # Recortar 1/3 arriba
#     bottom_crop = crop_amount - top_crop  # Recortar 2/3 abajo
    
#     img = img.crop((0, top_crop, target_w, temp_height - bottom_crop))
    
#     return img

def add_overlays(img_or_path, overlays_dir="static/images"):
    """
    Agrega overlays sobre la foto generada.
    Acepta Image, ruta, o bytes como resize_and_crop.
    RETORNA la imagen modificada.
    """
    try:
        # --- abrir imagen según el tipo (igual que resize_and_crop) ---
        if isinstance(img_or_path, Image.Image):
            base = img_or_path
        elif isinstance(img_or_path, (str, PathLike)):
            base = Image.open(img_or_path)
        elif isinstance(img_or_path, (bytes, bytearray, BytesIO)):
            bio = img_or_path if isinstance(img_or_path, BytesIO) else BytesIO(img_or_path)
            bio.seek(0)
            base = Image.open(bio)
        else:
            raise TypeError(f"img_or_path debe ser PIL.Image.Image, ruta o bytes/BytesIO")
        
        base = base.convert("RGBA")
        w, h = base.size

        # Cargar overlay
        overlay = Image.open(os.path.join(overlays_dir, "overlay_tina.png")).convert("RGBA")
        
        # Si el overlay no tiene el mismo tamaño, redimensionar
        if overlay.size != (w, h):
            overlay = overlay.resize((w, h), Image.LANCZOS)

        # Pegar overlay
        base.paste(overlay, (0, 0), overlay)

        # Retornar la imagen modificada (NO guardar, NO retornar boolean)
        return base.convert("RGB")
        
    except Exception as e:
        print(f"[ERROR] al agregar overlays: {e}")
        # En caso de error, retornar la imagen original si es posible
        if isinstance(img_or_path, Image.Image):
            return img_or_path
        return None
