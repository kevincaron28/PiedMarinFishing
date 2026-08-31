# -*- coding: utf-8 -*-
"""Écrit data/site-stats.json — les quelques chiffres affichés sur l'accueil.

Le répertoire pèse 74 Ko. Charger tout ça sur la page d'accueil pour afficher
« 45 tournois » serait absurde : ce fichier-ci fait quelques octets et dit la
même chose. Il est régénéré avec le reste, donc il ne peut pas mentir longtemps.

    python3 tools/build-stats.py

Les autres chiffres de l'accueil (saisons, records) se calculent dans le
navigateur à partir de fichiers qu'il charge déjà.
"""
import datetime
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    events = load("quebec-tournaments.json")
    # Un tournoi annulé ne compte pas : il est au répertoire pour prévenir,
    # pas pour gonfler un chiffre.
    active = [e for e in events if e.get("status") != "cancelled"]
    stats = {
        "generated": datetime.date.today().isoformat(),
        "tournaments": len(active),
        "shows": len([e for e in active if e.get("kind") == "show"]),
        "pages": len(load("tournament-pages.json")),
    }
    path = os.path.join(REPO, "data", "site-stats.json")
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(stats, ensure_ascii=False, indent=2) + "\n")
    print("site-stats.json : %s" % json.dumps(stats, ensure_ascii=False))
