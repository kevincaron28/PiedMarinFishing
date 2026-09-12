# -*- coding: utf-8 -*-
"""Écrit une fiche par pêcheur (pecheurs/) et par bateau (bateaux/).

Une fiche de pêcheur a une adresse à elle, et c'est tout l'intérêt : une
candidature de pro staff demande un lien, et « piedmarinfishing.com » ne dit
pas qui tu es. Chaque pêcheur peut maintenant coller la sienne.

Les fiches de bateau existent pour la même raison, plus une autre : celle qui
est en restauration a besoin d'un endroit où le chantier s'écrit, photo après
photo, ce qu'une carte sur la page Équipe ne permet pas.

    python3 tools/build-profile-pages.py

Le gabarit — menu, pied de page, bilinguisme par data-en — vient de
build-tournament-pages.py plutôt que d'être recopié : une seule définition,
donc pas de dérive entre les deux familles de fiches.
"""
import io
import json
import os
import re
import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://piedmarinfishing.com"

_spec = importlib.util.spec_from_file_location(
    "pages", os.path.join(REPO, "tools", "build-tournament-pages.py"))
pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages)

esc, pick, bilingual, section = pages.esc, pages.pick, pages.bilingual, pages.section
clamp_title, long_date = pages.clamp_title, pages.long_date


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def nav_for(current="team.html"):
    """Le menu du gabarit, avec l'onglet actif deplace sur `current`.

    Le gabarit arrive marque sur Tournois. Toutes les fiches passaient par ici
    et ressortaient marquees sur Equipe — une fiche d'espece annoncait donc
    « Equipe » comme page courante au lecteur d'ecran. L'appelant dit
    maintenant de quel onglet il depend.
    """
    html = pages.NAV.replace(' aria-current="page"', "")
    # La marque pointe elle aussi sur index.html et vient AVANT la liste : on
    # ne cherche l'onglet qu'a partir du <ul>, sinon nav_for("index.html")
    # decorerait l'ecusson.
    # On coupe sur le debut de balise seulement : la liste a gagne un id
    # (aria-controls), et chercher la balise complete a fait echouer le
    # generateur — bruyamment, ce qui valait mieux qu'un menu faux.
    head, sep, tail = html.partition('<ul class="nav-links"')
    needle = 'href="%s"' % current
    if needle not in tail:
        raise SystemExit("nav_for : aucun onglet %s dans le menu" % current)
    return head + sep + tail.replace(needle, needle + ' aria-current="page"', 1)


def head(title, desc, url, image, ld="", og_type="profile", current="team.html"):
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Page générée par tools/build-profile-pages.py — ne pas modifier à la main.
     Corrige data/team-members.json ou data/boats.json, puis relance le script.
     <base> ramène les chemins relatifs à la racine, cette page vivant un
     dossier plus bas. -->
