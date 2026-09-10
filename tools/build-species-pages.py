# -*- coding: utf-8 -*-
"""Écrit une fiche par espèce (especes/), pour les espèces qui la méritent.

CE QUE CE SCRIPT PROTÈGE — c'est sa seule raison d'être.

Une fiche d'espèce qui cite de la science pose une promesse : « ce qui est
écrit ici a été lu quelque part de sérieux ». Une page sans citation qui se
trompe, c'est un pêcheur qui raconte. Une page AVEC citations qui se trompe,
c'est une équipe qui a l'air de ne pas savoir lire un rapport — devant un
commanditaire, c'est pire que rien.

Le risque n'est pas théorique. La toute première recherche faite pour ce
dossier a retourné, au sujet du maskinongé du Saint-Laurent :

    « La population du fleuve Saint-Laurent est entièrement interdite de
      pêche et demeure protégée par la Loi fédérale sur les espèces en
      péril. »

C'est faux. On pêche le maskinongé dans le fleuve et on le remet à l'eau,
légalement. Le résumé confondait avec le chevalier cuivré. Recopiée telle
quelle, cette phrase publiait sur notre propre site quelque chose de faux ET
d'auto-incriminant.

D'où la règle, appliquée ici par du code et pas par de la bonne volonté :

    ON NE PUBLIE JAMAIS UNE AFFIRMATION QU'ON N'A PAS VÉRIFIÉE
    DANS LA SOURCE ELLE-MÊME.

Une affirmation ne sort sur la page que si DEUX conditions tiennent :
  1. elle porte « verified » (quelqu'un a ouvert la source et confirmé) ;
  2. TOUTES les sources qu'elle cite portent « verified » elles aussi.

Une affirmation non vérifiée n'est pas signalée sur la page : elle n'existe
pas. C'est voulu — un « à confirmer » publié est encore une publication.

SEUIL — même discipline que build-catch-pages.py :

    une source vérifiée     la fiche officielle, lue et datée
    des repères            au moins MARKS_MIN mesures de terrain
    de la substance        au moins BLOCKS_MIN blocs remplis

Le seuil a change de nature en cours de route, et il faut dire pourquoi. Il
exigeait d'abord 40 mots d'observation de l'equipe, au motif qu'une fiche
sans vecu n'a pas sa place sur un site d'equipe. C'etait le bon reglage pour
trois especes de vitrine; c'est le mauvais pour un ouvrage de reference que
l'equipe consulte sur l'eau avant de viser un poisson. Une fiche qui donne la
profondeur, la temperature et la periode de fraie rend service meme si
personne n'a encore ecrit son paragraphe.

Le bloc « terrain » reste, et reste ce qui distingue nos fiches de quatre
cents autres — il n'est simplement plus une condition d'existence.

Ce qui n'a PAS bouge : rien ne se publie sans source verifiee. La barriere
porte sur l'exactitude, pas sur l'ampleur.

    python3 tools/build-species-pages.py
    python3 tools/build-sitemap.py     # après

Le gabarit vient de build-tournament-pages.py et build-profile-pages.py
plutôt que d'être recopié.
"""
import io
import json
import os
import importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "especes")
SITE = "https://piedmarinfishing.com"

MARKS_MIN = 2
BLOCKS_MIN = 2

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


_uspec = importlib.util.spec_from_file_location(
    "units", os.path.join(REPO, "tools", "units.py"))
units = importlib.util.module_from_spec(_uspec)
_uspec.loader.exec_module(units)


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def words(value, lang="fr"):
    return len(pick(value, lang).split())


def claim_ok(claim, sources):
    """Une affirmation publiable : vérifiée, sourcée, et ses sources vérifiées.

    Le test porte sur la source AUTANT que sur l'affirmation. Vérifier une
    phrase contre un document dont on n'a jamais confirmé l'existence ne
    vérifie rien du tout.
    """
    if not claim.get("verified"):
        return False
    if not pick(claim.get("text"), "fr"):
        return False
    ids = claim.get("sources") or []
    if not ids:
        return False
    return all((sources.get(sid) or {}).get("verified") for sid in ids)


def marks_of(sp):
    return [m for m in (sp.get("marks") or []) if pick(m.get("value"), "fr")]


def blocks_of(sp):
    return [b for b in (sp.get("blocks") or []) if pick(b.get("body"), "fr")]


