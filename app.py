# app.py
"""
BrandMorpher - Flask app entrypoint (full file)
Wiring:
 - Loads .env automatically (python-dotenv)
 - Uses GeminiImageAdapter / GeminiCaptionAdapter when env flags are set
 - Falls back to local generator and template captions if Gemini isn't available or fails
"""

from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ if present

import os
import uuid
from pathlib import Path
import zipfile
from flask import Flask, request, send_file, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Local modules
from generate_creatives import generate_variations
from utils import create_zip, safe_filename

# Import adapters (these files should exist under adapters/)
# They implement GeminiImageAdapter, LocalCompositeAdapter, GeminiCaptionAdapter.
# If you replaced adapters with other providers, adjust imports accordingly.
try:
    from adapters.image_gen_adapter import GeminiImageAdapter, LocalCompositeAdapter
except Exception as e:
    # If import fails, define a minimal stub so app still runs (will always use local composition)
    print("Warning: could not import GeminiImageAdapter. Falling back to LocalCompositeAdapter. Error:", e)
    class LocalCompositeAdapter:
        def generate_images(self, prompt, count=1, size=1024, out_dir="./out"):
            return []
    GeminiImageAdapter = None

try:
    from adapters.caption_llm_adapter import GeminiCaptionAdapter
except Exception as e:
    print("Warning: could not import GeminiCaptionAdapter. Falling back to templates. Error:", e)
    GeminiCaptionAdapter = None

# App config
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev_secret")

BASE_DIR = Path(__file__).parent
UPLOADS = BASE_DIR / "uploads"
RUNS = BASE_DIR / "runs"
UPLOADS.mkdir(exist_ok=True)
RUNS.mkdir(exist_ok=True)

ALLOWED_EXT = {"png", "jpg", "jpeg"}

def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    # Read form fields
    brand = request.form.get("brand", "Brand")
    product = request.form.get("product", "Product")
    logo_file = request.files.get("logo")
    product_file = request.files.get("product")

    # Basic validation
    if not logo_file or not product_file:
        flash("Please upload both logo and product images.")
        return redirect(url_for("index"))

    if not (allowed(logo_file.filename) and allowed(product_file.filename)):
        flash("Allowed file types: png, jpg, jpeg")
        return redirect(url_for("index"))

    # Setup run directory
    run_id = uuid.uuid4().hex
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save uploads safely
    logo_fname = safe_filename(logo_file.filename)
    product_fname = safe_filename(product_file.filename)
    logo_path = run_dir / f"logo_{logo_fname}"
    product_path = run_dir / f"product_{product_fname}"
    logo_file.save(logo_path)
    product_file.save(product_path)

    # Read env flags
    use_image_api = os.environ.get("USE_IMAGE_API", "false").lower() == "true"
    use_llm = os.environ.get("USE_LLM", "false").lower() == "true"

    # === Image generation step (Gemini) ===
    # Attempt to produce a small set of generated product images (optional).
    # These generated images can be composited into final creatives (optional improvement).
    if use_image_api and 'GeminiImageAdapter' in globals():
        try:
            img_adapter = GeminiImageAdapter()
            sd_out = run_dir / "gemini_images"
            sd_paths = img_adapter.generate_images(prompt=f"Product photo of {product} by {brand}", count=6, size=1024, out_dir=str(sd_out))
            print("Gemini image produced:", sd_paths)
        except Exception as e:
            print("Gemini Image adapter failed (continuing):", e)

    # === Caption generation step (Gemini) ===
    captions_list = None
    if use_llm and 'GeminiCaptionAdapter' in globals():
        try:
            llm_adapter = GeminiCaptionAdapter()
            captions_list = llm_adapter.generate_captions(brand, product, n=12)
            print("Gemini captions sample:", captions_list[:3])
        except Exception as e:
            print("Gemini caption adapter failed (will use template captions):", e)
            captions_list = None

    # === Always produce final creatives using local compositor ===
    try:
        generate_variations(str(logo_path), str(product_path), out_dir=str(run_dir), n=12, size=1200, brand_name=brand, product_name=product)
    except Exception as e:
        # If the compositor fails, log and return an error to the user
        print("Error during generate_variations:", e)
        flash("Generation failed on server. Check server logs.")
        return redirect(url_for("index"))

    # === If captions_list produced by Gemini, overwrite captions.txt ===
    if captions_list:
        try:
            img_files = sorted([p for p in run_dir.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"]])
            out_lines = []
            for idx, img in enumerate(img_files[:len(captions_list)]):
                out_lines.append(f"{img.name}\t{captions_list[idx]}")
            (run_dir / "captions.txt").write_text("\n".join(out_lines), encoding="utf-8")
        except Exception as e:
            print("Failed to write Gemini captions to captions.txt:", e)

    # === Package into ZIP and send ===
    zip_path = RUNS / f"{run_id}.zip"
    try:
        create_zip(run_dir, zip_path)
    except Exception as e:
        print("Failed to create zip:", e)
        flash("Packaging failed on server.")
        return redirect(url_for("index"))

    # Serve file to user
    download_name = f"{brand}_{product}_creatives.zip".replace(" ", "_")
    return send_file(zip_path, as_attachment=True, download_name=download_name)

if __name__ == "__main__":
    # port and debug can be adjusted for production / demo
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
