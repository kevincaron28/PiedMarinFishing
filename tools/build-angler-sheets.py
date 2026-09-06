# -*- coding: utf-8 -*-
"""Fiche pro staff — une page Letter par pêcheur, en français et en anglais.

Une candidature pro staff se traite pêcheur par pêcheur : une marque de
cannes veut savoir ce que CE pêcheur a dans les mains, pas ce que l'équipe
fait en moyenne. Ce script écrit une page par pêcheur et par langue, à
envoyer avec la trousse de commandite.

Rien n'est saisi ici. Tout vient de data/ — le même matériel, les mêmes
résultats et les mêmes prises que la fiche web, donc les deux ne peuvent pas
diverger. Un pêcheur sans équipement n'a pas de section équipement plutôt
qu'une section vide.

    python3 tools/build-angler-sheets.py
    node tools/render-angler-sheets.js <dossier>
"""
import json, io, base64, os

REPO = "/home/user/PiedMarinFishing"
OUT = "/tmp/claude-0/-home-user-PiedMarinFishing/fd04c8b1-f2c9-52b0-bd85-87187f0e94aa/scratchpad/sheets"

def load(name):
    return json.load(io.open(os.path.join(REPO, name), encoding="utf-8"))

i18n = load("data/i18n.json")
members = load("data/team-members.json")
history = load("data/tournament-history.json")
catches = load("data/catches.json")
boats = load("data/boats.json")

def b64(path, mime):
    with open(os.path.join(REPO, path), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

CREST = b64("assets/img/logo-mark-light.png", "image/png")

def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

def tr(v, lang):
    return v.get(lang, v.get("fr", "")) if isinstance(v, dict) else (v or "")

# Le portrait est servi en 3:4. On le recadre sur le visage, comme la trousse,
# parce que les trois portraits ne cadrent pas le visage à la même hauteur.
FACE = {"kevin-caron": 0.19, "kevin-b": 0.27, "bobe": 0.50}
PORTRAIT_RATIO = 0.80  # largeur / hauteur

def portrait(path, face):
    from PIL import Image
    im = Image.open(os.path.join(REPO, path)).convert("RGB")
    w, h = im.size
    band = min(h, round(w / PORTRAIT_RATIO))
    top = min(max(round(face * h - band * 0.42), 0), h - band)
    im = im.crop((0, top, w, top + band))
    im.thumbnail((640, 800), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=86, optimize=True)
    return "data:image/jpeg;base64,%s" % base64.b64encode(buf.getvalue()).decode()

PHOTOS = {m["id"]: portrait(m["photo"], FACE.get(m["id"], 0.3))
          for m in members if m.get("photo")}

SPEC_ORDER = ["homeWater", "species", "technique", "personalBest", "dreamCatch", "since"]

L = {
 "fr": dict(
   kicker="Fiche pro staff", season="Saison 2027",
   about="Le pêcheur", gear="Ce que j'ai dans les mains",
   record="En tournoi", catchesT="Mes prises", teamT="L'équipe derrière",
   offerT="Ce que je peux offrir", honestT="Ce que je ne peux pas encore offrir",
   contactT="Parlons-nous",
   contactBody="Écrivez-nous en quelques lignes et on vous revient rapidement. Aucune formule imposée — on s'ajuste à ce qui a du sens pour vous.",
   sheetOf="Fiche complète :", teamsOf="équipes", ofLabel="sur",
   helmLabel="Aux commandes de", ownLabel="Propriétaire de",
   offers=[
     "Votre matériel sur l'eau à chaque sortie et à chaque tournoi, du printemps jusqu'à la glace.",
     "Votre marque nommée sur ma fiche publique, dans la section équipement.",
     "Des essais honnêtes, avec un retour franc — bon ou mauvais.",
     "Des mentions dans nos publications : photos de tournoi, vidéos et coulisses.",
   ]),
 "en": dict(
   kicker="Pro staff sheet", season="2027 Season",
   about="The angler", gear="What's in my hands",
   record="In competition", catchesT="My catches", teamT="The team behind me",
   offerT="What I can offer", honestT="What I can't offer yet",
   contactT="Let's talk",
   contactBody="Send us a few lines and we'll get back to you quickly. No fixed packages — we shape it around what makes sense for you.",
   sheetOf="Full profile:", teamsOf="teams", ofLabel="of",
   helmLabel="At the helm of", ownLabel="Owner of",
   offers=[
     "Your gear on the water every trip and every tournament, from spring through the ice.",
     "Your brand named on my public profile, in the gear section.",
     "Honest field testing, with straight feedback — good or bad.",
     "Mentions in our posts: tournament photos, video and behind the scenes.",
   ]),
}


def ordinal(n, lang):
    if lang == "en":
        if 10 <= n % 100 <= 20:
            suf = "th"
        else:
            suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return "%d%s" % (n, suf)
    return "1er" if n == 1 else "%de" % n


def long_date(value, lang):
    """Rend ce que la date connaît — « 2 mai 2026 », « mai 2026 » ou « 2026 »."""
    parts = str(value or "").split("-")
    if not parts or not parts[0].isdigit():
        return ""
    names = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                    "août", "septembre", "octobre", "novembre", "décembre"],
             "en": ["January", "February", "March", "April", "May", "June", "July",
                    "August", "September", "October", "November", "December"]}[lang]
    y = parts[0]
    if len(parts) < 2 or not parts[1].isdigit():
        return y
    m = names[int(parts[1]) - 1]
    if len(parts) < 3 or not parts[2].isdigit():
        return "%s %s" % (m.capitalize() if lang == "en" else m, y)
    d = int(parts[2])
    return "%s %d, %s" % (m, d, y) if lang == "en" else "%d %s %s" % (d, m, y)


