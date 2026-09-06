# -*- coding: utf-8 -*-
"""Écrit une fiche par prise (prises/), pour les prises qui la méritent.

SEUIL — c'est tout l'intérêt de ce script. Sept fiches de 24 mots nuiraient
plus qu'elles n'aideraient : elles seraient plus minces que merch.html, qui
échoue déjà notre propre contrôle SEO. Une prise n'a donc droit à sa page que
si elle a de quoi remplir une page :

    une date       au moins l'année et le mois
    un plan d'eau
    au moins PHOTOS_MIN photo   (la couverture plus la galerie)
    un récit d'au moins STORY_MIN mots  (champ « story », bilingue)

Le seuil portait d'abord sur les photos — trois — et pas assez sur le texte.
C'était l'inverse du bon reglage : la substance d'une fiche, c'est le récit,
pas le compte de photos. Une grande photo et 120 mots de récit font une page
qui merite son adresse; trois photos et deux phrases n'en font pas une.

Le seuil du récit est cale sur seo.js, qui refuse une page sous 120 mots.

Sur les données d'aujourd'hui, ce seuil produit ZÉRO page — et c'est la bonne
réponse, pas un bogue. Le script dit ce qui manque à chacune, prise par prise,
pour que la première qui franchit le seuil soit évidente.

    python3 tools/build-catch-pages.py
    python3 tools/build-sitemap.py     # après

Le gabarit — menu, pied de page, bilinguisme par data-en — vient de
build-tournament-pages.py plutôt que d'être recopié.
"""
import io
import json
import os
import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "prises")
SITE = "https://piedmarinfishing.com"

PHOTOS_MIN = 1
STORY_MIN = 120

_spec = importlib.util.spec_from_file_location(
    "pages", os.path.join(REPO, "tools", "build-tournament-pages.py"))
pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages)

_pspec = importlib.util.spec_from_file_location(
    "profiles", os.path.join(REPO, "tools", "build-profile-pages.py"))
profiles = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(profiles)

esc, pick, bilingual, section = pages.esc, pages.pick, pages.bilingual, pages.section
clamp_title, long_date = pages.clamp_title, pages.long_date
srcset_attrs = profiles.srcset_attrs


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def photos_of(c):
    """La couverture puis la galerie — le même ordre que la visionneuse."""
    out = []
    media = c.get("media") or {}
    if media.get("type") == "image" and media.get("src"):
        out.append({"src": media["src"], "alt": media.get("alt")})
    for g in (c.get("gallery") or []):
        src = g if isinstance(g, str) else (g or {}).get("src")
        if src:
            out.append({"src": src, "alt": (g or {}).get("alt") if isinstance(g, dict) else None})
    return out


def missing(c):
    """Ce qui manque à cette prise pour mériter sa page. Vide = elle l'a."""
    gaps = []
    date = str(c.get("date") or "")
    if len(date) < 7:
        gaps.append("date")
    if not pick(c.get("water"), "fr"):
        gaps.append("plan d'eau")
    n = len(photos_of(c))
    if n < PHOTOS_MIN:
        gaps.append("%d photo%s de plus" % (PHOTOS_MIN - n, "s" if PHOTOS_MIN - n > 1 else ""))
    words = len(pick(c.get("story"), "fr").split())
    if words < STORY_MIN:
        gaps.append("récit (%d/%d mots)" % (words, STORY_MIN))
    return gaps


def headline(c, lang, members):
    """« Maskinongé de 50 po — Kevin B. » : l'espèce, la taille, le pêcheur.

    Sans le suffixe du site : c'est aussi le fil de la description, où
    « — Pied Marin Fishing » se retrouverait au milieu d'une phrase.
    En anglais « Muskie of 50" » n'est pas de l'anglais; la virgule, elle,
    fonctionne dans les deux langues sans réécrire la mesure.
    """
    species = pick(c.get("species"), lang)
    measure = pick(c.get("measure"), lang)
    who = members.get(c.get("angler"), {}).get("name") or pick(c.get("anglerName"), lang)
    head = species + ((", " if lang == "en" else " de ") + measure if measure else "")
    return " — ".join(x for x in (head, who) if x)


