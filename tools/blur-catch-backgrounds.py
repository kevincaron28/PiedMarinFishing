# -*- coding: utf-8 -*-
"""Floute l'arrière-plan des photos de prises.

Un spot à maskinongé se garde. Une rive, une tour, un quai suffisent à le
situer, alors que le poisson et les pêcheurs, eux, doivent rester nets.

La méthode : une zone nette elliptique autour des sujets, un fond flouté,
et une transition adoucie pour que ça se lise comme une profondeur de champ
plutôt que comme une retouche.

Les originaux ne sont pas dans le dépôt : garde-les de ton côté, le
floutage n'est pas réversible une fois publié.
"""
from PIL import Image, ImageOps, ImageDraw, ImageFilter
import os, sys

W, H = 1200, 900
BLUR = 16          # assez pour effacer une ligne d'arbres ou une tour
FEATHER = 70       # douceur de la transition

# Le masque est une union d'ellipses, une par sujet plus une pour le poisson.
# Une seule grande ellipse ne marche pas : elle englobe forcément ce qui se
# trouve ENTRE les pêcheurs — sur la photo de Kevin B., une tour de
# communication passait pile entre les deux têtes.
# Coordonnées en fraction de l'image : (cx, cy, rx, ry).
JOBS = [
  ("5fdb2210-image.jpg", "assets/img/team/kevin-caron.jpg", ("fit", 0.45), [
      (0.50, 0.55, 0.155, 0.45),  # le pêcheur
      (0.50, 0.68, 0.33, 0.15),   # le saumon
  ]),
  ("a1f6e1a8-image.jpg", "assets/img/team/kevin-b.jpg", ("band", 0.13), [
      (0.40, 0.60, 0.155, 0.42),  # pêcheur de gauche
      (0.72, 0.58, 0.150, 0.44),  # pêcheur de droite
      (0.55, 0.62, 0.41, 0.19),   # le maskinongé
  ]),
  ("8c0cd388-image.jpg", "assets/img/team/bobe.jpg", ("fit", 0.45), [
      (0.60, 0.55, 0.145, 0.45),  # le pêcheur
      (0.48, 0.60, 0.31, 0.21),   # le maskinongé
  ]),
  ("ad08cb0e-image.jpg", "assets/img/catches/maskinonge-kevin-b-2.jpg", ("fit", 0.34), [
      (0.35, 0.56, 0.155, 0.45),  # pêcheur de gauche
      (0.71, 0.52, 0.165, 0.47),  # pêcheur de droite
      (0.48, 0.56, 0.43, 0.21),   # le maskinongé
  ]),
]
SRC = "/root/.claude/uploads/fd04c8b1-f2c9-52b0-bd85-87187f0e94aa"

def crop(im, mode):
    kind, val = mode
    if kind == "fit":
        return ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, val))
    w, h = im.size
    ch = int(round(w / (W / H)))
    top = max(0, min(int(round(h * val)), h - ch))
    return im.crop((0, top, w, top + ch)).resize((W, H), Image.LANCZOS)

for name, dest, mode, shapes in JOBS:
    path = os.path.join(SRC, name)
    if not os.path.exists(path):
        print("  source absente, ignorée :", name); continue
    im = crop(ImageOps.exif_transpose(Image.open(path)).convert("RGB"), mode)
    blurred = im.filter(ImageFilter.GaussianBlur(BLUR))

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for cx, cy, rx, ry in shapes:
        d.ellipse([(cx - rx) * W, (cy - ry) * H, (cx + rx) * W, (cy + ry) * H], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(FEATHER))

    out = Image.composite(im, blurred, mask)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    out.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
    print("  %-44s %.0f Ko" % (dest, os.path.getsize(dest) / 1024))