<base href="/">
<title data-en="%(title_en)s">%(title_fr)s</title>
<meta name="description" content="%(desc_fr)s" data-en-content="%(desc_en)s">
<link rel="canonical" href="%(url)s">
<link rel="alternate" hreflang="fr-ca" href="%(url)s">
<link rel="alternate" hreflang="en-ca" href="%(url)s?lang=en">
<link rel="alternate" hreflang="x-default" href="%(url)s">
<meta name="theme-color" content="#0b1e33">
<meta property="og:type" content="%(og_type)s">
<meta property="og:site_name" content="Pied Marin Fishing">
<meta property="og:locale" content="fr_CA">
<meta property="og:locale:alternate" content="en_CA">
<meta property="og:title" content="%(title_fr)s">
<meta property="og:description" content="%(desc_fr)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(image)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title_fr)s">
<meta name="twitter:description" content="%(desc_fr)s">
<meta name="twitter:image" content="%(image)s">
<link rel="icon" type="image/png" href="assets/img/favicon.png">
<link rel="apple-touch-icon" href="assets/img/favicon.png">
<link rel="stylesheet" href="assets/css/style.css">
%(ld)s
</head>
<body>
%(nav)s""" % {"title_fr": esc(title["fr"]), "title_en": esc(title["en"]),
              "desc_fr": esc(desc["fr"]), "desc_en": esc(desc["en"]),
              "url": url, "image": image, "ld": ld, "og_type": og_type,
              "nav": nav_for(current)}


VARIANTS = {}


def srcset_attrs(src, sizes):
    """Le srcset écrit en dur, à partir de data/image-variants.json.

    Les fiches ne rendent rien en JavaScript : c'est le générateur qui doit
    poser les largeurs. Une photo absente de la carte sort sans srcset, donc
    servie telle quelle — jamais cassée.
    """
    widths = VARIANTS.get(src)
    if not widths or len(widths) < 2:
        return ""
    stem, ext = os.path.splitext(src)
    top = max(widths)
    liste = ", ".join("%s %dw" % (src if w == top else "%s-%d%s" % (stem, w, ext), w)
                      for w in widths)
    return ' srcset="%s" sizes="%s"' % (esc(liste), esc(sizes))


def gallery_src(photo):
    """Le chemin d'une entree de galerie, qu'elle soit nue ou {src, alt}."""
    return photo.get("src") if isinstance(photo, dict) else photo


def gallery_html(photos, alt):
    """Une galerie où chaque photo peut porter sa propre description.

    Une entrée est soit un chemin tout court, soit {src, alt:{fr,en}}. Un
    chemin seul retombe sur la description commune — c'est mieux que rien,
    mais une photo qui montre quelque chose de précis mérite de le dire.
    """
    if not photos:
        return ""
    out = []
    for photo in photos:
        src = photo.get("src") if isinstance(photo, dict) else photo
        if not src:
            continue
        legende = pick(photo.get("alt"), "fr") if isinstance(photo, dict) else ""
        img = ('<img class="gal-img" src="%s"%s alt="%s" loading="lazy">'
               % (esc(src), srcset_attrs(src, "(max-width: 700px) 92vw, 260px"),
                  esc(legende or alt)))
        # L'anglais voyage en data-en-alt, comme partout sur les fiches.
        if isinstance(photo, dict) and pick(photo.get("alt"), "en") not in ("", legende):
            img = img.replace("<img ", '<img data-en-alt="%s" '
                              % esc(pick(photo.get("alt"), "en")), 1)
        # La description existait deja, mais seulement dans alt : elle ne
        # servait qu'aux lecteurs d'ecran. Elle devient visible — c'est ce qui
        # fait la difference entre un tas de photos et un journal de chantier.
        cap = bilingual("figcaption", photo.get("alt"), "gal-cap") if isinstance(photo, dict) else ""
        out.append('<figure class="gal-item">%s%s</figure>' % (img, cap))
    return '<div class="gal-grid" data-gallery>%s</div>' % "".join(out)


def ordinal(n, lang):
    if lang == "fr":
        return "1re" if n == 1 else "%de" % n
    v = n % 100
    suffixes = ["th", "st", "nd", "rd"]
    suffix = suffixes[(v - 20) % 10] if 20 <= v < 30 else None
    if suffix is None:
        suffix = suffixes[v] if v < 4 else suffixes[0]
    return "%d%s" % (n, suffix)


def placement_of(placement, field, lang, ui):
    """« 102e sur 309 » — un rang sans son peloton ne dit rien."""
    rank = ordinal(placement, lang)
    if not field:
        return rank
    return "%s %s" % (rank, ui[lang]["history.of"].replace("{n}", str(field)))


def top_percent(placement, field):
    if not placement or not field:
        return None
    return max(1, -(-placement * 100 // field))


def plural(ui, lang, base, n):
    return ui[lang]["%s.%s" % (base, "one" if n == 1 else "other")]


def describe(bits):
    """Assemble des phrases jusqu'à tenir entre 110 et 165 caractères."""
    out = ""
    for bit in bits:
        if not bit:
            continue
        if len(out) >= 110:
            break
        out = (out + " " + bit.rstrip(".") + ".").strip()
    if len(out) > 165:
        out = out[:164].rsplit(" ", 1)[0].rstrip(",;:.") + "…"
    return out


def angler_description(m, lang, ui):
    specs = m.get("specs") or {}
    name = m.get("name") or ""
    head = name
    role = pick(m.get("role"), lang)
    if role:
        head += ", %s" % (role[0].lower() + role[1:])
    head += " chez Pied Marin Fishing" if lang == "fr" else " with Pied Marin Fishing"
    bits = [head]
    for field, key in (("homeWater", "team.spec.homeWater"),
                       ("species", "team.spec.species"),
                       ("technique", "team.spec.technique"),
                       ("personalBest", "team.spec.personalBest")):
        value = pick(specs.get(field), lang)
        if value:
            bits.append("%s : %s" % (ui[lang][key], value) if lang == "fr"
                        else "%s: %s" % (ui[lang][key], value))
    return describe(bits)


