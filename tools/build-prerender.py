# -*- coding: utf-8 -*-
"""Écrit en dur, dans les pages racine, les listes que le JavaScript construit.

Sept pages racine ne portaient presque rien avant l'exécution de leur script :
sorties.html comptait 47 mots, team.html 65, catches.html 86. Les listes —
l'équipe, les sorties, les prises, les espèces, les résultats, le calendrier —
n'existaient qu'après le fetch d'un fichier de data/. Un robot qui ne lance
pas le JavaScript voyait un titre et un conteneur vide.

Ce script écrit la version française de ces listes DANS le conteneur, au
moment du commit, comme sync-html-fallbacks.py le fait pour les textes :

    python3 tools/build-prerender.py          # écrit
    python3 tools/build-prerender.py --check  # sort en code 1 si une page a dérivé

Rien ne change côté navigateur. Chaque script remplace le contenu de son
conteneur par innerHTML au premier rendu, comme avant : la version écrite ici
est remplacée, jamais doublée, et les filtres, la bascule de langue et les
sauts d'ancre (openHashTarget, openHashGroup, jumpToCatch) travaillent sur ce
que le script vient de rendre. Le HTML écrit reprend les mêmes classes que le
JavaScript pour que le premier affichage ne saute pas.

Ce qui n'est PAS écrit, et pourquoi :

- saison.html et le bandeau « Ce qui presse » : une pastille « ouvert » est
  une affirmation légale calculée le jour même (season.js, trois états). Une
  copie figée au commit dirait « ouvert » le lendemain de la fermeture.
- les règles générales d'especes.html : reg-guard et initGeneralRules les
  remplacent passé staleAfterMonths. Une copie dans le HTML survivrait à la
  péremption pour tout lecteur sans JavaScript.
- sur le calendrier, tout ce qui dépend du jour : « Passé », le décompte des
  inscriptions, le bouton .ics. La carte écrite ne dit que ce que les données
  disent — nom, date, lieu, espèce, note.
- la relève : prénom JAMAIS. Le nom affiché est celui de data/next-gen.json
  (des initiales), l'identifiant de l'entrée n'est écrit nulle part, et le
  jour exact de la prise est tronqué au mois, comme dans next-gen.js.

À relancer après toute modification de data/, avant sync-html-fallbacks.py.
"""
import importlib.util
import io
import json
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    "pages", os.path.join(REPO, "tools", "build-tournament-pages.py"))
pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages)

esc, pick, long_date, family = pages.esc, pages.pick, pages.long_date, pages.family

LANG = "fr"
NOTE = "<!-- Pré-rendu par tools/build-prerender.py : le script de la page le remplace au chargement. -->"


def load(name, default=None):
    try:
        with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
            return json.load(fh)
    except (IOError, OSError, ValueError):
        if default is None:
            raise
        return default


UI = load("i18n.json")["fr"]
VARIANTS = load("image-variants.json", {})


def t(key, **vars):
    """t() d'i18n.js, en français. Une clé absente arrête le script : la page
    afficherait le nom de la clé, ce qui se voit moins qu'un échec ici."""
    if key not in UI:
        raise SystemExit("clé i18n absente : %s" % key)
    raw = UI[key]
    return re.sub(r"\{(\w+)\}", lambda m: str(vars[m.group(1)]) if m.group(1) in vars
                  else m.group(0), raw)


def plural(base, n):
    """En français, 0 et 1 sont au singulier — la règle de plural() d'i18n.js."""
    return t("%s.%s" % (base, "one" if n < 2 else "other"), n=n)


def tr(value):
    return pick(value, LANG)


def fold(text):
    """Clé de tri insensible aux accents, comme localeCompare en français."""
    return "".join(c for c in unicodedata.normalize("NFD", text or "")
                   if unicodedata.category(c) != "Mn").lower()


def ordinal(n):
    return "1re" if n == 1 else "%de" % n


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def placement_of(placement, field):
    """« 102e sur 309 » — placementOf() d'util.js."""
    if not is_num(placement):
        return ""
    rank = ordinal(placement)
    return "%s %s" % (rank, t("history.of", n=field)) if is_num(field) else rank