def title_of(c, lang, members):
    """Le <title>, suffixe du site compris et longueur bornée."""
    return clamp_title(headline(c, lang, members))


def description(c, lang, members):
    """110–165 caractères : ce que Google montre sous le titre.

    Les faits sont séparés par des tirets plutôt que cousus en phrase :
    « sur Fleuve Saint-Laurent » manque son article, et il n'y a pas de règle
    fiable pour deviner celui d'un plan d'eau quelconque.
    """
    bits = [headline(c, lang, members)]
    water = pick(c.get("water"), lang)
    when = long_date(c.get("date"), lang)
    if water:
        bits.append(water)
    if when:
        bits.append(when)
    text = " — ".join(bits) + "."
    story = pick(c.get("story"), lang) or pick(c.get("notes"), lang)
    if len(text) < 110 and story:
        text = text + " " + story
    if len(text) > 165:
        text = text[:164].rsplit(" ", 1)[0].rstrip(" ,;:.—–-") + "…"
    return text


def facts_html(c, ui, members, events):
    """Les faits en grille, dans le style des specs de tournoi."""
    who = members.get(c.get("angler"))
    rows = []

    def row(icon, key, value, href=None):
        if not pick(value, "fr") and not pick(value, "en"):
            return
        inner = bilingual("span", value, "event-spec-value")
        if href:
            inner = '<a href="%s">%s</a>' % (esc(href), inner)
        rows.append('<div class="event-spec"><span class="event-spec-label">'
                    '<span aria-hidden="true">%s</span> %s</span>%s</div>'
                    % (icon, esc(ui["fr"][key]), inner))

    if who:
        row("🎣", "catches.angler", who.get("name"), "pecheurs/%s.html" % who["id"])
    elif pick(c.get("anglerName"), "fr"):
        row("🎣", "catches.angler", c.get("anglerName"))
    row("📏", "catches.measure", c.get("measure"))
    if c.get("date"):
        row("📅", "catches.date", {"fr": long_date(c["date"], "fr"),
                                   "en": long_date(c["date"], "en")})
    row("📍", "catches.water", c.get("water"))
    ev = events.get(c.get("event"))
    if ev:
        row("🏆", "catches.event", ev.get("name"), "history.html")
    return '<div class="event-specs tp-specs">%s</div>' % "".join(rows) if rows else ""


def gallery_html(c, ui):
    """Toutes les photos, la couverture en premier.

    Une page de prise existe d'abord pour ses photos — c'est la condition du
    seuil. Elles sont donc grandes, pas en vignettes.
    """
    shots = photos_of(c)
    if not shots:
        return ""
    cells = []
    for i, ph in enumerate(shots):
        alt = ph.get("alt") or c.get("species")
        img = ('<img src="%s"%s alt="%s" loading="%s" width="1200" height="900">'
               % (esc(ph["src"]),
                  srcset_attrs(ph["src"], "(max-width: 700px) 92vw, 720px"),
                  esc(pick(alt, "fr")), "eager" if i == 0 else "lazy"))
        if pick(alt, "en") and pick(alt, "en") != pick(alt, "fr"):
            img = img.replace("<img ", '<img data-en-alt="%s" ' % esc(pick(alt, "en")), 1)
        cap = bilingual("figcaption", ph.get("alt") or c.get("species"), "gal-cap")
        cells.append('<figure class="cp-shot">%s%s</figure>' % (img, cap))
    return '<div class="cp-gallery" data-gallery>%s</div>' % "".join(cells)


