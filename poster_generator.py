from PIL import Image, ImageDraw, ImageFont
import textwrap
import json
import os

# Paths to input files
background_path = "background.png"   # e.g., /mnt/data/7f55130d-2e71-42ed-80cd-d72dd2f0561d.jpeg
logo_path = "logo.png"                # your WinVinaya Foundation logo
text_file = "poster_text.txt"         # .txt file with numbered lines
output_path = "generated_poster.jpg"

# Font settings with bold support
def try_load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return None


def load_font_with_bold(base_path, size, want_bold=False):
    """Try to load a font. If want_bold=True, try common bold variants and return (font, has_bold_flag).
    Falls back to the base font or PIL default if not found."""
    # Try exact path first
    f = try_load_font(base_path, size)
    base_dir = os.path.dirname(base_path)
    basename = os.path.basename(base_path)
    name_no_ext, ext = os.path.splitext(basename)
    if f is None:
        # try bare name (system font lookup)
        f = try_load_font(name_no_ext + ext, size)
    if not want_bold:
        if f is None:
            return ImageFont.load_default(), False
        return f, True

    # want bold: try common bold file name patterns
    bold_candidates = [
        name_no_ext + 'bd' + ext,
        name_no_ext + '-bd' + ext,
        name_no_ext + 'b' + ext,
        name_no_ext + 'bold' + ext,
        'arialbd' + ext,
        'DejaVuSans-Bold' + ext,
    ]
    for cand in bold_candidates:
        cand_path = os.path.join(base_dir, cand) if base_dir else cand
        bf = try_load_font(cand_path, size)
        if bf:
            return bf, True

    # No bold font found; return base or default and indicate bold is unavailable
    if f is None:
        return ImageFont.load_default(), False
    return f, False


# Load fonts (prefer bold variants where requested)
title_font, _ = load_font_with_bold("arialbd.ttf", 160, want_bold=False)
subtitle_font, subtitle_has_bold = load_font_with_bold("arial.ttf", 100, want_bold=True)
body_font, body_has_bold = load_font_with_bold("arial.ttf", 80, want_bold=True)


def draw_bold_text(draw_obj, pos, text, font, fill, bold_available=True, stroke=2):
    """Draw text in bold. If a bold font is available, use it. Otherwise try stroke_width, then multi-draw fallback."""
    x, y = pos
    if bold_available:
        draw_obj.text((x, y), text, font=font, fill=fill)
        return
    # Try stroke_width API (Pillow >= 5-ish)
    try:
        draw_obj.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=fill)
        return
    except TypeError:
        # Older Pillow may not support stroke_width
        pass
    # Fallback: draw the text multiple times with small offsets to emulate bold
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
    for dx, dy in offsets:
        draw_obj.text((x + dx, y + dy), text, font=font, fill=fill)


# Load background
bg = Image.open(background_path).convert("RGBA")
draw = ImageDraw.Draw(bg)

# Assets handling: load images from assets/ folder
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
asset_files = []
if os.path.isdir(ASSETS_DIR):
    for fn in sorted(os.listdir(ASSETS_DIR)):
        if fn.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            asset_files.append(os.path.join(ASSETS_DIR, fn))


# Load logo and paste into a fixed-size box (preserve aspect ratio)
def paste_logo_fixed(bg_image, logo_file, box_size=(250, 250), gap=50):
    """Paste the logo into a fixed-size box at bottom-right without skewing.

    - box_size: (width, height) of the bounding box the logo should occupy
    - margin: distance from the image edges to the bounding box
    """
    logo_img = Image.open(logo_file).convert("RGBA")
    max_w, max_h = box_size

    # Preserve aspect ratio: thumbnail modifies in-place
    # Choose resampling filter compatible across Pillow versions
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        # Pillow < 9 fallback: use LANCZOS if present, else nearest
        resample = getattr(Image, 'LANCZOS', Image.NEAREST)
    logo_img.thumbnail((max_w, max_h), resample)

    # Create a transparent box of exact size and center the logo inside it
    box = Image.new("RGBA", box_size, (0, 0, 0, 0))
    offset_x = (max_w - logo_img.width) // 2
    offset_y = (max_h - logo_img.height) // 2
    box.paste(logo_img, (offset_x, offset_y), logo_img)

    # Compute position for bottom-right with margin
    pos_x = bg_image.width - gap - max_w
    pos_y = bg_image.height - gap - max_h
    bg_image.paste(box, (pos_x, pos_y), box)



