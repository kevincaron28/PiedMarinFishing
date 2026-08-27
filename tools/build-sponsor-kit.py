# -*- coding: utf-8 -*-
import json, io, base64, os, sys
REPO = "/home/user/PiedMarinFishing"
OUT  = "/tmp/claude-0/-home-user-PiedMarinFishing/fd04c8b1-f2c9-52b0-bd85-87187f0e94aa/scratchpad/kit"

i18n = json.load(io.open(REPO + "/data/i18n.json", encoding="utf-8"))
members = json.load(io.open(REPO + "/data/team-members.json", encoding="utf-8"))

def b64(path, mime):
    with open(REPO + "/" + path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())

CREST = b64("assets/img/logo-mark-light.png", "image/png")
PHOTOS = {m["id"]: b64(m["photo"], "image/jpeg") for m in members if m.get("photo")}

L = {
 "fr": dict(
   kicker="Trousse de commandite", season="Saison 2027",
   tagline="Une gang de pêcheurs du Québec — brochet, achigan, doré",
   whoTitle="Ce qu'on est", offerTitle="Ce qu'on peut offrir",
   crewTitle="Les pêcheurs", honestTitle="Ce qu'on ne peut pas encore offrir",
   contactTitle="Parlons-nous",
   contactBody="Écrivez-nous en quelques lignes : votre entreprise et ce qui vous intéresse. On s'ajuste à ce qui a du sens pour vous — aucune formule imposée.",
   site="piedmarinfishing.com", page=""),
 "en": dict(
   kicker="Sponsorship kit", season="2027 Season",
   tagline="A fishing crew from Québec — pike, bass, walleye",
   whoTitle="Who we are", offerTitle="What we can offer",
   crewTitle="The crew", honestTitle="What we can't offer yet",
   contactTitle="Let's talk",
   contactBody="Send us a few lines: your business and what interests you. We'll shape it around what makes sense for you — no fixed packages.",
   site="piedmarinfishing.com", page=""),
}

