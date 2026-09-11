# -*- coding: utf-8 -*-
"""Écrit une page par espèce ciblée : « Les tournois de doré au Québec ».

POURQUOI CES PAGES EXISTENT

Le guide répond à « quels tournois y a-t-il au Québec ». Les 41 fiches
répondent à « c'est quoi le Big Bass Challenge ». Entre les deux, personne ne
répondait à la question que les gens tapent vraiment :

    « tournoi pêche doré Québec 2027 »
    « tournoi achigan Montérégie »

Une page par espèce répond à celle-là, et elle ne coûte rien en contenu neuf :
c'est une vue sur des données qu'on tient déjà. Elle rassemble les tournois de
l'espèce, dit où et quand ils se tiennent, et renvoie vers la fiche de l'espèce
et vers la page qui dit si la saison est ouverte.

SEUIL — MIN_EVENTS

Une page « Les tournois de maskinongé au Québec » qui en liste UN n'est pas une
page, c'est une ligne. Le seuil est à quatre. Sur les données actuelles ça
donne quatre pages : achigan (22), doré (10), brochet (9), perchaude (4). La
truite (2), la carpe (1) et le maskinongé (1) restent dans le guide, où ils
sont très bien.

L'ESPÈCE EST DU TEXTE LIBRE, PAS UN IDENTIFIANT

data/quebec-tournaments.json écrit « Achigan », « Achigan, doré, brochet,
perchaude », « Brochet et perchaude ». On cherche donc le mot dans la chaîne,
sans accents ni casse — un tournoi multi-espèces compte pour chacune de celles
qu'il nomme, ce qui est exactement ce qu'un lecteur attend.

    python3 tools/build-species-hubs.py
    python3 tools/build-sitemap.py     # après
"""
import datetime
import io
import os
import unicodedata
import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "tournois")
SITE = "https://piedmarinfishing.com"
MIN_EVENTS = 4
START = "<!-- species-hubs:start -->"
END = "<!-- species-hubs:end -->"

_spec = importlib.util.spec_from_file_location(
    "pages", os.path.join(REPO, "tools", "build-tournament-pages.py"))
pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages)

esc, pick, bilingual, section = pages.esc, pages.pick, pages.bilingual, pages.section
date_phrase, load = pages.date_phrase, pages.load
NAV, FOOTER = pages.NAV, pages.FOOTER

# Le mot cherché, le nom affiché, et les fiches d'espèce à relier. Une espèce
# du guide peut couvrir plusieurs fiches : « achigan » vise les deux.
HUBS = [
    ("achigan", {"fr": "l'achigan", "en": "bass"},
     ["achigan-petite-bouche", "achigan-grande-bouche"]),
    ("dore", {"fr": "doré", "en": "walleye"}, ["dore-jaune", "dore-noir"]),
    ("brochet", {"fr": "brochet", "en": "pike"}, ["grand-brochet"]),
    ("perchaude", {"fr": "perchaude", "en": "yellow perch"}, ["perchaude"]),
    ("maskinonge", {"fr": "maskinongé", "en": "muskie"}, ["maskinonge"]),
    ("carpe", {"fr": "carpe", "en": "carp"}, ["carpe-commune"]),
    ("truite", {"fr": "truite", "en": "trout"}, ["truite-brune", "truite-arc-en-ciel"]),
]


def fold(text):
    """Sans accents ni casse : « Doré » et « dore » doivent se rencontrer."""
    low = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in low if unicodedata.category(c) != "Mn")


def matches(ev, word):
    return word in fold(pick(ev.get("species"), "fr"))


