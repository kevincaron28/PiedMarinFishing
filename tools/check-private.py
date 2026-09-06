# -*- coding: utf-8 -*-
"""Refuse qu'un numero identifiant parte en ligne.

Le depot est public. Un numero d'immatriculation de bateau, une plaque ou un
numero de serie n'ont rien a faire dans data/ ni dans une page generee — ni
dans une photo, ni, et c'est l'erreur qui a motive ce script, dans le TEXTE
qui decrit la photo. Le numero du Princecraft 1995 avait ete masque sur
l'image puis reecrit dans son texte alternatif, ou il est reste invisible
jusqu'a ce que les descriptions deviennent des legendes affichees.

    python3 tools/check-private.py     # sort en code 1 si quelque chose passe

A lancer avant de pousser, comme sync-html-fallbacks.py --check.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dossiers qui partent en ligne. Le bac a sable et .git n'y sont pas.
SCAN_DIRS = ["data", "tournois", "pecheurs", "bateaux", "prises"]
SCAN_ROOT_EXT = (".html",)

# Chaque motif : (nom, expression, raison). On vise juste plutot que large —
# un controle qui crie a tort finit par etre ignore.
PATTERNS = [
    ("immatriculation de bateau",
     re.compile(r"\b(?:QC|ON)[\s-]?\d{6,7}\b"),
     "immatriculation d'embarcation"),
    ("plaque d'immatriculation",
     re.compile(r"\b[A-Z]{3}[\s-]?\d{3}\b(?!\s*(?:po|lb|cm|mm|kg|pi|ft|in))"),
     "format de plaque"),
    # « registration » est ecarte a dessein : en anglais de tournoi il veut
    # dire « inscription », et il apparait partout dans le repertoire. Le mot
    # doit designer une IMMATRICULATION, et ce qui suit doit ressembler a un
    # identifiant — au moins six chiffres, ou un melange lettres+chiffres.
    ("numero nomme",
     re.compile(r"(?:immatricul\w*|plaque d'immatriculation|licen[cs]e plate|"
                r"num[ée]ro de s[ée]rie|serial number|hull (?:id|number)|\bVIN\b)"
                r"[^.\n]{0,20}?[:\s]\s*"
                r"((?=[A-Z0-9-]{6,})(?:[A-Z]+[\s-]?\d|\d{6})[A-Z0-9\s-]*)", re.I),
     "un identifiant suit un mot comme « immatriculation »"),
]


def files():
    for name in sorted(os.listdir(REPO)):
        if name.endswith(SCAN_ROOT_EXT):
            yield os.path.join(REPO, name)
    for d in SCAN_DIRS:
        p = os.path.join(REPO, d)
        if not os.path.isdir(p):
            continue
        for name in sorted(os.listdir(p)):
            if name.endswith((".json", ".html")):
                yield os.path.join(p, name)


def main():
    hits = []
    scanned = 0
    for path in files():
        scanned += 1
        with io.open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                for label, rx, why in PATTERNS:
                    m = rx.search(line)
                    if m:
                        hits.append((os.path.relpath(path, REPO), n, label, why,
                                     m.group(0)[:60]))
    if hits:
        print("REFUS — %d identifiant(s) trouve(s) dans ce qui part en ligne :\n" % len(hits))
        for f, n, label, why, txt in hits:
            print("  %s:%d" % (f, n))
            print("     %s — %s" % (label, why))
            print("     « %s »\n" % txt)
        print("Retire-les avant de pousser. Le depot est public.")
        return 1
    print("%d fichiers verifies — aucun numero identifiant. ✓" % scanned)
    return 0


if __name__ == "__main__":
    sys.exit(main())
