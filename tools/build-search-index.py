#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Écrit data/search-index.json — l'index de la recherche du site.

POURQUOI UN FICHIER ET PAS UNE RECHERCHE DANS LES PAGES
-------------------------------------------------------
Il y avait déjà deux recherches : une sur l'index des espèces, une sur le
guide des tournois. Chacune ne voyait que sa propre liste, et les 104 pages
générées n'étaient trouvables par aucune des deux. Quelqu'un qui cherche
« Destroyer » depuis une fiche d'espèce ne trouvait rien.

Un site statique n'a pas de serveur pour chercher. L'index est donc construit
ici, à partir des mêmes fichiers que les générateurs, et le navigateur le
charge **au premier usage seulement** — pas au chargement des pages.

CE QU'IL NE CONTIENT PAS
------------------------
Ni le corps des textes, ni les récits, ni la réglementation. On cherche des
PAGES, pas des phrases : un index de plein texte pèserait dix fois plus pour
répondre à une question que personne ne pose sur un site de 116 pages. Et
surtout, rien de ce que `tools/check-private.py` refuse — l'index passe par
le même contrôle que le reste du dépôt, puisqu'il vit dans `data/`.

Champs, volontairement courts : le fichier est téléchargé par les visiteurs.
    u  l'adresse         f  le nom français      e  le nom anglais
    g  le groupe (especes | tournois | prises | equipe | site)
    k  les mots-clés supplémentaires, une seule chaîne, déjà en minuscules
"""

import io
import json
import os
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "search-index.json")


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def pick(value, lang):
    if isinstance(value, dict):
        return (value.get(lang) or value.get("fr") or value.get("en") or "").strip()
    return (value or "").strip()


def fold(text):
    flat = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in flat if not unicodedata.combining(c)).lower()


def entry(url, fr, en, group, extra=()):
    keys = " ".join(fold(x) for x in extra if x)
    row = {"u": url, "f": fr, "g": group}
    if en and en != fr:
        row["e"] = en
    if keys:
        row["k"] = keys
    return row


def build():
    rows = []

    # --- les pages écrites à la main -------------------------------------
    # Leur nom vient du menu : si un onglet est renommé, la recherche suit.
    i18n = load("i18n.json")
    fr, en = i18n["fr"], i18n["en"]
    for url, key in [("index.html", "nav.home"), ("team.html", "nav.team"),
                     ("catches.html", "nav.catches"), ("history.html", "nav.history"),
                     ("calendar.html", "nav.calendar"), ("tournaments.html", "nav.guide"),
                     ("especes.html", "nav.species"), ("saison.html", "nav.season"),
                     ("sponsors.html", "nav.sponsors"), ("histoire.html", "nav.story"),
                     ("sorties.html", "nav.trips"), ("social.html", "nav.social")]:
        rows.append(entry(url, fr[key], en.get(key, ""), "site"))

    # --- espèces ----------------------------------------------------------
    kept = set(load("species-pages.json"))
    for sp in load("species.json"):
        if sp["id"] not in kept:
            continue
        name = sp.get("name")
        rows.append(entry("especes/%s.html" % sp["id"], pick(name, "fr"), pick(name, "en"),
                          "especes",
                          [sp.get("scientificName"), sp["id"], pick(sp.get("group"), "fr")]))

    # --- tournois ---------------------------------------------------------
    kept = set(load("tournament-pages.json"))
    for ev in load("quebec-tournaments.json"):
        if ev["id"] not in kept:
            continue
        name = ev.get("name")
        rows.append(entry("tournois/%s.html" % ev["id"], pick(name, "fr"), pick(name, "en"),
                          "tournois",
                          [pick(ev.get("region"), "fr"), pick(ev.get("region"), "en"),
                           pick(ev.get("water"), "fr"), pick(ev.get("species"), "fr"),
                           pick(ev.get("species"), "en"), pick(ev.get("organizer"), "fr"),
                           (ev.get("startDate") or "")[:4]]))

    # --- prises -----------------------------------------------------------
    kept = set(load("catch-pages.json"))
    members = {m["id"]: m for m in load("team-members.json")}
    for c in load("catches.json"):
        if c["id"] not in kept:
            continue
        who = members.get(c.get("angler"), {}).get("name") or ""
        rows.append(entry("prises/%s.html" % c["id"], pick(c.get("species"), "fr"),
                          pick(c.get("species"), "en"), "prises",
                          [pick(who, "fr"), pick(c.get("water"), "fr"),
                           pick(c.get("measure"), "fr"), (c.get("date") or "")[:4]]))

    # --- les sorties ------------------------------------------------------
    # Elles n'ont pas de page a elles : l'ancre mene au bon endroit du journal.
    for t in load("trips.json"):
        rows.append(entry("sorties.html#t-%s" % t["id"], pick(t.get("title"), "fr"),
                          pick(t.get("title"), "en"), "sorties",
                          [pick(t.get("water"), "fr"), pick(t.get("water"), "en"),
                           t.get("date", ""), (t.get("date") or "")[:4]]))

    # --- l'équipe ---------------------------------------------------------
    for m in load("team-members.json"):
        rows.append(entry("pecheurs/%s.html" % m["id"], pick(m.get("name"), "fr"),
                          pick(m.get("name"), "en"), "equipe",
                          [pick(m.get("role"), "fr"), pick(m.get("role"), "en")]))
    for b in load("boats.json"):
        rows.append(entry("bateaux/%s.html" % b["id"], pick(b.get("name"), "fr"),
                          pick(b.get("name"), "en"), "equipe",
                          [pick(b.get("model"), "fr"), str(b.get("year") or "")]))

    return rows


if __name__ == "__main__":
    rows = build()
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + "\n")
    by = {}
    for r in rows:
        by[r["g"]] = by.get(r["g"], 0) + 1
    size = os.path.getsize(OUT)
    print("data/search-index.json — %d pages, %.1f Ko" % (len(rows), size / 1024.0))
    for g in sorted(by):
        print("  %-10s %d" % (g, by[g]))
