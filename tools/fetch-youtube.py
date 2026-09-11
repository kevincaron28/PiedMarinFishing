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

# La page d'une chaîne porte son identifiant à plusieurs endroits. Le lien
# canonique est le plus stable des quatre — c'est le seul qui soit du HTML et
# non du JavaScript embarqué — alors on l'essaie en premier.
ID_PATTERNS = [
    re.compile(r'<link[^>]+rel="canonical"[^>]+href="https://www\.youtube\.com/channel/(UC[\w-]{22})"'),
    re.compile(r'"externalId"\s*:\s*"(UC[\w-]{22})"'),
    re.compile(r'<meta[^>]+itemprop="identifier"[^>]+content="(UC[\w-]{22})"'),
    re.compile(r'"channelId"\s*:\s*"(UC[\w-]{22})"'),
]

WHERE_TO_FIND = """\
Aucun identifiant de chaîne, et aucune adresse de chaîne pour le trouver.

Remplis l'un des deux dans data/videos.json :

    "channelUrl": "https://youtube.com/@piedmarinfishing"   (le script en déduit l'identifiant)
    "channelId":  "UC..."                                    (si tu l'as déjà)

Sans l'un des deux, ce script ne fait rien — et c'est voulu : il vaut mieux ne
rien ajouter que deviner une chaîne."""


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


def get(url):
    """Lit une page. Sans en-tete d'agent, YouTube repond parfois une erreur."""
    import urllib.request
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PiedMarinFishing/1.0 (+https://piedmarinfishing.com)",
                 "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, "replace")


def channel_id_in(html):
    """L'identifiant UC... trouve dans la page d'une chaine, sinon ''."""
    for rx in ID_PATTERNS:
        m = rx.search(html)
        if m and CHANNEL_RX.match(m.group(1)):
            return m.group(1)
    return ""


def resolve_channel_id(channel_url):
    """Deduit l'identifiant a partir de l'adresse @handle de la chaine.

    Le flux Atom veut un « UC... » et rien d'autre : ni le @handle, ni
    l'adresse. Le trouver a la main demande de lire le code source d'une page,
    ce qui n'est pas faisable sur un telephone. L'action, elle, a le reseau :
    elle le fait une fois et l'ecrit dans data/videos.json. Les fois suivantes
    le champ est deja rempli et cette fonction n'est plus appelee.
    """
    return channel_id_in(get(channel_url))


def fetch(channel_id):
    return get(FEED % channel_id)


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
    channel_url = (data.get("channelUrl") or "").strip()
    resolved = False

    if args.from_file:
        with io.open(args.from_file, encoding="utf-8") as fh:
            xml_text = fh.read()
    else:
        if not channel_id:
            if not channel_url:
                print(WHERE_TO_FIND)
                return 0
            print("Aucun channelId — on le cherche sur %s" % channel_url)
            try:
                channel_id = resolve_channel_id(channel_url)
            except Exception as exc:
                print("Page de la chaîne injoignable : %s" % exc, file=sys.stderr)
                return 1
            if not channel_id:
                print("L'identifiant n'est pas dans la page de %s.\n"
                      "YouTube a peut-être changé sa mise en page. Mets-le à la "
                      "main dans data/videos.json :\n    \"channelId\": \"UC...\""
                      % channel_url, file=sys.stderr)
                return 1
            print("Trouvé : %s — il sera écrit dans data/videos.json." % channel_id)
            data["channelId"] = channel_id
            resolved = True

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

    changed = bool(added) or any(not c for _, _, _, c in dated) or resolved
    if not changed:
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
