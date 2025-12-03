# generate_creatives.py
"""
Polished creative generator for BrandMorpher.

- Pillow compatibility (resampling)
- Robust font fallback
- Text wrapping with safe sizing
- Autocrop + enhancement for product
- Soft natural shadows, gradient backgrounds, vignette
- Exports PNG + high-quality JPG
- Provides generate_variations_improved and alias generate_variations
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
from pathlib import Path
import textwrap
import os

# Pillow resampling compatibility (Pillow 10+)
from PIL import Image as _PILImage
try:
    RESAMPLE_LANCZOS = _PILImage.Resampling.LANCZOS
except Exception:
    RESAMPLE_LANCZOS = getattr(_PILImage, "LANCZOS", _PILImage.BICUBIC)


def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)


def load_font(size=40):
    """
    Try a few common system fonts, then fall back to Pillow default.
    """
    candidates = [
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    for f in candidates:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def draw_text_with_wrap(draw, text, font, x, y, max_width=28, fill=(20, 20, 20)):
    """
    Draw wrapped text with safe measurement.
    max_width is in characters (approximate).
    """
    if font is None:
        # fallback simple drawing
        lines = textwrap.wrap(text, width=max_width)
        cur_y = y
        line_h = 18
        for line in lines:
            draw.text((x, cur_y), line, fill=fill)
            cur_y += line_h + 6
        return

    lines = textwrap.wrap(text, width=max_width)
    cur_y = y
    for line in lines:
        draw.text((x, cur_y), line, font=font, fill=fill)
        # attempt to measure line height robustly
        try:
            bbox = font.getbbox(line)
            line_h = bbox[3] - bbox[1]
        except Exception:
            try:
                line_h = font.getsize(line)[1]
            except Exception:
                line_h = 18
        cur_y += line_h + 6


def generate_caption(brand, product):
    templates = [
        f"{brand} {product} — style meets performance.",
        f"Upgrade your day with the {product} from {brand}.",
        f"Feel the difference with {brand}'s {product}. Shop now!",
        f"The {product} by {brand} — crafted for comfort and quality.",
        f"Special offer: grab the {product} by {brand} today."
    ]
    return random.choice(templates)


# ---------- Helper image tools ----------

def _autocrop_to_subject(img: Image.Image, threshold=10):
    """
    Autocrop to non-background pixels.
    For RGBA uses alpha; otherwise uses simple luminance threshold.
    """
    if img.mode == "RGBA":
        alpha = img.split()[-1]
        bbox = alpha.getbbox()
        if bbox:
            return img.crop(bbox)

    gray = img.convert("L")
    # mask: pixels not near-white (assume white-like bg)
    bw = gray.point(lambda p: 255 if p < (255 - threshold) else 0)
    bbox = bw.getbbox()
    if bbox:
        return img.crop(bbox)

    # fallback center-crop
    w, h = img.size
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    return img.crop((left, top, left + min_side, top + min_side))


def _apply_enhancements(img: Image.Image, upscale=1.25):
    """
    Slight upscale, then apply color/contrast/sharpness adjustments,
    then downsample to original size for crispness.
    """
    try:
        w, h = img.size
        new_w = max(1, int(w * upscale))
        new_h = max(1, int(h * upscale))
        img_up = img.resize((new_w, new_h), resample=RESAMPLE_LANCZOS)
    except Exception:
        img_up = img.copy()

    try:
        img_en = ImageEnhance.Color(img_up).enhance(1.05)
        img_en = ImageEnhance.Contrast(img_en).enhance(1.08)
        img_en = ImageEnhance.Brightness(img_en).enhance(1.02)
        img_en = ImageEnhance.Sharpness(img_en).enhance(1.2)
    except Exception:
        img_en = img_up

    # downsample back to original size for greater perceived sharpness
    try:
        img_final = img_en.resize((img.size[0], img.size[1]), resample=RESAMPLE_LANCZOS)
    except Exception:
        img_final = img_en
    return img_final


def _paste_with_soft_shadow(canvas: Image.Image, fg: Image.Image, pos: tuple, shadow_radius=16, offset=(12, 18), shadow_alpha=150):
    """
    Paste fg onto canvas at pos with a soft, blurred shadow.
    Returns new composite canvas.
    """
    x, y = pos
    if fg.mode != "RGBA":
        fg = fg.convert("RGBA")
    # create shadow image from fg alpha
    alpha = fg.split()[-1]
    shadow = Image.new("RGBA", fg.size, (0, 0, 0, shadow_alpha))
    # apply alpha as mask
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_radius))
    # place shadow on layer same size as canvas
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(shadow, (x + offset[0], y + offset[1]), shadow)
    canvas = Image.alpha_composite(canvas, layer)
    canvas.paste(fg, (x, y), fg)
    return canvas


# ---------- Main improved generator ----------

def generate_variations_improved(logo_path, product_path, out_dir="output", n=12, size=1200, brand_name="Brand", product_name="Product"):
    """
    Enhanced generator producing professional-looking creatives.
    - Use transparent PNG product/logo when possible for best results.
    - Exports both PNG and high-quality JPG per creative.
    """
    ensure_dir(out_dir)

    # Validate inputs
    if not Path(logo_path).exists():
        raise FileNotFoundError(f"Logo not found: {logo_path}")
    if not Path(product_path).exists():
        raise FileNotFoundError(f"Product image not found: {product_path}")

    logo = Image.open(logo_path).convert("RGBA")
    product = Image.open(product_path).convert("RGBA")

    captions = []
    font_large = load_font(size=58)
    font_small = load_font(size=30)
    font_badge = load_font(size=18)

    for i in range(n):
        # Background gradient
        base_a = random.choice([(250, 250, 250), (245, 248, 255), (255, 250, 245), (250, 255, 250)])
        base_b = tuple(min(255, c + random.randint(-18, 30)) for c in base_a)
        canvas = Image.new("RGBA", (size, size), base_a + (255,))
        # vertical gradient
        grad = Image.new("RGBA", (1, size))
        for y in range(size):
            ratio = y / (size - 1)
            r = int(base_a[0] * (1 - ratio) + base_b[0] * ratio)
            g = int(base_a[1] * (1 - ratio) + base_b[1] * ratio)
            b = int(base_a[2] * (1 - ratio) + base_b[2] * ratio)
            grad.putpixel((0, y), (r, g, b, 255))
        grad = grad.resize((size, size))
        canvas = Image.alpha_composite(canvas, grad)

        # subtle bloom overlay
        overlay = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        centre = (int(size * 0.6) + random.randint(-60, 60), int(size * 0.28) + random.randint(-40, 40))
        for rad, a in [(size // 2, 18), (size // 3, 12), (size // 6, 8)]:
            mask = Image.new("L", (size, size), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([centre[0] - rad, centre[1] - rad, centre[0] + rad, centre[1] + rad], fill=a)
            piece = Image.new("RGBA", (size, size), (255, 255, 255, 0))
            piece.putalpha(mask)
            overlay = Image.alpha_composite(overlay, piece)
        canvas = Image.alpha_composite(canvas, overlay)

        # Prepare product: autocrop, enhance, resize
        prod_cropped = _autocrop_to_subject(product)
        # ensure minimum size
        min_side = 240
        if prod_cropped.width < min_side or prod_cropped.height < min_side:
            prod_cropped = prod_cropped.resize((min_side, min_side), resample=RESAMPLE_LANCZOS)
        prod_enh = _apply_enhancements(prod_cropped, upscale=1.25)

        max_prod = int(size * 0.62)
        prod_ratio = prod_enh.width / max(1, prod_enh.height)
        if prod_enh.width >= prod_enh.height:
            new_w = max_prod
            new_h = max(120, int(max_prod / prod_ratio))
        else:
            new_h = max_prod
            new_w = max(120, int(max_prod * prod_ratio))
        prod_final = prod_enh.resize((new_w, new_h), resample=RESAMPLE_LANCZOS)

        # position + soft shadow
        px = (size - prod_final.width) // 2 + random.randint(-20, 20)
        py = int(size * 0.36) - prod_final.height // 2 + random.randint(-20, 20)
        canvas = _paste_with_soft_shadow(canvas, prod_final, (px, py), shadow_radius=18, offset=(12, 18), shadow_alpha=150)

        draw = ImageDraw.Draw(canvas)

        # Logo pill
        logo_small_w = int(size * 0.12)
        logo_ratio = logo.width / max(1, logo.height)
        logo_small_h = int(logo_small_w / logo_ratio)
        try:
            logo_small = logo.copy().resize((logo_small_w, logo_small_h), resample=RESAMPLE_LANCZOS)
        except Exception:
            logo_small = logo.copy().resize((max(40, logo_small_w), max(20, logo_small_h)))

        lx, ly = 36, 36
        pill_w, pill_h = logo_small_w + 18, logo_small_h + 12
        pill = Image.new("RGBA", (pill_w, pill_h), (255, 255, 255, 220))
        pdraw = ImageDraw.Draw(pill)
        try:
            pdraw.rounded_rectangle([0, 0, pill_w, pill_h], radius=12, fill=(255, 255, 255, 220))
        except Exception:
            pdraw.rectangle([0, 0, pill_w, pill_h], fill=(255, 255, 255, 220))
        canvas.paste(pill, (lx - 8, ly - 6), pill)
        canvas.paste(logo_small, (lx, ly), logo_small)

        # Headline block bottom-left
        headline_templates = [
            f"Introducing {product_name}",
            f"{brand_name} presents {product_name}",
            f"{product_name} — Now available",
            f"Meet the new {product_name}"
        ]
        headline = random.choice(headline_templates)
        txt_x = 52
        txt_y = size - 200

        # headline shadow + text
        try:
            draw.text((txt_x + 1, txt_y + 1), headline, font=font_large, fill=(0, 0, 0, 90))
            draw.text((txt_x, txt_y), headline, font=font_large, fill=(255, 255, 255))
        except Exception:
            draw.text((txt_x, txt_y), headline, fill=(20, 20, 20))

        sub = random.choice([f"Shop now • {brand_name}", f"Limited offer • {brand_name}", f"Free shipping • {brand_name}"])
        try:
            draw.text((txt_x, txt_y + 62), sub, font=font_small, fill=(245, 245, 245))
        except Exception:
            draw.text((txt_x, txt_y + 62), sub, fill=(80, 80, 80))

        # Optional badge top-right
        if random.random() < 0.5:
            badge_text = random.choice(["20% OFF", "NEW", "BESTSELLER", "LIMITED"])
            badge_w, badge_h = 150, 56
            bx = size - badge_w - 44
            by = 44
            badge = Image.new("RGBA", (badge_w, badge_h), (255, 80, 60, 230))
            bd = ImageDraw.Draw(badge)
            try:
                w, h = bd.textsize(badge_text, font=font_badge)
            except Exception:
                w, h = (len(badge_text) * 10, 24)
            bd.text(((badge_w - w) // 2, (badge_h - h) // 2 - 2), badge_text, font=font_badge, fill=(255, 255, 255))
            canvas.paste(badge, (bx, by), badge)

        # subtle vignette
        vign = Image.new("L", (size, size), 0)
        vdraw = ImageDraw.Draw(vign)
        vdraw.ellipse([-int(size * 0.15), -int(size * 0.15), int(size * 1.15), int(size * 1.15)], fill=80)
        vign = vign.filter(ImageFilter.GaussianBlur(radius=200))
        black_v = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        black_v.putalpha(vign)
        canvas = Image.alpha_composite(canvas, black_v)

        # final convert & save
        final = canvas.convert("RGB")
        filename_base = f"creative_{i+1:02d}"
        out_path_png = Path(out_dir) / f"{filename_base}.png"
        out_path_jpg = Path(out_dir) / f"{filename_base}.jpg"
        final.save(out_path_png, format="PNG", optimize=True)
        final.save(out_path_jpg, quality=94, optimize=True)

        caption = generate_caption(brand_name, product_name)
        captions.append(f"{filename_base}.jpg\t{caption}")

    # write captions mapping to JPGs
    with open(Path(out_dir) / "captions.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(captions))

    return Path(out_dir).resolve()


# Backward-compatibility alias
def generate_variations(logo_path, product_path, out_dir="output", n=12, size=1200, brand_name="Brand", product_name="Product"):
    """
    Alias for backwards compatibility: calls the improved generator.
    """
    return generate_variations_improved(logo_path, product_path, out_dir=out_dir, n=n, size=size, brand_name=brand_name, product_name=product_name)


# Quick CLI test
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python generate_creatives.py logo.png product.png [out_dir]")
        sys.exit(1)
    logo_p = sys.argv[1]
    product_p = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else "output"
    outp = generate_variations_improved(logo_p, product_p, out_dir=out, n=12, brand_name="Brand", product_name="Product")
    print("Done. Look in", outp)
