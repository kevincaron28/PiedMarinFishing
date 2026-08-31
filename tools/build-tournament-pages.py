# -*- coding: utf-8 -*-
"""Écrit une fiche par tournoi dans tournois/, à partir du répertoire.

Les 34 tournois du guide vivent tous sur UNE adresse. Quelqu'un qui cherche
« Tournoi Destroyer 2026 inscription » ne trouve donc rien : Google n'a qu'une
page à offrir, et elle parle de 34 tournois à la fois. Une fiche par tournoi
répond à ces recherches précises.

Le français est écrit en dur dans le HTML — c'est lui que lisent les robots —
et l'anglais voyage dans des attributs data-en qu'assets/js/tournament-page.js
échange au clic. Rien n'est rendu en JavaScript.

    python3 tools/build-tournament-pages.py

À relancer après toute modification de data/quebec-tournaments.json, puis
enchaîner avec build-structured-data.py et build-sitemap.py.

SEUIL — une fiche mince nuit plus qu'elle n'aide. Un tournoi n'a droit à sa
page que s'il atteint SCORE_MIN sur les dix champs qui intéressent un lecteur.
Les étapes de circuit sont couvertes sur la page de leur circuit plutôt que
d'avoir chacune la leur : « Deuxième des quatre étapes » ne fait pas une page.
Une étape orpheline (circuit absent ou sous le seuil) redevient éligible.
"""
import io
import json
import os
import re
import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "tournois")
SITE = "https://piedmarinfishing.com"
SCORE_MIN = 6

FIELDS = ["location", "species", "organizer", "link", "notes"]
SPEC_FIELDS = ["fee", "teamSize", "hours", "format", "deadline"]

# Le JSON-LD Event est déjà écrit et testé ailleurs : on l'importe plutôt que
# d'en tenir une deuxième version qui finirait par diverger.
_spec = importlib.util.spec_from_file_location(
    "structured", os.path.join(REPO, "tools", "build-structured-data.py"))
structured = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(structured)

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def pick(value, lang):
    """Un champ bilingue est soit une chaîne simple, soit {fr, en}."""
    if isinstance(value, dict):
        return value.get(lang) or value.get("fr") or value.get("en") or ""
    return value or ""


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def long_date(value, lang):
    """Rend ce qu'on sait : 2026, mai 2026, ou 2 mai 2026."""
    if not value:
        return ""
    parts = value.split("-")
    year = parts[0]
    if len(parts) == 1:
        return year
    month = int(parts[1])
    if len(parts) == 2:
        return ("%s %s" % (MONTHS_EN[month - 1], year) if lang == "en"
                else "%s %s" % (MONTHS_FR[month - 1], year))
    day = int(parts[2])
    return ("%s %d, %s" % (MONTHS_EN[month - 1], day, year) if lang == "en"
            else "%d %s %s" % (day, MONTHS_FR[month - 1], year))


def date_phrase(ev, lang):
    start, end = ev.get("startDate") or "", ev.get("endDate") or ""
    if not start:
        return ""
    if end and end != start:
        return "%s – %s" % (long_date(start, lang), long_date(end, lang))
    return long_date(start, lang)


def score(ev):
    specs = ev.get("specs") or {}
    return (sum(1 for f in FIELDS if pick(ev.get(f), "fr").strip())
            + sum(1 for f in SPEC_FIELDS if pick(specs.get(f), "fr").strip()))


def qualifies(ev, by_id):
    if score(ev) < SCORE_MIN:
        return False
    if ev.get("kind") == "stop":
        parent = by_id.get(ev.get("circuit"))
        # L'étape est déjà détaillée sur la page de son circuit.
        if parent and qualifies_circuit(parent):
            return False
    return True


def qualifies_circuit(ev):
    return ev.get("kind") == "circuit" and score(ev) >= SCORE_MIN


def clamp_title(name):
    """Google coupe un titre autour de 60 caractères."""
    full = "%s — Pied Marin Fishing" % name
    if len(full) <= 62:
        return full
    if len(name) <= 62:
        return name
    cut = name[:59].rsplit(" ", 1)[0]
    return cut + "…"