def boat_description(b, lang, ui):
    specs = b.get("specs") or {}
    bits = [pick(b.get("name"), lang)]
    for field, key in (("model", "boats.spec.model"), ("year", "boats.spec.year"),
                       ("length", "boats.spec.length"), ("engine", "boats.spec.engine"),
                       ("electronics", "boats.spec.electronics")):
        value = pick(specs.get(field), lang)
        if value:
            bits.append("%s : %s" % (ui[lang][key], value) if lang == "fr"
                        else "%s: %s" % (ui[lang][key], value))
    bits.append(pick(b.get("description"), lang))
    return describe(bits)


ANGLER_SPECS = [("homeWater", "team.spec.homeWater", "🌊"),
                ("species", "team.spec.species", "🐟"),
                ("technique", "team.spec.technique", "🎯"),
                ("dreamCatch", "team.spec.dreamCatch", "⭐"),
                ("personalBest", "team.spec.personalBest", "🏅"),
                ("since", "team.spec.since", "📅")]

BOAT_SPECS = [("model", "boats.spec.model"), ("year", "boats.spec.year"),
              ("length", "boats.spec.length"), ("engine", "boats.spec.engine"),
              ("trolling", "boats.spec.trolling"),
              ("electronics", "boats.spec.electronics")]


def icon_specs(specs, rows, ui):
    """Les rangées d'une fiche : celles qui sont vides ne sont pas écrites.

    La carte de la page Équipe montre les cases vides pour qu'elles se
    remplissent; une fiche publique, elle, est une vitrine — un « — » y a
    l'air d'un oubli.
    """
    out = []
    for row in rows:
        field, key = row[0], row[1]
        icon = row[2] if len(row) > 2 else ""
        value = specs.get(field)
        if not pick(value, "fr"):
            continue
        label = {"fr": ui["fr"][key], "en": ui["en"][key]}
        marker = '<span aria-hidden="true">%s</span> ' % icon if icon else ""
        out.append('<div class="event-spec"><span class="event-spec-label">%s%s</span>%s</div>'
                   % (marker, bilingual("span", label), bilingual("span", value, "event-spec-value")))
    return "".join(out)


MEASURE_RE = re.compile(r'([\d]+(?:[.,][\d]+)?)\s*(po|lb|kg|cm|in|"|\u2033)', re.I)


def parse_measure(text):
    """Même lecture que parseMeasure() dans assets/js/util.js."""
    m = MEASURE_RE.search(str(text or ""))
    if not m:
        return None
    unit = m.group(2).lower()
    unit = "po" if unit in ('"', "\u2033") else unit
    return float(m.group(1).replace(",", ".")), unit


def team_records(catches):
    """Le record d'équipe par espèce, comme le temple de la renommée.

    À unité différente on garde le premier plutôt que de comparer des pouces
    à des livres — exactement la règle de records() dans catches.js.
    """
    best = {}
    for c in catches:
        parsed = parse_measure(pick(c.get("measure"), "fr"))
        key = pick(c.get("species"), "fr").strip().lower()
        if not parsed or not key:
            continue
        held = best.get(key)
        if not held or (held[1][1] == parsed[1] and parsed[0] > held[1][0]):
            best[key] = (c, parsed)
    return [c for c, _ in best.values()]


def result_rows(rows, ui, tp_index):
    """Les sorties d'un pêcheur, la plus récente en premier."""
    out = []
    for r in sorted(rows, key=lambda x: x.get("date") or "", reverse=True):
        placement, field = r.get("placement"), r.get("fieldSize")
        place = {"fr": "", "en": ""}
        if placement:
            place = {lang: placement_of(placement, field, lang, ui) for lang in ("fr", "en")}
        pct = top_percent(placement, field)
        pct_html = ""
        if pct:
            pct_html = bilingual("span", {
                "fr": ui["fr"]["history.topPercent"].replace("{n}", str(pct)),
                "en": ui["en"]["history.topPercent"].replace("{n}", str(pct))},
                "placement-pct")
        # Le nom pointe vers la fiche du tournoi quand elle existe : la même
        # sortie vue depuis le pêcheur et depuis l'événement.
        target = r.get("id") if r.get("id") in tp_index else pages.family(r.get("id"))
        label = bilingual("strong", r.get("name"))
        if target in tp_index:
            label = '<a href="tournois/%s.html">%s</a>' % (esc(target), label)
        when = {lang: long_date(r.get("date"), lang) for lang in ("fr", "en")}
        out.append('<li class="ap-result">%s<span class="ap-result-meta">%s%s%s</span></li>'
                   % (label,
                      bilingual("span", when, "ap-result-date") if r.get("date") else "",
                      bilingual("span", place, "ap-result-place") if placement else "",
                      pct_html))
    return "".join(out)


