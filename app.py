from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, abort
import os, uuid, base64
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import qrcode
# Tus utilidades (no cambian)
from utils.image_processing import upscale_vertical, resize_and_crop, add_overlays
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
    Espera JSON:
      {
        "image": "data:image/jpeg;base64,...",
        "character": "look_a"
      }
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

    # Llama a tu pipeline (Gemini + post-procesos opcionales)
    result_img = generate_with_gemini(temp_path, character)
    # Ejemplo si quieres aplicar tus utilidades: 610x930px
    result_img = resize_and_crop(result_img, 610, 930)
    # result_img = upscale_vertical(result_img)
    result_img = add_overlays(result_img)

    # Guardar resultado
    result_filename = f"photo_{unique_id}.jpg"
    result_path = os.path.join(RESULT_FOLDER, result_filename)
    result_img.save(result_path, "PNG", quality=95, optimize=True)

    return jsonify({
        "filename": result_filename,
        "redirect_url": url_for("preview", filename=result_filename)
    })

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