def missing(sp, sources):
    """Ce qui manque à cette espèce pour mériter sa page. Vide = elle l'a."""
    gaps = []
    src = sources.get(sp.get("source"))
    if not (src and src.get("verified")):
        gaps.append("source vérifiée")
    n = len(marks_of(sp))
    if n < MARKS_MIN:
        gaps.append("repères (%d/%d)" % (n, MARKS_MIN))
    b = len(blocks_of(sp))
    if b < BLOCKS_MIN:
        gaps.append("blocs (%d/%d)" % (b, BLOCKS_MIN))
    return gaps


def cited(sp, sources):
    """Les sources réellement citées par une affirmation publiée, dans l'ordre."""
    out = []
    for c in (sp.get("claims") or []):
        if not claim_ok(c, sources):
            continue
        for sid in c["sources"]:
            if sid not in out:
                out.append(sid)
    return out


def citation_text(src, lang):
    """Auteurs (année). Titre. Éditeur.

    La citation complète, pas juste le lien : les PDF gouvernementaux changent
    d'adresse sans prévenir, et un lien mort n'est plus une source. Auteurs,
    année, titre et éditeur permettent de retrouver le document ailleurs.
    """
    bits = []
    if src.get("authors"):
        bits.append("%s (%s)." % (src["authors"], src.get("year") or "s.d."))
    title = pick(src.get("title"), lang)
    if title:
        bits.append(title + ".")
    pub = pick(src.get("publisher"), lang)
    if pub:
        bits.append(pub + ".")
    return " ".join(bits)


def claims_html(sp, sources, order):
    """Les affirmations, chacune avec le renvoi numéroté vers sa source.

    Le lien porte le chemin complet de la page, pas seulement « #src-... ».
    Ces fiches vivent un dossier plus bas et déclarent <base href="/"> pour
    que les chemins relatifs marchent : une ancre nue se résout alors contre
    la BASE, pas contre la page — cliquer un renvoi renvoyait à l'accueil.
    """
    rows = []
    page = "especes/%s.html" % sp["id"]
    for c in (sp.get("claims") or []):
        if not claim_ok(c, sources):
            continue
        # Tries : « 2 1 » derriere une phrase se lit comme une coquille.
        marks = "".join(
            '<a class="sp-ref" href="%s#src-%s"><sup>%d</sup></a>'
            % (esc(page), esc(sid), order.index(sid) + 1)
            for sid in sorted(c["sources"], key=order.index))
        rows.append("<li>%s %s</li>" % (bilingual("span", c.get("text")), marks))
    return '<ul class="sp-claims">%s</ul>' % "".join(rows) if rows else ""


def sources_html(sources, order, ui):
    """Le bloc Sources, numéroté comme les renvois."""
    rows = []
    for i, sid in enumerate(order):
        src = sources[sid]
        text = {lang: citation_text(src, lang) for lang in ("fr", "en")}
        link = ""
        if src.get("url"):
            # Le libelle passe par bilingual : ecrit en dur, « consulter »
            # restait en francais sur la version anglaise de la fiche.
            link = ' <a class="sp-src-link" href="%s" rel="noopener nofollow" target="_blank">%s</a>' % (
                esc(src["url"]),
                bilingual("span", {"fr": ui["fr"]["sp.consult"], "en": ui["en"]["sp.consult"]}))
        rows.append('<li id="src-%s"><span class="sp-num">%d.</span> %s%s</li>'
                    % (esc(sid), i + 1, bilingual("span", text), link))
    return '<ol class="sp-sources">%s</ol>' % "".join(rows) if rows else ""


def description(sp, lang):
    """110–165 caractères, tirés de l'introduction plutôt qu'inventés."""
    name = pick(sp.get("name"), lang)
    intro = pick(sp.get("intro"), lang)
    if not intro:
        # Beaucoup de fiches n'ont pas d'introduction écrite à la main. Plutôt
        # qu'une description tronquée sous le minimum de 110 caractères, on
        # compose avec ce que la fiche porte vraiment.
        bits = [pick(b.get("body"), lang) for b in blocks_of(sp)]
        intro = " ".join(x for x in bits if x)
    text = "%s — %s" % (name, intro) if intro else name
    if len(text) > 165:
        text = text[:164].rsplit(" ", 1)[0].rstrip(" ,;:.—–-") + "…"
    return text


