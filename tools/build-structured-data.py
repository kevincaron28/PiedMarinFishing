# -*- coding: utf-8 -*-
"""Écrit les données structurées JSON-LD dans index.html et tournaments.html.

Le guide contient des dizaines de tournois avec dates, lieux et organisateurs :
c'est exactement ce que les moteurs de recherche affichent dans leurs résultats
« événements ». Sans balisage, cette information leur reste invisible.

Le bloc est écrit en dur dans le HTML plutôt qu'injecté par JavaScript : un
robot le lit alors sans exécuter la page. Relance ce script après avoir modifié
data/quebec-tournaments.json.

    python3 tools/build-structured-data.py

Le site fonctionne parfaitement sans avoir relancé le script — les données
structurées seront simplement en retard d'une édition.
"""
import json
import io
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://piedmarinfishing.com"
START = "<!-- structured-data:start -->"
END = "<!-- structured-data:end -->"


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def fr(value):
    """Les champs bilingues acceptent une chaîne simple ou {fr, en}."""
    if isinstance(value, dict):
        return value.get("fr") or value.get("en") or ""
    return value or ""


def team_json():
    """Accueil : l'équipe et le site lui-même, liés par @id.

    Le nœud WebSite dit aux moteurs que piedmarinfishing.com est un site
    bilingue publié par l'équipe — c'est ce qui permet d'associer le nom de
    l'équipe au domaine plutôt qu'à une page isolée."""
    members = load("team-members.json")
    socials = load("socials.json")
    i18n = load("i18n.json")["fr"]
    team = {
        "@type": "SportsTeam",
        "@id": SITE + "/#team",
        "name": "Pied Marin Fishing",
        "sport": "Fishing",
        "url": SITE + "/",
        "logo": SITE + "/assets/img/logo.png",
        "image": SITE + "/assets/img/og-card.png",
        "description": i18n.get("index.desc", ""),
        "email": "info@piedmarinfishing.com",
        "areaServed": {"@type": "AdministrativeArea", "name": "Québec, Canada"},
        "member": [{"@type": "Person", "name": fr(m.get("name"))} for m in members],
        "sameAs": [s["url"] for s in socials
                   if s.get("url", "").startswith("http")],
    }
    site = {
        "@type": "WebSite",
        "@id": SITE + "/#website",
        "url": SITE + "/",
        "name": "Pied Marin Fishing",
        "description": i18n.get("index.desc", ""),
        "inLanguage": ["fr-CA", "en-CA"],
        "publisher": {"@id": team["@id"]},
    }
    return {"@context": "https://schema.org", "@graph": [site, team]}


def event_json(ev):
    """Un événement n'est publiable que s'il porte une date de début."""
    start = ev.get("startDate") or ""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", start):
        return None

    place_name = fr(ev.get("location")) or fr(ev.get("region")) or "Québec"
    node = {
        # Schema.org a un sous-type pour les salons : plus juste qu'« Event »,
        # et les moteurs le comprennent aussi bien.
        "@type": "ExhibitionEvent" if ev.get("kind") == "show" else "Event",
        "name": fr(ev.get("name")),
        "startDate": start,
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": ("https://schema.org/EventCancelled"
                        if ev.get("status") == "cancelled"
                        else "https://schema.org/EventScheduled"),
        "location": {
            "@type": "Place",
            "name": place_name,
            "address": {
                "@type": "PostalAddress",
                "addressLocality": place_name,
                "addressRegion": fr(ev.get("region")) or "Québec",
                "addressCountry": "CA",
            },
        },
    }
    end = ev.get("endDate") or ""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", end) and end != start:
        node["endDate"] = end
    if fr(ev.get("notes")):
        node["description"] = fr(ev["notes"])
    if fr(ev.get("organizer")):
        node["organizer"] = {"@type": "Organization", "name": fr(ev["organizer"])}
    if ev.get("link", "").startswith("http"):
        node["url"] = ev["link"]
    return node


def guide_json():
    """Le guide : la liste des tournois, rattachée au même site."""
    events = [e for e in (event_json(x) for x in load("quebec-tournaments.json")) if e]
    events.sort(key=lambda e: e["startDate"])
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Tournois de pêche au Québec",
        "url": SITE + "/tournaments.html",
        "isPartOf": {"@id": SITE + "/#website"},
        "numberOfItems": len(events),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": e}
            for i, e in enumerate(events)
        ],
    }


def write_block(page, payload):
    path = os.path.join(REPO, page)
    with io.open(path, encoding="utf-8") as fh:
        html = fh.read()

    # "</" doit être neutralisé : sinon le navigateur ferme le <script> trop tôt.
    body = json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")
    block = (START
             + '\n<script type="application/ld+json">\n' + body + "\n</script>\n"
             + END)

    if START in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), block, html, flags=re.S)
    else:
        html = html.replace("</head>", block + "\n</head>", 1)

    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return len(body)


if __name__ == "__main__":
    n = write_block("index.html", team_json())
    print("index.html        WebSite + SportsTeam  %5d octets" % n)
    guide = guide_json()
    n = write_block("tournaments.html", guide)
    print("tournaments.html  ItemList de %2d Event  %5d octets"
          % (guide["numberOfItems"], n))
