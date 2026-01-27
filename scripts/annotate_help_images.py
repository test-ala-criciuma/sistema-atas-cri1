"""Annotate help images with arrows and labels automatically.
Saves annotated images alongside originals with suffix '-annotated'.

Usage: python scripts/annotate_help_images.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'static', 'help')
if not os.path.exists(BASE):
    raise SystemExit('Static help folder not found: ' + BASE)

# Basic font: try to use a TTF, fallback to default
try:
    FONT = ImageFont.truetype('DejaVuSans-Bold.ttf', 18)
except Exception:
    try:
        FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except Exception:
        FONT = ImageFont.load_default()

# Annotations defined as list of (image_name, list of annotations)
# Each annotation: {'xy': (x_frac,y_frac), 'text': 'Label', 'target': (x2_frac,y2_frac)}
ANNOTATIONS = {
    'help-login-desktop.png': [
        {'xy': (0.22, 0.55), 'text': 'Usuário', 'target': (0.35, 0.55)},
        {'xy': (0.72, 0.55), 'text': 'Campo Senha', 'target': (0.78, 0.55)},
        {'xy': (0.5, 0.75), 'text': 'Entrar', 'target': (0.5, 0.8)},
    ],
    'help-login-password-focus-desktop.png': [
        {'xy': (0.85, 0.5), 'text': 'Botão olho', 'target': (0.78, 0.5)},
    ],
    'help-after-login-desktop.png': [
        {'xy': (0.18, 0.35), 'text': 'Criar Ata', 'target': (0.25, 0.35)},
        {'xy': (0.7, 0.25), 'text': 'Próxima Reunião', 'target': (0.75, 0.28)},
    ],
    'help-index-desktop.png': [
        {'xy': (0.16, 0.26), 'text': 'Criar Ata rápido', 'target': (0.22, 0.28)},
        {'xy': (0.72, 0.28), 'text': 'Próxima Reunião', 'target': (0.78, 0.3)},
    ],
    'help-nova_ata-desktop.png': [
        {'xy': (0.35, 0.4), 'text': 'Tipo de Ata', 'target': (0.3, 0.45)},
        {'xy': (0.63, 0.56), 'text': 'Data', 'target': (0.6, 0.6)},
    ],
    'help-sacramental-desktop.png': [
        {'xy': (0.5, 0.18), 'text': 'Tema', 'target': (0.5, 0.24)},
        {'xy': (0.25, 0.45), 'text': 'Hinos', 'target': (0.2, 0.48)},
        {'xy': (0.75, 0.45), 'text': 'Discursantes', 'target': (0.78, 0.48)},
        {'xy': (0.5, 0.88), 'text': 'Salvar', 'target': (0.5, 0.92)},
    ],
    'help-configuracoes-desktop.png': [
        {'xy': (0.5, 0.22), 'text': 'Templates', 'target': (0.5, 0.26)},
        {'xy': (0.8, 0.6), 'text': 'Editar', 'target': (0.78, 0.6)},
    ],
}

OUT_SUFFIX = '-annotated'

def draw_arrow(draw, x1, y1, x2, y2, color=(255, 99, 71), width=5):
    # main line
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    # arrowhead
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    head_length = 15
    angle1 = angle + math.radians(25)
    angle2 = angle - math.radians(25)
    x3 = x2 - head_length * math.cos(angle1)
    y3 = y2 - head_length * math.sin(angle1)
    x4 = x2 - head_length * math.cos(angle2)
    y4 = y2 - head_length * math.sin(angle2)
    draw.polygon([(x2, y2), (x3, y3), (x4, y4)], fill=color)


def annotate_image(filename, anns):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print('Missing', filename)
        return
    img = Image.open(path).convert('RGBA')
    w, h = img.size
    overlay = Image.new('RGBA', img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    for ann in anns:
        tx, ty = ann['xy']
        tgtx, tgty = ann['target']
        x1, y1 = int(tx * w), int(ty * h)
        x2, y2 = int(tgtx * w), int(tgty * h)
        # draw arrow
        draw_arrow(draw, x1, y1, x2, y2, color=(124,58,237,255), width=max(3, int(w/300)))
        # label box near source point
        text = ann['text']
        padding = 8
        font = FONT
        try:
            tw, th = font.getsize(text)
        except Exception:
            # fallback using textbbox
            bbox = draw.textbbox((0,0), text, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        box_w, box_h = tw + padding*2, th + padding
        bx = x1 - box_w//2
        by = y1 - box_h - 10
        # Clip to image
        bx = max(6, min(bx, w - box_w - 6))
        by = max(6, min(by, h - box_h - 6))
        # rounded rectangle background
        rect_color = (28, 20, 33, 220)
        # draw rectangle with corner radius
        r = 8
        draw.rounded_rectangle((bx, by, bx+box_w, by+box_h), radius=r, fill=rect_color)
        # draw text
        draw.text((bx + padding, by + padding//2), text, font=font, fill=(236, 232, 255, 255))
    out = Image.alpha_composite(img, overlay)
    base, ext = os.path.splitext(path)
    outpath = base + OUT_SUFFIX + ext
    out.convert('RGB').save(outpath, quality=90)
    print('Saved', outpath)


def main():
    for fname, anns in ANNOTATIONS.items():
        annotate_image(fname, anns)

if __name__ == '__main__':
    main()
