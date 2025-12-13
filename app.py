import os, uuid, base64, threading
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import qrcode
# Tus utilidades (no cambian)
from utils.image_processing import upscale_vertical, resize_and_crop, add_overlays
from utils.video_processing import add_video_overlay
from utils.ai_generation import generate_with_gemini
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__, static_url_path='/apps/mentiras/static', static_folder='static')

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config["APPLICATION_ROOT"] = "/apps/mentiras"
#app.config.update(
#    APPLICATION_ROOT="/apps/mentiras",
#    PREFERRED_URL_SCHEME="https"
#)

# --- Rutas de archivos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "static", "results")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# --- ALMACENAMIENTO DE ESTATUS BASEADO EN ARCHIVOS (Para Gunicorn/Multi-worker) ---
import json

def get_status_file_path(task_id):
    return os.path.join(RESULT_FOLDER, f"status_{task_id}.json")

def save_task_status(task_id, status_data):
    """Guarda el estado en un archivo JSON para que cualquier worker lo vea."""
    try:
        with open(get_status_file_path(task_id), 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        print(f"Error guardando status {task_id}: {e}")

def load_task_status(task_id):
    """Lee el estado desde el archivo JSON."""
    path = get_status_file_path(task_id)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def background_video_task(task_id, temp_path, character, raw_video_path, result_path, overlay_path):
    """
    Función que corre en un hilo separado. Actualiza el archivo de estado en disco.
    """
    try:
        # STEP 1: Iniciando
        print(f"[Task {task_id}] Iniciando generación...")
        save_task_status(task_id, {"status": "processing", "step": "starting", "progress": 5})

        from utils.ai_generation import generate_with_gemini
        from utils.video_processing import add_video_overlay
        
        # STEP 2: Generando Video RAW
        print(f"[Task {task_id}] Llamando a Gemini Veo...")
        save_task_status(task_id, {"status": "processing", "step": "generating_raw_video", "progress": 20})
        
        generate_with_gemini(temp_path, character, raw_video_path)
        
        # STEP 3: Overlay
        print(f"[Task {task_id}] Agregando overlay...")
        save_task_status(task_id, {"status": "processing", "step": "adding_overlay", "progress": 80})

        if os.path.exists(overlay_path):
            add_video_overlay(raw_video_path, overlay_path, result_path)
            if os.path.exists(raw_video_path):
                os.remove(raw_video_path)
        else:
            print(f"Overlay no encontrado en {overlay_path}, usando video original.")
            if os.path.exists(result_path): os.remove(result_path)
            os.rename(raw_video_path, result_path)
            
        # STEP 4: Finalizar
        print(f"[Task {task_id}] Finalizado.")
        save_task_status(task_id, {
            "status": "completed",
            "progress": 100,
            "filename": os.path.basename(result_path)
        })

    except Exception as e:
        print(f"[Task {task_id}] Error CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        # Guardar error detallado en el archivo de estado
        save_task_status(task_id, {
            "status": "failed", 
            "error": str(e),
            "step": "error"
        })

# --- Home ---
@app.route("/")
def index():
    return render_template("index.html")

# --- (NUEVO) Selección de personaje sin género ---
@app.route("/select-character")
def select_character():
    # Ejemplo: pasa una lista de personajes si los muestras como tarjetas/botones
    characters = ["look_a", "look_b", "look_c"]
    return render_template("select_character.html", characters=characters)

# --- Back-compat: si entran con /select-character/<gender>, redirige al nuevo ---
@app.route("/select-character/<gender>")
def select_character_legacy(gender):
    return redirect(url_for("select_character"), code=301)

# --- Cámara / captura ---
@app.route("/capture")
def capture():
    # Puedes leer ?character=look_a desde querystring para preseleccionar
    character = request.args.get("character")
    return render_template("capture.html", character=character)

# --- Generación ---
@app.route("/generate-photo", methods=["POST"])
def generate_photo():
    """
    Espera JSON: { "image": "...", "character": "..." }
    """
    data = request.get_json(silent=True) or {}
    image_b64 = data.get("image")
    character = data.get("character")

    if not image_b64 or not character:
        return jsonify({"error": "Faltan parámetros: image y character"}), 400

    try:
        header, b64 = image_b64.split(",", 1)
    except ValueError:
        return jsonify({"error": "Formato base64 inválido"}), 400

    # ID único para nombres de archivo
    unique_id = uuid.uuid4().hex[:8]
    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{unique_id}.jpg")

    # Guardar imagen subida
    try:
        img = Image.open(BytesIO(base64.b64decode(b64)))
        img = img.convert("RGB")
        img.save(temp_path, "JPEG", quality=92, optimize=True)
    except (UnidentifiedImageError, ValueError) as e:
        return jsonify({"error": f"Imagen inválida: {e}"}), 400

    # Configuración de archivos
    raw_video_filename = f"raw_video_{unique_id}.mp4"
    raw_video_path = os.path.join(RESULT_FOLDER, raw_video_filename)
    
    result_filename = f"video_{unique_id}.mp4"
    result_path = os.path.join(RESULT_FOLDER, result_filename)

    overlay_path = os.path.join(BASE_DIR, "static", "images", "overlay_tina.png")
    
    # Task ID
    task_id = unique_id 
    
    # 1. Crear archivo de estado INICIAL (Processing) antes de lanzar el hilo
    # Esto asegura que si el worker del status corre rápido, encuentre algo.
    save_task_status(task_id, {"status": "processing"})

    # Iniciar hilo
    thread = threading.Thread(
        target=background_video_task,
        args=(task_id, temp_path, character, raw_video_path, result_path, overlay_path)
    )
    thread.start()

    # Construir la URL manualmente para evitar errores de Nginx
    # Esto asegura que siempre tenga el prefijo /apps/mentiras
    status_url = f"/apps/mentiras/status/{task_id}"

    # Responder INMEDIATAMENTE con 202 Accepted y el ID de tarea
    return jsonify({
        "message": "Generación iniciada",
        "task_id": task_id,
        "status_url": status_url
    }), 202

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    # 1. Intentar cargar estado desde el archivo compartido .json
    status_data = load_task_status(task_id)
    
    if status_data:
        response = status_data.copy()
        if status_data['status'] == 'completed':
            response['redirect_url'] = url_for("preview", filename=status_data['filename'])
        return jsonify(response)

    # 2. Fallback: Si no hay archivo JSON, buscamos el video final por si acaso
    # (Ejemplo: se borró el json pero quedó el mp4)
    expected_filename = f"video_{task_id}.mp4"
    expected_path = os.path.join(RESULT_FOLDER, expected_filename)

    if os.path.exists(expected_path):
        return jsonify({
            "status": "completed",
            "filename": expected_filename,
            "redirect_url": url_for("preview", filename=expected_filename)
        })

    # 3. Si no hay ni JSON ni Video -> 404
    return jsonify({"status": "not_found"}), 404

# --- Preview ---
@app.route("/preview/<filename>")
def preview(filename):
    return render_template(
        "preview.html",
        result_url=url_for("serve_result", filename=filename),
        filename=filename
    )

# --- QR / descarga ---
@app.route("/qr/<filename>")
def qr(filename):
    #BASE_URL = "https://344.226.49.191.sslip.io.226.49.191.sslip.io"  # TODO: cámbialo en prod
    BASE_URL = "http://127.0.0.1:5000"  # TODO: cámbialo en prod
    download_url = f"{BASE_URL}{url_for('serve_result', filename=filename)}"

    qr_img = qrcode.make(download_url)
    qr_filename = f"qr_{filename}.png"
    qr_path = os.path.join(RESULT_FOLDER, qr_filename)
    qr_img.save(qr_path)

    return render_template(
        "qr.html",
        qr_url=url_for("serve_result", filename=qr_filename),
        download_url=download_url
    )

# --- Servir resultados ---
@app.route("/results/<path:filename>")
def serve_result(filename):
    # Seguridad básica: no permitir subir fuera de la carpeta
    safe_path = os.path.normpath(os.path.join(RESULT_FOLDER, filename))
    if not safe_path.startswith(RESULT_FOLDER):
        abort(403)
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