def gear_html(c, ui, members):
    """Le matériel du pêcheur, lu sur sa fiche.

    C'est la question qu'une marque et un lecteur posent tous les deux devant
    une grosse prise : avec quoi? On ne le recopie pas dans catches.json — il
    vit dans team-members.json, et le lien vers la fiche du pêcheur suit.
    """
    who = members.get(c.get("angler"))
    gear = [g for g in ((who or {}).get("gear") or []) if pick(g.get("value"), "fr")]
    if not gear:
        return ""
    rows = "".join(
        '<div class="event-spec"><span class="event-spec-label">%s</span>%s</div>'
        % (bilingual("span", g.get("label")), bilingual("span", g.get("value"), "event-spec-value"))
        for g in gear)
    link = ('<a class="member-history-link" href="pecheurs/%s.html">%s</a>'
            % (esc(who["id"]), bilingual("span", {"fr": ui["fr"]["team.viewProfile"],
                                                  "en": ui["en"]["team.viewProfile"]})))
    return '<div class="event-specs tp-specs">%s</div>%s' % (rows, link)


def related(c, kept):
    """Trois voisines : même espèce d'abord, puis même pêcheur, puis le reste.

    Des fiches sans liens entre elles sont des culs-de-sac — la même règle que
    pour les tournois, et la même raison.
    """
    pool = [x for x in kept if x["id"] != c["id"]]
    same_species = [x for x in pool if pick(x.get("species"), "fr") == pick(c.get("species"), "fr")]
    same_angler = [x for x in pool if x.get("angler") == c.get("angler") and x not in same_species]
    out, seen = [], set()
    for x in same_species + same_angler + pool:
        if x["id"] in seen:
            continue
        seen.add(x["id"])
        out.append(x)
        if len(out) == 3:
            break
    return out


def render(c, ui, members, events, kept):
    title = {lang: title_of(c, lang, members) for lang in ("fr", "en")}
    h1 = {lang: headline(c, lang, members) for lang in ("fr", "en")}
    desc = {lang: description(c, lang, members) for lang in ("fr", "en")}
    url = "%s/prises/%s.html" % (SITE, c["id"])
    shots = photos_of(c)
    image = "%s/%s" % (SITE, shots[0]["src"]) if shots else "%s/assets/img/og-card.png" % SITE

    body = []
    facts = facts_html(c, ui, members, events)
    if facts:
        body.append(section({"fr": ui["fr"]["cp.facts"], "en": ui["en"]["cp.facts"]},
                            facts, key="cp.facts"))

    story = bilingual("p", c.get("story"), "tp-notes")
    if story:
        body.append(section({"fr": ui["fr"]["cp.story"], "en": ui["en"]["cp.story"]},
                            story, alt=True, key="cp.story"))

    gallery = gallery_html(c, ui)
    if gallery:
        # Une seule photo sous un titre au pluriel se remarque.
        gkey = "cp.gallery" if len(photos_of(c)) > 1 else "cp.photo"
        body.append(section({"fr": ui["fr"][gkey], "en": ui["en"][gkey]},
                            gallery, key=gkey))

    gear = gear_html(c, ui, members)
    if gear:
        body.append(section({"fr": ui["fr"]["cp.gear"], "en": ui["en"]["cp.gear"]},
                            gear, alt=True, key="cp.gear"))

    near = related(c, kept)
    if near:
        rows = "".join(
            '<li><a href="prises/%s.html">%s</a></li>'
            % (esc(x["id"]), bilingual("span", {"fr": headline(x, "fr", members),
                                                "en": headline(x, "en", members)}))
            for x in near)
        body.append(section({"fr": ui["fr"]["cp.related"], "en": ui["en"]["cp.related"]},
                            '<ul class="tp-related">%s</ul>' % rows, key="cp.related"))

    body.append('<section><div class="container"><div class="callout-actions">'
                '<a class="btn btn-ghost" href="catches.html">%s</a></div></div></section>'
                % bilingual("span", {"fr": ui["fr"]["cp.back"], "en": ui["en"]["cp.back"]}))

    return """%(head)s
<div class="page-header">
  <div class="container">
    <span class="kicker" data-i18n="cp.kicker">%(kicker)s</span>
    <h1 data-en="%(h1_en)s">%(h1_fr)s</h1>
    %(sub)s
  </div>
</div>

%(body)s
%(footer)s""" % {
        "head": profiles.head(title, desc, url, image, catch_ld(c, url, image, members),
                              og_type="article"),
        "kicker": esc(ui["fr"]["cp.kicker"]),
        "h1_fr": esc(h1["fr"]), "h1_en": esc(h1["en"]),
        "sub": bilingual("p", c.get("water"), "tp-when") if pick(c.get("water"), "fr") else "",
        "body": "\n\n".join(body),
        "footer": pages.FOOTER,
    }


