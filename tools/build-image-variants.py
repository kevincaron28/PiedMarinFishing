# -*- coding: utf-8 -*-
"""Écrit les versions réduites des photos, et la carte qui dit lesquelles existent.

Le site servait le fichier d'origine partout. Une vignette du temple de la
renommée, affichée à 72 pixels, recevait une image de 1200 : seize fois trop.
La page Prises pesait 1,27 Mo pour huit photos.

    python3 tools/build-image-variants.py

Pour chaque photo, on écrit `<nom>-<largeur>.jpg` à côté de l'originale, et
data/image-variants.json note les largeurs disponibles. Le navigateur choisit
lui-même grâce à srcset — le JS et les générateurs lisent la carte, et une
photo absente de la carte est simplement servie telle quelle.

À relancer après tout ajout de photo dans assets/img/{catches,team,boats}.
"""
import io
import json
import os

from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ("assets/img/catches", "assets/img/team", "assets/img/boats")
WIDTHS = (160, 400, 800)
# Une photo de téléphone fait 4000px et 5 Mo. L'affichage le plus large du site
# en demande 652, soit 1304 sur un écran à double densité : au-delà de 1600, on
# stocke du poids que personne ne recevra jamais. La source est donc réduite sur
# place, une fois, à la première exécution.
#
# Garde tes originaux ailleurs : ce dossier est la copie du site, pas l'archive.
MAX_SOURCE = 1600
QUALITY = 82
EXTS = (".jpg", ".jpeg", ".png")


def variant_path(src, width):
    stem, ext = os.path.splitext(src)
    return "%s-%d%s" % (stem, width, ext)


def fresh(src, out):
    """Une variante déjà écrite après sa source n'a pas à être refaite."""
    return os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(src)


def cap_source(rel, report):
    """Ramène une source démesurée à MAX_SOURCE, sur place."""
    src = os.path.join(REPO, rel)
    im = Image.open(src)
    if im.width <= MAX_SOURCE:
        return im
    avant = os.path.getsize(src)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    petite = im.resize((MAX_SOURCE, round(MAX_SOURCE * im.height / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if rel.lower().endswith(".png"):
        petite.save(buf, "PNG", optimize=True)
    else:
        petite.save(buf, "JPEG", quality=88, optimize=True, progressive=True)
    # Recompresser une image déjà compressée peut la faire GROSSIR. Une source
    # à peine au-dessus du plafond ne vaut alors pas la perte de qualité : on
    # n'écrit que si on y gagne vraiment.
    if buf.tell() >= avant:
        return im
    with open(src, "wb") as fh:
        fh.write(buf.getvalue())
    report.append(("↓ source ramenée à %dpx  %s" % (MAX_SOURCE, rel),
                   avant - os.path.getsize(src)))
    return Image.open(src)


def build(rel, report):
    src = os.path.join(REPO, rel)
    im = cap_source(rel, report)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    widths = [w for w in WIDTHS if w < im.width]
    for w in widths:
        out_rel = variant_path(rel, w)
        out = os.path.join(REPO, out_rel)
        if fresh(src, out):
            continue
        h = round(w * im.height / im.width)
        small = im.resize((w, h), Image.LANCZOS)
        if out_rel.lower().endswith(".png"):
            small.save(out, "PNG", optimize=True)
        else:
            small.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        report.append((out_rel, os.path.getsize(out)))
    # La largeur d'origine ferme la liste : c'est elle que srcset sert en haut
    # de gamme, sous son nom de fichier normal.
    return sorted(widths + [im.width])


if __name__ == "__main__":
    carte, report, sources = {}, [], 0
    for d in DIRS:
        directory = os.path.join(REPO, d)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.lower().endswith(EXTS):
                continue
            # Ne pas prendre une variante pour une source.
            stem = os.path.splitext(name)[0]
            if stem.rsplit("-", 1)[-1].isdigit() and int(stem.rsplit("-", 1)[-1]) in WIDTHS:
                continue
            rel = "%s/%s" % (d, name)
            carte[rel] = build(rel, report)
            sources += 1

    path = os.path.join(REPO, "data", "image-variants.json")
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(carte, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    for rel, size in report:
        if rel.startswith("↓"):
            print("  %-58s -%4d Ko" % (rel, size // 1024))
        else:
            print("  écrit  %-50s %5d Ko" % (rel, size // 1024))
    print("\n%d photo(s), %d variante(s) écrite(s) cette fois." % (sources, len(report)))
    for rel, widths in sorted(carte.items()):
        print("  %-46s %s" % (rel, " ".join("%dw" % w for w in widths)))
