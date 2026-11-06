"""Conversion PDF -> PPTX : chaque page est rendue en image haute qualité
et posée plein cadre sur une diapositive (contenu non éditable, identique au PDF)."""
import io
import os

import pymupdf as fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Emu

EMU_PER_POINT = 12700          # 1 pt PDF = 1/72 pouce = 12700 EMU
MAX_SLIDE_EMU = 51206400       # limite PowerPoint : 56 pouces
MIN_SLIDE_EMU = 914400         # limite PowerPoint : 1 pouce
MAX_PIXELS = 12000             # garde-fou mémoire par côté d'image


def _slide_size(width_pt, height_pt):
    """Taille de diapo (EMU) au même ratio que la page, dans les limites PowerPoint."""
    w, h = width_pt * EMU_PER_POINT, height_pt * EMU_PER_POINT
    scale = 1.0
    if max(w, h) > MAX_SLIDE_EMU:
        scale = MAX_SLIDE_EMU / max(w, h)
    elif min(w, h) < MIN_SLIDE_EMU:
        scale = MIN_SLIDE_EMU / min(w, h)
    return int(w * scale), int(h * scale)


DPI = 600  # qualité maximale, image PNG sans perte


def output_path_for(pdf_path):
    """Chemin du .pptx à côté du PDF, sans écraser un fichier existant."""
    base = os.path.splitext(pdf_path)[0]
    out = base + ".pptx"
    n = 2
    while os.path.exists(out):
        out = f"{base} ({n}).pptx"
        n += 1
    return out


def convert(pdf_path, pptx_path=None, dpi=DPI, image_format="png",
            jpeg_quality=95, progress=None, cancel=None):
    """Convertit pdf_path en pptx. Retourne le chemin du .pptx créé.

    progress(page_courante, total) est appelé après chaque page.
    cancel() -> True interrompt la conversion.
    """
    if pptx_path is None:
        pptx_path = output_path_for(pdf_path)

    doc = fitz.open(pdf_path)
    if doc.needs_pass:
        raise ValueError("Ce PDF est protégé par un mot de passe.")
    if doc.page_count == 0:
        raise ValueError("Ce PDF ne contient aucune page.")

    first = doc[0].rect
    slide_w, slide_h = _slide_size(first.width, first.height)

    prs = Presentation()
    prs.slide_width = Emu(slide_w)
    prs.slide_height = Emu(slide_h)
    blank = prs.slide_layouts[6]  # mise en page vide

    total = doc.page_count
    for i, page in enumerate(doc):
        if cancel and cancel():
            raise InterruptedError("Conversion annulée.")

        rect = page.rect
        zoom = dpi / 72.0
        longest = max(rect.width, rect.height) * zoom
        if longest > MAX_PIXELS:
            zoom *= MAX_PIXELS / longest
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False,
                              annots=True)

        if image_format == "jpeg":
            data = pix.tobytes("jpeg", jpg_quality=jpeg_quality)
        else:
            data = pix.tobytes("png")

        # Page à la taille de la diapo en gardant ses proportions (centrée)
        ratio = min(slide_w / rect.width, slide_h / rect.height)
        pic_w, pic_h = int(rect.width * ratio), int(rect.height * ratio)
        left, top = (slide_w - pic_w) // 2, (slide_h - pic_h) // 2

        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(io.BytesIO(data), Emu(left), Emu(top),
                                 Emu(pic_w), Emu(pic_h))
        pix = None
        if progress:
            progress(i + 1, total)

    doc.close()
    prs.save(pptx_path)
    return pptx_path
