"""Génère l'icône de l'app (dessin original) : assets/icon.png, icon.icns, icon.ico"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4096  # supersampling, réduit à 1024
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # fond : dégradé orange vertical dans un carré arrondi (marge macOS ~10 %)
    m = int(S * 0.09)
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    top, bot = (255, 150, 60), (226, 72, 22)
    for y in range(S):
        gd.line([(0, y), (S, y)], fill=lerp(top, bot, y / S) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([m, m, S - m, S - m], radius=int(S * 0.19), fill=255)
    # ombre portée
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([m, m + 40, S - m, S - m + 40], radius=int(S * 0.19), fill=(0, 0, 0, 90))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(60)))
    img.paste(grad, (0, 0), mask)
    # reflet "verre" en haut
    gloss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(gloss).ellipse([m - S * 0.3, m - S * 0.62, S - m + S * 0.3, S * 0.42], fill=(255, 255, 255, 46))
    gm = Image.new("L", (S, S), 0); gm.paste(mask)
    img.alpha_composite(Image.composite(gloss, Image.new("RGBA", (S, S)), gm))

    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    O = (232, 86, 30, 255)
    # document PDF (coin replié)
    x0, y0, x1, y1 = S * 0.22, S * 0.19, S * 0.60, S * 0.70
    f = S * 0.09
    dsh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(dsh).polygon([(x0, y0 + 30), (x1 - f, y0 + 30), (x1, y0 + f + 30), (x1, y1 + 30), (x0, y1 + 30)], fill=(120, 30, 0, 110))
    img.alpha_composite(dsh.filter(ImageFilter.GaussianBlur(45)))
    d.polygon([(x0, y0), (x1 - f, y0), (x1, y0 + f), (x1, y1), (x0, y1)], fill=W)
    d.polygon([(x1 - f, y0), (x1 - f, y0 + f), (x1, y0 + f)], fill=(255, 205, 170, 255))
    for i in range(3):
        yy = y0 + S * (0.08 + i * 0.045)
        d.rounded_rectangle([x0 + S * 0.05, yy, x0 + S * (0.24 if i < 2 else 0.17), yy + S * 0.018], radius=S * 0.009, fill=(250, 170, 120, 255))
    font = ImageFont.truetype(FONT, int(S * 0.105))
    d.text(((x0 + x1) / 2, y0 + S * 0.27), "PDF", font=font, fill=O, anchor="mm")

    # diapositive (rectangle 16:9) avec un graphique
    sx0, sy0, sx1, sy1 = S * 0.42, S * 0.55, S * 0.82, S * 0.80
    ssh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(ssh).rounded_rectangle([sx0, sy0 + 35, sx1, sy1 + 35], radius=S * 0.025, fill=(120, 30, 0, 120))
    img.alpha_composite(ssh.filter(ImageFilter.GaussianBlur(45)))
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=S * 0.025, fill=W)
    d.rounded_rectangle([sx0 + S * 0.03, sy0 + S * 0.03, sx1 - S * 0.03, sy1 - S * 0.03], radius=S * 0.012, outline=(250, 170, 120, 255), width=int(S * 0.008))
    bx = sx0 + S * 0.07
    for i, h in enumerate((0.06, 0.10, 0.08, 0.13)):
        d.rounded_rectangle([bx + i * S * 0.065, sy1 - S * 0.05 - S * h, bx + i * S * 0.065 + S * 0.04, sy1 - S * 0.05], radius=S * 0.008, fill=O)

    # flèche courbe du document vers la diapo
    import math
    aw = int(S * 0.028)
    cx, cy, r = S * 0.665, S * 0.37, S * 0.15
    a0, a1 = -95, 62
    d.arc([cx - r, cy - r, cx + r, cy + r], start=a0, end=a1, fill=W, width=aw)
    t = math.radians(a1)
    ex, ey = cx + (r - aw / 2) * math.cos(t), cy + (r - aw / 2) * math.sin(t)
    tx, ty = -math.sin(t), math.cos(t)          # tangente (sens horaire)
    nx, ny = math.cos(t), math.sin(t)           # normale
    L, Wd = S * 0.075, S * 0.055
    tip = (ex + tx * L, ey + ty * L)
    d.polygon([tip, (ex + nx * Wd, ey + ny * Wd), (ex - nx * Wd, ey - ny * Wd)], fill=W)

    icon = img.resize((1024, 1024), Image.LANCZOS)
    os.makedirs(OUT, exist_ok=True)
    icon.save(os.path.join(OUT, "icon.png"))
    icon.save(os.path.join(OUT, "icon.icns"))
    icon.save(os.path.join(OUT, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    main()