def build_description(ev, lang):
    """Assemble des phrases jusqu'à tenir entre 110 et 165 caractères."""
    name = pick(ev.get("name"), lang)
    bits = []
    when = date_phrase(ev, lang)
    where = pick(ev.get("location"), lang) or pick(ev.get("region"), lang)
    head = name
    if when:
        head += (" on " if lang == "en" else " le ") + when
    if where:
        head += (" at " if lang == "en" else " à ") + where
    bits.append(head.rstrip(".") + ".")

    specs = ev.get("specs") or {}
    sp = pick(ev.get("species"), lang)
    if sp:
        bits.append(sp + ".")
    for field in ("fee", "teamSize", "format"):
        value = pick(specs.get(field), lang)
        if value:
            bits.append(value + ".")
    org = pick(ev.get("organizer"), lang)
    if org:
        bits.append(("Organized by " if lang == "en" else "Organisé par ") + org + ".")
    notes = pick(ev.get("notes"), lang)
    if notes:
        bits.append(notes)

    out = ""
    for bit in bits:
        candidate = (out + " " + bit).strip()
        if len(out) >= 110:
            break
        out = candidate
    out = re.sub(r"\s+", " ", out).strip()
    if len(out) > 165:
        out = out[:164].rsplit(" ", 1)[0].rstrip(",;:.") + "…"
    return out


def bilingual(tag, value, cls="", extra=""):
    """Un élément dont le français est visible et l'anglais en attribut."""
    fr, en = pick(value, "fr"), pick(value, "en")
    if not fr and not en:
        return ""
    attrs = ' class="%s"' % cls if cls else ""
    if extra:
        attrs += " " + extra
    if en and en != fr:
        attrs += ' data-en="%s"' % esc(en)
    return "<%s%s>%s</%s>" % (tag, attrs, esc(fr), tag)


SPEC_ROWS = [("fee", "spec.fee", "💵", True), ("teamSize", "spec.teamSize", "👥", True),
             ("maxTeams", "spec.maxTeams", "🚩", False), ("hours", "spec.hours", "⏱", False),
             ("deadline", "spec.deadline", "📋", False), ("format", "spec.format", "🎯", False)]

NAV = """
<header class="site-header">
  <nav class="nav">
    <a class="brand" href="index.html">
      <img src="assets/img/logo.png" class="brand-logo" data-i18n-alt="brand.alt" alt="Écusson de l'équipe Pied Marin Fishing : un brochet au-dessus de l'eau">
      <span>Pied Marin Fishing<span class="brand-sub" data-i18n="brand.sub">Équipe Québec</span></span>
    </a>
    <ul class="nav-links">
      <li><a href="index.html" data-i18n="nav.home">Accueil</a></li>
      <li><a href="team.html" data-i18n="nav.team">Équipe</a></li>
      <li><a href="catches.html" data-i18n="nav.catches">Prises</a></li>
      <li><a href="history.html" data-i18n="nav.history">Résultats</a></li>
      <li><a href="calendar.html" data-i18n="nav.calendar">Notre calendrier</a></li>
      <li><a href="tournaments.html" aria-current="page" data-i18n="nav.guide">Tournois</a></li>
      <li><a href="social.html" data-i18n="nav.social">Réseaux</a></li>
      <li><a href="sponsors.html" data-i18n="nav.sponsors">Commanditaires</a></li>
    </ul>
    <div class="nav-actions">
      <div class="lang-switch" role="group" data-i18n-aria-label="lang.label" aria-label="Langue">
        <button type="button" data-lang="fr" aria-pressed="true">FR</button>
        <button type="button" data-lang="en" aria-pressed="false">EN</button>
      </div>
      <button class="nav-toggle" aria-expanded="false" data-i18n="nav.menu">☰ Menu</button>
    </div>
  </nav>
</header>
"""

FOOTER = """
<footer class="site-footer">
  <div class="container">
    <div class="footer-bottom">
      <span data-i18n="footer.copyright">© <span data-year></span> Pied Marin Fishing</span>
      <span><a href="index.html" data-i18n="footer.backHome">Retour à l'accueil</a></span>
    </div>
  </div>
</footer>

<script src="assets/js/analytics.js"></script>
<script src="assets/js/main.js"></script>
<script src="assets/js/util.js"></script>
<script src="assets/js/i18n.js"></script>
<script src="assets/js/tournament-page.js"></script>
</body>
</html>
"""


def specs_html(ev, ui):
    specs = ev.get("specs") or {}
    rows = []
    for field, key, icon, always in SPEC_ROWS:
        value = specs.get(field)
        # Même règle que dans le répertoire : « Format : Non publié » n'a aucun
        # sens sur un salon, où il n'y a pas d'équipe.
        if not pick(value, "fr") and not (always and ev.get("kind") != "show"):
            continue
        if not pick(value, "fr"):
            value = {"fr": ui["fr"]["spec.notPublished"], "en": ui["en"]["spec.notPublished"]}
            cls = "event-spec spec-empty"
        else:
            cls = "event-spec"
        label = {"fr": ui["fr"][key], "en": ui["en"][key]}
        rows.append(
            '<div class="%s">'
            '<span class="event-spec-label"><span aria-hidden="true">%s</span> %s</span>'
            "%s</div>"
            % (cls, icon, bilingual("span", label), bilingual("span", value, "event-spec-value")))
    for field, key in (("organizer", "tp.organizer"), ("species", "tp.species"),
                       ("location", "tp.location"), ("region", "tp.region")):
        if not pick(ev.get(field), "fr"):
            continue
        label = {"fr": ui["fr"][key], "en": ui["en"][key]}
        rows.append('<div class="event-spec"><span class="event-spec-label">%s</span>%s</div>'
                    % (bilingual("span", label), bilingual("span", ev[field], "event-spec-value")))
    return "".join(rows)