def build(m, lang):
    t = i18n[lang]
    s = L[lang]
    mid = m["id"]
    name = m.get("name") or mid
    role = tr(m.get("role"), lang)
    bio = tr(m.get("bio"), lang)

    # Caractéristiques — dans un ordre choisi, et seulement celles renseignées.
    specs = m.get("specs") or {}
    spec_html = "".join(
        '<div class="sp"><span class="sp-l">%s</span><span class="sp-v">%s</span></div>'
        % (esc(t.get("team.spec." + f, f)), esc(tr(specs[f], lang)))
        for f in SPEC_ORDER if tr(specs.get(f), lang))

    # Équipement — la section qu'une marque lit en premier. Vide, elle n'existe
    # pas : une liste à moitié remplie dessert la candidature.
    gear = [g for g in (m.get("gear") or []) if tr(g.get("value"), lang)]
    gear_html = "".join(
        '<div class="gr"><span class="gr-l">%s</span><span class="gr-v">%s</span></div>'
        % (esc(tr(g.get("label"), lang)), esc(tr(g.get("value"), lang))) for g in gear)

    # Résultats — les nôtres, tels quels. Le classement dit aussi la taille du
    # peloton : « 99e » seul ne veut rien dire, « 99e sur 329 » oui.
    mine = [r for r in history if mid in (r.get("members") or [])]
    mine.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
    places = [r["placement"] for r in mine if isinstance(r.get("placement"), int)]
    tiles = []
    if mine:
        tiles.append((str(len(mine)), t["team.record.events.other" if len(mine) > 1
                                        else "team.record.events.one"]))
    if places:
        best = min(places)
        field = next((r.get("fieldSize") for r in mine if r.get("placement") == best), None)
        tiles.append((ordinal(best, lang) + (" %s %d" % (s["ofLabel"], field) if field else ""),
                      t["team.record.best"]))
    res_html = "".join(
        '<div class="rw"><span class="rw-n">%s</span><span class="rw-d">%s</span>'
        '<span class="rw-p">%s</span></div>'
        % (esc(tr(r.get("name"), lang)), esc(long_date(r.get("date"), lang)),
           esc("%s%s" % (ordinal(r["placement"], lang),
                         " / %d %s" % (r["fieldSize"], s["teamsOf"]) if r.get("fieldSize") else ""))
           if isinstance(r.get("placement"), int) else "")
        for r in mine)

    cs = [c for c in catches if c.get("angler") == mid]
    cs.sort(key=lambda c: str(c.get("date") or ""), reverse=True)
    catch_html = "".join(
        '<div class="ct"><span class="ct-s">%s</span><span class="ct-m">%s</span>'
        '<span class="ct-w">%s</span></div>'
        % (esc(tr(c.get("species"), lang)), esc(tr(c.get("measure"), lang) or "—"),
           esc(tr(c.get("water"), lang)))
        for c in cs)

    helm = [b for b in boats if b.get("skipper") == mid]
    owned = [b for b in boats if b.get("owner") == mid and b not in helm]
    boat = ""
    picked, label = (helm[0], s["helmLabel"]) if helm else \
                    ((owned[0], s["ownLabel"]) if owned else (None, ""))
    if picked:
        bits = [tr(picked.get("name"), lang)]
        eng = tr((picked.get("specs") or {}).get("engine"), lang)
        if eng:
            bits.append(eng)
        boat = ('<div class="boat"><span class="boat-l">%s</span><span>%s</span></div>'
                % (esc(label), esc(" · ".join(x for x in bits if x))))

    blocks = []
    photo = PHOTOS.get(mid, "")
    intro = ('<div class="intro">%s<div class="intro-b"><p class="bio">%s</p>%s%s</div></div>'
             % ('<img class="pt" src="%s">' % photo if photo else "",
                esc(bio), '<div class="sps">%s</div>' % spec_html if spec_html else "", boat))
    blocks.append('<div class="section"><h2>%s</h2>%s</div>' % (esc(s["about"]), intro))

    if gear_html:
        blocks.append('<div class="section"><h2>%s</h2><div class="grs">%s</div></div>'
                      % (esc(s["gear"]), gear_html))
    if res_html:
        tile_html = "".join('<div class="tile"><b>%s</b><span>%s</span></div>' % (esc(a), esc(b))
                            for a, b in tiles)
        blocks.append('<div class="section"><h2>%s</h2><div class="tiles">%s</div>'
                      '<div class="rws">%s</div></div>' % (esc(s["record"]), tile_html, res_html))
    if catch_html:
        blocks.append('<div class="section"><h2>%s</h2><div class="cts">%s</div></div>'
                      % (esc(s["catchesT"]), catch_html))

    offers = "".join("<li>%s</li>" % esc(o) for o in s["offers"])
    blocks.append('<div class="section"><h2>%s</h2><ul>%s</ul></div>' % (esc(s["offerT"]), offers))
    # La même franchise que la trousse : pas de chiffres d'audience inventés.
    blocks.append('<div class="section"><h2>%s</h2><div class="honest">%s</div></div>'
                  % (esc(s["honestT"]), esc(t["sponsors.honestBody"])))

    return TEMPLATE % dict(
        lang=lang, crest=CREST, kicker=esc(s["kicker"]), name=esc(name), role=esc(role),
        season=esc(s["season"]), sheetOf=esc(s["sheetOf"]),
        url="piedmarinfishing.com/pecheurs/%s" % esc(mid),
        body="".join(blocks), contactT=esc(s["contactT"]), contactBody=esc(s["contactBody"]))