def catch_ld(c, url, image, members):
    """JSON-LD Article : une fiche de prise est un récit illustré, pas un
    événement ni un produit. On ne déclare que ce qui est vrai — pas de date
    de publication inventée, pas d'auteur si la prise n'a pas de pêcheur au
    roster."""
    ld = {"@context": "https://schema.org", "@type": "Article",
          "headline": headline(c, "fr", members), "url": url,
          "image": image, "inLanguage": "fr-CA",
          "isPartOf": {"@type": "WebSite", "name": "Pied Marin Fishing", "url": SITE + "/"}}
    who = members.get(c.get("angler"))
    if who:
        ld["author"] = {"@type": "Person", "name": who.get("name"),
                        "url": "%s/pecheurs/%s.html" % (SITE, who["id"])}
    story = pick(c.get("story"), "fr") or pick(c.get("notes"), "fr")
    if story:
        ld["description"] = story[:300]
    return ('<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"))


def main():
    # srcset_attrs lit un dictionnaire que build-profile-pages.py ne remplit
    # que dans SON main() : importé comme module, il reste vide et les fiches
    # sortaient sans srcset. On le remplit ici aussi.
    profiles.VARIANTS.update(load("image-variants.json"))
    ui = load("i18n.json")
    catches = load("catches.json")
    members = {m["id"]: m for m in load("team-members.json")}
    events = {e["id"]: e for e in load("tournament-history.json")}

    kept = [c for c in catches if not missing(c)]
    below = [(c, missing(c)) for c in catches if missing(c)]

    os.makedirs(OUT_DIR, exist_ok=True)
    # Une prise qui repasse sous le seuil — une photo retirée, un récit vidé —
    # laisserait sinon une page orpheline, absente du sitemap mais servie.
    keep_files = {"%s.html" % c["id"] for c in kept}
    for name in sorted(os.listdir(OUT_DIR)):
        if name.endswith(".html") and name not in keep_files:
            os.remove(os.path.join(OUT_DIR, name))
            print("  retirée : prises/%s (passée sous le seuil)" % name)

    for c in kept:
        path = os.path.join(OUT_DIR, "%s.html" % c["id"])
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(render(c, ui, members, events, kept))
        n = len(photos_of(c))
        print("  prises/%s.html  %d photo%s, récit de %d mots"
              % (c["id"], n, "s" if n > 1 else "",
                 len(pick(c.get("story"), "fr").split())))

    # L'index que lisent les cartes de prises et les fiches de pêcheur : sans
    # lui, une page generee n'aurait aucun lien entrant — une orpheline.
    index_path = os.path.join(REPO, "data", "catch-pages.json")
    with io.open(index_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(sorted(c["id"] for c in kept), ensure_ascii=False, indent=2) + "\n")

    print("\n%d fiche(s) sur %d prise(s)." % (len(kept), len(catches)))
    if below:
        print("\nSous le seuil — il manque :")
        for c, gaps in below:
            print("  %-24s %s" % (c["id"], ", ".join(gaps)))
        print("\n(seuil : date, plan d'eau, %d photo%s, récit de %d mots)"
              % (PHOTOS_MIN, "s" if PHOTOS_MIN > 1 else "", STORY_MIN))
    if kept:
        print("\nÉtape suivante :\n  python3 tools/build-sitemap.py")


if __name__ == "__main__":
    main()