def stop_rows(stops):
    out = []
    for st in stops:
        when = {"fr": date_phrase(st, "fr"), "en": date_phrase(st, "en")}
        out.append(
            '<li class="tp-stop">%s%s%s</li>'
            % (bilingual("strong", st.get("name")),
               bilingual("span", when, "tp-stop-date") if pick(when, "fr") else "",
               bilingual("span", st.get("location"), "tp-stop-place")))
    return "".join(out)


def section(title, body, alt=False, key=None):
    head = '<div class="section-head">%s</div>' % bilingual(
        "h2", title, extra=('data-i18n="%s"' % key) if key else "")
    return ('<section%s><div class="container">%s%s</div></section>'
            % (' class="alt"' if alt else "", head, body))


def related(ev, kept):
    """Quatre fiches voisines, pour que les pages se tiennent entre elles.

    Vingt-deux pages sans liens entre elles sont vingt-deux culs-de-sac : un
    lecteur qui atterrit sur une fiche depuis Google n'a nulle part où aller,
    et les moteurs ne voient pas de grappe. On propose donc d'abord la même
    région, puis la même espèce, puis n'importe quoi d'autre — jamais la page
    courante, jamais deux fois la même.
    """
    def same(field, other):
        return (pick(ev.get(field), "fr").strip()
                and pick(other.get(field), "fr") == pick(ev.get(field), "fr"))

    pool = [e for e in kept if e["id"] != ev["id"]]
    ranked = ([e for e in pool if same("region", e)]
              + [e for e in pool if same("species", e) and not same("region", e)]
              + pool)
    out, seen = [], set()
    for e in ranked:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        out.append(e)
        if len(out) == 4:
            break
    return out