def build(lang):
    t = i18n[lang]; s = L[lang]
    def tr(v): return v.get(lang) if isinstance(v, dict) else (v or "")
    facts = [t["sponsors.fact%d" % i] for i in range(1, 6)]
    offers = [(t["sponsors.offer%d" % i], t["sponsors.offer%db" % i]) for i in range(1, 6)]
    crew = "".join(
      '<div class="crew"><img src="%s"><div class="crew-n">%s</div><div class="crew-r">%s</div></div>'
      % (PHOTOS.get(m["id"], ""), m["name"], tr(m.get("role"))) for m in members)
    factli = "".join("<li>%s</li>" % f for f in facts)
    offerli = "".join('<div class="off"><b>%s</b><span>%s</span></div>' % (a, b) for a, b in offers)

    return """<!DOCTYPE html><html lang="%(lang)s"><head><meta charset="utf-8"><style>
@page { size: letter; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Liberation Sans", Helvetica, Arial, sans-serif; color: #10202f;
       -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sheet { width: 8.5in; height: 11in; position: relative; overflow: hidden;
         page-break-after: always; background: #fbf9f4; }
.sheet:last-child { page-break-after: auto; }
.band { background: linear-gradient(135deg, #071726 0%%, #123452 55%%, #157a76 100%%);
        color: #fff; padding: 0.4in 0.62in 0.34in; position: relative; }
.band img.crest { position: absolute; right: 0.45in; top: 50%%; transform: translateY(-50%%);
                  width: 1.3in; opacity: 0.9; }
.kick { font-size: 8.5pt; letter-spacing: 0.18em; text-transform: uppercase; color: #e8bd6a; font-weight: 700; }
h1 { font-family: "Liberation Serif", Georgia, serif; font-size: 25pt; line-height: 1.05; margin: 6pt 0 5pt; }
.tag { font-size: 10.5pt; color: rgba(255,255,255,0.85); max-width: 5in; }
.season { margin-top: 9pt; display: inline-block; background: rgba(255,255,255,0.14);
          padding: 3pt 10pt; border-radius: 99px; font-size: 8.5pt; letter-spacing: 0.08em; }
.body { padding: 0.24in 0.62in 0; }
h2 { font-family: "Liberation Serif", Georgia, serif; font-size: 12.5pt; color: #0b2038;
     margin: 0 0 7pt; padding-bottom: 4pt; border-bottom: 2px solid rgba(16,32,47,0.12);
     letter-spacing: 0.02em; }
.section { margin-bottom: 0.115in; }
ul { list-style: none; }
li { position: relative; padding: 2.2pt 0 2.2pt 15pt; font-size: 8.8pt; line-height: 1.28; color: #2c4351; }
li::before { content: "\\2713"; position: absolute; left: 0; color: #157a76; font-weight: 700; }
.crews { display: flex; gap: 12pt; margin-top: 4pt; }
.crew { flex: 1; text-align: center; }
.crew img { width: 100%%; height: 0.9in; object-fit: cover; border-radius: 7pt; display: block; }
.crew-n { font-family: "Liberation Serif", Georgia, serif; font-size: 10pt; margin-top: 4pt; color: #0b2038; }
.crew-r { font-size: 7.2pt; letter-spacing: 0.08em; text-transform: uppercase; color: #157a76; font-weight: 700; }
.offs { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6pt; }
.off { background: #fff; border: 1px solid rgba(16,32,47,0.1); border-left: 3px solid #3fb6ad;
       border-radius: 6pt; padding: 6pt 9pt; }
.off b { display: block; font-size: 9.2pt; color: #0b2038; margin-bottom: 2.5pt; }
.off span { font-size: 8pt; color: #47606f; line-height: 1.4; }
.honest { background: #f6f3ea; border: 1px solid rgba(16,32,47,0.1); border-radius: 8pt;
          padding: 7pt 11pt; font-size: 8.5pt; line-height: 1.38; color: #2c4351; }
.contact { background: #0b2038; color: #fff; border-radius: 8pt; padding: 9pt 13pt; }
.contact h3 { font-family: "Liberation Serif", Georgia, serif; font-size: 11.5pt; margin-bottom: 4pt; }
.contact p { font-size: 8.6pt; color: rgba(255,255,255,0.82); line-height: 1.45; margin-bottom: 7pt; }
.contact .mail { display: inline-block; background: #157a76; color: #fff; padding: 6pt 13pt;
                 border-radius: 99px; font-size: 9.4pt; font-weight: 700; text-decoration: none; }
.contact .soc { margin-top: 7pt; font-size: 7.8pt; color: rgba(255,255,255,0.7); }
.foot { position: absolute; bottom: 0.28in; left: 0.62in; right: 0.62in; display: flex;
        justify-content: space-between; font-size: 8pt; color: #8296a3;
        border-top: 1px solid rgba(16,32,47,0.1); padding-top: 6pt; }
</style></head><body>

<div class="sheet">
  <div class="band">
    <img class="crest" src="%(crest)s">
    <div class="kick">%(kicker)s</div>
    <h1>Pied Marin Fishing</h1>
    <div class="tag">%(tagline)s</div>
    <div class="season">%(season)s</div>
  </div>
  <div class="body">
    <div class="section"><h2>%(whoTitle)s</h2><ul>%(facts)s</ul></div>
    <div class="section"><h2>%(crewTitle)s</h2><div class="crews">%(crew)s</div></div>
    <div class="section"><h2>%(offerTitle)s</h2><div class="offs">%(offers)s</div></div>
    <div class="section"><h2>%(honestTitle)s</h2><div class="honest">%(honestBody)s</div></div>
    <div class="contact">
      <h3>%(contactTitle)s</h3>
      <p>%(contactBody)s</p>
      <a class="mail" href="mailto:info@piedmarinfishing.com">info@piedmarinfishing.com</a>
      <div class="soc">piedmarinfishing.com &nbsp;·&nbsp; Instagram, Facebook, YouTube, TikTok : @piedmarinfishing</div>
    </div>
  </div>
  <div class="foot"><span>%(site)s</span><span>%(season)s</span></div>
</div>
</body></html>""" % dict(
      lang=lang, crest=CREST, kicker=s["kicker"], tagline=s["tagline"], season=s["season"],
      whoTitle=s["whoTitle"], facts=factli, crewTitle=s["crewTitle"], crew=crew,
      offerTitle=s["offerTitle"], offers=offerli, honestTitle=s["honestTitle"],
      honestBody=t["sponsors.honestBody"], contactTitle=s["contactTitle"],
      contactBody=s["contactBody"], site=s["site"], page=s["page"])

for lang in ("fr", "en"):
    p = os.path.join(OUT, "kit-%s.html" % lang)
    io.open(p, "w", encoding="utf-8").write(build(lang))
    print("  écrit :", p, "(%.1f Ko)" % (os.path.getsize(p)/1024))
