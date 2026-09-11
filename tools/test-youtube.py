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

print("\n--- `date` et `published` ne sont pas la meme chose ---")
# Le flux dit que PXwFXozk-5c a ete mise en ligne le 2025-11-02. Notre fiche
# dit « 2025 » : l'annee de la SORTIE. Les deux doivent survivre cote a cote.
data = fresh()
by_id = {e["videoId"]: e for e in found}
filled = yt.fill_published(data["videos"], by_id)
check("`date` écrite à la main intacte", data["videos"][0]["date"] == "2025",
      data["videos"][0]["date"])
check("`published` écrit par le robot", data["videos"][0]["published"] == "2025-11-02",
      data["videos"][0].get("published"))
check("un seul champ rempli", len(filled) == 1, len(filled))
check("rien d'autre n'a bougé", data["videos"][0]["title"] == CURATED["title"])

data = fresh()
data["videos"][0]["published"] = "2026-08-26"       # deja connu
yt.fill_published(data["videos"], by_id)
check("un `published` déjà écrit n'est jamais retouché",
      data["videos"][0]["published"] == "2026-08-26", data["videos"][0]["published"])

data = fresh()
yt.fill_published(data["videos"], by_id)
again = yt.fill_published(data["videos"], by_id)
check("deuxième passage : plus rien à remplir", len(again) == 0, len(again))

data = fresh()
data["videos"][0]["videoId"] = "inconnu1234"        # absente du flux
check("une vidéo absente du flux reste sans `published`",
      len(yt.fill_published(data["videos"], by_id)) == 0)

print("\n--- une nouveaute n'invente pas la date de sortie ---")
data = fresh()
added = yt.merge(data, found)
neuf = [a for a in added if a["videoId"] == "Kq9PmZn3XyT"][0]
check("`date` laissée vide", neuf["date"] == "", neuf["date"])
check("`published` = la date du flux", neuf["published"] == "2026-05-16", neuf["published"])

print("\n--- les mots-cles de fin de titre sont coupes ---")
cases = [
    ("Maskinongé dans l'épuisette 🎣 Remise à l'eau #musky #pêchequébec #muskyfishing",
     "Maskinongé dans l'épuisette 🎣 Remise à l'eau"),
    ("Un brochet qui saute #shorts", "Un brochet qui saute"),
    ("Sortie du 1er mai", "Sortie du 1er mai"),
    ("Doré #1 de la saison", "Doré #1 de la saison"),      # au milieu : on garde
    ("#shorts", "#shorts"),                                 # rien d'autre : on garde
]
for brut, attendu in cases:
    got = yt.clean_title(brut)
    check("« %s » → « %s »" % (brut[:34], attendu[:34]), got == attendu, got)

data = fresh()
added = yt.merge(data, [{"videoId": "aBcDeFgHiJk", "date": "2026-09-07",
                         "title": "Remise à l'eau #musky #shorts"}])
check("le titre stocké est nettoyé", added[0]["title"]["fr"] == "Remise à l'eau", added[0]["title"]["fr"])
check("mais « #shorts » a quand même donné portrait",
      added[0]["orientation"] == "portrait", added[0]["orientation"])
check("l'identifiant vient du titre nettoyé", added[0]["id"] == "remise-a-l-eau", added[0]["id"])

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

print("\n--- l'identifiant se déduit de la page de la chaîne ---")
REAL = "UCaBcDeFgHiJkLmNoPqRsTuV"
shapes = {
    "lien canonique": '<link rel="canonical" href="https://www.youtube.com/channel/%s">' % REAL,
    "externalId": '{"externalId":"%s","title":"Pied Marin Fishing"}' % REAL,
    "meta itemprop": '<meta itemprop="identifier" content="%s">' % REAL,
    "channelId dans le JS": 'var x = {"channelId": "%s"};' % REAL,
}
for nom, html in shapes.items():
    check("trouvé par %s" % nom, yt.channel_id_in("<html>" + html + "</html>") == REAL,
          yt.channel_id_in(html))

check("le lien canonique l'emporte sur un autre identifiant plus haut",
      yt.channel_id_in(
          '"channelId":"UCzzzzzzzzzzzzzzzzzzzzzz"'
          '<link rel="canonical" href="https://www.youtube.com/channel/%s">' % REAL) == REAL)
check("page sans identifiant → chaîne vide", yt.channel_id_in("<html>rien ici</html>") == "")
check("une page d'erreur ne donne rien",
      yt.channel_id_in("<html><title>404 Not Found</title></html>") == "")
check("un identifiant tronqué est refusé",
      yt.channel_id_in('"externalId":"UCtroplcourt"') == "")

print("\n--- la forme de l'identifiant de chaîne est contrôlée ---")
check("UC + 22 accepté", bool(yt.CHANNEL_RX.match("UCaBcDeFgHiJkLmNoPqRsTuV")))
check("un @handle refusé", not yt.CHANNEL_RX.match("@piedmarinfishing"))
check("une URL refusée", not yt.CHANNEL_RX.match("https://youtube.com/@piedmarinfishing"))
check("trop court refusé", not yt.CHANNEL_RX.match("UCabc"))

print("\n%d vérifications passées, %d échec(s)" % (
    51 - len(fails), len(fails)))
sys.exit(1 if fails else 0)
