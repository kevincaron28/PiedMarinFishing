#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ajoute les nouvelles vidéos de la chaîne dans data/videos.json.

POURQUOI UN SCRIPT ET PAS UN FLUX DANS LE NAVIGATEUR
----------------------------------------------------
YouTube publie un flux Atom public et sans jeton pour chaque chaîne :

    https://www.youtube.com/feeds/videos.xml?channel_id=UC...

Mais il ne porte aucun en-tête CORS : une page ne peut pas le lire elle-même.
Le contourner par un relais tiers reviendrait à faire passer nos visiteurs
par un service qu'on ne contrôle pas, pour un fichier qui change une fois par
mois. On le lit donc ici — dans une action GitHub programmée — et on écrit le
résultat dans le dépôt. Le site, lui, continue de lire un fichier local,
comme il lit data/catches.json. Aucun script tiers, aucun témoin, aucun
bandeau de consentement : la position de assets/js/analytics.js tient.

CE QUE LE SCRIPT NE FAIT JAMAIS
-------------------------------
Il n'écrase AUCUNE entrée existante. Les titres bilingues, `orientation`,
`angler`, `catch` et `featured` sont écrits à la main et valent mieux que ce
que le flux sait dire — le flux ne donne qu'un titre, dans une seule langue.
Une vidéo déjà connue est laissée exactement telle quelle.

USAGE
-----
    python3 tools/fetch-youtube.py                 # va chercher le flux
    python3 tools/fetch-youtube.py --dry-run       # dit ce qu'il ferait
    python3 tools/fetch-youtube.py --from-file f   # lit un flux déjà enregistré

Le code de sortie est 0 quand il n'y a rien à faire (pas d'identifiant de
chaîne, aucune nouveauté) : dans une action programmée, « rien de neuf » est
le cas normal, pas une panne. Il n'est non nul que sur une vraie erreur.
"""

import argparse
import io
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEOS = os.path.join(REPO, "data", "videos.json")
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=%s"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# Un identifiant de chaîne YouTube : « UC » suivi de 22 caractères.
CHANNEL_RX = re.compile(r"^UC[A-Za-z0-9_-]{22}$")
# Un identifiant de vidéo en fait exactement 11. assets/js/video.js impose la
# même longueur et, sur un identifiant tordu, retombe sans bruit sur le bloc
# « bientôt » de l'accueil — une vidéo qui n'existe pas prendrait la place de
# la vraie. Ce qui n'a pas la bonne forme n'entre pas dans le fichier.
VIDEO_RX = re.compile(r"^[A-Za-z0-9_-]{11}$")

WHERE_TO_FIND = """\
Aucun identifiant de chaîne dans data/videos.json (champ « channelId »).

Pour le trouver : ouvre https://www.youtube.com/@piedmarinfishing, clic droit
« Afficher le code source », cherche « channelId ». C'est la chaîne qui
commence par UC et fait 24 caractères. Colle-la dans data/videos.json :

    "channelId": "UC..."