def stat_tiles(tiles):
    """Les mêmes tuiles que le palmarès — mêmes classes, donc même style."""
    return ('<div class="grid grid-%d ap-stats">%s</div>'
            % (min(len(tiles), 4),
               "".join('<div class="stat-card">%s%s</div>'
                       % (bilingual("div", num, "num"), bilingual("div", label, "label"))
                       for num, label in tiles)))


def person_ld(m, url, photo):
    ld = {"@context": "https://schema.org", "@type": "Person",
          "name": m.get("name"), "url": url,
          "memberOf": {"@type": "SportsTeam", "name": "Pied Marin Fishing",
                       "url": SITE + "/"}}
    role = pick(m.get("role"), "fr")
    if role:
        ld["jobTitle"] = role
    if photo:
        ld["image"] = "%s/%s" % (SITE, photo)
    bio = pick(m.get("bio"), "fr")
    if bio:
        ld["description"] = bio
    return ld


def render_angler(m, ui, results, catches, boats, tp_index, cp_index, videos=(),
                  prev=None, nxt=None):
    name = m.get("name") or m.get("id")
    role = m.get("role") or {}
    title = {lang: clamp_title(", ".join(x for x in (name, pick(role, lang)) if x))
             for lang in ("fr", "en")}
    desc = {lang: angler_description(m, lang, ui) for lang in ("fr", "en")}
    url = "%s/pecheurs/%s.html" % (SITE, m["id"])
    photo = m.get("photo") or ""
    image = "%s/%s" % (SITE, photo) if photo else "%s/assets/img/og-card.png" % SITE

    body = []

    # Parcours — la photo et la bio, côte à côte.
    alt = m.get("photoAlt") or {"fr": name, "en": name}
    photo_html = ('<img class="ap-photo" src="%s"%s alt="%s" width="900" height="1200">'
                  % (esc(photo), srcset_attrs(photo, "(max-width: 700px) 92vw, 260px"),
                     esc(pick(alt, "fr")))) if photo else ""
    if photo_html and pick(alt, "en") != pick(alt, "fr"):
        photo_html = photo_html.replace("<img ", '<img data-en-alt="%s" ' % esc(pick(alt, "en")))
    bio = bilingual("p", m.get("bio"), "ap-bio") if pick(m.get("bio"), "fr") else ""
    if photo_html or bio:
        body.append(section({"fr": ui["fr"]["ap.about"], "en": ui["en"]["ap.about"]},
                            '<div class="ap-intro">%s<div class="ap-intro-body">%s</div></div>'
                            % (photo_html, bio), key="ap.about"))

    specs = icon_specs(m.get("specs") or {}, ANGLER_SPECS, ui)
    if specs:
        body.append(section({"fr": ui["fr"]["ap.specs"], "en": ui["en"]["ap.specs"]},
                            '<div class="event-specs tp-specs">%s</div>' % specs,
                            alt=True, key="ap.specs"))

    # Équipement — la section que regarde une marque. Vide, elle n'existe pas :
    # une liste de matériel à moitié remplie dessert la candidature.
    gear = [g for g in (m.get("gear") or []) if pick(g.get("value"), "fr")]
    if gear:
        rows = "".join(
            '<div class="event-spec"><span class="event-spec-label">%s</span>%s</div>'
            % (bilingual("span", g.get("label")), bilingual("span", g.get("value"), "event-spec-value"))
            for g in gear)
        body.append(section({"fr": ui["fr"]["ap.gear"], "en": ui["en"]["ap.gear"]},
                            '<div class="event-specs tp-specs">%s</div>' % rows, key="ap.gear"))

    mine = [r for r in results if m["id"] in (r.get("members") or [])]
    if mine:
        placements = [r["placement"] for r in mine if isinstance(r.get("placement"), int)]
        best = min(placements) if placements else None
        best_field = None
        for r in mine:
            if r.get("placement") == best:
                best_field = r.get("fieldSize")
                break
        tiles = [({"fr": str(len(mine)), "en": str(len(mine))},
                  {"fr": plural(ui, "fr", "team.record.events", len(mine)),
                   "en": plural(ui, "en", "team.record.events", len(mine))})]
        if best:
            tiles.append(({"fr": placement_of(best, best_field, "fr", ui),
                           "en": placement_of(best, best_field, "en", ui)},
                          {"fr": ui["fr"]["team.record.best"], "en": ui["en"]["team.record.best"]}))
        top3 = len([p for p in placements if p <= 3])
        if top3:
            tiles.append(({"fr": str(top3), "en": str(top3)},
                          {"fr": ui["fr"]["team.record.top3"], "en": ui["en"]["team.record.top3"]}))
        link = ('<a class="member-history-link" href="history.html?member=%s">%s</a>'
                % (esc(m["id"]), bilingual("span", {"fr": ui["fr"]["team.viewResults"],
                                                    "en": ui["en"]["team.viewResults"]})))
        body.append(section({"fr": ui["fr"]["ap.record"], "en": ui["en"]["ap.record"]},
                            "%s<ul class=\"ap-results\">%s</ul>%s"
                            % (stat_tiles(tiles), result_rows(mine, ui, tp_index), link),
                            alt=True, key="ap.record"))

    # Records d'équipe détenus — ce qu'une marque regarde en premier. Calculé
    # sur le journal complet, pas sur les seules prises du pêcheur : détenir
    # le record ne veut rien dire s'il n'est pas comparé à ceux des autres.
    held = [c for c in team_records(catches) if c.get("angler") == m["id"]]
    if held:
        rows = "".join(
            '<li class="ap-record-held">%s%s</li>'
            % (bilingual("span", c.get("species"), "ap-record-species"),
               bilingual("span", c.get("measure"), "ap-record-measure"))
            for c in held)
        body.append(section({"fr": ui["fr"]["ap.records"], "en": ui["en"]["ap.records"]},
                            '<ul class="ap-records">%s</ul>' % rows, key="ap.records"))

    mine_catches = [c for c in catches if c.get("angler") == m["id"]]
    if mine_catches:
        # Chaque vignette mène à SA prise, pas à la liste filtrée du pêcheur.
        # Quand la prise a sa propre fiche, c'est là qu'on va — sinon vers son
        # ancre sur la page des prises.
        cards = "".join(
            '<a class="ap-catch" href="%s">%s%s</a>'
            % ("prises/%s.html" % esc(c["id"]) if c["id"] in cp_index
               else "catches.html#c-%s" % esc(c["id"]),
               '<img src="%s"%s alt="" loading="lazy" width="120" height="90">'
               % (esc((c.get("media") or {}).get("src") or ""),
                  srcset_attrs((c.get("media") or {}).get("src") or "", "68px"))
               if (c.get("media") or {}).get("src") else "",
               '<span class="ap-catch-body">%s%s</span>'
               % (bilingual("span", c.get("species"), "ap-catch-species"),
                  bilingual("span", c.get("measure"), "ap-catch-measure")
                  if pick(c.get("measure"), "fr") else ""))
            for c in mine_catches)
        # Le même lien nommé que la section des résultats : une vignette
        # cliquable ne dit pas où elle mène.
        more = ('<a class="member-history-link" href="catches.html?angler=%s">%s</a>'
                % (esc(m["id"]), bilingual("span", {"fr": ui["fr"]["team.viewCatches"],
                                                    "en": ui["en"]["team.viewCatches"]})))
        body.append(section({"fr": ui["fr"]["ap.catches"], "en": ui["en"]["ap.catches"]},
                            '<div class="ap-catches">%s</div>%s' % (cards, more),
                            key="ap.catches"))

    # Son bateau — celui qu'il barre, sinon celui qu'il possède.
    his = ([b for b in boats if b.get("skipper") == m["id"]]
           or [b for b in boats if b.get("owner") == m["id"]])
    if his:
        rows = "".join(
            '<li><a href="bateaux/%s.html">%s</a></li>' % (esc(b["id"]), bilingual("span", b.get("name")))
            for b in his)
        body.append(section({"fr": ui["fr"]["ap.boat"], "en": ui["en"]["ap.boat"]},
                            '<ul class="tp-related">%s</ul>' % rows, alt=True, key="ap.boat"))

    # Ses vidéos. Le champ « angler » de data/videos.json existait depuis le
    # début et ne servait à rien : la vidéo du 50 po de Kevin B. n'apparaissait
    # ni sur sa fiche ni sur la page de la prise. Un champ de données qui ne
    # mène nulle part est un lien manquant qui ne se voit pas.
    mine = [v for v in videos if v.get("angler") == m["id"] and v.get("videoId")]
    if mine:
        cards = "".join(pages.video_card(v, {"fr": long_date(v.get("date"), "fr"),
                                             "en": long_date(v.get("date"), "en")})
                        for v in mine)
        body.append(section({"fr": ui["fr"]["member.videos"], "en": ui["en"]["member.videos"]},
                            '<div class="video-list">%s</div>' % cards, key="member.videos"))

    # La fiche pro staff en PDF, écrite par tools/build-angler-sheets.py à
    # partir des mêmes données que cette page. Les deux versions sont offertes
    # côte à côte quelle que soit la langue affichée : une marque anglophone
    # ne devrait pas avoir à basculer l'interface pour trouver la sienne.
    sheets = "".join(
        '<a class="btn btn-ghost" href="assets/docs/pro-staff-%s-%s.pdf" download>%s</a>'
        % (esc(m["id"]), lang,
           bilingual("span", {"fr": ui["fr"]["ap.sheet%s" % lang.capitalize()],
                              "en": ui["en"]["ap.sheet%s" % lang.capitalize()]}))
        for lang in ("fr", "en"))
    body.append(section({"fr": ui["fr"]["ap.sheetTitle"], "en": ui["en"]["ap.sheetTitle"]},
                        '%s<div class="callout-actions">%s</div>'
                        % (bilingual("p", {"fr": ui["fr"]["ap.sheetBody"],
                                           "en": ui["en"]["ap.sheetBody"]}, "tp-notes"), sheets),
                        alt=True, key="ap.sheetTitle"))

    body.append('<section><div class="container"><div class="callout-actions">'
                '<a class="btn btn-ghost" href="team.html">%s</a></div></div></section>'
                % bilingual("span", {"fr": ui["fr"]["ap.back"], "en": ui["en"]["ap.back"]}))

    ld = ('<script type="application/ld+json">\n%s\n</script>'
          % json.dumps(person_ld(m, url, photo), ensure_ascii=False, indent=2).replace("</", "<\\/"))

    return """%(head)s
<div class="page-header">
  <div class="container">
    %(crumbs)s
    <span class="kicker" data-i18n="ap.kicker">%(kicker)s</span>
    <h1>%(name)s</h1>
    %(role)s
  </div>
</div>

%(body)s
<section class="siblings-wrap"><div class="container">%(siblings)s</div></section>
%(footer)s""" % {
        "head": head(title, desc, url, image, ld),
        "crumbs": pages.breadcrumb("equipe", name, url),
        "siblings": pages.siblings(prev, nxt),
        "kicker": esc(ui["fr"]["ap.kicker"]),
        "name": esc(name),
        "role": bilingual("p", role, "tp-when") if pick(role, "fr") else "",
        "body": "\n\n".join(body),
        "footer": pages.FOOTER,
    }