TEMPLATE = """<!DOCTYPE html><html lang="%(lang)s"><head><meta charset="utf-8"><style>
@page { size: letter; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Liberation Sans", Helvetica, Arial, sans-serif; color: #10202f;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sheet { width: 8.5in; height: 11in; position: relative; overflow: hidden; background: #fbf9f4; }
.band { background: linear-gradient(135deg, #071726 0%%, #123452 55%%, #157a76 100%%);
        color: #fff; padding: 0.26in 0.62in 0.22in; position: relative; }
.band img.crest { position: absolute; right: 0.45in; top: 50%%; transform: translateY(-50%%);
                  width: 1.15in; opacity: 0.9; }
.kick { font-size: 8.5pt; letter-spacing: 0.18em; text-transform: uppercase;
        color: #e8bd6a; font-weight: 700; }
h1 { font-family: "Liberation Serif", Georgia, serif; font-size: 26pt; line-height: 1.02;
     margin: 5pt 0 3pt; }
.role { font-size: 9pt; letter-spacing: 0.1em; text-transform: uppercase;
        color: rgba(255,255,255,0.8); font-weight: 700; }
.sheetof { margin-top: 8pt; font-size: 8pt; color: rgba(255,255,255,0.72); }
.sheetof b { color: #fff; font-weight: 400; }
.body { padding: 0.14in 0.62in 0; display: flex; flex-direction: column;
        height: calc(11in - 1.72in - 0.5in); }
h2 { font-family: "Liberation Serif", Georgia, serif; font-size: 11.5pt; color: #0b2038;
     margin: 0 0 4pt; padding-bottom: 2.5pt; border-bottom: 2px solid rgba(16,32,47,0.12); }
.section { margin-bottom: 5pt; }

.intro { display: flex; gap: 11pt; }
.pt { width: 1.2in; height: 1.5in; object-fit: cover; border-radius: 7pt; flex: 0 0 auto; }
.intro-b { flex: 1; min-width: 0; }
.bio { font-size: 8.6pt; line-height: 1.36; color: #2c4351; }
.sps { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5pt 10pt; margin-top: 5pt; }
.sp { display: flex; justify-content: space-between; gap: 6pt; font-size: 8pt;
      border-bottom: 1px dotted rgba(16,32,47,0.16); padding-bottom: 1pt; }
.sp-l { color: #6b8393; white-space: nowrap; }
.sp-v { color: #0b2038; font-weight: 700; text-align: right; }
.boat { margin-top: 5pt; font-size: 8pt; color: #2c4351; }
.boat-l { color: #6b8393; margin-right: 5pt; }

.grs { display: grid; grid-template-columns: 1fr 1fr; gap: 3pt 9pt; }
.gr { background: #fff; border: 1px solid rgba(16,32,47,0.1); border-left: 3px solid #3fb6ad;
      border-radius: 5pt; padding: 3pt 8pt; }
.gr-l { display: block; font-size: 7pt; letter-spacing: 0.08em; text-transform: uppercase;
        color: #157a76; font-weight: 700; }
.gr-v { display: block; font-size: 8.6pt; color: #0b2038; line-height: 1.3; margin-top: 1pt; }

.tiles { display: flex; gap: 8pt; margin-bottom: 5pt; }
.tile { background: #0b2038; color: #fff; border-radius: 6pt; padding: 4pt 11pt; }
.tile b { display: block; font-family: "Liberation Serif", Georgia, serif; font-size: 13pt; }
.tile span { font-size: 7pt; letter-spacing: 0.06em; text-transform: uppercase;
             color: rgba(255,255,255,0.72); }
.rw { display: flex; align-items: baseline; gap: 8pt; font-size: 8.4pt; padding: 2pt 0;
      border-bottom: 1px solid rgba(16,32,47,0.08); }
.rw-n { flex: 1; color: #0b2038; font-weight: 700; }
.rw-d { color: #8296a3; font-size: 7.6pt; }
.rw-p { color: #157a76; font-weight: 700; white-space: nowrap; }

.cts { display: grid; grid-template-columns: 1fr 1fr; gap: 3pt 10pt; }
.ct { display: flex; align-items: baseline; gap: 6pt; font-size: 8.4pt; padding: 1.5pt 0;
      border-bottom: 1px solid rgba(16,32,47,0.08); }
.ct-s { color: #0b2038; font-weight: 700; }
.ct-m { color: #157a76; font-weight: 700; }
.ct-w { flex: 1; text-align: right; color: #8296a3; font-size: 7.4pt; }

ul { list-style: none; }
li { position: relative; padding: 1pt 0 1pt 14pt; font-size: 8.6pt; line-height: 1.3; color: #2c4351; }
li::before { content: "\\2713"; position: absolute; left: 0; color: #157a76; font-weight: 700; }
.honest { background: #f6f3ea; border: 1px solid rgba(16,32,47,0.1); border-radius: 7pt;
          padding: 4pt 10pt; font-size: 8pt; line-height: 1.32; color: #2c4351; }

.contact { background: #0b2038; color: #fff; border-radius: 8pt; padding: 7pt 13pt;
           margin-top: auto; }
.contact h3 { font-family: "Liberation Serif", Georgia, serif; font-size: 11pt; margin-bottom: 3pt; }
.contact p { font-size: 8pt; color: rgba(255,255,255,0.8); line-height: 1.34; margin-bottom: 5pt; }
.contact .mail { display: inline-block; background: #157a76; color: #fff; padding: 5pt 12pt;
                 border-radius: 99px; font-size: 9pt; font-weight: 700; text-decoration: none; }
.contact .soc { margin-top: 6pt; font-size: 7.4pt; color: rgba(255,255,255,0.68); }
.foot { position: absolute; bottom: 0.24in; left: 0.62in; right: 0.62in; display: flex;
        justify-content: space-between; font-size: 7.6pt; color: #8296a3; }
</style></head><body>
<div class="sheet">
  <div class="band">
    <img class="crest" src="%(crest)s">
    <div class="kick">%(kicker)s</div>
    <h1>%(name)s</h1>
    <div class="role">%(role)s</div>
    <div class="sheetof">%(sheetOf)s <b>%(url)s</b></div>
  </div>
  <div class="body">%(body)s
  <div class="contact">
    <h3>%(contactT)s</h3>
    <p>%(contactBody)s</p>
    <a class="mail" href="mailto:info@piedmarinfishing.com">info@piedmarinfishing.com</a>
    <div class="soc">piedmarinfishing.com &nbsp;·&nbsp; Instagram, Facebook, YouTube, TikTok : @piedmarinfishing</div>
  </div>
  </div>
  <div class="foot"><span>Pied Marin Fishing</span><span>%(season)s</span></div>
</div>
</body></html>"""

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for m in members:
        for lang in ("fr", "en"):
            p = os.path.join(OUT, "sheet-%s-%s.html" % (m["id"], lang))
            io.open(p, "w", encoding="utf-8").write(build(m, lang))
        print("  %-14s fr + en" % m["id"])
    print("\nÉtape suivante :\n  node tools/render-angler-sheets.js %s" % OUT)