def render(ev, by_id, stops_of, history, ui, kept):
    fr_name = pick(ev.get("name"), "fr")
    title = {"fr": clamp_title(fr_name), "en": clamp_title(pick(ev.get("name"), "en"))}
    desc = {"fr": build_description(ev, "fr"), "en": build_description(ev, "en")}
    url = "%s/tournois/%s.html" % (SITE, ev["id"])
    when = {"fr": date_phrase(ev, "fr") or ui["fr"]["tp.dateTBD"],
            "en": date_phrase(ev, "en") or ui["en"]["tp.dateTBD"]}

    body = [section({"fr": ui["fr"]["tp.infoTitle"], "en": ui["en"]["tp.infoTitle"]},
                    '<div class="event-specs tp-specs">%s</div>' % specs_html(ev, ui))]

    if pick(ev.get("notes"), "fr"):
        body.append(section({"fr": ui["fr"]["tp.aboutTitle"], "en": ui["en"]["tp.aboutTitle"]},
                            bilingual("p", ev["notes"], "tp-notes"), alt=True))

    stops = stops_of.get(ev["id"]) or []
    if stops:
        stops = sorted(stops, key=lambda s: s.get("startDate") or "9999")
        body.append(section({"fr": ui["fr"]["tp.stopsTitle"], "en": ui["en"]["tp.stopsTitle"]},
                            '<ul class="tp-stops">%s</ul>' % stop_rows(stops)))

    parent = by_id.get(ev.get("circuit")) if ev.get("kind") == "stop" else None
    if parent:
        inner = bilingual("strong", parent.get("name"))
        if qualifies_circuit(parent):
            inner = '<a href="tournois/%s.html">%s</a>' % (esc(parent["id"]), inner)
        body.append(section({"fr": ui["fr"]["tp.partOfTitle"], "en": ui["en"]["tp.partOfTitle"]},
                            '<p class="tp-parent">%s</p>' % inner, alt=True))

    ours = [h for h in history if h.get("id", "").startswith(ev["id"])
            or pick(h.get("name"), "fr") == fr_name]
    if ours:
        rows = "".join(
            '<li>%s%s</li>' % (
                bilingual("strong", {"fr": "%s — %s%s" % (
                    pick(h.get("name"), "fr"), h.get("placement", "?"),
                    "e sur %s" % h["fieldSize"] if h.get("fieldSize") else "e"),
                    "en": "%s — %s%s" % (
                    pick(h.get("name"), "en"), h.get("placement", "?"),
                    " of %s" % h["fieldSize"] if h.get("fieldSize") else "")}),
                bilingual("span", h.get("notes"), "tp-history-note"))
            for h in ours)
        body.append(section({"fr": ui["fr"]["tp.ourResult"], "en": ui["en"]["tp.ourResult"]},
                            '<ul class="tp-history">%s</ul>' % rows))

    peers = related(ev, kept)
    if peers:
        rows = "".join(
            '<li><a href="tournois/%s.html">%s%s</a></li>'
            % (esc(p["id"]), bilingual("span", p.get("name")),
               bilingual("span", {"fr": date_phrase(p, "fr") or pick(p.get("region"), "fr"),
                                  "en": date_phrase(p, "en") or pick(p.get("region"), "en")},
                         "tp-related-meta"))
            for p in peers)
        body.append(section({"fr": ui["fr"]["tp.related"], "en": ui["en"]["tp.related"]},
                            '<ul class="tp-related">%s</ul>' % rows, alt=True))

    cta = []
    if (ev.get("link") or "").startswith("http"):
        cta.append('<a class="btn btn-teal" href="%s" target="_blank" rel="noopener">%s</a>'
                   % (esc(ev["link"]),
                      bilingual("span", {"fr": ui["fr"]["tp.organizerBtn"],
                                         "en": ui["en"]["tp.organizerBtn"]})))
    cta.append('<a class="btn btn-ghost" href="tournaments.html">%s</a>'
               % bilingual("span", {"fr": ui["fr"]["tp.backToGuide"],
                                    "en": ui["en"]["tp.backToGuide"]}))
    body.append('<section><div class="container"><div class="callout">%s'
                '<div class="callout-actions">%s</div></div></div></section>'
                % (bilingual("p", {"fr": ui["fr"]["tp.confirm"], "en": ui["en"]["tp.confirm"]}),
                   "".join(cta)))

    ld = structured.event_json(ev)
    ld_block = ""
    if ld:
        ld["url"] = url
        ld = dict(ld, **{"@context": "https://schema.org"})
        ld_block = ('<script type="application/ld+json">\n%s\n</script>'
                    % json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"))

    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Page générée par tools/build-tournament-pages.py — ne pas modifier à la
     main : la prochaine exécution écraserait tout. Corrige plutôt le tournoi
     dans data/quebec-tournaments.json, puis relance le script.
     <base> ramène à la racine les chemins relatifs du menu et le fetch de
     data/i18n.json, cette page vivant un dossier plus bas. -->
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
%(ld)s
</head>
<body>
%(nav)s
<div class="page-header">
  <div class="container">
    <span class="kicker" data-i18n="tp.kicker">Répertoire des tournois</span>
    %(h1)s
    <p class="tp-when">%(when)s</p>
  </div>
</div>

%(body)s
%(footer)s""" % {
        "title_fr": esc(title["fr"]), "title_en": esc(title["en"]),
        "desc_fr": esc(desc["fr"]), "desc_en": esc(desc["en"]),
        "url": url, "site": SITE, "ld": ld_block, "nav": NAV, "footer": FOOTER,
        "h1": bilingual("h1", ev.get("name")),
        "when": bilingual("span", when),
        "body": "\n\n".join(body),
    }


if __name__ == "__main__":
    events = load("quebec-tournaments.json")
    history = load("tournament-history.json")
    i18n = load("i18n.json")
    ui = {"fr": i18n["fr"], "en": i18n["en"]}
    by_id = {e["id"]: e for e in events}
    stops_of = {}
    for e in events:
        if e.get("kind") == "stop" and e.get("circuit"):
            stops_of.setdefault(e["circuit"], []).append(e)

    kept = [e for e in events if qualifies(e, by_id)]
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    existing = {f for f in os.listdir(OUT_DIR) if f.endswith(".html")}
    written = set()
    for ev in kept:
        name = "%s.html" % ev["id"]
        with io.open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(render(ev, by_id, stops_of, history, ui, kept))
        written.add(name)
    # Un tournoi retiré du répertoire ne doit pas laisser sa fiche en ligne.
    for stale in sorted(existing - written):
        os.remove(os.path.join(OUT_DIR, stale))
        print("  supprimée :", stale)

    index_path = os.path.join(REPO, "data", "tournament-pages.json")
    with io.open(index_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(sorted(e["id"] for e in kept), ensure_ascii=False, indent=2) + "\n")

    print("%d fiches écrites dans tournois/ (%d tournois au répertoire)"
          % (len(kept), len(events)))
    for ev in sorted(events, key=lambda e: -score(e)):
        mark = "✓" if ev in kept else " "
        print("  %s %-46s %2d/10  %s" % (mark, pick(ev.get("name"), "fr")[:46],
                                         score(ev), ev.get("kind") or "—"))
