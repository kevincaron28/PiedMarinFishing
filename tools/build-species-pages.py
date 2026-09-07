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

    une introduction        au moins INTRO_MIN mots
    des affirmations        au moins CLAIMS_MIN, vérifiées
    du terrain              au moins FIELD_MIN mots d'observation de l'équipe

Le bloc « terrain » n'est pas décoratif et n'exige aucune source : c'est le
seul contenu de la page qu'aucune ferme à contenu ne peut produire. Une fiche
qui n'a que de la science recopiée n'a pas sa place sur un site d'équipe — il
en existe déjà quatre cents meilleures. Sans terrain, pas de fiche.

Sur les données d'aujourd'hui, ce seuil produit ZÉRO page, et c'est la bonne
réponse : rien n'est encore vérifié. Le script imprime alors la liste de ce
qu'il faut aller vérifier, source par source et affirmation par affirmation.

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

INTRO_MIN = 60
CLAIMS_MIN = 3
FIELD_MIN = 40

_spec = importlib.util.spec_from_file_location(
    "pages", os.path.join(REPO, "tools", "build-tournament-pages.py"))
pages = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pages)

_pspec = importlib.util.spec_from_file_location(
    "profiles", os.path.join(REPO, "tools", "build-profile-pages.py"))
profiles = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(profiles)

esc, pick, bilingual, section = pages.esc, pages.pick, pages.bilingual, pages.section
clamp_title = pages.clamp_title


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


def missing(sp, sources):
    """Ce qui manque à cette espèce pour mériter sa page. Vide = elle l'a."""
    gaps = []
    n = words(sp.get("intro"))
    if n < INTRO_MIN:
        gaps.append("introduction (%d/%d mots)" % (n, INTRO_MIN))
    ok = [c for c in (sp.get("claims") or []) if claim_ok(c, sources)]
    if len(ok) < CLAIMS_MIN:
        gaps.append("affirmations vérifiées (%d/%d)" % (len(ok), CLAIMS_MIN))
    f = words(sp.get("field"))
    if f < FIELD_MIN:
        gaps.append("terrain (%d/%d mots)" % (f, FIELD_MIN))
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


def render(sp, ui, sources):
    name = sp.get("name")
    title = {lang: clamp_title(pick(name, lang)) for lang in ("fr", "en")}
    desc = {lang: description(sp, lang) for lang in ("fr", "en")}
    url = "%s/especes/%s.html" % (SITE, sp["id"])
    image = "%s/assets/img/og-card.png" % SITE
    order = cited(sp, sources)

    body = []
    intro = bilingual("p", sp.get("intro"), "tp-notes")
    if intro:
        body.append('<section><div class="container">%s</div></section>' % intro)

    claims = claims_html(sp, sources, order)
    if claims:
        body.append(section({"fr": ui["fr"]["sp.science"], "en": ui["en"]["sp.science"]},
                            claims, alt=True, key="sp.science"))

    field = bilingual("p", sp.get("field"), "tp-notes")
    if field:
        body.append(section({"fr": ui["fr"]["sp.field"], "en": ui["en"]["sp.field"]},
                            field, key="sp.field"))

    srcs = sources_html(sources, order, ui)
    if srcs:
        body.append(section({"fr": ui["fr"]["sp.sources"], "en": ui["en"]["sp.sources"]},
                            srcs, alt=True, key="sp.sources"))

    # La réglementation ne vit jamais sur cette page : elle change, et une
    # limite périmée affichée chez nous est pire que pas de limite du tout.
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
            fh.write(render(sp, ui, sources))
        print("  especes/%s.html  %d affirmation(s) vérifiée(s), %d source(s)"
              % (sp["id"], len([c for c in sp["claims"] if claim_ok(c, sources)]),
                 len(cited(sp, sources))))

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
        print("\n(seuil : introduction de %d mots, %d affirmations vérifiées, "
              "%d mots de terrain)" % (INTRO_MIN, CLAIMS_MIN, FIELD_MIN))
    checklist(species, src_list)
    if kept:
        print("\nÉtape suivante :\n  une page d'index especes.html (sinon les fiches"
              "\n  générées n'ont aucun lien entrant), puis"
              "\n  python3 tools/build-sitemap.py")


if __name__ == "__main__":
    main()
