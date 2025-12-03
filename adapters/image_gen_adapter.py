# adapters/image_gen_adapter.py
"""
Gemini Image adapter.

Behavior:
- If google-generativeai is installed and GEMINI_API_KEY is set, it will attempt
  to call Gemini's image generation endpoint (via SDK).
- If SDK/key missing or an error occurs, it will fall back to local placeholder images so your demo always works.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

# Try import Gemini SDK
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

class ImageGenAdapter:
    def generate_images(self, prompt: str, count: int = 1, size: int = 1024, out_dir: str = "./out") -> list:
        raise NotImplementedError

class GeminiImageAdapter(ImageGenAdapter):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        if GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                print("Gemini SDK configure error:", e)

    def generate_images(self, prompt: str, count: int = 1, size: int = 1024, out_dir: str = "./out") -> list:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        saved = []

        # If SDK or key missing -> fallback
        if not GENAI_AVAILABLE or not self.api_key:
            return self._local_placeholders(prompt, count, size, out_dir)

        try:
            # Many SDKs support something like genai.generate_image or genai.images.generate.
            # We'll attempt common call patterns and handle responses defensively.

            # Try modern method 'genai.generate_image' (if present)
            if hasattr(genai, "generate_image"):
                # Example call: genai.generate_image(model="gpt-image-1", prompt=prompt, size=f"{size}x{size}", n=count)
                resp = genai.generate_image(model="gpt-image-1", prompt=prompt, size=f"{size}x{size}", n=count)
                # resp may have a list of items with 'b64' or 'b64_json' fields
                items = []
                if isinstance(resp, dict) and "data" in resp:
                    items = resp["data"]
                elif hasattr(resp, "image"):
                    items = [resp.image]
                elif isinstance(resp, list):
                    items = resp
                else:
                    # fallback to treating resp as a single item
                    items = [resp]

                for i, it in enumerate(items):
                    b64 = None
                    if isinstance(it, dict):
                        b64 = it.get("b64") or it.get("b64_json") or it.get("b64String") or it.get("b64Data")
                        # some providers return 'image' -> {'b64_json': "..."}
                        if not b64 and "image" in it and isinstance(it["image"], dict):
                            b64 = it["image"].get("b64_json")
                    elif hasattr(it, "b64"):
                        b64 = getattr(it, "b64", None)
                    if not b64:
                        continue
                    import base64
                    img_bytes = base64.b64decode(b64)
                    outp = Path(out_dir) / f"gemini_img_{i+1:02d}.png"
                    with open(outp, "wb") as f:
                        f.write(img_bytes)
                    saved.append(str(outp))

            # Try alternate path: genai.images.generate (another SDK shape)
            elif hasattr(genai, "images") and hasattr(genai.images, "generate"):
                resp = genai.images.generate(model="image-bison-001", prompt=prompt, size=f"{size}x{size}", n=count)
                # resp handling similar to above
                items = []
                if isinstance(resp, dict) and "data" in resp:
                    items = resp["data"]
                elif isinstance(resp, list):
                    items = resp
                else:
                    items = [resp]

                import base64
                for i, it in enumerate(items):
                    b64 = None
                    if isinstance(it, dict):
                        b64 = it.get("b64_json") or it.get("b64")
                    if not b64 and hasattr(it, "b64_json"):
                        b64 = it.b64_json
                    if b64:
                        img_bytes = base64.b64decode(b64)
                        outp = Path(out_dir) / f"gemini_img_{i+1:02d}.png"
                        with open(outp, "wb") as f:
                            f.write(img_bytes)
                        saved.append(str(outp))

            else:
                # SDK present but structure unknown -> try a generic generate_text as fallback
                txt_resp = genai.generate_text(model="gemini-1.5-mini", prompt=f"Create {count} image descriptions for: {prompt}", max_output_tokens=200)
                # Not ideal; fallback to placeholder images
                print("Gemini SDK present but image interface not detected; falling back to placeholders.")
                return self._local_placeholders(prompt, count, size, out_dir)

            # If nothing saved, fallback
            if not saved:
                return self._local_placeholders(prompt, count, size, out_dir)
            return saved

        except Exception as e:
            print("Gemini image generation error:", e)
            return self._local_placeholders(prompt, count, size, out_dir)

    def _local_placeholders(self, prompt, count, size, out_dir):
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        saved = []
        for i in range(count):
            img = Image.new('RGB', (size, size), (240, 240, 245))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
            except:
                font = ImageFont.load_default()
            text = f"[Gemini Placeholder]\n{prompt[:80]}"
            draw.multiline_text((30,30), text, fill=(30,30,30), font=font)
            outp = Path(out_dir) / f"gemini_placeholder_{i+1:02d}.png"
            img.save(outp)
            saved.append(str(outp))
        return saved

class LocalCompositeAdapter(ImageGenAdapter):
    """Simple local compositing adapter (keeps earlier behavior)."""
    def generate_images(self, prompt: str, count: int = 1, size: int = 1024, out_dir: str = "./out") -> list:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        saved = []
        for i in range(count):
            img = Image.new('RGB', (size, size), tuple([200 + (i*5)%50]*3))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
            except:
                font = ImageFont.load_default()
            draw.text((40, size//2 - 20), prompt[:40] + ("..." if len(prompt)>40 else ""), fill=(255,255,255), font=font)
            outp = Path(out_dir)/f"local_composite_{i+1:02d}.png"
            img.save(outp)
            saved.append(str(outp))
        return saved
