# -*- coding: utf-8 -*-
"""Lit une fiche d'espèce enregistrée depuis quebec.ca et en sort les faits.

POURQUOI CE SCRIPT EXISTE. L'environnement de travail n'a pas accès aux sites
externes : impossible d'ouvrir quebec.ca pour vérifier quoi que ce soit. La
seule façon honnête de citer une source est donc de la LIRE — et pour ça il
faut que quelqu'un enregistre la page (Ctrl+S, format « page web complète »,
un fichier .mht) et l'envoie.

Ce script transforme ce .mht en faits structurés. Il ne décide rien et
n'écrit rien dans data/ : il extrait, il affiche, et un humain choisit ce qui
mérite d'être publié. C'est volontaire — une fiche d'espèce recopiée
automatiquement serait exactement le contenu générique qu'on cherche à
éviter, et la barrière de vérification perdrait son sens si le script se
vérifiait lui-même.

    python3 tools/import-qc-species.py fiche.mht [autre.mht ...]
    python3 tools/import-qc-species.py --json fiche.mht > brouillon.json
    python3 tools/import-qc-species.py --table *.mht

Les fiches de quebec.ca suivent toutes le même gabarit : un bloc
d'identité (noms, statut), puis des sections titrées. Le sommaire « Dans
cette page » répète ces titres avant le contenu; on s'en sert pour savoir
quelles sections chercher, puis on le saute.
"""
import email
import html
import io
import json
import os
import re
import sys
from email import policy

# Les libellés du bloc d'identité, dans l'ordre où quebec.ca les présente.
IDENTITY = ["Nom français", "Autre(s) nom(s) français", "Nom anglais",
            "Nom scientifique", "Grand groupe", "Sous-groupe", "Espèce à statut"]


def page_text(path):
    """Le texte visible du .mht, une ligne par élément, sans doublon consécutif."""
    with open(path, "rb") as fh:
        msg = email.message_from_binary_file(fh, policy=policy.default)
    url = msg.get("Snapshot-Content-Location") or ""
    raw = None
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            raw = part.get_payload(decode=True).decode("utf-8", "replace")
            break
    if raw is None:
        raise SystemExit("aucun HTML dans %s" % path)
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = html.unescape(re.sub(r"(?s)<[^>]+>", "\n", raw))
    out, prev = [], None
    for line in (l.strip() for l in text.split("\n")):
        if line and line != prev and len(line) > 1:
            out.append(line)
            prev = line
    return out, url, raw


def rejoin(lines):
    """quebec.ca coupe « 54 et 68 \\n cm » : on recolle l'unité à son nombre."""
    out = []
    for line in lines:
        if out and re.match(r"^(cm|mm|m|kg|g|lb|po|ans|°C|p\.)\b", line):
            out[-1] = out[-1] + " " + line
        else:
            out.append(line)
    return out


def parse(path):
    lines, url, raw = page_text(path)
    doc = {"file": os.path.basename(path), "url": url}

    # Bloc d'identité : chaque libellé est suivi de sa valeur.
    for i, line in enumerate(lines):
        if line in IDENTITY and i + 1 < len(lines) and lines[i + 1] not in IDENTITY:
            doc.setdefault(line, lines[i + 1])

    # Le sommaire donne la liste des sections de CETTE fiche — elles varient
    # d'une espèce à l'autre (« Espèce exotique envahissante » n'existe que
    # sur certaines). Le lire évite d'en coder une liste en dur qui vieillit.
    try:
        start = lines.index("Dans cette page :")
    except ValueError:
        doc["sections"] = {}
        return doc
    titles, i = [], start + 1
    while i < len(lines) and lines[i] not in ("Références", "À consulter aussi"):
        if lines[i] in titles:
            break
        titles.append(lines[i])
        i += 1

    # Le contenu commence après le sommaire, à la première répétition du
    # premier titre.
    body = lines[i:]
    idx = {}
    for t in titles:
        for j, line in enumerate(body):
            if line == t and j not in idx.values():
                idx[t] = j
                break
    order = sorted(idx.items(), key=lambda kv: kv[1])
    sections = {}
    for n, (title, j) in enumerate(order):
        end = order[n + 1][1] if n + 1 < len(order) else len(body)
        chunk = rejoin(body[j + 1:end])
        if chunk:
            sections[title] = chunk
    doc["sections"] = sections

    # Les liens utiles : la source officielle de la reglementation, le
    # registre federal, etc.
    doc["links"] = sorted(set(
        m.group(1) for m in re.finditer(r'href="(https://www\.(?:quebec|canada)\.ca[^"]+)"', raw)
        if "reglementation" in m.group(1) or "peche-sportive" in m.group(1)
        or "especes-peril" in m.group(1)))
    return doc


def brief(doc):
    s = doc.get("sections", {})
    name = doc.get("Nom français", "?")
    status = doc.get("Espèce à statut", "")
    keys = [k for k in s if re.search(r"(?i)envahissa|complément|désignation|pêche", k)]
    print("=" * 72)
    print("%s  (%s)" % (name, doc.get("Nom scientifique", "?")))
    print("  EN : %s" % doc.get("Nom anglais", "?"))
    if status:
        print("  STATUT : %s" % status)
    print("  sections : %s" % ", ".join(s.keys()))
    if keys:
        print("  ⚑ sections à lire en priorité : %s" % ", ".join(keys))
    for k in keys:
        txt = " ".join(s[k])
        print("     %s → %s" % (k, txt[:400] + ("…" if len(txt) > 400 else "")))


def table(docs):
    print("%-26s %-30s %-22s %s" % ("ESPÈCE", "SCIENTIFIQUE", "STATUT", "SECTIONS PARTICULIÈRES"))
    print("-" * 118)
    for d in docs:
        extra = [k for k in d.get("sections", {})
                 if re.search(r"(?i)envahissa|complément|désignation", k)]
        print("%-26s %-30s %-22s %s" % (
            d.get("Nom français", "?")[:25],
            d.get("Nom scientifique", "?")[:29],
            (d.get("Espèce à statut") or "—")[:21],
            ", ".join(extra) or "—"))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        raise SystemExit(__doc__)
    docs = [parse(a) for a in args]
    if "--json" in flags:
        print(json.dumps(docs if len(docs) > 1 else docs[0], ensure_ascii=False, indent=2))
    elif "--table" in flags:
        table(docs)
    else:
        for d in docs:
            brief(d)