def top_percent(placement, field):
    if not is_num(placement) or not is_num(field) or field < 1:
        return None
    return max(1, -(-placement * 100 // field))


def img_attrs(src, sizes):
    """PMF_IMG.attrs() : un srcset seulement si les variantes existent."""
    widths = VARIANTS.get(src)
    if not widths or len(widths) < 2:
        return ""
    stem, ext = os.path.splitext(src)
    top = max(widths)
    liste = ", ".join("%s %dw" % (src if w == top else "%s-%d%s" % (stem, w, ext), w)
                      for w in widths)
    return ' srcset="%s" sizes="%s"' % (esc(liste), esc(sizes))


def date_parts(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    bits = raw.split("-")
    try:
        year = int(bits[0])
    except ValueError:
        return None
    month = int(bits[1]) - 1 if len(bits) > 1 and bits[1].isdigit() else None
    day = int(bits[2]) if len(bits) > 2 and bits[2].isdigit() else None
    return year, month, day


ABBR = ["JAN", "FÉV", "MARS", "AVR", "MAI", "JUIN",
        "JUIL", "AOÛT", "SEPT", "OCT", "NOV", "DÉC"]


def date_badge(value, tbd):
    """dateBadgeHTML() d'util.js."""
    p = date_parts(value)
    if not p:
        return '<span class="day date-tbd">%s</span>' % esc(tbd)
    year, month, day = p
    if month is not None and day is not None:
        return ('<span class="month">%s</span><span class="day">%d</span>'
                '<span class="year">%d</span>' % (ABBR[month], day, year))
    if month is not None:
        return '<span class="month">%s</span><span class="day year-only">%d</span>' % (
            ABBR[month], year)
    return '<span class="day year-only">%d</span>' % year


MEASURE_RE = re.compile(r'([\d]+(?:[.,][\d]+)?)\s*(po|lb|kg|cm|in|"|″)', re.I)


def parse_measure(text):
    m = MEASURE_RE.search(str(text or ""))
    if not m:
        return None
    unit = m.group(2).lower()
    return float(m.group(1).replace(",", ".")), ("po" if unit in ('"', "″") else unit)


# ----------------------------------------------------------------- données

MEMBERS = load("team-members.json")
MEMBER_BY_ID = {m["id"]: m for m in MEMBERS}
BOATS = load("boats.json")
ALL_CATCHES = [c for c in load("catches.json") if c]
CATCH_PAGES = set(load("catch-pages.json", []))
TOURNAMENT_PAGES = set(load("tournament-pages.json", []))


def history_rows():
    """PMF_HISTORY.load() : la plus récente d'abord, l'ordre du fichier à égalité."""
    return sorted(load("tournament-history.json"), key=lambda r: r.get("date") or "",
                  reverse=True)


def wall_catches():
    """PMF_CATCHES.load() : le mur seulement (showcase !== false), la vedette en
    tête, puis de la plus récente à la plus ancienne."""
    rows = [c for c in ALL_CATCHES if c.get("showcase") is not False]
    rows.sort(key=lambda c: c.get("date") or "", reverse=True)
    rows.sort(key=lambda c: not c.get("featured"))
    return rows


def summarize(rows):
    """PMF_HISTORY.summarize()."""
    placements = [r["placement"] for r in rows if is_num(r.get("placement"))]
    best_row = None
    for r in rows:
        if is_num(r.get("placement")) and (best_row is None
                                           or r["placement"] < best_row["placement"]):
            best_row = r
    best_figure = None
    for r in rows:
        f = (r.get("figures") or [None])[0]
        if not f:
            continue
        txt = re.sub(r"[^\d.]", "", tr(f.get("value")).replace(",", "."))
        try:
            n = float(txt)
        except ValueError:
            continue
        if best_figure is None or n > best_figure[0]:
            best_figure = (n, f)
    return {
        "events": len(rows),
        "best": min(placements) if placements else None,
        "bestField": best_row.get("fieldSize") if best_row and is_num(best_row.get("fieldSize")) else None,
        "top3": len([p for p in placements if p <= 3]),
        "seasons": len({(r.get("date") or "")[:4] for r in rows if (r.get("date") or "")[:4]}),
        "bestFigure": best_figure[1] if best_figure else None,
    }


# ------------------------------------------------------------------ équipe

def team_grid():
    results = history_rows()
    wall = wall_catches()
    cards = []
    for m in MEMBERS:
        name = tr(m.get("name")) or "?"
        initials = str(m.get("initials") or name)[:2].upper()
        role = tr(m.get("role"))
        if m.get("photo"):
            photo = ('<div class="member-photo has-photo"><img class="member-photo-img" src="%s"%s '
                     'alt="%s" loading="lazy" width="900" height="1200"></div>'
                     % (esc(m["photo"]), img_attrs(m["photo"], "(max-width: 560px) 90vw, (max-width: 1000px) 46vw, 346px"),
                        esc(tr(m.get("photoAlt")) or name)))
        else:
            photo = '<div class="member-photo"><span class="member-initials">%s</span></div>' % esc(initials)
        specs = m.get("specs") or {}
        rows = "".join(
            '<div class="spec-row"><dt><span class="spec-icon" aria-hidden="true">%s</span>%s</dt>'
            '<dd>%s</dd></div>' % (icon, esc(t(key)), esc(tr(specs.get(field))))
            for field, key, icon in (("homeWater", "team.spec.homeWater", "🌊"),
                                     ("species", "team.spec.species", "🐟"))
            if tr(specs.get(field)))
        mine = [r for r in results if m.get("id") in (r.get("members") or [])]
        s = summarize(mine)
        bits = ["<span><b>%d</b> %s</span>" % (s["events"], esc(plural("team.record.events", s["events"])))]
        if s["best"]:
            bits.append("<span><b>%s</b> %s</span>" % (esc(placement_of(s["best"], s["bestField"])),
                                                       esc(t("team.record.best"))))
        if s["top3"]:
            bits.append("<span><b>%d</b> %s</span>" % (s["top3"], esc(t("team.record.top3"))))
        caught = [c for c in wall if c.get("angler") == m.get("id")]
        if caught:
            bits.append("<span><b>%d</b> %s</span>" % (len(caught), esc(plural("team.catchCount", len(caught)))))
        link = ('<a class="member-history-link member-profile-link" href="pecheurs/%s.html">%s</a>'
                % (esc(m["id"]), esc(t("team.viewProfile")))) if m.get("id") else ""
        cards.append(
            '<div class="member-card">%s<div class="member-body">%s<h2>%s</h2>'
            '<dl class="member-specs">%s</dl><div class="member-record">%s</div>%s</div></div>'
            % (photo, '<span class="member-role">%s</span>' % esc(role) if role else "",
               esc(name), rows, "".join(bits), link))
    return "\n".join(cards)


def nextgen_list():
    """La relève, comme next-gen.js : des initiales, la relation, le mois.

    Jamais l'identifiant de l'entrée (c'est un prénom), jamais de jour exact.
    """
    kids = load("next-gen.json", [])
    by_id = {c.get("id"): c for c in wall_catches()}
    out = []
    for k in kids if isinstance(kids, list) else []:
        name, relation = tr(k.get("name")), tr(k.get("relation"))
        title = name or relation
        if not title:
            continue
        badge = ('<span class="nextgen-initial">%s</span>' % esc(name[:1].upper()) if name
                 else '<span class="nextgen-initial nextgen-sprout" aria-hidden="true">🌱</span>')
        parent = ""
        if name and relation:
            parent = ('<a class="nextgen-parent" href="pecheurs/%s.html">%s</a>'
                      % (esc(k["parent"]), esc(relation)) if k.get("parent")
                      else '<span class="nextgen-parent">%s</span>' % esc(relation))
        status = t("team.nextGen.status.%s" % k["status"]) if k.get("status") else ""
        first = by_id.get(k.get("catch")) if k.get("catch") else None
        first_line = ""
        if first:
            bits = [b for b in (tr(first.get("species")),
                                long_date((first.get("date") or "")[:7], LANG)) if b]
            first_line = '<p class="nextgen-first"><b>%s</b> %s</p>' % (
                esc(t("team.nextGen.firstCatch")), esc(" — ".join(bits)))
        story = tr(k.get("story"))
        out.append(
            '<article class="nextgen-card"><div class="nextgen-badge">%s</div><div class="nextgen-body">'
            '%s<h3>%s</h3>%s%s%s</div></article>'
            % (badge, '<span class="nextgen-status">%s</span>' % esc(status) if status else "",
               esc(title), parent, '<p class="nextgen-story">%s</p>' % esc(story) if story else "",
               first_line))
    return "\n".join(out)


def boat_list():
    out = []
    for b in BOATS:
        name = tr(b.get("name")) or "—"
        specs = b.get("specs") or {}
        rows = "".join('<div class="spec-row"><dt>%s</dt><dd>%s</dd></div>'
                       % (esc(t(key)), esc(tr(specs.get(field))))
                       for field, key in (("engine", "boats.spec.engine"),
                                          ("electronics", "boats.spec.electronics"))
                       if tr(specs.get(field)))
        skipper, owner = MEMBER_BY_ID.get(b.get("skipper")), MEMBER_BY_ID.get(b.get("owner"))

        def crew(m):
            return '<a href="pecheurs/%s.html">%s</a>' % (esc(m["id"]), esc(tr(m.get("name"))))
        crew_row = ""
        if skipper and owner and skipper["id"] == owner["id"]:
            crew_row = '<div class="boat-skipper">%s %s</div>' % (esc(t("boats.skipperOwner")), crew(skipper))
        else:
            parts = []
            if skipper:
                parts.append("%s %s" % (esc(t("boats.skipper")), crew(skipper)))
            if owner:
                parts.append("%s %s" % (esc(t("boats.owner")), crew(owner)))
            if parts:
                crew_row = '<div class="boat-skipper">%s</div>' % "<br>".join(parts)
        status = (b.get("restoration") or {}).get("status") or ""
        badge = ('<span class="boat-status">%s</span>' % esc(t("boats.restoring"))
                 if status == "restoration" else
                 '<span class="boat-status is-done">%s</span>' % esc(t("boats.restored"))
                 if status in ("restored", "done") else "")
        link = ('<a class="member-history-link" href="bateaux/%s.html">%s</a>'
                % (esc(b["id"]), esc(t("boats.viewPage")))) if b.get("id") else ""
        photo = ('<img src="%s"%s alt="%s" class="boat-photo-img">'
                 % (esc(b["image"]), img_attrs(b["image"], "(max-width: 760px) 92vw, 420px"),
                    esc(t("boats.photoAlt", name=name)))) if b.get("image") else ""
        out.append('<article class="boat-card"><div class="boat-photo">%s</div><div class="boat-body">'
                   '%s<h3>%s</h3><dl class="member-specs boat-specs">%s</dl>%s%s</div></article>'
                   % (photo, badge, esc(name), rows, crew_row, link))
    return "\n".join(out)


# ----------------------------------------------------------------- sorties

def trips():
    rows = load("trips.json", [])
    videos = {v.get("videoId"): v for v in (load("videos.json", {}) or {}).get("videos") or []}
    boats = {b["id"]: b for b in BOATS}
    catch_by_id = {c.get("id"): c for c in ALL_CATCHES}
    ordered = sorted(rows, key=lambda r: r.get("date") or "", reverse=True)

    def block(key, body):
        return ('<div class="trip-block"><h3 class="trip-block-title">%s</h3>%s</div>'
                % (esc(t(key)), body)) if body else ""

    def catch_html(cid):
        c = catch_by_id.get(cid)
        if not c:
            return ""
        photo = (c.get("media") or {}).get("src") or ""
        who = MEMBER_BY_ID.get(c.get("angler"))
        bits = " · ".join(b for b in (tr(c.get("measure")), tr(who.get("name")) if who else "") if b)
        inner = (('<img class="trip-catch-thumb" src="%s"%s alt="" loading="lazy" width="160" height="120">'
                  % (esc(photo), img_attrs(photo, "(max-width: 700px) 45vw, 160px"))) if photo else "")
        inner += ('<span class="trip-catch-body"><span class="trip-catch-species">%s</span>%s</span>'
                  % (esc(tr(c.get("species"))),
                     '<span class="trip-catch-meta">%s</span>' % esc(bits) if bits else ""))
        if cid in CATCH_PAGES:
            return '<a class="trip-catch" href="prises/%s.html">%s</a>' % (esc(cid), inner)
        return '<figure class="trip-catch trip-catch-flat">%s</figure>' % inner

    def video_html(vid):
        v = videos.get(vid)
        if not v:
            return ""
        return ('<a class="trip-video" href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener">'
                '<img class="trip-video-thumb" loading="lazy" width="320" height="180" alt="" '
                'src="https://i.ytimg.com/vi/%s/mqdefault.jpg"><span>%s</span></a>'
                % (esc(vid), esc(vid), esc(tr(v.get("title")))))

    out = []
    for trip in ordered:
        boat = boats.get(trip.get("boat"))
        chips = "".join('<a class="angler-chip" href="pecheurs/%s.html">%s</a>'
                        % (esc(i), esc(tr(MEMBER_BY_ID[i].get("name"))))
                        for i in trip.get("members") or [] if i in MEMBER_BY_ID)
        crew = ('<div class="trip-crew">%s</div>' % chips if chips else "")
        if boat:
            crew += '<p class="trip-boat"><a href="bateaux/%s.html">%s</a></p>' % (
                esc(boat["id"]), esc(tr(boat.get("name"))))
        caught = "".join(catch_html(c) for c in trip.get("catches") or [])
        vids = "".join(video_html(v) for v in trip.get("videos") or [])
        story, conditions = tr(trip.get("story")), tr(trip.get("conditions"))
        n = len(trip.get("catches") or [])
        out.append(
            '<article class="trip" id="t-%s"><header class="trip-head"><p class="trip-when">%s</p>'
            '<h2>%s</h2>%s%s</header>%s%s%s%s%s</article>'
            % (esc(trip.get("id") or ""), esc(long_date(trip.get("date"), LANG)), esc(tr(trip.get("title"))),
               '<p class="trip-water">%s</p>' % esc(tr(trip.get("water"))) if tr(trip.get("water")) else "",
               '<p class="trip-tally">%s</p>' % esc(plural("trips.catchCount", n)) if n else "",
               block("trips.crew", crew),
               block("trips.conditions", "<p>%s</p>" % esc(conditions) if conditions else ""),
               '<div class="trip-story"><p>%s</p></div>' % esc(story) if story else "",
               block("trips.caught", '<div class="trip-catches">%s</div>' % caught if caught else ""),
               block("trips.video", vids)))
    return "\n".join(out), plural("trips.count", len(ordered))


# ------------------------------------------------------------------ prises

def catch_photos(c):
    media = c.get("media") or {}
    photos = []
    if media.get("type") == "image" and media.get("src"):
        photos.append((media["src"], media.get("alt")))
    for g in c.get("gallery") or []:
        src = g if isinstance(g, str) else (g or {}).get("src")
        if src:
            photos.append((src, g.get("alt") if isinstance(g, dict) else None))
    return photos


def catches_page():
    """La vedette, le temple de la renommée et la grille — catches.js sans filtre."""
    events = {e.get("id"): e for e in load("tournament-history.json")}
    rows = wall_catches()

    def describe(c):
        angler = MEMBER_BY_ID.get(c.get("angler"))
        angler_name = tr(angler.get("name")) if angler else (tr(c.get("anglerName")) or c.get("angler") or "")
        when = long_date(c.get("date"), LANG)
        ev = events.get(c.get("event")) if c.get("event") else None
        facts = []
        if when:
            facts.append("📅 " + when)
        if tr(c.get("water")):
            facts.append("📍 " + tr(c.get("water")))
        if ev:
            facts.append("🏆 " + tr(ev.get("name")))
        species = tr(c.get("species")) or "—"
        return {"angler": angler, "name": angler_name, "facts": facts, "species": species,
                "measure": tr(c.get("measure")), "notes": tr(c.get("notes")),
                "alt": " — ".join(b for b in (species, angler_name, tr(c.get("water"))) if b)}

    def media_html(c, d, sizes="(max-width: 760px) 92vw, 346px"):
        photos = catch_photos(c)
        if photos:
            badge = ('<span class="catch-photo-count" aria-hidden="true">1/%d</span>' % len(photos)
                     if len(photos) > 1 else "")
            src, alt = photos[0]
            return ('<button type="button" class="catch-media-btn" data-catch="%s" data-photo="0" aria-label="%s">'
                    '<img class="catch-media-img" src="%s"%s alt="%s" loading="lazy">%s</button>'
                    % (esc(c["id"]), esc(t("catches.openPhoto")), esc(src), img_attrs(src, sizes),
                       esc(tr(alt) or d["alt"]), badge))
        media = c.get("media") or {}
        if media.get("type") == "youtube" and media.get("videoId"):
            return ('<button type="button" class="catch-facade" data-video="%s" aria-label="%s">'
                    '<img class="catch-media-img" alt="" loading="lazy" src="https://i.ytimg.com/vi/%s/hqdefault.jpg">'
                    '<span class="video-play" aria-hidden="true"></span></button>'
                    % (esc(media["videoId"]), esc(t("catches.playVideo")), esc(media["videoId"])))
        return '<div class="catch-empty-media"><span>%s</span></div>' % esc(t("catches.noMedia"))

    def body_html(c, d, tag):
        chip = ""
        if d["name"]:
            chip = ('<a class="angler-chip" href="history.html?member=%s">%s</a>' % (esc(d["angler"]["id"]), esc(d["name"]))
                    if d["angler"] else '<span class="angler-chip">%s</span>' % esc(d["name"]))
        release = ""
        if isinstance(c.get("released"), bool):
            release = ('<span class="catch-release">%s</span>' % esc(t("catch.released")) if c["released"]
                       else '<span class="catch-release is-kept">%s</span>' % esc(t("catch.kept")))
        media = c.get("media") or {}
        video = ""
        if media.get("type") != "youtube" and media.get("videoId"):
            video = ('<a class="catch-video-link" href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener">'
                     '<span aria-hidden="true">▶</span> %s</a>' % (esc(media["videoId"]), esc(t("catches.watchVideo"))))
        story = ('<a class="catch-story-link" href="prises/%s.html">%s</a>' % (esc(c["id"]), esc(t("catches.readStory")))
                 if c.get("id") in CATCH_PAGES else "")
        return ('<div class="catch-head"><%s>%s</%s>%s</div>%s%s%s%s%s%s'
                % (tag, esc(d["species"]), tag,
                   '<span class="catch-measure">%s</span>' % esc(d["measure"]) if d["measure"] else "",
                   '<div class="catch-anglers">%s</div>' % chip if chip else "", release,
                   '<div class="catch-facts">%s</div>' % "".join("<span>%s</span>" % esc(f) for f in d["facts"])
                   if d["facts"] else "",
                   '<p class="catch-notes">%s</p>' % esc(d["notes"]) if d["notes"] else "",
                   story, video))

    featured = next((c for c in rows if c.get("featured")), None)
    featured_html = ""
    if featured:
        d = describe(featured)
        featured_html = ('<article class="featured-catch" id="c-%s"><div class="catch-media featured-media">%s'
                         '<span class="featured-flag">%s</span></div><div class="catch-body featured-body">%s</div></article>'
                         % (esc(featured["id"]), media_html(featured, d, "(max-width: 760px) 92vw, 583px"),
                            esc(t("catches.featured")), body_html(featured, d, "h2")))

    # records() : une prise par espèce, la plus grande à unité égale.
    best = {}
    for c in rows:
        parsed = parse_measure(tr(c.get("measure")))
        key = pick(c.get("species"), "fr")
        if not parsed or not key:
            continue
        held = best.get(key)
        if not held or (held[1][1] == parsed[1] and parsed[0] > held[1][0]):
            best[key] = (c, parsed)
    hall = sorted((c for c, _ in best.values()), key=lambda c: fold(tr(c.get("species"))))
    hall_html = ""
    if len(hall) >= 2:
        items = []
        for c in hall:
            d = describe(c)
            photos = catch_photos(c)
            thumb = ('<img class="hall-thumb" src="%s"%s alt="" loading="lazy" width="120" height="90">'
                     % (esc(photos[0][0]), img_attrs(photos[0][0], "72px"))) if photos else ""
            items.append('<button type="button" class="hall-item" data-catch="%s" data-photo="0">%s'
                         '<span class="hall-body"><span class="hall-species">%s</span>'
                         '<span class="hall-measure">%s</span>%s</span></button>'
                         % (esc(c["id"]), thumb, esc(tr(c.get("species"))), esc(tr(c.get("measure"))),
                            '<span class="hall-angler">%s</span>' % esc(d["name"]) if d["name"] else ""))
        hall_html = "\n".join(items)

    grid = "\n".join('<article class="catch-card" id="c-%s"><div class="catch-media">%s</div>'
                   '<div class="catch-body">%s</div></article>'
                   % (esc(c["id"]), media_html(c, describe(c)), body_html(c, describe(c), "h3"))
                   for c in rows if c is not featured)
    return featured_html, hall_html, grid, plural("catches.count", len(rows))


# ---------------------------------------------------------------- espèces

def species_index():
    """La grille d'especes.html, groupée par statut comme species.js.

    Le statut est le statut de conservation écrit par le ministère, pas une
    affirmation sur la saison : il ne périme pas avec le calendrier.
    """
    live = set(load("species-pages.json", []))
    rows = [s for s in load("species.json") if s and s.get("id") in live]

    def fr(v):
        return (v.get("fr") or v.get("en") if isinstance(v, dict) else v) or ""

    groups = [("sportive", "sp.groupSport", True, lambda s: not fr(s.get("status"))),
              ("statut", "sp.groupStatus", False,
               lambda s: fr(s.get("status")) and not re.search("envahissant", fr(s.get("status")), re.I)),
              ("envahissante", "sp.groupInvasive", False,
               lambda s: re.search("envahissant", fr(s.get("status")), re.I))]

    def card(s):
        status = tr(s.get("status"))
        marks = [m for m in s.get("marks") or [] if tr(m.get("value"))][:2]
        return ('<a class="sp-card" href="especes/%s.html"><span class="sp-card-name">%s</span>%s%s%s</a>'
                % (esc(s["id"]), esc(tr(s.get("name"))),
                   '<em class="sp-card-sci">%s</em>' % esc(s["scientificName"]) if s.get("scientificName") else "",
                   '<span class="sp-card-status">%s</span>' % esc(status) if status else "",
                   "".join('<div class="sp-card-mark"><span>%s</span>%s</div>'
                           % (esc(tr(m.get("label"))), esc(tr(m.get("value")))) for m in marks)))

    chips, blocks = [], []
    for gid, key, open_, match in groups:
        members = [s for s in rows if match(s)]
        if not members:
            continue
        chips.append('<a class="sp-chip" href="especes.html#sp-%s">%s <span class="sp-chip-n">%d</span></a>'
                     % (gid, esc(t(key)), len(members)))
        blocks.append('<details class="sp-group" id="sp-%s"%s><summary class="sp-group-head"><h2>%s</h2>'
                      '<span class="sp-group-count">%s</span></summary><p class="tp-notes sp-group-note">%s</p>'
                      '<div class="sp-grid">%s</div></details>'
                      % (gid, " open" if open_ else "", esc(t(key)), esc(plural("sp.groupCount", len(members))),
                         esc(t(key + "Note")), "\n".join(card(s) for s in members)))
    return "\n".join(blocks), "".join(chips), len(chips), t("sp.indexCount", n=len(rows))


# --------------------------------------------------------------- résultats

def history_page():
    rows = history_rows()
    s = summarize(rows)
    if s["top3"] > 0:
        third = (s["top3"], plural("history.stat.top3", s["top3"]))
    elif s["bestFigure"]:
        third = (tr(s["bestFigure"].get("value")), t("history.stat.bestScore"))
    else:
        third = (s["top3"], plural("history.stat.top3", s["top3"]))
    tiles = [(s["events"], plural("history.stat.events", s["events"])),
             (placement_of(s["best"], s["bestField"]) if s["best"] else "—", t("history.stat.best")),
             third,
             (s["seasons"], plural("history.stat.seasons", s["seasons"]))]
    stats = "".join('<div class="stat-card"><div class="num">%s</div><div class="label">%s</div></div>'
                    % (esc(str(n)), esc(label)) for n, label in tiles)

    table = ""
    if len(rows) >= 2:
        head = "".join("<th>%s</th>" % esc(t(k)) for k in
                       ("history.col.season", "history.col.event", "history.col.place", "history.col.score"))
        body = []
        for r in rows:
            pct = top_percent(r.get("placement"), r.get("fieldSize"))
            place = "—"
            if is_num(r.get("placement")):
                place = esc(ordinal(r["placement"]))
                if is_num(r.get("fieldSize")):
                    place += " " + esc(t("history.of", n=r["fieldSize"]))
            first = (r.get("figures") or [None])[0]
            score = tr(first.get("value")) if first else (tr(r.get("weight")) if r.get("weight") else "—")
            body.append("<tr><td>%s</td><td>%s</td><td>%s%s</td><td>%s</td></tr>"
                        % (esc(str(r.get("date") or "")[:4] or "—"), esc(tr(r.get("name"))), place,
                           ' <span class="table-pct">%s</span>' % esc(t("history.topPercent", n=pct)) if pct else "",
                           esc(score)))
        table = ('<table class="record-table"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>'
                 % (head, "".join(body)))

    cards = []
    for r in rows:
        placement, field = r.get("placement"), r.get("fieldSize")
        place = ('<span class="placement %s">%s</span>'
                 % ({1: "gold", 2: "silver", 3: "bronze"}.get(placement, ""), esc(ordinal(placement)))
                 if is_num(placement) else
                 '<span class="placement placement-unknown" title="%s">—</span>' % esc(t("history.resultPending")))
        pct = top_percent(placement, field)
        meta = []
        for value, prefix in ((r.get("location"), "📍 "), (r.get("region"), ""),
                              (r.get("species"), "🎣 "), (r.get("organizer"), "")):
            if value:
                meta.append("<span>%s%s</span>" % (prefix, esc(tr(value))))
        figures = []
        if r.get("weight"):
            figures.append("<span><b>%s</b> %s</span>" % (esc(tr(r["weight"])), esc(t("history.weight"))))
        if r.get("bigFish"):
            figures.append("<span><b>%s</b> %s</span>" % (esc(tr(r["bigFish"])), esc(t("history.bigFish"))))
        for f in r.get("figures") or []:
            if tr(f.get("value")):
                figures.append("<span><b>%s</b> %s</span>" % (esc(tr(f.get("value"))), esc(tr(f.get("label")))))
        anglers = "".join('<a class="angler-chip" href="?member=%s">%s</a>'
                          % (esc(i), esc(tr(MEMBER_BY_ID[i].get("name")) if i in MEMBER_BY_ID else i))
                          for i in r.get("members") or [])
        notes = tr(r.get("notes"))
        cards.append(
            '<article class="result-card"><div class="event-date">%s</div><div class="result-main">'
            '<div class="event-title">%s</div><div class="event-meta">%s</div>%s%s%s</div>'
            '<div class="result-place">%s%s%s</div></article>'
            % (date_badge(r.get("date"), "") if date_parts(r.get("date")) else
               '<span class="month">%s</span><span class="day">?</span>' % esc(t("events.tbd")),
               esc(tr(r.get("name"))), "".join(meta),
               '<div class="result-figures">%s</div>' % "".join(figures) if figures else "",
               '<div class="angler-chips"><span class="angler-label">%s</span>%s</div>'
               % (esc(t("history.anglers")), anglers) if anglers else "",
               '<p class="result-notes">%s</p>' % esc(notes) if notes else "",
               place,
               '<span class="placement-of">%s</span>' % esc(t("history.of", n=field)) if is_num(field) else "",
               '<span class="placement-pct">%s</span>' % esc(t("history.topPercent", n=pct)) if pct else ""))
    return stats, table, "\n".join(cards), plural("history.count", len(rows))


# --------------------------------------------------------------- calendrier

def calendar():
    """Notre calendrier, sans rien de ce qui dépend du jour.

    events.js ajoute « Passé », le décompte des inscriptions et le bouton .ics
    au chargement; une copie figée au commit les rendrait faux le lendemain.
    """
    events = load("team-schedule.json", [])

    def order_key(ev):
        start = ev.get("startDate") or ""
        if re.match(r"^\d{4}$", start) and re.match(r"^\d{4}-\d{2}-\d{2}$", ev.get("previousDate") or ""):
            return start + ev["previousDate"][4:]
        return start.ljust(10, "9")

    events = sorted(events, key=order_key)
    page_by_family = {family(i): i for i in sorted(TOURNAMENT_PAGES)}
    history = {}
    for r in load("tournament-history.json"):
        history.setdefault(family(r.get("id")), []).append(r)

    def page_for(ev):
        if ev.get("id") in TOURNAMENT_PAGES:
            return ev["id"]
        return page_by_family.get(family(ev.get("id")))

    cards = []
    for ev in events:
        # badgeField vaut "type" sur notre calendrier : la pastille est le type.
        name, badge_text = tr(ev.get("name")), tr(ev.get("type"))
        badge = ('<span class="badge%s">%s</span>' % (" gold" if ev.get("status") == "tentative" else "",
                                                      esc(badge_text))) if badge_text else ""
        state = ('<span class="badge red">%s</span>' % esc(t("events.cancelled"))
                 if ev.get("status") == "cancelled" else "")
        page = page_for(ev)
        meta = []
        for value, prefix, trimmed in ((ev.get("location"), "📍 ", False), (ev.get("region"), "", True),
                                       (ev.get("species"), "🎣 ", False), (ev.get("organizer"), "", True)):
            if tr(value) and not (trimmed and page):
                meta.append("<span>%s%s</span>" % (prefix, esc(tr(value))))
        specs = ""
        if not page:
            spec_rows = []
            for field, key, icon, always in pages.SPEC_ROWS:
                value = tr((ev.get("specs") or {}).get(field))
                if not value and not (always and ev.get("kind") != "show"):
                    continue
                spec_rows.append('<div class="event-spec%s"><span class="event-spec-label">'
                                 '<span aria-hidden="true">%s</span> %s</span><span class="event-spec-value">%s</span></div>'
                                 % ("" if value else " spec-empty", icon, esc(t(key)),
                                    esc(value or t("spec.notPublished"))))
            specs = '<div class="event-specs">%s</div>' % "".join(spec_rows) if spec_rows else ""
        notes = tr(ev.get("notes"))
        record = ""
        mine = history.get(family(ev.get("id"))) or []
        places = [r["placement"] for r in mine if is_num(r.get("placement"))]
        if places:
            best = min(places)
            field = next((r.get("fieldSize") for r in mine if r.get("placement") == best), None)
            record = ('<div class="event-record"><span><b>%s</b> %s</span><span><b>%s</b> %s</span>'
                      '<a href="history.html">%s</a></div>'
                      % (esc(ordinal(len(mine) + 1)), esc(t("events.ourNth")),
                         esc(placement_of(best, field)), esc(t("team.record.best")),
                         esc(t("events.ourResults"))))
        cta = ""
        if page:
            cta += '<a class="btn btn-teal" href="tournois/%s.html">%s</a>' % (esc(page), esc(t("events.cardPage")))
        if ev.get("link"):
            cta += ('<a class="btn %s" href="%s" target="_blank" rel="noopener">%s</a>'
                    % ("btn-ghost" if page else "btn-teal", esc(ev["link"]), esc(t("events.organizerSite"))))
        cards.append(
            '<article class="event-card%s" id="ev-%s"><div class="event-date">%s</div><div>'
            '<div class="event-title">%s %s%s</div><div class="event-meta">%s</div>%s%s%s</div>'
            '<div class="event-cta">%s</div></article>'
            % (" event-inactive" if ev.get("status") == "cancelled" else "", esc(ev.get("id") or ""),
               date_badge(ev.get("startDate"), t("events.tbd")), esc(name), badge, state, "".join(meta), specs,
               '<p class="event-notes">%s</p>' % esc(notes) if notes else "", record, cta))
    return "\n".join(cards), plural("filters.count", len(events))


# ------------------------------------------------------------------ boutique

def merch():
    data = load("merch.json", {})
    products = data.get("products") or []
    if not products:
        return '<div class="empty-state">%s</div>' % esc(t("merch.empty"))
    keys = {"available": "merch.available", "soon": "merch.soon", "soldout": "merch.soldOut"}
    out = []
    for p in products:
        name = tr(p.get("name")) or "—"
        status = p.get("status")
        tone = "" if status == "available" else " navy" if status == "soldout" else " gold"
        cta = ""
        if status == "available":
            href = p.get("url") or data.get("storeUrl") or ""
            if href:
                cta = '<a class="btn btn-teal" href="%s" target="_blank" rel="noopener">%s</a>' % (
                    esc(href), esc(t("merch.order")))
            elif data.get("orderEmail"):
                from urllib.parse import quote
                cta = '<a class="btn btn-teal" href="mailto:%s?subject=%s">%s</a>' % (
                    esc(data["orderEmail"]), quote("%s — %s" % (t("merch.emailSubject"), name)),
                    esc(t("merch.orderEmail")))
        sizes = ('<div class="merch-sizes">%s</div>' % "".join("<span>%s</span>" % esc(s) for s in p["sizes"])
                 if p.get("sizes") else "")
        photo = ('<img src="%s" alt="%s" class="merch-photo-img">' % (esc(p["image"]), esc(t("merch.photoAlt", name=name)))
                 if p.get("image") else "")
        out.append('<article class="merch-card"><div class="merch-photo">%s</div><div class="merch-body">'
                   '<div class="merch-head"><h2>%s</h2><span class="badge%s">%s</span></div>'
                   '<div class="merch-price">%s</div><p>%s</p>%s%s</div></article>'
                   % (photo, esc(name), tone, esc(t(keys.get(status, "merch.soon"))),
                      esc(tr(p.get("price")) or t("merch.priceTBD")), esc(tr(p.get("description"))), sizes, cta))
    return "\n".join(out)


# ------------------------------------------------------------- écriture

BREAK_RE = re.compile(r"(</(?:div|dt|dd|p|h2|h3|li|tr|td|th|span|a|button|summary|figure|em|b)>|<img [^>]*>)(?=<)")


def fill(html, opener, inner, page):
    """Remplace le contenu de l'élément dont la balise ouvrante matche `opener`.

    La balise fermante se trouve en comptant les ouvertures et fermetures du
    même nom, comme close_at() de sync-html-fallbacks.py.
    """
    m = re.search(opener, html)
    if not m:
        raise SystemExit("%s : conteneur introuvable (%s)" % (page, opener))
    tag = re.match(r"<(\w+)", m.group(0)).group(1)
    depth, pos = 1, m.end()
    rx = re.compile(r"</?%s\b" % tag, re.I)
    while depth:
        n = rx.search(html, pos)
        if not n:
            raise SystemExit("%s : balise %s jamais fermée" % (page, tag))
        depth += -1 if n.group(0)[1] == "/" else 1
        pos = n.end()
    end = n.start()
    # Un saut de ligne entre deux éléments, comme les gabarits multilignes du
    # JavaScript : sans lui, un lecteur de texte brut collait « favoriRivière ».
    inner = BREAK_RE.sub(r"\1\n", inner)
    body =(NOTE + inner) if inner and not inner.startswith("<!--") and tag != "span" and tag != "p" else inner
    return html[:m.end()] + body + html[end:]


def set_hidden(html, opener, hidden, page):
    """Pose ou retire l'attribut hidden sur une balise — comme le fait le script
    de la page au premier rendu (section du temple, du palmarès, pastilles)."""
    m = re.search(opener, html)
    if not m:
        raise SystemExit("%s : balise introuvable (%s)" % (page, opener))
    tag = m.group(0)
    bare = re.sub(r"\s+hidden(?=[\s>])", "", tag)
    new = bare[:-1] + " hidden>" if hidden else bare
    return html[:m.start()] + new + html[m.end():]


def build():
    out = {}

    team = {"team-grid": team_grid(), "nextgen": nextgen_list(), "boats": boat_list()}
    out["team.html"] = [
        ("fill", r'<div id="team-grid"[^>]*>', team["team-grid"]),
        ("fill", r'<div id="nextgen-list"[^>]*>', team["nextgen"]),
        ("hide", r'<section id="releve"[^>]*>', not team["nextgen"]),
        ("fill", r'<div id="boat-list"[^>]*>', team["boats"]),
    ]

    trip_html, trip_count = trips()
    out["sorties.html"] = [
        ("fill", r'<div id="trip-list"[^>]*>', trip_html),
        ("fill", r'<p class="result-count" id="trip-count"[^>]*>', esc(trip_count)),
    ]

    featured, hall, grid, count = catches_page()
    out["catches.html"] = [
        ("fill", r'<span class="result-count" id="result-count"[^>]*>', esc(count)),
        ("fill", r'<div id="featured-catch"[^>]*>', featured),
        ("hide", r'<div class="hall-section" data-hall-section[^>]*>', not hall),
        ("fill", r'<div id="hall-of-fame"[^>]*>', hall),
        ("fill", r'<div id="catch-grid"[^>]*>', grid),
    ]

    grid_html, chips, n_chips, sp_count = species_index()
    out["especes.html"] = [
        ("fill", r'<span class="result-count" data-species-count[^>]*>', esc(sp_count)),
        ("fill", r'<nav class="sp-nav" data-species-nav[^>]*>', chips),
        ("hide", r'<nav class="sp-nav" data-species-nav[^>]*>', n_chips < 2),
        ("fill", r'<div data-species-grid[^>]*>', grid_html),
    ]

    stats, table, cards, h_count = history_page()
    out["history.html"] = [
        ("fill", r'<div id="history-stats"[^>]*>', stats),
        ("hide", r'<div class="record-section" data-table-section[^>]*>', not table),
        ("fill", r'<div id="record-table"[^>]*>', table),
        ("fill", r'<span class="result-count" id="result-count"[^>]*>', esc(h_count)),
        ("fill", r'<div id="result-list"[^>]*>', cards),
    ]

    cal, cal_count = calendar()
    out["calendar.html"] = [
        ("fill", r'<span class="result-count" id="result-count"[^>]*>', esc(cal_count)),
        ("fill", r'<div id="event-list"[^>]*>', cal),
    ]

    out["merch.html"] = [("fill", r'<div id="merch-grid"[^>]*>', merch())]
    return out


def main():
    check = "--check" in sys.argv[1:]
    drift = []
    for page, ops in build().items():
        path = os.path.join(REPO, page)
        with io.open(path, encoding="utf-8") as fh:
            before = fh.read()
        html = before
        for op, opener, value in ops:
            html = fill(html, opener, value, page) if op == "fill" else set_hidden(html, opener, value, page)
        if html != before:
            drift.append(page)
            if not check:
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(html)
    if check:
        for page in drift:
            print("  à régénérer :", page)
        print("%d page(s) pré-rendue(s) en retard sur data/." % len(drift))
        sys.exit(1 if drift else 0)
    print("%d page(s) réécrite(s) : %s" % (len(drift), ", ".join(drift) or "aucune"))


if __name__ == "__main__":
    main()