# Try to load positions.json and use coordinates if available
positions_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positions.json")
positions = None
logo_box = (250, 250)
if os.path.exists(positions_file):
    try:
        with open(positions_file, 'r', encoding='utf-8') as pf:
            pj = json.load(pf)
            positions = pj.get('positions', {})
            logo_box = tuple(pj.get('logo_size', logo_box))
    except Exception:
        positions = None

# If a logo coordinate is provided explicitly (key 'logo' or '0'), paste centered there,
# otherwise fall back to bottom-right fixed placement.
def paste_logo_at_coordinate(bg_image, logo_file, coord, box_size=(250,250)):
    logo_img = Image.open(logo_file).convert('RGBA')
    max_w, max_h = box_size
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = getattr(Image, 'LANCZOS', Image.NEAREST)
    logo_img.thumbnail((max_w, max_h), resample)
    box = Image.new('RGBA', box_size, (0,0,0,0))
    offset_x = (max_w - logo_img.width) // 2
    offset_y = (max_h - logo_img.height) // 2
    box.paste(logo_img, (offset_x, offset_y), logo_img)
    # coord is bg-image pixel coordinate to center the box on
    cx, cy = coord
    pos_x = int(cx - max_w/2)
    pos_y = int(cy - max_h/2)
    bg_image.paste(box, (pos_x, pos_y), box)

# Use positions if available
if positions:
    # check for explicit 'logo' or '0' key
    if 'logo' in positions:
        try:
            coord = positions['logo']
            paste_logo_at_coordinate(bg, logo_path, coord, box_size=logo_box)
        except Exception:
            paste_logo_fixed(bg, logo_path, box_size=logo_box, gap=50)
    elif '0' in positions:
        try:
            coord = positions['0']
            paste_logo_at_coordinate(bg, logo_path, coord, box_size=logo_box)
        except Exception:
            paste_logo_fixed(bg, logo_path, box_size=logo_box, gap=50)
    else:
        paste_logo_fixed(bg, logo_path, box_size=logo_box, gap=50)
else:
    paste_logo_fixed(bg, logo_path, box_size=logo_box, gap=50)

