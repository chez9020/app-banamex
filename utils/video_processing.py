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

        # Guardar (sin audio si el original no tiene, o con audio si tiene)
        # Veo genera video sin audio usualmente, pero si tuviera, esto lo preserva?
        # CompositeVideoClip preserva el audio de la primera clip usualmente si se maneja bien,
        # pero para asegurar:
        final_video.write_videofile(
            output_path, 
            codec='libx264', 
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            logger=None  # Silenciar logs en consola
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