def species_ld(sp, url, sources, order):
    """JSON-LD Article, avec « citation » quand des sources sont publiées.

    On ne déclare que ce qui est vrai : pas de date de publication inventée,
    et aucune citation qui ne soit pas déjà visible sur la page.
    """
    ld = {"@context": "https://schema.org", "@type": "Article",
          "headline": pick(sp.get("name"), "fr"), "url": url,
          "inLanguage": "fr-CA",
          "about": {"@type": "Thing", "name": pick(sp.get("name"), "fr")},
          "isPartOf": {"@type": "WebSite", "name": "Pied Marin Fishing",
                       "url": SITE + "/"}}
    if sp.get("scientificName"):
        ld["about"]["alternateName"] = sp["scientificName"]
    intro = pick(sp.get("intro"), "fr")
    if intro:
        ld["description"] = intro[:300]
    refs = []
    for sid in order:
        src = sources[sid]
        ref = {"@type": "CreativeWork", "name": pick(src.get("title"), "fr")}
        if src.get("url"):
            ref["url"] = src["url"]
        refs.append(ref)
    if refs:
        ld["citation"] = refs
    return ('<script type="application/ld+json">\n%s\n</script>'
            % json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/"))


def marks_html(sp):
    """Les chiffres qu'on veut sur l'eau : taille, profondeur, température,
    fraie. En grille plutôt qu'en prose — sur un téléphone, dans un bateau,
    on cherche une valeur, on ne lit pas un paragraphe."""
    rows = []
    for m in marks_of(sp):
        # Le métrique reste la seule valeur enregistrée; l'impérial est
        # calculé ici. Écrire les deux dans data/ garantirait qu'ils finissent
        # par se contredire, et c'est le chiffre du bateau qu'on lirait mal.
        value = {lang: units.convert(pick(m.get("value"), lang), lang)
                 for lang in ("fr", "en")}
        rows.append('<div class="event-spec"><span class="event-spec-label">%s</span>%s</div>'
                    % (bilingual("span", m.get("label")),
                       bilingual("span", value, "event-spec-value")))
    return '<div class="event-specs tp-specs">%s</div>' % "".join(rows) if rows else ""


def blocks_html(sp, ui):
    """Les sections descriptives : reconnaître, distinguer, où, état."""
    out = []
    for b in blocks_of(sp):
        title = b.get("title")
        # h2 et non h3 : ces blocs sont des sections de la page, pas des
        # sous-sections des « repères » qui les précèdent. En h3 ils se
        # rangeaient sous le mauvais titre dans la liste d'un lecteur d'écran.
        out.append('<div class="sp-block">%s%s</div>'
                   % (bilingual("h2", title, "sp-block-title"),
                      bilingual("p", b.get("body"))))
    return "".join(out)


def rules_html(sp, rules, zones, ui, regs):
    """La réglementation qui vise CETTE espèce, tirée de data/regulations.json.

    Kevin : « je pense pas qu'on devrait avoir une page juste pour les
    règlements, cela devrait être sur chaque fiche du poisson. » Il a raison —
    la question « je peux-tu le garder? » se pose en regardant le poisson, pas
    en cherchant une autre page. La page dédiée a donc disparu et son contenu
    vit ici.

    Rien n'est recopié à la main : une règle ajoutée au fichier apparaît sur
    toutes les fiches qu'elle nomme au prochain build.
    """
    mine = [r for r in rules if sp["id"] in (r.get("speciesPages") or [])]
    if not mine:
        return ""
    names = {z["id"]: z.get("name") for z in zones}
    ROWS = [("period", "reg.period", "📅"), ("limit", "reg.limit", "🎣"),
            ("length", "reg.length", "📏"), ("gear", "reg.gear", "🪝")]
    cards = []
    for r in mine:
        scope = {lang: " · ".join(pick(names.get(z), lang) or z
                                  for z in (r.get("zones") or [])) for lang in ("fr", "en")}
        rows = []
        for key, label, icon in ROWS:
            if not pick(r.get(key), "fr"):
                continue
            lab = bilingual("span", {"fr": ui["fr"][label], "en": ui["en"][label]})
            rows.append('<div class="event-spec"><span class="event-spec-label">'
                        '<span aria-hidden="true">%s</span> %s</span>%s</div>'
                        % (icon, lab, bilingual("span", r.get(key), "event-spec-value")))
        note = bilingual("p", r.get("detail"), "reg-detail")
        cards.append('<div class="sp-reg">%s<div class="event-specs tp-specs">%s</div>%s</div>'
                     % (bilingual("h3", scope, "sp-reg-scope"), "".join(rows), note))

    src = (regs.get("official") or {})
    link = ""
    if src.get("url"):
        link = ' <a class="sp-src-link" href="%s" target="_blank" rel="noopener">%s</a>' % (
            esc(src["url"]),
            bilingual("span", {"fr": ui["fr"]["reg.official"], "en": ui["en"]["reg.official"]}))
    season = bilingual("p", regs.get("season"), "reg-season")
    stamp = {lang: ui[lang]["reg.updated"].replace(
        "{date}", long_date(regs.get("updated"), lang) or (regs.get("updated") or ""))
        for lang in ("fr", "en")}
    # Un renvoi vers la page qui CALCULE l'etat de la saison. Le bloc ci-dessus
    # donne les dates; saison.html dit ou on en est aujourd'hui. Les deux se
    # nourrissent du meme regulations.json, donc ils ne peuvent pas diverger.
    seen = ' <a class="sp-src-link" href="saison.html">%s</a>' % bilingual(
        "span", {"fr": ui["fr"]["season.stripLink"], "en": ui["en"]["season.stripLink"]})
    foot = ('<p class="reg-note">%s%s%s</p>'
            % (bilingual("span", {"fr": ui["fr"]["reg.disclaimer"],
                                  "en": ui["en"]["reg.disclaimer"]}), link, seen))
    # data-reg-updated : le garde-fou d'obsolescence. Ces pages sont generees,
    # donc rien ne peut expirer au build — c'est assets/js/reg-guard.js qui
    # efface le bloc quand la date depasse le delai. Sans lui, deplacer la
    # reglementation sur des pages statiques perdait la garantie que la page
    # ne peut pas mentir si personne n'y touche.
    return ('<div class="sp-regs" data-reg-updated="%s" data-reg-months="%s">'
            '%s%s%s%s</div>'
            % (esc(regs.get("updated") or ""), esc(str(regs.get("staleAfterMonths") or 12)),
               season, bilingual("p", stamp, "reg-stamp"), "".join(cards), foot))


def catches_html(sp, catches, cp_index, members, ui):
    """Nos prises de cette espèce : une photo chacune, avec sa légende.

    L'autre moitié du lien : une fiche d'espèce qui ne dit pas qu'on en a
    sorti une est un cul-de-sac, alors que c'est justement ce qui distingue
    nos fiches de celles du ministère. La photo, elle, est la seule chose que
    la fiche du ministère ne peut pas avoir — et pour identifier un malachigan
    sur un quai, elle vaut trois lignes de description.

    Une vignette par prise, jamais la galerie : le maskinongé de Kevin B. a
    cinq photos sur SA fiche, les remettre ici la dupliquerait et enterrerait
    l'identification. La couverture suffit, le reste est à un clic.

    Le seuil d'ici n'est pas celui des fiches de prise. Une prise sans fiche
    — faute d'un récit écrit — garde sa photo : ce qu'elle montre ne dépend
    pas de savoir si on a raconté la journée. Elle mène alors à sa carte sur
    l'index, qui porte déjà une ancre « #c-<id> » et se met en évidence à
    l'arrivée; pas à l'index tout court, où il faudrait la chercher.
    """
    # speciesId plutôt que le nom français. L'appariement par nom exigeait que
    # « Saumon chinook » soit écrit à la lettre près dans deux fichiers; il ne
    # l'était pas, et la prise ne rejoignait aucune fiche — sans erreur, sans
    # avertissement, sans que rien ne paraisse. Un identifiant se vérifie.
    mine = [c for c in catches if c.get("speciesId") == sp["id"]]
    if not mine:
        return ""
    cells = []
    for c in mine:
        who = members.get(c.get("angler")) or {}
        label = {lang: " — ".join(x for x in (
            pick(c.get("measure"), lang),
            who.get("name") or pick(c.get("anglerName"), lang),
            long_date(c.get("date"), lang)) if x) for lang in ("fr", "en")}
        href = ("prises/%s.html" % c["id"]) if c["id"] in cp_index \
            else "catches.html#c-%s" % c["id"]
        media = c.get("media") or {}
        src = media.get("src") if media.get("type") == "image" else ""
        shot = ""
        if src:
            alt = media.get("alt") or c.get("species")
            # Toujours en différé : ce bloc vit au deuxième écran, jamais au
            # premier, et une vignette qui bloque l'affichage des repères
            # annulerait le travail fait pour les remonter.
            img = ('<img src="%s"%s alt="%s" loading="lazy" width="400" height="300">'
                   % (esc(src),
                      profiles.srcset_attrs(src, "(max-width: 700px) 44vw, 220px"),
                      esc(pick(alt, "fr"))))
            if pick(alt, "en") and pick(alt, "en") != pick(alt, "fr"):
                img = img.replace("<img ", '<img data-en-alt="%s" ' % esc(pick(alt, "en")), 1)
            shot = img
        # Sans mesure ni date ni pêcheur la légende serait vide : on met alors
        # le nom de l'espèce, plutôt qu'une vignette qui ne dit rien.
        if not pick(label, "fr"):
            label = {lang: pick(sp.get("name"), lang) for lang in ("fr", "en")}
        cells.append('<a class="sp-catch" href="%s">%s%s</a>'
                     % (esc(href), shot, bilingual("span", label, "sp-catch-cap")))
    return '<div class="sp-catches">%s</div>' % "".join(cells)


def source_html(sp, sources, ui, order=()):
    """D'où vient tout ça, et quand on l'a lu. La page le dit en toutes
    lettres, y compris que l'anglais est notre traduction d'une source
    française — ne pas le dire laisserait croire à une version officielle."""
    src = sources.get(sp.get("source")) or {}
    # Si la source de la fiche figure déjà dans la liste numérotée des
    # renvois, la réécrire ici la donnerait deux fois de suite au lecteur.
    listed = sp.get("source") in (order or ())
    text = ({"fr": "", "en": ""} if listed
            else {lang: citation_text(src, lang) for lang in ("fr", "en")})
    when = sp.get("consulted") or ""
    # Deux notes selon ce que la fiche porte : dès qu'un bloc « sur l'eau »
    # existe, dire que TOUT vient du ministère serait faux — et c'est
    # exactement le genre de fausse attribution que la barrière existe pour
    # empêcher, dans l'autre sens.
    # Une espèce sans fiche gouvernementale ne peut pas porter la même note que
    # les 46 autres. Le dire est plus important que d'avoir la fiche : un
    # lecteur qui voit partout « source : gouvernement du Québec » supposerait
    # que celle-ci aussi, et c'est exactement la fausse attribution qu'on
    # refuse depuis le début.
    if sp.get("noGov"):
        key = "sp.sourceNoteNoGov"
    elif pick(sp.get("field"), "fr"):
        key = "sp.sourceNoteField"
    else:
        key = "sp.sourceNote"
    note = {lang: ui[lang][key].replace("{date}", long_date(when, lang) or when)
            for lang in ("fr", "en")}
    link = ""
    if src.get("url"):
        link = ' <a class="sp-src-link" href="%s" target="_blank" rel="noopener">%s</a>' % (
            esc(src["url"]),
            bilingual("span", {"fr": ui["fr"]["sp.consult"], "en": ui["en"]["sp.consult"]}))
    head = ('<p class="sp-origin">%s%s</p>' % (bilingual("span", text), link)
            if (pick(text, "fr") or not listed) else "")
    return head + bilingual("p", note, "sp-origin-note")


def render(sp, ui, sources, rules=(), zones=(), regs=None,
           catches=(), cp_index=(), members=None):
    name = sp.get("name")
    title = {lang: clamp_title(pick(name, lang)) for lang in ("fr", "en")}
    desc = {lang: description(sp, lang) for lang in ("fr", "en")}
    url = "%s/especes/%s.html" % (SITE, sp["id"])
    image = "%s/assets/img/og-card.png" % SITE
    regs = regs or {}
    members = members or {}
    order = cited(sp, sources)

    # L'ORDRE COMPTE, et il a été mesuré. Les repères venaient après
    # l'introduction : 425 px avant le premier chiffre sur un écran de 844, soit
    # la moitié d'un écran brûlée avant ce qu'on est venu chercher. Et la
    # réglementation arrivait cinquième, alors que « je peux-tu le garder? » est
    # la deuxième question, pas la cinquième.
    #
    # Les chiffres d'abord, la règle ensuite, la prose après. Une fiche qu'on
    # ouvre sur un bateau se lit de haut en bas une seule fois.
    body = []
    marks = marks_html(sp)
    if marks:
        body.append(section({"fr": ui["fr"]["sp.marks"], "en": ui["en"]["sp.marks"]},
                            marks, key="sp.marks"))

    reg = rules_html(sp, rules, zones, ui, regs)
    if reg:
        body.append(section({"fr": ui["fr"]["sp.rules"], "en": ui["en"]["sp.rules"]},
                            reg, alt=True, key="sp.rules"))

    # Le bloc de l'équipe passe devant la prose du ministère. Sur un bateau,
    # « comment NOUS on le pêche » vaut plus que la description officielle —
    # et c'est la seule partie de la fiche que personne d'autre ne peut
    # écrire. Il sortait avant-dernier.
    field = bilingual("p", sp.get("field"), "tp-notes")
    ours = catches_html(sp, catches, cp_index, members, ui)
    if field or ours:
        body.append(section({"fr": ui["fr"]["sp.field"], "en": ui["en"]["sp.field"]},
                            (field or "") + ours, key="sp.field"))

    blocks = blocks_html(sp, ui)
    if blocks:
        body.append('<section><div class="container">%s</div></section>' % blocks)

    intro = bilingual("p", sp.get("intro"), "tp-notes")
    if intro:
        body.append('<section class="alt"><div class="container">%s</div></section>' % intro)

    claims = claims_html(sp, sources, order)
    if claims:
        body.append(section({"fr": ui["fr"]["sp.science"], "en": ui["en"]["sp.science"]},
                            claims, key="sp.science"))

    # Quand une fiche est batie sur plusieurs sources croisees, elles doivent
    # TOUTES apparaitre : dire « selon le G3E » en cachant les deux autres
    # laisserait croire a une source unique la ou il y en a trois qui
    # s'accordent — et c'est precisement l'accord qui donne sa valeur au
    # chiffre publie.
    extra = [x for x in ([sp.get("source")] + (sp.get("alsoSources") or []))
             if x and x in sources and x not in order]
    listed = order + extra
    # source_html doit voir la liste FINALE, sinon il reecrit en tete une
    # citation que la liste numerotee donne juste en dessous.
    origin = source_html(sp, sources, ui, listed)
    srcs = sources_html(sources, listed, ui)
    body.append(section({"fr": ui["fr"]["sp.sources"], "en": ui["en"]["sp.sources"]},
                        origin + srcs, alt=not bool(field), key="sp.sources"))

    body.append('<section><div class="container">%s<div class="callout-actions">'
                '<a class="btn btn-ghost" href="especes.html">%s</a></div></div></section>'
                % (bilingual("p", {"fr": ui["fr"]["sp.regNote"], "en": ui["en"]["sp.regNote"]},
                             "tp-notes"),
                   bilingual("span", {"fr": ui["fr"]["sp.back"], "en": ui["en"]["sp.back"]})))

    sci = ('<p class="tp-when"><em>%s</em></p>' % esc(sp["scientificName"])
           if sp.get("scientificName") else "")
    return """%(head)s
<div class="page-header">
  <div class="container">
    <span class="kicker" data-i18n="sp.kicker">%(kicker)s</span>
    <h1 data-en="%(h1_en)s">%(h1_fr)s</h1>
    %(sci)s
  </div>
</div>

%(body)s
%(footer)s""" % {
        "head": profiles.head(title, desc, url, image,
                              species_ld(sp, url, sources, order), og_type="article"),
        "kicker": esc(ui["fr"]["sp.kicker"]),
        "h1_fr": esc(pick(name, "fr")), "h1_en": esc(pick(name, "en")),
        "sci": sci,
        "body": "\n\n".join(body),
        "footer": pages.FOOTER,
    }


def checklist(species, sources):
    """Ce qu'il reste à aller vérifier, prêt à être travaillé ligne par ligne.

    C'est la vraie sortie du script tant qu'aucune fiche ne passe. Un document
    de vérification séparé se serait périmé; imprimé par le script, il dit
    toujours l'état réel des données.
    """
    todo_src = [s for s in sources if not s.get("verified")]
    if todo_src:
        print("\nSOURCES À VÉRIFIER — ouvrir le lien, confirmer que le document")
        print("existe, qu'il est bien de cet auteur et qu'il couvre ce sujet.")
        for s in todo_src:
            print("\n  [%s]  %s" % (s["id"], citation_text(s, "fr")))
            if s.get("url"):
                print("      %s" % s["url"])
            else:
                print("      (aucun lien — il faut retrouver le document)")
            print("      couvre : %s" % pick(s.get("covers"), "fr"))
            print("      → puis : \"verified\": {\"by\": \"...\", \"date\": \"AAAA-MM-JJ\"}")

    for sp in species:
        todo = [c for c in (sp.get("claims") or []) if not c.get("verified")]
        if not todo:
            continue
        print("\nAFFIRMATIONS À VÉRIFIER — %s" % pick(sp.get("name"), "fr"))
        for c in todo:
            text = pick(c.get("text"), "fr") or "(à écrire)"
            print("\n  [%s] %s" % (c["id"], text))
            print("      sources : %s" % (", ".join(c.get("sources") or []) or "AUCUNE"))
            if c.get("verify"):
                print("      à vérifier : %s" % c["verify"])


def main():
    profiles.VARIANTS.update(load("image-variants.json"))
    ui = load("i18n.json")
    species = load("species.json")
    src_list = load("sources.json")
    catches = load("catches.json")
    members = {m["id"]: m for m in load("team-members.json")}
    try:
        cp_index = set(load("catch-pages.json"))
    except (IOError, OSError, ValueError):
        cp_index = set()
    try:
        regs = load("regulations.json")
    except (IOError, OSError, ValueError):
        regs = {}
    sources = {s["id"]: s for s in src_list}

    # Une source citée mais absente du registre casserait la numérotation
    # sans que rien ne le dise. On le dit.
    for sp in species:
        for c in (sp.get("claims") or []):
            for sid in (c.get("sources") or []):
                if sid not in sources:
                    raise SystemExit(
                        "source inconnue « %s » citée par %s/%s" % (sid, sp["id"], c["id"]))

    kept = [sp for sp in species if not missing(sp, sources)]
    below = [(sp, missing(sp, sources)) for sp in species if missing(sp, sources)]

    os.makedirs(OUT_DIR, exist_ok=True)
    keep_files = {"%s.html" % sp["id"] for sp in kept}
    for name in sorted(os.listdir(OUT_DIR)):
        if name.endswith(".html") and name not in keep_files:
            os.remove(os.path.join(OUT_DIR, name))
            print("  retirée : especes/%s (passée sous le seuil)" % name)

    for sp in kept:
        with io.open(os.path.join(OUT_DIR, "%s.html" % sp["id"]), "w", encoding="utf-8") as fh:
            fh.write(render(sp, ui, sources, regs.get("rules") or [],
                            regs.get("zones") or [], regs, catches, cp_index, members))
        print("  especes/%-22s %d repère(s), %d bloc(s), %d affirmation(s)"
              % (sp["id"] + ".html", len(marks_of(sp)), len(blocks_of(sp)),
                 len([c for c in (sp.get("claims") or []) if claim_ok(c, sources)])))

    index_path = os.path.join(REPO, "data", "species-pages.json")
    with io.open(index_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(sorted(sp["id"] for sp in kept), ensure_ascii=False, indent=2) + "\n")

    ok_src = len([s for s in src_list if s.get("verified")])
    print("\n%d fiche(s) sur %d espèce(s). %d source(s) vérifiée(s) sur %d."
          % (len(kept), len(species), ok_src, len(src_list)))
    if below:
        print("\nSous le seuil — il manque :")
        for sp, gaps in below:
            print("  %-20s %s" % (sp["id"], ", ".join(gaps)))
        print("\n(seuil : source vérifiée, %d repères, %d blocs)"
              % (MARKS_MIN, BLOCKS_MIN))
    checklist(species, src_list)
    if kept:
        print("\nÉtape suivante :\n  une page d'index especes.html (sinon les fiches"
              "\n  générées n'ont aucun lien entrant), puis"
              "\n  python3 tools/build-sitemap.py")


if __name__ == "__main__":
    main()
