# -*- coding: utf-8 -*-
"""Vérifie que les liens du site existent, ET que ceux qui devraient exister existent.

Deux questions différentes, et la seconde est la seule qui trouve quelque chose
une fois le site en place :

  1. CASSÉ  — un href pointe vers un fichier qui n'existe pas.
  2. MANQUANT — deux pages parlent du même poisson, du même pêcheur ou du même
     bateau et ne se pointent pas. Rien n'est cassé, et pourtant le visiteur
     tombe dans un cul-de-sac.

Un vérificateur de liens ordinaire ne voit que la première. C'est la seconde
qui a montré que les 5 fiches de prise et les 47 fiches d'espèce parlaient des
mêmes poissons sans jamais se renvoyer l'une à l'autre.

    python3 tools/check-links.py            # rapport complet
    python3 tools/check-links.py --brief    # juste les totaux

Sort en code 1 s'il reste un lien cassé. Les liens manquants sont signalés
mais ne font pas échouer : certains sont des choix, pas des oublis.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["tournois", "pecheurs", "bateaux", "prises", "especes"]
HREF = re.compile(r'href="([^"]+)"')
IMG = re.compile(r'<img[^>]+src="([^"]+)"')


def load(name):
    with io.open(os.path.join(REPO, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def pages():
    out = [f for f in sorted(os.listdir(REPO)) if f.endswith(".html")]
    for d in DIRS:
        p = os.path.join(REPO, d)
        if os.path.isdir(p):
            out += ["%s/%s" % (d, f) for f in sorted(os.listdir(p)) if f.endswith(".html")]
    return out


SCRIPT = re.compile(r"(?is)<script[^>]*>.*?</script>")


def read(page, strip_scripts=True):
    """Le HTML de la page, sans les <script>.

    Les pages rendues en JavaScript portent des gabarits comme
    href="${esc(s.url)}" : ce sont des chaînes de code, pas des liens, et les
    scanner faisait signaler un lien cassé qui n'existe pas.
    """
    with io.open(os.path.join(REPO, page), encoding="utf-8") as fh:
        html = fh.read()
    return SCRIPT.sub(" ", html) if strip_scripts else html


def broken():
    """Les href internes qui ne mènent nulle part.

    Les fiches générées déclarent <base href="/">, donc un chemin relatif s'y
    résout depuis la RACINE et non depuis leur dossier — c'est la même subtilité
    qui avait cassé les ancres des fiches d'espèce.
    """
    bad = []
    for page in pages():
        html = read(page)
        has_base = '<base href="/">' in html
        for href in HREF.findall(html):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            if target.startswith("/"):
                # Un chemin absolu part de la racine du SITE, pas du disque :
                # os.path.join(REPO, "/assets/…") rendait "/assets/…" et
                # signalait comme cassées les 18 références de 404.html.
                root = target.lstrip("/")
            elif has_base or "/" not in page:
                root = target
            else:
                root = os.path.normpath(os.path.join(os.path.dirname(page), target))
            if not os.path.exists(os.path.join(REPO, root)):
                bad.append((page, href, root))
    return bad


SRCSET = re.compile(r'srcset="([^"]+)"')


def images():
    """Les <img> dont le fichier n'est pas sur le disque — srcset compris.

    Le srcset est la moitié qui manquait : une page peut offrir quatre
    largeurs d'une photo dont une seule existe, et le navigateur choisit
    parfois la mauvaise. Rien ne casse sur l'écran du développeur.
    """
    bad = []
    for page in pages():
        html = read(page)
        candidates = list(IMG.findall(html))
        for value in SRCSET.findall(html):
            for part in value.split(","):
                url = part.strip().split(" ")[0]
                if url:
                    candidates.append(url)
        for src in candidates:
            if src.startswith(("http", "data:")):
                continue
            if not os.path.exists(os.path.join(REPO, src.split("?")[0].lstrip("/"))):
                bad.append((page, src))
    return bad


def variants():
    """Chaque largeur déclarée dans image-variants.json existe-t-elle vraiment?"""
    bad = []
    try:
        table = load("image-variants.json")
    except (IOError, OSError, ValueError):
        return bad
    for src, widths in table.items():
        stem, ext = os.path.splitext(src)
        top = max(widths) if widths else None
        for w in widths:
            f = src if w == top else "%s-%d%s" % (stem, w, ext)
            if not os.path.exists(os.path.join(REPO, f)):
                bad.append((src, w, f))
    return bad


def expected():
    """Les liens qui devraient exister entre deux pages qui parlent du même sujet."""
    want = []
    catches = load("catches.json")
    species = load("species.json")
    members = {m["id"]: m for m in load("team-members.json")}
    boats = load("boats.json")
    videos = (load("videos.json") or {}).get("videos") or []
    cp = set(load("catch-pages.json"))
    sp = set(load("species-pages.json"))
    known = {s["id"] for s in species}

    for c in catches:
        sid = c.get("speciesId")
        if c["id"] in cp and sid and sid in sp:
            want.append(("prises/%s.html" % c["id"], "especes/%s.html" % sid,
                         "la prise et la fiche de son espèce"))
            want.append(("especes/%s.html" % sid, "prises/%s.html" % c["id"],
                         "la fiche d'espèce et la prise qu'on en a"))
        if c["id"] in cp and c.get("angler") in members:
            want.append(("prises/%s.html" % c["id"], "pecheurs/%s.html" % c["angler"],
                         "la prise et son pêcheur"))

    for b in boats:
        for role in ("skipper", "owner"):
            who = b.get(role)
            if who in members:
                want.append(("bateaux/%s.html" % b["id"], "pecheurs/%s.html" % who,
                             "le bateau et son %s" % role))

    # Une vidéo qui nomme un pêcheur ou une prise doit apparaître sur leur
    # page. Le champ existait depuis le début sans jamais mener nulle part —
    # un champ de données orphelin est un lien manquant qu'on ne voit pas.
    for v in videos:
        vid = (v.get("videoId") or "").strip()
        if not vid:
            continue
        if v.get("angler") in members:
            want.append(("pecheurs/%s.html" % v["angler"], vid,
                         "la vidéo sur la fiche de son pêcheur"))
        if v.get("catch") and v["catch"] in cp:
            want.append(("prises/%s.html" % v["catch"], vid,
                         "la vidéo sur la page de la prise"))

    missing = []
    for src, dst, why in want:
        if not os.path.exists(os.path.join(REPO, src)):
            continue
        html = read(src)
        if dst not in html:
            missing.append((src, dst, why))
    return missing, want


def orphans():
    """Un speciesId qui ne mene a aucune espece.

    Le lien prise -> fiche d'espece se faisait par nom francais exact. « Saumon
    chinook » n'etait ecrit pareil nulle part ailleurs : la prise ne rejoignait
    aucune fiche, et rien ne le disait — pas d'erreur, pas d'avertissement, une
    section vide et personne pour s'en apercevoir. Un identifiant, lui, se
    verifie. Un champ ABSENT est un oubli; un champ VIDE est une decision, et
    ce controle respecte la difference.
    """
    species = {s["id"] for s in load("species.json")}
    out = []
    for c in load("catches.json"):
        if "speciesId" not in c:
            out.append((c["id"], "(champ absent)", "aucun speciesId sur cette prise"))
        elif c["speciesId"] and c["speciesId"] not in species:
            out.append((c["id"], c["speciesId"], "aucune espece ne porte cet identifiant"))
        # showcase decide si la prise monte sur le mur ou reste sur la fiche de
        # son espece. Un champ absent vaudrait « oui » par defaut cote
        # JavaScript, et une photo de journal se retrouverait sur le mur sans
        # que personne l'ait decide. Le silence est le mauvais defaut ici.
        if "showcase" not in c:
            out.append((c["id"], "(champ absent)", "aucun showcase : le mur ou la fiche?"))
        elif not isinstance(c["showcase"], bool):
            out.append((c["id"], repr(c["showcase"]), "showcase doit valoir true ou false"))
    return out


def main():
    brief = "--brief" in sys.argv
    bad = broken()
    imgs = images()
    vars_ = variants()
    missing, want = expected()
    orph = orphans()

    print("%d pages examinées." % len(pages()))
    print("Liens cassés   : %d" % len(bad))
    print("Images absentes: %d" % len(imgs))
    print("Variantes absentes: %d" % len(vars_))
    print("Liens manquants: %d (sur %d attendus)" % (len(missing), len(want)))
    print("speciesId orphelins: %d" % len(orph))

    if not brief:
        for page, href, root in bad:
            print("\n  ✗ %s\n      href=%s  →  %s introuvable" % (page, href, root))
        for page, src in imgs:
            print("\n  ✗ %s\n      %s absent du disque" % (page, src))
        for src, w, f in vars_:
            print("\n  ✗ %s déclare la largeur %d\n      %s absent du disque" % (src, w, f))
        if missing:
            print("\nCES DEUX PAGES PARLENT DU MÊME SUJET ET NE SE POINTENT PAS :")
            for src, dst, why in missing:
                print("  %-38s → %-34s  (%s)" % (src, dst, why))
        for cid, sid, why in orph:
            print("\n  ✗ data/catches.json — %s\n      %s : %s" % (cid, sid, why))
    return 1 if bad or imgs or vars_ or orph else 0


if __name__ == "__main__":
    sys.exit(main())