def tasks_html(tasks, ui):
    """Le chantier en deux colonnes : ce qui est fait, ce qu'il reste.

    Kevin a donné une liste, pas un journal — la rendre en entrées datées
    aurait demandé d'inventer des dates. Une liste dit d'ailleurs mieux ce
    qu'un chantier a de particulier : où il en est, et où il s'en va.
    """
    if not tasks:
        return ""
    done = [t for t in tasks if t.get("done")]
    todo = [t for t in tasks if not t.get("done")]
    # Un chantier a trois états, pas deux : le plancher dont le bois est taillé
    # mais qui attend le sablage et le tapis n'est ni fait ni intact. Il reste
    # du côté « à faire » — c'est là qu'il est vrai — mais il se distingue, et
    # il ne compte pas dans le pourcentage tant qu'il n'est pas fini.
    pct = int(round(100.0 * len(done) / len(tasks)))

    def column(rows, key, cls):
        if not rows:
            return ""
        items = ""
        for t in rows:
            tag = ""
            if t.get("progress"):
                tag = bilingual("span", {"fr": ui["fr"]["bp.taskProgress"],
                                         "en": ui["en"]["bp.taskProgress"]}, "bp-task-now")
            items += ('<li%s>%s%s</li>'
                      % (' class="is-progress"' if t.get("progress") else "",
                         bilingual("span", t.get("label")), tag))
        return ('<div class="bp-task-col %s">%s<ul>%s</ul></div>'
                % (cls, bilingual("h3", {"fr": ui["fr"][key], "en": ui["en"][key]},
                                  "bp-task-head"), items))

    label = {lang: ui[lang]["bp.progress"].replace("{done}", str(len(done)))
                                          .replace("{total}", str(len(tasks)))
             for lang in ("fr", "en")}
    # aria-hidden sur la barre : le compte est déjà écrit juste à côté, en
    # toutes lettres. La répéter n'ajouterait rien à la lecture vocale.
    bar = ('<div class="bp-progress">%s'
           '<div class="bp-progress-track" aria-hidden="true">'
           '<span class="bp-progress-fill" style="width:%d%%"></span></div></div>'
           % (bilingual("span", label, "bp-progress-label"), pct))
    return ("%s<div class=\"bp-tasks\">%s%s</div>"
            % (bar, column(done, "bp.tasksDone", "is-done"),
               column(todo, "bp.tasksTodo", "is-todo")))


