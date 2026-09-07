# -*- coding: utf-8 -*-
"""Reconstruit les LIGNES d'un tableau PDF a partir des coordonnees.

Sans les coordonnees, l'extraction met « Dore jaune 6 37 cm a 53 cm » d'un
cote et « 15 juin 2026 au 31 octobre 2026 » de l'autre, sans dire lesquelles
vont ensemble. Sur une page de reglementation, apparier une espece avec les
mauvaises dates peut valoir une amende a quelqu'un. On garde donc X et Y.
"""
import re, sys, zlib
sys.path.insert(0, ".")
from importlib.util import spec_from_file_location, module_from_spec
import os
_s = spec_from_file_location("pdftext", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf-text.py"))
_m = module_from_spec(_s); _s.loader.exec_module(_m)
streams, cmaps = _m.streams, _m.cmaps

def page_rows(content, table, ytol=4.0):
    """[(y, [(x, texte), ...]), ...] du haut vers le bas."""
    items = []
    for blk in re.finditer(rb"BT(.*?)ET", content, re.S):
        body = blk.group(1)
        # Td OU Tm : un bloc positionne par une matrice de texte etait
        # silencieusement jete, et sa cellule disparaissait du tableau.
        pos = re.search(rb"([\d.\-]+)\s+([\d.\-]+)\s+Td", body)
        if pos:
            x, y = float(pos.group(1)), float(pos.group(2))
        else:
            pos = re.search(rb"([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+"
                            rb"([\d.\-]+)\s+([\d.\-]+)\s+Tm", body)
            if not pos:
                continue
            x, y = float(pos.group(5)), float(pos.group(6))
        # Les Td suivants dans le meme bloc descendent d'une ligne.
        dy = 0.0
        for m in re.finditer(rb"(?:([\d.\-]+)\s+([\d.\-]+)\s+Td)|<([0-9A-Fa-f]+)>\s*Tj", body):
            if m.group(3) is None:
                if m.start() != pos.start():
                    dy += float(m.group(2))
                continue
            h = m.group(3).decode()
            txt = "".join(table.get(int(h[i:i+4], 16), "") for i in range(0, len(h), 4))
            if txt.strip():
                items.append((round(y + dy, 1), x, txt))
    rows, cur, cy = [], [], None
    for y, x, txt in sorted(items, key=lambda t: (-t[0], t[1])):
        if cy is None or abs(y - cy) <= ytol:
            cur.append((x, txt)); cy = y if cy is None else cy
        else:
            rows.append((cy, sorted(cur))); cur = [(x, txt)]; cy = y
    if cur:
        rows.append((cy, sorted(cur)))
    return rows

if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    table = cmaps(data)
    pages = [s for s in streams(data) if b"Tj" in s]
    want = [int(a) for a in sys.argv[2:]] or range(len(pages))
    for i in want:
        if i >= len(pages):
            continue
        print("########## bloc %d ##########" % i)
        for y, cells in page_rows(pages[i], table):
            line = "  |  ".join("%s" % t for _, t in cells)
            if line.strip():
                print("  %s" % line)
