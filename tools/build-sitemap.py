# -*- coding: utf-8 -*-
"""Régénère sitemap.xml à partir de l'historique git.

La date <lastmod> écrite à la main devient fausse dès le commit suivant, et un
sitemap qui ment sur ses dates est vite ignoré par les moteurs. Ici la date
vient de git : pour chaque page, le dernier commit qui a touché la page ou une
des données qu'elle affiche. Une page modifiée mais pas encore commitée est
datée d'aujourd'hui.

Chaque entrée déclare aussi ses deux langues (hreflang), comme les balises
<link rel="alternate"> des pages elles-mêmes.

    python3 tools/build-sitemap.py

merch.html et 404.html sont volontairement absentes : la première porte
noindex tant que la boutique est vide, la seconde n'a rien à indexer.
"""
import datetime
import io
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://piedmarinfishing.com"

# page -> (priorité, fréquence, données affichées par la page)
# data/i18n.json compte pour toutes : c'est là que vit le texte.
PAGES = [
    ("index.html",       "1.0", "weekly",  ["data/featured-video.json"]),
    ("tournaments.html", "0.9", "weekly",  ["data/quebec-tournaments.json"]),
    ("calendar.html",    "0.8", "weekly",  ["data/team-schedule.json"]),
    ("sponsors.html",    "0.8", "monthly", ["data/sponsors.json"]),
    ("team.html",        "0.7", "monthly", ["data/team-members.json", "data/boats.json",
                                            "data/catches.json", "data/tournament-history.json"]),
    ("catches.html",     "0.7", "monthly", ["data/catches.json", "data/team-members.json",
                                            "data/tournament-history.json"]),
    ("history.html",     "0.6", "monthly", ["data/tournament-history.json",
                                            "data/team-members.json"]),
    ("social.html",      "0.5", "monthly", ["data/socials.json"]),
]
COMMON = ["data/i18n.json"]
# Les fiches de tournoi sont générées : elles suivent le répertoire et le
# script qui les écrit, pas une date saisie à la main.
PAGE_DEPS = ["data/quebec-tournaments.json", "tools/build-tournament-pages.py"]
TODAY = datetime.date.today().isoformat()


def git(*args):
    return subprocess.check_output(("git",) + args, cwd=REPO).decode("utf-8").strip()


def last_change(path):
    """Date du dernier commit touchant le fichier — ou aujourd'hui s'il est modifié."""
    if git("status", "--porcelain", "--", path):
        return TODAY
    return git("log", "-1", "--format=%cs", "--", path) or TODAY


def lastmod(page, deps):
    return max(last_change(p) for p in [page] + deps + COMMON)


def url(page, priority, freq, deps):
    loc = SITE + ("/" if page == "index.html" else "/" + page)
    alt = SITE + "/" + ("" if page == "index.html" else page)
    return "\n".join([
        "  <url>",
        "    <loc>%s</loc>" % loc,
        '    <xhtml:link rel="alternate" hreflang="fr-ca" href="%s"/>' % alt,
        '    <xhtml:link rel="alternate" hreflang="en-ca" href="%s?lang=en"/>' % alt,
        '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % alt,
        "    <lastmod>%s</lastmod>" % lastmod(page, deps),
        "    <changefreq>%s</changefreq>" % freq,
        "    <priority>%s</priority>" % priority,
        "  </url>",
    ])


def tournament_pages():
    """Une entrée par fiche écrite dans tournois/."""
    out = []
    directory = os.path.join(REPO, "tournois")
    if not os.path.isdir(directory):
        return out
    for name in sorted(f for f in os.listdir(directory) if f.endswith(".html")):
        out.append(("tournois/" + name, "0.6", "monthly", PAGE_DEPS))
    return out


if __name__ == "__main__":
    PAGES += tournament_pages()
    body = "\n".join(url(p, prio, freq, deps) for p, prio, freq, deps in PAGES)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
           '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + body + "\n</urlset>\n")
    with io.open(os.path.join(REPO, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)
    for page, _, _, deps in PAGES:
        print("%-18s %s" % (page, lastmod(page, deps)))