def render_boat(b, ui, members_by_id, prev=None, nxt=None):
    title = {lang: clamp_title(pick(b.get("name"), lang)) for lang in ("fr", "en")}
    desc = {lang: boat_description(b, lang, ui) for lang in ("fr", "en")}
    url = "%s/bateaux/%s.html" % (SITE, b["id"])
    gallery = [p for p in (b.get("gallery") or []) if p]
    # UNE ENTREE DE GALERIE N'EST PAS UN CHEMIN. C'est soit un chemin, soit
    # {src, alt:{fr,en}} — gallery_html() le sait, cette ligne-ci l'ignorait.
    # Resultat : un bateau sans `image` mais avec une galerie mettait le dict
    # Python entier dans og:image, et le guillemet du texte francais fermait
    # l'attribut au milieu du <head>. Aucune page de partage n'affichait
    # d'apercu, et rien ne criait — le lien existait, il etait juste absurde.
    hero = b.get("image") or (gallery_src(gallery[0]) if gallery else "")
    if hero and not isinstance(hero, str):
        raise SystemExit("og:image doit etre un chemin, pas %r (bateau %s)"
                         % (type(hero).__name__, b.get("id")))
    image = "%s/%s" % (SITE, hero) if hero else "%s/assets/img/og-card.png" % SITE

    body = []
    resto = b.get("restoration") or {}
    status = resto.get("status") or ""
    if status in ("restoration", "done", "restored"):
        key = "bp.inProgress" if status == "restoration" else "bp.done"
        body.append('<section><div class="container"><div class="notice notice-ours">%s</div>'
                    "</div></section>"
                    % bilingual("span", {"fr": ui["fr"][key], "en": ui["en"][key]}))

    if pick(b.get("description"), "fr"):
        body.append(section({"fr": ui["fr"]["ap.about"], "en": ui["en"]["ap.about"]},
                            bilingual("p", b.get("description"), "tp-notes"), key="ap.about"))

    specs = icon_specs(b.get("specs") or {}, BOAT_SPECS, ui)
    if specs:
        body.append(section({"fr": ui["fr"]["ap.specs"], "en": ui["en"]["ap.specs"]},
                            '<div class="event-specs tp-specs">%s</div>' % specs,
                            alt=True, key="ap.specs"))

    # À bord — capitaine et propriétaire, chacun vers sa fiche. Quand c'est la
    # même personne, une seule ligne : « Capitaine et propriétaire ».
    crew = []
    skipper, owner = b.get("skipper"), b.get("owner")
    pairs = ([(skipper, "boats.skipperOwner")] if skipper and skipper == owner
             else [(skipper, "boats.skipper"), (owner, "boats.owner")])
    for member_id, key in pairs:
        person = members_by_id.get(member_id)
        if not person:
            continue
        label = {"fr": ui["fr"][key].rstrip(" :"), "en": ui["en"][key].rstrip(" :")}
        crew.append('<div class="event-spec"><span class="event-spec-label">%s</span>'
                    '<span class="event-spec-value"><a href="pecheurs/%s.html">%s</a></span></div>'
                    % (bilingual("span", label), esc(member_id), esc(person.get("name") or member_id)))
    if crew:
        body.append(section({"fr": ui["fr"]["bp.crew"], "en": ui["en"]["bp.crew"]},
                            '<div class="event-specs tp-specs">%s</div>' % "".join(crew),
                            key="bp.crew"))

    if gallery:
        alt = ui["fr"]["boats.photoAlt"].replace("{name}", pick(b.get("name"), "fr"))
        body.append(section({"fr": ui["fr"]["bp.gallery"], "en": ui["en"]["bp.gallery"]},
                            gallery_html(gallery, alt), alt=True, key="bp.gallery"))

    # Le journal de chantier, du plus récent au plus ancien. Vide, la section
    # n'existe pas — comme partout ailleurs sur le site.
    entries = [e for e in (resto.get("entries") or []) if pick(e.get("title"), "fr")
               or pick(e.get("body"), "fr")]
    # Un chantier annoncé mais sans entrée n'aurait qu'une pastille et rien
    # d'autre : l'intro dit où le bateau en est en attendant la première photo.
    intro = (bilingual("p", resto.get("intro"), "bp-intro")
             if pick(resto.get("intro"), "fr") else "")
    tasks = tasks_html([t for t in (resto.get("tasks") or [])
                        if pick(t.get("label"), "fr")], ui)
    if entries or intro or tasks:
        items = []
        for e in sorted(entries, key=lambda x: x.get("date") or "", reverse=True):
            when = {lang: long_date(e.get("date"), lang) for lang in ("fr", "en")}
            photos = [p for p in (e.get("photos") or []) if p]
            items.append(
                '<li class="bp-log-item">%s%s%s%s</li>'
                % (bilingual("span", when, "bp-log-date") if e.get("date") else "",
                   bilingual("h3", e.get("title"), "bp-log-title") if pick(e.get("title"), "fr") else "",
                   bilingual("p", e.get("body"), "bp-log-body") if pick(e.get("body"), "fr") else "",
                   gallery_html(photos, pick(e.get("title"), "fr") or pick(b.get("name"), "fr"))))
        log = '<ol class="bp-log">%s</ol>' % "".join(items) if items else ""
        body.append(section({"fr": ui["fr"]["bp.restoration"], "en": ui["en"]["bp.restoration"]},
                            intro + tasks + log, key="bp.restoration"))

    body.append('<section><div class="container"><div class="callout-actions">'
                '<a class="btn btn-ghost" href="team.html#bateaux">%s</a></div></div></section>'
                % bilingual("span", {"fr": ui["fr"]["bp.back"], "en": ui["en"]["bp.back"]}))

    return """%(head)s
<div class="page-header">
  <div class="container">
    %(crumbs)s
    <span class="kicker" data-i18n="bp.kicker">%(kicker)s</span>
    %(h1)s
  </div>
</div>

%(body)s
<section class="siblings-wrap"><div class="container">%(siblings)s</div></section>
%(footer)s""" % {
        "head": head(title, desc, url, image, og_type="article"),
        "crumbs": pages.breadcrumb("equipe", b.get("name"), url),
        "siblings": pages.siblings(prev, nxt),
        "kicker": esc(ui["fr"]["bp.kicker"]),
        "h1": bilingual("h1", b.get("name")),
        "body": "\n\n".join(body),
        "footer": pages.FOOTER,
    }


