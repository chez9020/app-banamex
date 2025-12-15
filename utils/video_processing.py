import os
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

def add_video_overlay(video_path, overlay_path, output_path):
    """
    Superpone una imagen (overlay_path) sobre un video (video_path) 
    y guarda el resultado en output_path.
    El overlay se redimensiona al tamaño del video.
    """
    try:
        # Cargar video
        video = VideoFileClip(video_path)
        w, h = video.size

        # Cargar overlay
        # ImageClip soporta transparencia (PNG) automáticamente
        overlay = ImageClip(overlay_path).resized((w, h))

        # Asegurar que el overlay dure lo mismo que el video
        overlay = overlay.with_duration(video.duration)

        # Componer: video fondo, overlay encima
        final_video = CompositeVideoClip([video, overlay])
        
        # ELIMINAR AUDIO EXPLÍCITAMENTE
        final_video.audio = None

        # Guardar (sin audio)
        final_video.write_videofile(
            output_path, 
            codec='libx264', 
            audio=False,  # Asegura que no se incluya track de audio
            logger=None   # Silenciar logs
        )
        
        # Cerrar clips para liberar recursos
        video.close()
        overlay.close()
        final_video.close()
        
        return output_path

    except Exception as e:
        print(f"Error procesando video overlay: {e}")
        # Retornar None o lanzar error
        raise e