def is_past(ev, today):
    """La DERNIÈRE seconde que la date pouvait désigner : « 2026 » court
    jusqu'au 31 décembre, « 2026-05 » jusqu'au 31 mai. Une date approximative
    ne doit pas faire passer un tournoi pour fini avant qu'il le soit."""
    value = ev.get("endDate") or ev.get("startDate") or ""
    parts = value.split("-")
    try:
        year = int(parts[0])
    except (ValueError, IndexError):
        return False
    if len(parts) == 1:
        end = datetime.date(year, 12, 31)
    elif len(parts) == 2:
        month = int(parts[1])
        nxt = datetime.date(year + month // 12, month % 12 + 1, 1)
        end = nxt - datetime.timedelta(days=1)
    else:
        end = datetime.date(year, int(parts[1]), int(parts[2]))
    return end < today


def rows_html(events, kept_ids, ui):
    out = []
    for ev in events:
        when = {lang: date_phrase(ev, lang) for lang in ("fr", "en")}
        if not pick(when, "fr"):
            when = {lang: ui[lang]["sh.noDate"] for lang in ("fr", "en")}
        meta = {lang: " · ".join(x for x in (pick(when, lang),
                                             pick(ev.get("location"), lang),
                                             pick(ev.get("region"), lang)) if x)
                for lang in ("fr", "en")}
        inner = (bilingual("span", ev.get("name"), "sh-name")
                 + bilingual("span", meta, "sh-meta"))
        # Le lien n'existe que si la fiche existe : on lit la liste retenue
        # plutôt que de rejouer le seuil et risquer d'en diverger.
        if ev["id"] in kept_ids:
            out.append('<li><a href="tournois/%s.html">%s</a></li>' % (esc(ev["id"]), inner))
        else:
            out.append('<li><span class="sh-flat">%s</span></li>' % inner)
    return '<ul class="sh-list">%s</ul>' % "".join(out)


def facts(events, key, ui):
    """Les régions ou les mois représentés, comptés — pas une opinion."""
    seen = {}
    for ev in events:
        val = pick(ev.get(key), "fr")
        if val:
            seen[val] = seen.get(val, 0) + 1
    if not seen:
        return ""
    ordered = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    return '<div class="sh-tags">%s</div>' % "".join(
        '<span class="sh-tag">%s <span class="sh-tag-n">%d</span></span>'
        % (esc(name), n) for name, n in ordered)


def render(word, label, sheets, events, kept_ids, ui, sp_pages, total):
    fr_sp, en_sp = label["fr"], label["en"]
    title = {lang: ui[lang]["sh.title"].replace("{sp}", label[lang]) for lang in ("fr", "en")}
    desc = {lang: ui[lang]["sh.desc"].replace("{sp}", label[lang])
            .replace("{n}", str(len(events))) for lang in ("fr", "en")}
    url = "%s/tournois/espece-%s.html" % (SITE, word)

    today = datetime.date.today()
    dated = sorted((e for e in events if e.get("startDate")),
                   key=lambda e: e["startDate"])
    upcoming = [e for e in dated if not is_past(e, today)]
    past = [e for e in dated if is_past(e, today)]
    undated = [e for e in events if not e.get("startDate")]
    body = []

    body.append('<section><div class="container">%s%s</div></section>'
                % (bilingual("p", {"fr": ui["fr"]["sh.intro"], "en": ui["en"]["sh.intro"]},
                                   "tp-notes"),
                   facts(events, "region", ui)))

    # Ce qui s'en vient d'abord : c'est la seule section qui serve à planifier.
    alt = True
    for key, group in (("sh.upcoming", upcoming), ("sh.undated", undated),
                       ("sh.past", past)):
        if not group:
            continue
        body.append(section({"fr": ui["fr"][key], "en": ui["en"][key]},
                            rows_html(group, kept_ids, ui), alt=alt))
        alt = not alt

    links = []
    for sid in sheets:
        if sid in sp_pages:
            links.append('<a class="btn btn-ghost" href="especes/%s.html">%s</a>'
                         % (esc(sid), bilingual("span", {"fr": ui["fr"]["sh.sheetLink"],
                                                         "en": ui["en"]["sh.sheetLink"]})))
            break
    links.append('<a class="btn btn-teal" href="saison.html">%s</a>'
                 % bilingual("span", {"fr": ui["fr"]["sh.seasonLink"],
                                      "en": ui["en"]["sh.seasonLink"]}))
    links.append('<a class="btn btn-ghost" href="tournaments.html">%s</a>'
                 % bilingual("span", {lang: ui[lang]["sh.allGuide"].replace("{n}", str(total))
                                      for lang in ("fr", "en")}))
    body.append('<section><div class="container"><div class="callout">%s'
                '<div class="callout-actions">%s</div></div></div></section>'
                % (bilingual("p", {"fr": ui["fr"]["tp.confirm"], "en": ui["en"]["tp.confirm"]}),
                   "".join(links)))

    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Page générée par tools/build-species-hubs.py — ne pas modifier à la main.
     Corrige data/quebec-tournaments.json, puis relance le script.
     <base> ramène à la racine les chemins relatifs, cette page vivant un
     dossier plus bas. -->
<base href="/">
<title data-en="%(title_en)s">%(title_fr)s</title>
<meta name="description" content="%(desc_fr)s" data-en-content="%(desc_en)s">
<link rel="canonical" href="%(url)s">
<link rel="alternate" hreflang="fr-ca" href="%(url)s">
<link rel="alternate" hreflang="en-ca" href="%(url)s?lang=en">
<link rel="alternate" hreflang="x-default" href="%(url)s">
<meta name="theme-color" content="#0b1e33">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Pied Marin Fishing">
<meta property="og:locale" content="fr_CA">
<meta property="og:locale:alternate" content="en_CA">
<meta property="og:title" content="%(title_fr)s">
<meta property="og:description" content="%(desc_fr)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(site)s/assets/img/og-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title_fr)s">
<meta name="twitter:description" content="%(desc_fr)s">
<meta name="twitter:image" content="%(site)s/assets/img/og-card.png">
<link rel="icon" type="image/png" href="assets/img/favicon.png">
<link rel="apple-touch-icon" href="assets/img/favicon.png">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
%(nav)s
<div class="page-header">
  <div class="container">
    <span class="kicker" data-i18n="sh.kicker">Tournois par espèce</span>
    %(h1)s
  </div>
</div>

%(body)s
%(footer)s""" % {
        "title_fr": esc(title["fr"]), "title_en": esc(title["en"]),
        "desc_fr": esc(desc["fr"]), "desc_en": esc(desc["en"]),
        "url": url, "site": SITE, "nav": NAV, "footer": FOOTER,
        "h1": bilingual("h1", {lang: ui[lang]["sh.h1"].replace("{sp}", label[lang])
                               for lang in ("fr", "en")}),
        "body": "\n\n".join(body),
    }


if __name__ == "__main__":
    events = load("quebec-tournaments.json")
    i18n = load("i18n.json")
    ui = {"fr": i18n["fr"], "en": i18n["en"]}
    kept_ids = set(load("tournament-pages.json"))
    sp_pages = set(load("species-pages.json"))
    tournament_ids = {e["id"] for e in events}

    written = []
    for word, label, sheets in HUBS:
        mine = [e for e in events if matches(e, word)]
        if len(mine) < MIN_EVENTS:
            print("  sous le seuil : %-12s %d/%d tournois" % (label["fr"], len(mine), MIN_EVENTS))
            continue
        name = "espece-%s.html" % word
        # Un préfixe explicite plutôt qu'un nom nu : « tournois/achigan.html »
        # entrerait en collision le jour où un tournoi porte cet identifiant,
        # et le générateur des fiches écraserait la page sans rien dire.
        assert name[:-5] not in tournament_ids, "collision d'identifiant : %s" % name
        with io.open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(render(word, label, sheets, mine, kept_ids, ui, sp_pages, len(events)))
        written.append((word, len(mine), name))

    # Sans lien entrant, ces pages n'existent que pour qui connaît leur adresse.
    # Le bandeau vit dans le guide, entre deux marqueurs, pour qu'il suive la
    # liste des pages retenues au lieu d'être recopié à la main et de dériver
    # le jour où une espèce passe sous le seuil.
    # data-i18n et NON data-en : le guide est une page écrite à la main, servie
    # par i18n.js, qui ne connaît pas data-en. Le bloc est généré mais il
    # atterrit chez un moteur de traduction différent de celui des fiches —
    # les pastilles restaient en français en mode anglais.
    chips = "".join(
        '<a class="sh-chip" href="tournois/%s">'
        '<span data-i18n="sh.chip.%s">%s</span>'
        '<span class="sh-chip-n">%d</span></a>'
        % (esc(name), esc(word), esc(ui["fr"]["sh.chip." + word]), n)
        for word, n, name in written)
    block = START + (
        '\n    <nav class="sh-nav" data-i18n-aria-label="sh.navLabel" '
        'aria-label="%s">\n      <span class="sh-nav-lead" data-i18n="sh.navLead">%s</span>'
        '\n      %s\n    </nav>\n    ' % (
            esc(ui["fr"]["sh.navLabel"]), esc(ui["fr"]["sh.navLead"]), chips)
    ) + END
    guide = os.path.join(REPO, "tournaments.html")
    with io.open(guide, encoding="utf-8") as fh:
        html = fh.read()
    import re as _re
    html = _re.sub(_re.escape(START) + r".*?" + _re.escape(END), lambda m: block,
                   html, flags=_re.S)
    with io.open(guide, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("%d page(s) par espèce dans tournois/" % len(written))
    for word, n, name in written:
        print("  ✓ %-12s %2d tournois  →  %s" % (ui["fr"]["sh.chip." + word], n, name))
