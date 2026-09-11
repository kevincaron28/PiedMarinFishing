#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles du lecteur de flux YouTube — sans réseau.

Le flux n'est pas joignable depuis tous les environnements, et de toute façon
ce n'est pas lui qu'on veut vérifier : c'est la promesse que le robot ne
détruit pas le travail fait à la main. Chaque contrôle part d'un flux écrit
ici et d'une liste de vidéos en mémoire.
"""

import importlib.util
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("yt", os.path.join(HERE, "fetch-youtube.py"))
yt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(yt)

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
 <yt:channelId>UCaBcDeFgHiJkLmNoPqRsTuV</yt:channelId>
 <title>Pied Marin Fishing</title>
 <entry>
  <id>yt:video:Kq9PmZn3XyT</id><yt:videoId>Kq9PmZn3XyT</yt:videoId>
  <title>Ouverture du doré 2026 — première sortie de l'année</title>
  <published>2026-05-16T22:03:11+00:00</published>
  <media:group><media:title>Ouverture du doré 2026 — première sortie de l'année</media:title></media:group>
 </entry>
 <entry>
  <id>yt:video:PXwFXozk-5c</id><yt:videoId>PXwFXozk-5c</yt:videoId>
  <title>Un titre tout neuf que YouTube renvoie maintenant</title>
  <published>2025-11-02T18:22:40+00:00</published>
  <media:group><media:title>Un titre tout neuf</media:title></media:group>
 </entry>
 <entry>
  <id>yt:video:zzTopShrt9A</id><yt:videoId>zzTopShrt9A</yt:videoId>
  <title>Un brochet qui saute juste à côté du bateau #Shorts</title>
  <published>2026-07-04T11:00:00+00:00</published>
  <media:group><media:title>Un brochet qui saute</media:title></media:group>
 </entry>
</feed>"""

# Une entrée écrite à la main, avec tout ce que le flux ne sait pas dire.
CURATED = {
    "id": "fin-saison-2025-musky",
    "videoId": "PXwFXozk-5c",
    "orientation": "portrait",
    "title": {"fr": "Fin de saison 2025 en force", "en": "Closing out 2025 in style"},
    "angler": "kevin-b",
    "date": "2025",
    "featured": True,
    "catch": "maskinonge-kevin-b",
}

fails = []


def check(label, ok, detail=""):
    print("  %s %s%s" % ("✅" if ok else "❌", label, "" if ok else "  — " + str(detail)))
    if not ok:
        fails.append(label)


def fresh():
    return {"channelUrl": "https://youtube.com/@piedmarinfishing",
            "channelId": "UCaBcDeFgHiJkLmNoPqRsTuV",
            "videos": [json.loads(json.dumps(CURATED))]}


print("--- le flux se lit ---")
found = yt.entries(FEED)
check("trois entrées lues", len(found) == 3, len(found))
check("identifiants de vidéo extraits",
      [f["videoId"] for f in found] == ["Kq9PmZn3XyT", "PXwFXozk-5c", "zzTopShrt9A"])
check("date réduite au jour", found[0]["date"] == "2026-05-16", found[0]["date"])

print("\n--- ce qui est écrit à la main n'est JAMAIS touché ---")
data = fresh()
yt.merge(data, found)
kept = [v for v in data["videos"] if v["videoId"] == "PXwFXozk-5c"]
check("l'entrée existante reste unique", len(kept) == 1, len(kept))
check("le titre bilingue survit au titre du flux", kept[0]["title"] == CURATED["title"], kept[0]["title"])
check("orientation conservée", kept[0]["orientation"] == "portrait")
check("angler conservé", kept[0].get("angler") == "kevin-b")
check("catch conservé", kept[0].get("catch") == "maskinonge-kevin-b")
check("featured conservé", kept[0].get("featured") is True)
check("date à la main conservée", kept[0]["date"] == "2025", kept[0]["date"])

print("\n--- ce qui est neuf arrive complet ---")
data = fresh()
added = yt.merge(data, found)
check("deux nouveautés", len(added) == 2, [a["videoId"] for a in added])
check("ordre chronologique croissant",
      [a["date"] for a in added] == sorted(a["date"] for a in added))
