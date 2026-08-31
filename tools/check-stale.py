# -*- coding: utf-8 -*-
"""Dit ce qui demande une vérification dans le répertoire des tournois.

Un guide de tournois vieillit tout seul : les dates d'une saison deviennent
celles de l'an dernier, et les trous qu'on n'a pas comblés restent invisibles
tant qu'on ne les cherche pas. Ce script remplace la relecture des 42 entrées
par une liste courte, pour que chaque séance de recherche parte d'un plan.

    python3 tools/check-stale.py            # rapport complet
    python3 tools/check-stale.py --brief    # juste les totaux

Il ne modifie rien et ne va sur aucun site : il lit data/quebec-tournaments.json
et compare aux dates du jour. Le travail de recherche reste manuel, et c'est
voulu — une date inventée coûte plus cher au répertoire qu'une date manquante.
"""
import datetime
import io
import json
import os
import re
import sys

import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date.today()
SEASON = str(TODAY.year)

# Le barème vient de build-tournament-pages.py plutôt que d'être recopié ici :
# deux copies finissent toujours par diverger, et ce rapport mentirait alors
# sur ce qui manque à une entrée pour mériter sa fiche.
_spec = importlib.util.spec_from_file_location(
    "pages", os.path.join(REPO, "tools", "build-tournament-pages.py"))
pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages)


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def fr(value):
    if isinstance(value, dict):
        return value.get("fr") or value.get("en") or ""
    return value or ""


def score(ev):
    return pages.score(ev)


def missing(ev):
    fields, spec_fields, _ = pages.rubric(ev)
    specs = ev.get("specs") or {}
    gaps = [f for f in fields if not fr(ev.get(f)).strip()]
    gaps += ["specs." + f for f in spec_fields if not fr(specs.get(f)).strip()]
    return gaps


def season_of(ev):
    m = re.match(r"^(\d{4})", ev.get("startDate") or "")
    return m.group(1) if m else None


def bucket(events):
    """Répartit le répertoire en quatre paquets d'action."""
    out = {"passe": [], "sansDate": [], "sousSeuil": [], "aVenir": []}
    for ev in events:
        if ev.get("status") == "cancelled":
            continue
        start = ev.get("startDate") or ""
        if not start:
            out["sansDate"].append(ev)
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", start):
            if datetime.date.fromisoformat(start) < TODAY:
                out["passe"].append(ev)
            else:
                out["aVenir"].append(ev)
        elif start < SEASON:
            out["passe"].append(ev)
        if score(ev) < pages.rubric(ev)[2] and ev.get("kind") not in ("stop", "circuit"):
            out["sousSeuil"].append(ev)
    return out


def show(title, events, why, detail=None):
    if not events:
        return
    print("\n%s  (%d)" % (title, len(events)))
    print("  %s" % why)
    for ev in sorted(events, key=lambda e: (e.get("startDate") or "", fr(e.get("name")))):
        line = "   • %-46s" % fr(ev.get("name"))[:46]
        if ev.get("startDate"):
            line += " %-10s" % ev["startDate"]
        print(line)
        if detail:
            extra = detail(ev)
            if extra:
                print("       %s" % extra)


if __name__ == "__main__":
    events = load("quebec-tournaments.json")
    b = bucket(events)
    active = [e for e in events if e.get("status") != "cancelled"]
    seasons = sorted({s for s in (season_of(e) for e in active) if s})
    next_season = str(TODAY.year + 1)

    print("Répertoire : %d tournois (%d actifs), saisons %s"
          % (len(events), len(active), ", ".join(seasons) or "aucune"))
    print("Aujourd'hui : %s" % TODAY.isoformat())
    if next_season not in seasons:
        print("\n⚠  Aucune date %s au répertoire. Tant que ça dure, le guide n'affiche"
              "\n   que des dates %s — il aura l'air abandonné au printemps. Les"
              "\n   organisateurs publient surtout de novembre à mars."
              % (next_season, seasons[-1] if seasons else "?"))

    if "--brief" in sys.argv:
        print("\npassés %d · sans date %d · sous le seuil %d · à venir %d"
              % (len(b["passe"]), len(b["sansDate"]), len(b["sousSeuil"]), len(b["aVenir"])))
        raise SystemExit(0)

    show("À REPORTER SUR LA SAISON SUIVANTE", b["passe"],
         "Ces éditions sont passées. Cherche la date %s chez l'organisateur." % next_season,
         lambda e: "→ %s" % e["link"] if (e.get("link") or "").startswith("http") else
                   "→ aucun lien : à trouver")

    show("SANS DATE PUBLIÉE", b["sansDate"],
         "Annoncées mais pas datées. À revérifier à chaque passage.",
         lambda e: "→ %s" % e["link"] if (e.get("link") or "").startswith("http") else
                   "→ aucun lien : à trouver")

    show("SOUS LE SEUIL DE FICHE", b["sousSeuil"],
         "Il leur manque peu pour mériter leur page. Les circuits en ont une d'office.",
         lambda e: "%d/%d — manque : %s"
                   % (score(e), pages.score_max(e), ", ".join(missing(e))))

    show("ENCORE À VENIR", b["aVenir"],
         "Rien à faire : ces dates tiennent toujours.")

    print("\n%d à reporter · %d sans date · %d sous le seuil · %d à venir"
          % (len(b["passe"]), len(b["sansDate"]), len(b["sousSeuil"]), len(b["aVenir"])))