# Read data from text file
with open(text_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Remove empty lines and clean text
lines = [line.strip() for line in lines if line.strip()]

# Example expected format:
# 1. Title text
# 2. Subtitle text
# 3. Body paragraph
# 4. Footer text

# Assign dynamically
title_text = lines[0] if len(lines) > 0 else ""
subtitle_text = lines[1] if len(lines) > 1 else ""
body_text = lines[2] if len(lines) > 2 else ""
footer_text = lines[3] if len(lines) > 3 else ""

# Center title
def text_size(draw_obj, text, font):
    # textbbox returns (left, top, right, bottom)
    bbox = draw_obj.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

# Title placement: use positions.json if available (key '1') else center near top
title_w, title_h = text_size(draw, title_text, font=title_font)
if positions and '1' in positions:
    try:
        tx, ty = positions['1']
        draw_bold_text(draw, (tx - title_w/2, ty - title_h/2), title_text, title_font, fill=(0, 80, 180), bold_available=True)
    except Exception:
        draw_bold_text(draw, ((bg.width - title_w)/2, 150), title_text, title_font, fill=(0, 80, 180), bold_available=True)
else:
    draw_bold_text(draw, ((bg.width - title_w)/2, 150), title_text, title_font, fill=(0, 80, 180), bold_available=True)

# Subtitle below title
# Subtitle placement: use positions.json key '2' if available, else default below title
subtitle_w, subtitle_h = text_size(draw, subtitle_text, font=subtitle_font)
if positions and '2' in positions:
    try:
        sx, sy = positions['2']
        draw_bold_text(draw, (sx - subtitle_w/2, sy - subtitle_h/2), subtitle_text, subtitle_font, fill=(220, 100, 0), bold_available=subtitle_has_bold)
    except Exception:
        draw_bold_text(draw, ((bg.width - subtitle_w)/2, 250), subtitle_text, subtitle_font, fill=(220, 100, 0), bold_available=subtitle_has_bold)
else:
    draw_bold_text(draw, ((bg.width - subtitle_w)/2, 250), subtitle_text, subtitle_font, fill=(220, 100, 0), bold_available=subtitle_has_bold)

# Body text (wrapped)
# Body text placement: use positions.json key '3' as top-left start if available
line_width = 40
if positions and '3' in positions:
    try:
        bx, by = positions['3']
        offset_x = int(bx)
        offset_y = int(by)
        for line in textwrap.wrap(body_text, width=line_width):
            draw.text((offset_x, offset_y), line, font=body_font, fill=(0, 0, 0))
            offset_y += int(body_font.size * 1.2)
    except Exception:
        margin = 100
        offset = 400
        for line in textwrap.wrap(body_text, width=line_width):
            draw.text((margin, offset), line, font=body_font, fill=(0, 0, 0))
            offset += int(body_font.size * 1.2)
else:
    margin = 100
    offset = 400
    for line in textwrap.wrap(body_text, width=line_width):
        draw.text((margin, offset), line, font=body_font, fill=(0, 0, 0))
        offset += int(body_font.size * 1.2)

# Footer (bottom center)
# Footer placement: use positions.json key '4' if available, else bottom center
footer_w, footer_h = text_size(draw, footer_text, font=subtitle_font)
if positions and '4' in positions:
    try:
        fx, fy = positions['4']
        draw.text((fx - footer_w/2, fy - footer_h/2), footer_text, fill=(80, 80, 80), font=subtitle_font)
    except Exception:
        draw.text(((bg.width - footer_w)/2, bg.height - 200), footer_text, fill=(80, 80, 80), font=subtitle_font)
else:
    draw.text(((bg.width - footer_w)/2, bg.height - 200), footer_text, fill=(80, 80, 80), font=subtitle_font)

# Save final image (convert to RGB for JPEG)
def place_assets(bg_image, files, max_width_ratio=0.4, max_height_ratio=0.4):
    """Place assets on the poster:
    - If 1 image: center it exactly at poster center.
    - If 2 images: place them centered vertically, left and right of center.
    - If >2: spread evenly across the horizontal center line.
    Images are resized to fit within max_width_ratio * bg.width per image and max_height_ratio * bg.height.
    """
    n = len(files)
    if n == 0:
        return
    bw, bh = bg_image.size
    max_w = int(bw * max_width_ratio)
    max_h = int(bh * max_height_ratio)

    imgs = []
    for f in files:
        try:
            im = Image.open(f).convert('RGBA')
            im.thumbnail((max_w, max_h), Image.LANCZOS)
            imgs.append(im)
        except Exception:
            continue

    if not imgs:
        return

    center_x = bw // 2
    center_y = bh // 2

    if len(imgs) == 1:
        im = imgs[0]
        pos_x = center_x - im.width // 2
        pos_y = center_y - im.height // 2
        bg_image.paste(im, (pos_x, pos_y), im)
        return

    if len(imgs) == 2:
        left = imgs[0]
        right = imgs[1]
        spacing = int(bw * 0.05)
        pos_left_x = center_x - spacing//2 - left.width
        pos_right_x = center_x + spacing//2
        pos_y = center_y - max(left.height, right.height) // 2
        bg_image.paste(left, (pos_left_x, pos_y), left)
        bg_image.paste(right, (pos_right_x, pos_y), right)
        return

    # more than 2: distribute across center line
    total = len(imgs)
    # compute total width and spacing
    total_imgs_w = sum(im.width for im in imgs)
    available_w = int(bw * 0.8)
    gap = max(10, (available_w - total_imgs_w) // (total - 1)) if total > 1 else 0
    start_x = center_x - (total_imgs_w + gap*(total-1)) // 2
    x = start_x
    for im in imgs:
        pos_y = center_y - im.height // 2
        bg_image.paste(im, (int(x), int(pos_y)), im)
        x += im.width + gap


place_assets(bg, asset_files)

final = bg.convert("RGB")
final.save(output_path)
print(f"✅ Poster saved as {output_path}")