short = [a for a in added if a["videoId"] == "zzTopShrt9A"][0]
check("« #Shorts » donne orientation=portrait", short["orientation"] == "portrait", short["orientation"])
regular = [a for a in added if a["videoId"] == "Kq9PmZn3XyT"][0]
check("sans marqueur, orientation reste vide", regular["orientation"] == "")
check("anglais laissé vide, pas inventé", regular["title"]["en"] == "")
check("français = le titre YouTube",
      regular["title"]["fr"] == "Ouverture du doré 2026 — première sortie de l'année")
check("marquée à relire", regular["reviewed"] is False)
check("identifiant sans accent ni espace",
      regular["id"] == "ouverture-du-dore-2026-premiere", regular["id"])

print("\n--- une date d'année seule se précise, une date au jour non ---")
data = fresh()
by_id = {e["videoId"]: e for e in found}
fixed = yt.precise_dates(data["videos"], by_id)
check("« 2025 » devient « 2025-11-02 »", data["videos"][0]["date"] == "2025-11-02",
      data["videos"][0]["date"])
check("un seul champ signalé", len(fixed) == 1, len(fixed))
check("rien d'autre n'a bougé", data["videos"][0]["title"] == CURATED["title"])

data = fresh()
data["videos"][0]["date"] = "2025-01-09"          # déjà précise, et fausse
yt.precise_dates(data["videos"], by_id)
check("une date au jour n'est jamais retouchée", data["videos"][0]["date"] == "2025-01-09",
      data["videos"][0]["date"])

data = fresh()
data["videos"][0]["date"] = "2019"                 # l'année contredit le flux
clash = yt.precise_dates(data["videos"], by_id)
check("une année qui contredit le flux est laissée telle quelle",
      data["videos"][0]["date"] == "2019", data["videos"][0]["date"])
check("et le conflit est signalé", clash and clash[0][3] is True)

data = fresh()
yt.precise_dates(data["videos"], by_id)
again = yt.precise_dates(data["videos"], by_id)
check("deuxième passage : plus rien à préciser", len(again) == 0, len(again))

print("\n--- deux passages de suite n'ajoutent rien la seconde fois ---")
data = fresh()
yt.merge(data, found)
n1 = len(data["videos"])
again = yt.merge(data, found)
check("second passage : 0 ajout", len(again) == 0, len(again))
check("la liste n'a pas bougé", len(data["videos"]) == n1)

print("\n--- les collisions d'identifiant se règlent ---")
data = fresh()
data["videos"].append({"id": "ouverture-du-dore-2026-premiere", "videoId": "aaaaaaaaaaa",
                       "title": {"fr": "x", "en": "x"}, "date": "2020", "featured": False})
added = yt.merge(data, found)
ids = [v["id"] for v in data["videos"]]
check("aucun identifiant en double", len(ids) == len(set(ids)), ids)

print("\n--- un flux abîmé ne passe pas pour vide ---")
try:
    yt.entries("<feed><entry>")
    check("XML invalide rejeté", False, "aucune exception")
except Exception as exc:
    check("XML invalide rejeté", exc.__class__.__name__ == "ParseError", exc)
check("flux sans entrée = liste vide", yt.entries(
    '<feed xmlns="http://www.w3.org/2005/Atom"><title>x</title></feed>') == [])
check("identifiant de vidéo trop long rejeté", yt.entries(
    '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">'
    '<entry><yt:videoId>DOUZECARACTS</yt:videoId><title>t</title></entry></feed>') == [])
check("entrée sans videoId ignorée", yt.entries(
    '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">'
    '<entry><title>t</title></entry></feed>') == [])

print("\n--- la forme de l'identifiant de chaîne est contrôlée ---")
check("UC + 22 accepté", bool(yt.CHANNEL_RX.match("UCaBcDeFgHiJkLmNoPqRsTuV")))
check("un @handle refusé", not yt.CHANNEL_RX.match("@piedmarinfishing"))
check("une URL refusée", not yt.CHANNEL_RX.match("https://youtube.com/@piedmarinfishing"))
check("trop court refusé", not yt.CHANNEL_RX.match("UCabc"))

print("\n%d vérifications passées, %d échec(s)" % (
    34 - len(fails), len(fails)))
sys.exit(1 if fails else 0)
