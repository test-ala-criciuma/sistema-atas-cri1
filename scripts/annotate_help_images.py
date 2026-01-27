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
    # Desktop annotations
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

    # Mobile variants (fractional positions adjusted for portrait)
    'help-login-mobile.png': [
        {'xy': (0.2, 0.45), 'text': 'Usuário', 'target': (0.35, 0.45)},
        {'xy': (0.8, 0.45), 'text': 'Campo Senha', 'target': (0.78, 0.45)},
        {'xy': (0.5, 0.8), 'text': 'Entrar', 'target': (0.5, 0.9)},
    ],
    'help-login-password-focus-mobile.png': [
        {'xy': (0.92, 0.5), 'text': 'Botão olho', 'target': (0.88, 0.5)},
    ],
    'help-after-login-mobile.png': [
        {'xy': (0.18, 0.2), 'text': 'Criar Ata', 'target': (0.25, 0.22)},
        {'xy': (0.6, 0.18), 'text': 'Próxima Reunião', 'target': (0.7, 0.22)},
    ],
    'help-index-mobile.png': [
        {'xy': (0.12, 0.18), 'text': 'Criar Ata rápido', 'target': (0.2, 0.22)},
        {'xy': (0.65, 0.18), 'text': 'Próxima Reunião', 'target': (0.72, 0.25)},
    ],
    'help-nova_ata-mobile.png': [
        {'xy': (0.35, 0.45), 'text': 'Tipo de Ata', 'target': (0.3, 0.5)},
        {'xy': (0.63, 0.66), 'text': 'Data', 'target': (0.6, 0.7)},
    ],
    'help-sacramental-mobile.png': [
        {'xy': (0.5, 0.14), 'text': 'Tema', 'target': (0.5, 0.2)},
        {'xy': (0.18, 0.42), 'text': 'Hinos', 'target': (0.15, 0.46)},
        {'xy': (0.8, 0.42), 'text': 'Discursantes', 'target': (0.82, 0.48)},
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


def build_svg_for(filename, anns):
    # Build SVG that embeds the original raster and draws vector arrows and text
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print('Missing', filename)
        return
    img = Image.open(path)
    w, h = img.size
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    # embed the image by relative filename (SVG will be served from the same dir)
    svg_lines.append(f'<image href="{filename}" x="0" y="0" width="{w}" height="{h}" />')
    # defs for arrow style
    svg_lines.append('<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#7c3aed"/></marker></defs>')
    for ann in anns:
        tx, ty = ann['xy']
        tgtx, tgty = ann['target']
        x1, y1 = int(tx * w), int(ty * h)
        x2, y2 = int(tgtx * w), int(tgty * h)
        # line with marker
        svg_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#7c3aed" stroke-width="6" stroke-linecap="round" marker-end="url(#arrowhead)" />')
        # label background
        text = ann['text'].replace('&','&amp;').replace('<','&lt;')
        # compute label position offset
        lx = x1 - 80 if x1 > w/2 else x1 + 10
        ly = y1 - 30 if y1 > 40 else y1 + 10
        # background rect
        svg_lines.append(f'<rect x="{lx}" y="{ly}" rx="6" ry="6" width="140" height="28" fill="#1c1421" fill-opacity="0.86" />')
        svg_lines.append(f'<text x="{lx+10}" y="{ly+19}" font-family="DejaVu Sans, Arial, sans-serif" font-size="14" fill="#ece8ff">{text}</text>')
    svg_lines.append('</svg>')
    out_svg = os.path.join(BASE, os.path.splitext(filename)[0] + OUT_SUFFIX + '.svg')
    with open(out_svg, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines))
    print('Saved', out_svg)


def main():
    for fname, anns in ANNOTATIONS.items():
        annotate_image(fname, anns)
        # Also generate a vector SVG overlay
        build_svg_for(fname, anns)

if __name__ == '__main__':
    main()