def write_dir(dirname, files):
    """Écrit un dossier et retire les fiches devenues orphelines."""
    out_dir = os.path.join(REPO, dirname)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    existing = {f for f in os.listdir(out_dir) if f.endswith(".html")}
    for name, html in files.items():
        with io.open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(html)
    for stale in sorted(existing - set(files)):
        os.remove(os.path.join(out_dir, stale))
        print("  supprimée :", os.path.join(dirname, stale))


if __name__ == "__main__":
    try:
        VARIANTS.update(load("image-variants.json"))
    except IOError:
        pass  # pas de variantes, pas de srcset : les photos sortent en pleine taille
    members = load("team-members.json")
    boats = load("boats.json")
    results = load("tournament-history.json")
    catches = load("catches.json")
    tp_index = set(load("tournament-pages.json"))
    try:
        cp_index = set(load("catch-pages.json"))
    except (IOError, OSError, ValueError):
        cp_index = set()
    i18n = load("i18n.json")
    ui = {"fr": i18n["fr"], "en": i18n["en"]}
    members_by_id = {m["id"]: m for m in members}

    videos = (load("videos.json") or {}).get("videos") or []
    # Deux familles courtes : trois pecheurs, deux bateaux. Elles gardent
    # l'ordre du fichier de donnees, qui est celui des pages d'index.
    def around(rows, i, folder):
        def link(other):
            return ("%s/%s.html" % (folder, other["id"]), other.get("name")) if other else None
        return (link(rows[i - 1]) if i else None,
                link(rows[i + 1]) if i + 1 < len(rows) else None)

    write_dir("pecheurs", {
        "%s.html" % m["id"]: render_angler(m, ui, results, catches, boats, tp_index,
                                           cp_index, videos, *around(members, i, "pecheurs"))
        for i, m in enumerate(members)})
    write_dir("bateaux", {
        "%s.html" % b["id"]: render_boat(b, ui, members_by_id, *around(boats, i, "bateaux"))
        for i, b in enumerate(boats)})

    print("%d fiches de pêcheur, %d fiches de bateau" % (len(members), len(boats)))
    for m in members:
        gear = len([g for g in (m.get("gear") or []) if pick(g.get("value"), "fr")])
        print("  pecheurs/%-16s %d élément(s) d'équipement" % (m["id"] + ".html", gear))
    for b in boats:
        resto = b.get("restoration") or {}
        print("  bateaux/%-18s %d photo(s), %d entrée(s) de chantier"
              % (b["id"] + ".html", len(b.get("gallery") or []),
                 len(resto.get("entries") or [])))