Sans elle, ce script ne fait rien — et c'est voulu : il vaut mieux ne rien
ajouter que deviner une chaîne."""


def load():
    with io.open(VIDEOS, encoding="utf-8") as fh:
        return json.load(fh)


def save(data):
    with io.open(VIDEOS, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def slug(text, taken):
    """Un identifiant lisible tiré du titre, sans accent ni doublon."""
    flat = unicodedata.normalize("NFKD", text or "")
    flat = "".join(c for c in flat if not unicodedata.combining(c))
    flat = re.sub(r"[^a-zA-Z0-9]+", "-", flat).strip("-").lower()
    # Cinq mots suffisent à reconnaitre une video; au-dela c'est du bruit.
    flat = "-".join(flat.split("-")[:5]) or "video"
    base, n = flat, 2
    while flat in taken:
        flat, n = "%s-%d" % (base, n), n + 1
    return flat


def entries(xml_text):
    """Les vidéos du flux, de la plus récente à la plus ancienne."""
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("atom:entry", NS):
        vid = e.findtext("yt:videoId", "", NS).strip()
        if not VIDEO_RX.match(vid):
            continue
        title = (e.findtext("atom:title", "", NS) or "").strip()
        group = e.find("media:group", NS)
        if not title and group is not None:
            title = (group.findtext("media:title", "", NS) or "").strip()
        published = (e.findtext("atom:published", "", NS) or "").strip()
        out.append({"videoId": vid, "title": title, "date": published[:10]})
    return out


def fetch(channel_id):
    import urllib.request
    req = urllib.request.Request(
        FEED % channel_id,
        # Sans en-tête d'agent, YouTube répond parfois une page d'erreur.
        headers={"User-Agent": "PiedMarinFishing/1.0 (+https://piedmarinfishing.com)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def precise_dates(videos, by_id):
    """Complete une date d'annee seule avec la date exacte du flux.

    Seule exception a la regle « on ne touche pas a l'existant », et elle ne
    porte pas sur de l'editorial : la date de publication appartient a
    YouTube, pas a nous. Les deux premieres videos portaient « 2025 » tout
    court; a egalite de date, l'accueil ne pouvait pas savoir laquelle etait
    la derniere. Une date deja precise au jour n'est jamais retouchee.
    """
    fixed = []
    for v in videos:
        cur = (v.get("date") or "").strip()
        if len(cur) >= 10:                     # deja AAAA-MM-JJ
            continue
        e = by_id.get((v.get("videoId") or "").strip())
        if not e or not e["date"]:
            continue
        if cur and not e["date"].startswith(cur):
            # Le flux contredit l'annee ecrite a la main : on ne trancherait
            # pas a sa place, on le signale.
            fixed.append((v, cur, e["date"], True))
            continue
        v["date"] = e["date"]
        fixed.append((v, cur, e["date"], False))
    return fixed


def merge(data, found):
    """Ajoute ce qui manque. Ne touche a rien de ce qui existe."""
    videos = data.setdefault("videos", [])
    known = {(v.get("videoId") or "").strip() for v in videos}
    taken = {(v.get("id") or "").strip() for v in videos}
    added = []
    # Le flux arrive de la plus recente a la plus ancienne, mais on ne s'y fie
    # pas : on trie nous-memes pour que la liste garde son ordre chronologique
    # meme si YouTube change d'idee. Les dates vides passent en premier.
    for e in sorted(found, key=lambda x: x["date"]):
        if e["videoId"] in known:
            continue
        item = {
            "id": slug(e["title"], taken),
            "videoId": e["videoId"],
            # Le flux ne dit pas si une video est verticale, et une verticale
            # rendue en 16:9 se retrouve cernee de noir. « #shorts » dans le
            # titre est la seule indication fiable : c'est l'auteur qui l'a
            # ecrite, pas une deduction. Sans elle, le champ reste vide et le
            # rapport le signale.
            "orientation": "portrait" if "#short" in e["title"].lower() else "",
            # Une seule langue : le titre tel qu'il est sur YouTube. tr()
            # retombe sur le francais tant que l'anglais n'est pas ecrit.
            "title": {"fr": e["title"], "en": ""},
            "date": e["date"],
            "featured": False,
            # Mis a false par le robot, a true par un humain qui a relu le
            # titre anglais et l'orientation.
            "reviewed": False,
        }
        taken.add(item["id"])
        known.add(item["videoId"])
        videos.append(item)
        added.append(item)
    return added


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-file", help="lire un flux enregistré au lieu de l'aller chercher")
    ap.add_argument("--dry-run", action="store_true", help="ne rien écrire")
    args = ap.parse_args()

    data = load()
    channel_id = (data.get("channelId") or "").strip()

    if args.from_file:
        with io.open(args.from_file, encoding="utf-8") as fh:
            xml_text = fh.read()
    else:
        if not channel_id:
            print(WHERE_TO_FIND)
            return 0
        if not CHANNEL_RX.match(channel_id):
            print("channelId « %s » n'a pas la forme d'un identifiant YouTube "
                  "(UC + 22 caractères)." % channel_id, file=sys.stderr)
            return 1
        try:
            xml_text = fetch(channel_id)
        except Exception as exc:                      # réseau, 404, coupure
            print("Flux injoignable : %s" % exc, file=sys.stderr)
            return 1

    try:
        found = entries(xml_text)
    except ET.ParseError as exc:
        print("Flux illisible : %s" % exc, file=sys.stderr)
        return 1

    if not found:
        print("Le flux ne contient aucune vidéo.", file=sys.stderr)
        return 1

    dated = precise_dates(data.get("videos", []), {e["videoId"]: e for e in found})
    added = merge(data, found)
    print("%d vidéo(s) au flux, %d déjà connue(s), %d ajoutée(s)."
          % (len(found), len(found) - len(added), len(added)))

    for v, before, after, clash in dated:
        if clash:
            print("  ! %-13s date écrite à la main « %s », le flux dit « %s » — "
                  "laissée telle quelle, à trancher à la main"
                  % (v["videoId"], before, after), file=sys.stderr)
        else:
            print("  ~ %-13s date précisée : « %s » → « %s »"
                  % (v["videoId"], before or "(vide)", after))

    if not added and not any(not c for _, _, _, c in dated):
        return 0

    for v in added:
        print("  + %-13s %s  %s" % (v["videoId"], v["date"], v["title"]["fr"]))
    if added:
        print("\nÀ relire à la main sur chaque nouvelle entrée :\n"
              "  · title.en — le titre anglais (sinon le français s'affiche dans les deux langues)\n"
              "  · orientation — « portrait » pour un Short, sinon laisser vide\n"
              "  · angler / catch — pour que la vidéo apparaisse sur la fiche du pêcheur ou de la prise\n"
              "  · reviewed — passe-le à true quand c'est fait")

    if args.dry_run:
        print("\n--dry-run : rien n'a été écrit.")
        return 0

    save(data)
    print("\ndata/videos.json mis à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
