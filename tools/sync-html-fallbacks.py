# -*- coding: utf-8 -*-
"""Resynchronise le texte français écrit en dur dans les pages HTML.

Chaque page porte une copie française du texte, visible avant que
assets/js/i18n.js s'exécute — et c'est cette copie-là que lisent les robots
des moteurs de recherche et les aperçus de lien. Elle doit donc rester
identique à data/i18n.json, sinon Google indexe une vieille phrase.

Le script recopie data/i18n.json vers :
  - le contenu des éléments  data-i18n / data-i18n-text
  - les attributs            data-i18n-content / -alt / -aria-label / -href
  - les balises og:title, twitter:title      (depuis <title>)
  - les balises og:description, twitter:desc (depuis <meta name=description>)

    python3 tools/sync-html-fallbacks.py          # applique
    python3 tools/sync-html-fallbacks.py --check  # signale sans écrire

Les clés dont la valeur contient une accolade ({year}, {count}) sont laissées
telles quelles : leur version HTML est volontairement différente.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATTRS = {"content": "content", "alt": "alt", "aria-label": "aria-label", "href": "href"}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def close_at(html, start, tag):
    """Position du </tag> qui ferme l'élément ouvert avant `start`."""
    depth = 1
    pos = start
    pattern = re.compile(r"</?%s\b" % re.escape(tag), re.I)
    while depth:
        m = pattern.search(html, pos)
        if not m:
            return -1
        depth += -1 if m.group(0)[1] == "/" else 1
        pos = m.end()
    return m.start()


def sync(page, strings, changes):
    path = os.path.join(REPO, page)
    with io.open(path, encoding="utf-8") as fh:
        html = fh.read()
    before = html

    # 1. Contenu des éléments. On repart de la fin pour que les positions
    #    déjà trouvées restent valides malgré les remplacements.
    marks = list(re.finditer(r'<(\w+)\b[^>]*?\bdata-i18n(?:-text)?="([\w.]+)"[^>]*>', html))
    for m in reversed(marks):
        key, tag = m.group(2), m.group(1)
        value = strings.get(key)
        if value is None or "{" in value:
            continue
        end = close_at(html, m.end(), tag)
        if end < 0:
            continue
        current = html[m.end():end]
        if current != value:
            changes.append((page, key, current, value))
            html = html[:m.end()] + value + html[end:]

    # 2. Attributs pilotés par i18n.
    for suffix, attr in ATTRS.items():
        pattern = re.compile(r'(data-i18n-%s="([\w.]+)"\s+%s=")([^"]*)(")'
                             % (re.escape(suffix), re.escape(attr)))

        def swap(m):
            value = strings.get(m.group(2))
            if value is None or "{" in value:
                return m.group(0)
            if esc(value) != m.group(3):
                changes.append((page, m.group(2), m.group(3), esc(value)))
            return m.group(1) + esc(value) + m.group(4)

        html = pattern.sub(swap, html)

    # 3. Aperçus de lien : ils recopient le titre et la description de la page.
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    desc = re.search(r'<meta name="description"[^>]*\scontent="([^"]*)"', html)
    for kind, source in (("title", title), ("description", desc)):
        if not source:
            continue
        text = source.group(1).strip()
        for prop in ('property="og:%s"' % kind, 'name="twitter:%s"' % kind):
            pattern = re.compile(r'(<meta %s content=")([^"]*)(">)' % re.escape(prop))
            found = pattern.search(html)
            if found and found.group(2) != text:
                changes.append((page, prop, found.group(2), text))
            html = pattern.sub(lambda m: m.group(1) + text + m.group(3), html)

    if html != before and "--check" not in sys.argv:
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
    return html != before


if __name__ == "__main__":
    with io.open(os.path.join(REPO, "data", "i18n.json"), encoding="utf-8") as fh:
        strings = json.load(fh)["fr"]

    changes = []
    # Les fiches générées (tournois, pêcheurs, bateaux) portent le même menu
    # que le reste du site : leur texte français doit suivre data/i18n.json
    # comme celui des autres pages.
    pages = sorted(f for f in os.listdir(REPO) if f.endswith(".html"))
    for dirname in ("tournois", "pecheurs", "bateaux"):
        sub = os.path.join(REPO, dirname)
        if os.path.isdir(sub):
            pages += sorted(os.path.join(dirname, f)
                            for f in os.listdir(sub) if f.endswith(".html"))
    touched = [p for p in pages if sync(p, strings, changes)]

    for page, key, old, new in changes:
        print("%-34s %s\n   - %s\n   + %s" % (page, key, old, new))
    verb = "à corriger" if "--check" in sys.argv else "corrigées"
    print("\n%d divergence(s) %s dans %d page(s) sur %d."
          % (len(changes), verb, len(touched), len(pages)))
    sys.exit(1 if changes and "--check" in sys.argv else 0)
