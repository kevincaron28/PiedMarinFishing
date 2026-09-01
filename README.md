# Pied Marin Fishing

Pied Marin Fishing - Fishing Team Quebec

A static website for the team: landing page, roster, socials, our tournament
schedule, a guide to fishing tournaments across Québec, and a sponsor pitch
page. Live at [piedmarinfishing.com](https://piedmarinfishing.com).

## Pages

| File | Purpose |
|---|---|
| `index.html` | Landing page |
| `team.html` | Roster — bios, angler specs, per-member record, and the team boats |
| `catches.html` | Catch log with photos and video |
| `history.html` | *Résultats / Results* — every tournament fished, filterable by member and season |
| `calendar.html` | Our own upcoming tournament schedule |
| `tournaments.html` | Québec tournament directory (for any angler, not just the team) |
| `merch.html` | Shop — under construction |
| `social.html` | Social media links |
| `404.html` | Not-found page, served by GitHub Pages at any depth |
| `tournois/*.html` | One generated page per documented tournament |
| `pecheurs/*.html` | One generated profile per angler — its own URL, so it can be pasted into a pro-staff application |
| `bateaux/*.html` | One generated page per boat — specs, crew, gallery, and the restoration log for the one under way |
| `sponsors.html` | Sponsor pitch, with a downloadable PDF kit |

No build step, no framework, no dependencies — plain HTML/CSS/JS. Every
content-heavy part of the site reads from a JSON file in `data/` so you can
update the site without touching the markup.

## Bilingual (FR / EN)

The site is **French by default** with an EN toggle in the header. The
visitor's choice is remembered in `localStorage`, so it carries across pages
and return visits. You can also link straight to a language with
`?lang=en` / `?lang=fr`.

There are two kinds of translated text:

**1. Interface strings** live in `data/i18n.json`, keyed by language:

```json
{ "fr": { "nav.team": "Équipe" }, "en": { "nav.team": "Team" } }
```

Markup opts in with an attribute naming the key:

| Attribute | Translates |
|---|---|
| `data-i18n` | the element's inner HTML (links/`<code>` allowed in the string) |
| `data-i18n-text` | the element's text only (used for `<title>`) |
| `data-i18n-placeholder` | an input's placeholder |
| `data-i18n-content` | a meta tag's `content` |
| `data-i18n-alt` / `data-i18n-aria-label` | `alt` / `aria-label` |
| `data-i18n-href` | a link's `href` — used for the two-language sponsor kit |

`{year}` in a string is replaced with the current year. Counts use
`…count.one` / `…count.other` — the plural rule differs per language
(French treats 0 as singular, English doesn't) and is handled for you.

The HTML ships with French copy inline as the fallback, so if the JSON ever
fails to load the site still reads correctly in French.

**2. Content in data files** — any translatable field accepts *either* a
plain string (identical in both languages, e.g. a proper noun) *or* an
object:

```json
"species": { "fr": "Doré", "en": "Walleye" },
"organizer": "Pro-Bass Canada"
```

Mix the two freely. Fields supporting this: `name`, `location`, `region`,
`species`, `organizer`, `type`, `notes` on events; `role`, `bio` on
team members; `name`, `handle` on socials.

Two things are deliberate: the region filter keys off the **French** value
internally, so switching language never resets the visitor's selection; and
search matches against *all* translations, so a French query still finds an
English-only entry.

To add a language, add a third block to `data/i18n.json`, add its code to
`SUPPORTED` in `assets/js/i18n.js`, add month names to `MONTHS` in
`assets/js/util.js`, and add a button to the `.lang-switch` in each page.

## Scripts

| File | Role |
|---|---|
| `util.js` | shared helpers (month names, date parsing, escaping, ordinals) |
| `i18n.js` | the FR/EN engine — must load before any renderer |
| `main.js` | nav toggle, footer year |
| `events.js` | upcoming-event lists (calendar + tournament guide) |
| `history.js` | results rendering **and** the shared `PMF_HISTORY` store |
| `team.js` | roster cards (reads `PMF_HISTORY` for the record strip) |
| `video.js` | homepage featured video (click-to-load facade) |
| `boats.js` | team boats section on the team page |
| `merch.js` | shop product grid |
| `calendar-view.js` | season-at-a-glance calendar + list/calendar toggle |
| `catches.js` | catch gallery **and** the shared `PMF_CATCHES` store |
| `sponsors.js` | partner logos — hides its whole section when there are none |
| `analytics.js` | GoatCounter beacon — inert until a site code is filled in |

Load order matters: `util.js` → `i18n.js` → renderer. `team.html` also loads
`history.js`, because the record strip on each card is computed from the
results data.

`tournament-page.js` is the exception: the generated pages under `tournois/`,
`pecheurs/` and `bateaux/` carry French in the HTML and English in `data-en`
attributes, and it swaps the two on the language click. Nothing on those pages
is rendered by JavaScript — that is the whole point of generating them.

## Build tools

These are run by hand, not at deploy time — GitHub Pages serves the repo as-is.

| File | Role |
|---|---|
| `tools/build-tournament-pages.py` | writes `tournois/*.html` from `data/quebec-tournaments.json`, and the index `data/tournament-pages.json` |
| `tools/build-profile-pages.py` | writes `pecheurs/*.html` and `bateaux/*.html` from `data/team-members.json` and `data/boats.json` |
| `tools/build-structured-data.py` | refreshes the JSON-LD blocks in the hand-written pages |
| `tools/build-sitemap.py` | rewrites `sitemap.xml`, with `lastmod` taken from git per page **and its data dependencies** |
| `tools/sync-html-fallbacks.py` | copies the French from `data/i18n.json` into the hard-coded HTML, and regenerates the `og:`/`twitter:` tags — `--check` exits 1 on drift |
| `tools/check-stale.py` | lists what has gone by, what has no date, and what sits below the page threshold |
| `tools/build-sponsor-kit.py` | builds the sponsor-kit HTML from `data/i18n.json` |
| `tools/render-sponsor-kit.js` | renders that HTML to PDF with Chromium |

The usual order after a content change:

```bash
python3 tools/build-tournament-pages.py   # if a tournament changed
python3 tools/build-profile-pages.py      # if a member or a boat changed
python3 tools/build-structured-data.py
python3 tools/sync-html-fallbacks.py
python3 tools/build-sitemap.py            # last — it reads git for lastmod
```

`build-profile-pages.py` imports its template — nav, footer, the `data-en`
helpers — from `build-tournament-pages.py` rather than copying it, so the two
families of generated pages cannot drift apart.

## Logo assets

| File | Use |
|---|---|
| `logo.png` | full crest on its cream paper — nav badge |
| `favicon.png` | browser tab / touch icon |
| `logo-mark-light.png` | white crest, transparent background — for dark surfaces |
| `logo-mark-dark.png` | navy crest, transparent background — for light surfaces |

The two `logo-mark-*` files are knockouts generated from `logo.png` (the
cream paper turned transparent, the ink recoloured). They're used as faint
watermarks behind the hero copy, behind the initials on each team card, and
in the video placeholder. If you replace the crest, regenerate both marks so
they stay in sync.

## Editing content

- **Team roster** → `data/team-members.json`. Each entry supports `id`
  (see **Members ↔ results**), `name`, `role`, `initials` (used as the
  placeholder photo), `bio`, and a `specs` block. Swap `initials`
  for a real headshot by editing the `member-photo` markup in
  `assets/js/team.js` if you add photo files under `assets/img/`.
- **Social links** → `data/socials.json`. `icon` must be one of
  `instagram`, `facebook`, `youtube`, `tiktok`, `mail` (see `social.html`),
  or add a new SVG to the `ICONS` map there.
- **Our schedule** → `data/team-schedule.json`.
- **Québec tournament directory** → `data/quebec-tournaments.json`.
- **Past results** → `data/tournament-history.json`.
- **Team boats** → `data/boats.json`.
- **Shop products** → `data/merch.json`.
- **Catches** → `data/catches.json`, photos in `assets/img/catches/`.
- **Featured video** → `data/featured-video.json`. Paste a YouTube video id
  (or a full YouTube URL — `watch?v=`, `youtu.be`, `shorts/` and `embed/`
  links are all parsed) into `videoId` and the homepage placeholder becomes
  the real clip. The homepage shows a click-to-load thumbnail rather than a
  live embed, so nothing is requested from YouTube until a visitor presses
  play, and the player then loads from `youtube-nocookie.com`.

  Optional fields added since: `photo` (a path under `assets/img/team/`,
  which replaces the initials and hides the crest watermark) and `photoAlt`
  (what the photo actually shows — write it yourself; it is the alt text).

  `assets/img/team/` holds **portraits only** — 3:4, roughly 900x1200 — and
  `assets/img/catches/` holds the catch photos at 4:3. Keeping the two apart
  matters: a file used on both pages shows the same image twice to anyone
  walking the site.

  **Verify anything you attribute before publishing it.** The cards once
  carried a quote each; the field is gone, but the lesson holds for bios and
  notes. The obvious Thoreau line about men who fish without knowing it is
  not fish they are after is apocryphal — the American Museum of Fly Fishing
  traced it and it appears nowhere in his work. It was nearly used here.

### Members ↔ results

Each member in `data/team-members.json` carries a stable `id`
(`kevin-caron`, `kevin-b`, `bobe`). Results reference those ids in a
`members` array, and that one link drives everything else:

```json
// data/team-members.json          // data/tournament-history.json
{ "id": "bobe", "name": "BOBE" }   { "members": ["kevin-caron", "bobe"], … }
```

- The record strip on each team card (tournaments fished, best finish,
  podiums) is **computed** from the results — never typed in by hand.
- "Voir son palmarès" links to `history.html?member=<id>`, which preselects
  that angler in the filter.
- The angler chips on each result link back the same way.

So adding one result with the right ids updates the results page, both
anglers' cards, and the team-wide stat tiles at once. If you add a member,
give them an `id` and use it in `members`; a result referencing an unknown
id still renders (it shows the raw id instead of a name).

### Angler specs

Each member has a `specs` block. Every row always renders — an empty value
shows a muted `—` so the card doubles as a fill-in sheet:

```json
"specs": {
  "homeWater": "Lac Saint-Pierre",
  "species": { "fr": "Achigan à petite bouche", "en": "Smallmouth bass" },
  "technique": "", "dreamCatch": "", "personalBest": "", "since": "2016"
}
```

To add or reorder spec rows, edit `SPEC_FIELDS` in `assets/js/team.js` and
add the matching `team.spec.*` labels to `data/i18n.json`.

### Angler gear

`gear` is the list a brand actually reads, so it behaves the opposite way from
`specs`: rows you leave out simply do not exist, and an empty `gear` array
hides the whole section. A half-filled tackle list does the application more
harm than no list at all.

```json
"gear": [
  { "label": { "fr": "Canne", "en": "Rod" },
    "value": { "fr": "St. Croix Mojo Bass 7'1\" MH", "en": "St. Croix Mojo Bass 7'1\" MH" } },
  { "label": { "fr": "Moulinet", "en": "Reel" }, "value": "Shimano Curado 200K" }
]
```

Both `label` and `value` take either a plain string or a `{fr, en}` pair, and
the order in the file is the order on the page. Put the things a sponsor cares
about first: rod, reel, line, and the go-to lure.

Run `python3 tools/build-profile-pages.py` after any change.

### Angler profile pages

Each member gets `pecheurs/<id>.html` — a real address to paste into a
pro-staff application. The page assembles itself from what is already in
`data/team-members.json` plus the results and catches logs: background, specs,
gear, the tournament record (with the percentile for each finish), the
documented catches, and a link to their boat. Every section hides itself when
its data is empty, so nothing has to be filled in before the page is usable.

The profile carries `Person` JSON-LD naming Pied Marin Fishing as the team, so
a search engine can connect the angler to the crew.

### Team boats

Boats appear as a section at the bottom of the team page (`#bateaux`), and
each card links through to the boat's own page. Same fill-in-sheet behaviour
as the angler specs — on the card every row shows, empty ones show `—`; on the
generated page the empty rows are simply left out:

```json
{
  "id": "boat-1",
  "name": { "fr": "Le Pied Marin", "en": "Le Pied Marin" },
  "skipper": "kevin-caron",
  "image": "assets/img/boats/boat-1.jpg",
  "description": { "fr": "…", "en": "…" },
  "specs": {
    "model": "Princecraft Xpedition 186",
    "year": "2022", "length": "18' 6\"",
    "engine": "Mercury 150 CT", "trolling": "Minn Kota Ulterra 112",
    "electronics": "Humminbird Helix 9"
  }
}
```

`skipper` takes a **member id** — set it and the card links through to that
angler's profile. Leave `image` empty and the crest watermark stands in. Add
more boats by adding more entries; they stack vertically.

To change which spec rows appear, edit `BOAT_SPEC_FIELDS` in
`assets/js/boats.js` and add matching `boats.spec.*` labels to
`data/i18n.json`.

A boat can be owned by one member and run by another: `skipper` and `owner`
each hold a member `id`. When they are the same person the two lines merge
into one rather than repeating the name.

### Boat pages and the restoration log

Each boat also gets `bateaux/<id>.html`, with a photo gallery and — when
there is one — the restoration log. The card on the team page links to it and
shows a status pill when a boat is in the shop.

```json
"gallery": ["assets/img/boats/1995-1.jpg", "assets/img/boats/1995-2.jpg"],
"restoration": {
  "status": "restoration",
  "entries": [
    { "date": "2026-08-15",
      "title": { "fr": "Ponçage du plancher", "en": "Sanding the floor" },
      "body":  { "fr": "…", "en": "…" },
      "photos": ["assets/img/boats/resto-1.jpg"] }
  ]
}
```

`status` takes `""` (nothing shown), `"restoration"` (*En restauration*) or
`"restored"` (*Restauré*). Entries are sorted newest first by the tool, so the
order in the file does not matter. `date` may be partial — `"2026"`,
`"2026-07"` or `"2026-07-15"` — and only what is known gets printed. An entry
needs a title or a body; `photos` is optional.

Empty `gallery` and empty `entries` each hide their own section, so a boat
that is not being worked on shows no restoration heading at all.

Run `python3 tools/build-profile-pages.py` after any change.

### Shop

`data/merch.json` holds a shop-wide `orderEmail` and optional `storeUrl`,
plus the product list:

```json
{
  "id": "tee",
  "name": { "fr": "T-shirt de l'équipe", "en": "Team t-shirt" },
  "description": { "fr": "…", "en": "…" },
  "price": "35 $",
  "sizes": ["S", "M", "L", "XL", "2XL"],
  "image": "assets/img/merch/tee.jpg",
  "url": "",
  "status": "available"
}
```

`status` is `available`, `soon` or `soldout` and drives the badge. **There is
no checkout** — deliberately, since this is a static site with no payment
backend. The order button falls back in this order: the product's own `url`
→ the shop-wide `storeUrl` → a `mailto:` link pre-filled with the product
name. Sold-out items get no button. If you later open a real store
(Shopify, Square, Etsy…), just fill in `storeUrl` and every product points
at it.

### Result entry shape

```json
{
  "id": "unique-id",
  "name": "Tournament name",
  "date": "2025-08-09",
  "region": "Outaouais",
  "location": { "fr": "…", "en": "…" },
  "species": { "fr": "Doré", "en": "Walleye" },
  "organizer": "",
  "placement": 1,
  "fieldSize": 41,
  "weight": "21,35 lb",
  "bigFish": "6,05 lb",
  "members": ["kevin-caron", "kevin-b"],
  "link": "",
  "notes": ""
}
```

`placement` and `fieldSize` are numbers; 1st/2nd/3rd get a podium colour and
the ordinal is written correctly per language (1re/2e vs 1st/2nd). Leave
either as `null` when the result isn't recorded yet — the card shows a muted
`—` rather than inventing a finish, and the stat tiles ignore it.

**Partial dates.** `date` may be `"2024"`, `"2024-05"` or `"2024-05-03"`.
Use the shortest form you can actually vouch for; the date badge shows only
what's known, and the season filter still works off the year either way.

**Scoring figures.** Weight tournaments can use the `weight` and `bigFish`
shortcuts. Length events (catch-photo-release, measured on a ruler) supply
their own labelled figures instead:

```json
"figures": [
  { "value": "104 cm", "label": { "fr": "2 plus longs brochets", "en": "2 longest pike" } }
]
```

A figure with an empty `value` doesn't render, so you can leave the labels in
place as a reminder of what to fill in.

All schedule/directory entries share this shape (any text field may be a
plain string or a `{ "fr": …, "en": … }` pair — see **Bilingual** above):

```json
{
  "id": "unique-id",
  "name": "Tournament name",
  "startDate": "2026-08-28",
  "endDate": "2026-08-30",
  "region": "Montérégie",
  "location": { "fr": "Plan d'eau", "en": "Lake / venue" },
  "species": { "fr": "Achigan", "en": "Bass" },
  "organizer": "Who runs it",
  "type": { "fr": "Étape de circuit", "en": "Circuit Stop" },
  "status": "confirmed",
  "link": "https://...",
  "notes": "Anything worth flagging"
}
```

Leave `startDate`/`endDate` as an empty string `""` for a recurring or
date-TBC entry. Partial dates work here too: `"2026-05"` renders as MAI 2026
when the organizer has only announced a month.

`status` drives the badge and the filtering:

| status | effect |
|---|---|
| `confirmed` | normal teal species badge |
| `tentative` | gold badge — date or details unverified |
| `cancelled` | red "Annulé / Cancelled" badge; **hidden from Upcoming** |

**List / Calendar.** The guide has two views of the same filtered set. The
calendar is a twelve-month season overview rather than a month-at-a-time
calendar: the season clusters into May–October, so paging through empty
winter months would hide its shape, and seeing the whole year at once is
what surfaces weekend collisions between circuits. Teal = a tournament,
gold = more than one that day, outline = today. Click a day to see its
cards. Month-only and undated events can't sit on a grid, so they appear as
a note under their month and in a strip below the calendar. The chosen view
is remembered in `localStorage`.

`initEventList` takes an `onRender({ filtered, renderCard })` callback — that
is how the calendar stays in sync with the filters without duplicating any
of them.

**Year.** Options are built from the dates in the data — add 2027 events and
2027 appears by itself. It defaults to *all years* rather than the current
one, so newly added future seasons are never hidden from the person who just
added them. Undated recurring entries aren't tied to a season, so a year
choice never filters them out.

**Upcoming / Past / All.** The guide defaults to *Upcoming* so a visitor sees
what they can still fish. Past events stay in the file (dimmed, badged
"Passé") because a finished season is the best predictor of next year's
dates. This is computed from the dates — nothing to maintain by hand. An
undated entry never counts as past, and a cancelled one never counts as
upcoming.

### Circuits, stops and seasons

Two fields classify every entry:

| Field | Values |
|---|---|
| `kind` | `single` (a one-off tournament), `circuit` (a series), `stop` (one leg of a series) |
| `circuit` | on a stop: the parent circuit's `id` |

A circuit carries **no dates of its own** — its stops do. Its *season* is
therefore inherited from its earliest stop; an entry with no date at all
belongs to no season and stays visible whichever season is selected.

The guide is organised by season, not by filters. There are only two
controls left: a season switch and a search box.

- The **season switch appears only when there is more than one season to
  show.** Today the directory covers 2026 alone, so it stays hidden and the
  page goes straight to the content. Add a 2027 tournament and the switch
  appears on its own, opening on the current year. Nothing to maintain.
- Within a season the list is **grouped by month** (`MAI 2026 · 4 événements`),
  which is why there is no month filter any more. Circuit stops appear in
  their own month, tagged with the name of their series, and the series
  themselves are listed once at the top with their stop count and link. So
  "what's on in June" and "what is this circuit" are both answerable without
  losing the other. Anything without a published date closes the page under
  *Dates pas encore publiées*.

A `tier` field still exists on every entry and is set to `regional`
throughout. The Bassmaster Elite and MLF Bass Pro Tour series were removed
in August 2026 — the directory covers events an angler here can actually
enter. `events.js` still accepts the `when`, `kind` and `year` filter
options; no page passes them, but they work if a future page wants one.

### Catches

`data/catches.json` is a catch log, not a photo dump — each entry names its
angler by member `id` and optionally the result it came from, so the gallery
links back into the roster and the palmarès:

```json
{
  "id": "brochet-2026",
  "angler": "kevin-caron",
  "species": { "fr": "Brochet", "en": "Pike" },
  "measure": "104 cm",
  "date": "2026-05-02",
  "water": { "fr": "Lac Saint-Pierre", "en": "Lac Saint-Pierre" },
  "event": "formule-brochet-2026",
  "media": { "type": "image", "src": "assets/img/catches/brochet-2026.jpg" },
  "gallery": [
    { "src": "assets/img/catches/brochet-2026-b.jpg",
      "alt": { "fr": "Le brochet de profil", "en": "The pike in profile" } }
  ],
  "featured": true
}
```

- `media.type` is `image` (with `src`) or `youtube` (with `videoId`). Leave it
  empty and the crest stands in with a *Photo à venir* label.
- A YouTube tile shows a thumbnail and only contacts YouTube once someone
  presses play — same click-to-load facade as the homepage video.
- `gallery` holds more photos of the **same** fish. `media` stays the cover
  shown on the card; the extra shots appear after it in the lightbox and the
  card gets a `1/3` badge. An entry is either a plain path or an object with
  its own bilingual `alt`; leave the array empty when there is only one photo.
- Clicking any photo opens the lightbox: arrows, swipe, Esc, full keyboard
  support — and nothing advances on its own.
- `featured: true` on **one** catch lifts it into the large *Prise vedette /
  Featured catch* block above the grid, where it is no longer repeated as a
  card. Applying any filter hides that block and returns every match to the
  grid. Set it on a different catch to move the spotlight.
- `event` takes a **`tournament-history.json` id**, and `angler` a
  **`team-members.json` id**. Each team card shows its angler's catch count
  and deep-links to `catches.html?angler=<id>`.
- `date` accepts the same partial forms as everywhere else — `"2026"`,
  `"2026-05"` or `"2026-05-02"`.

Resize photos to roughly 1200px on the long edge before committing; full
camera files bloat the repo for no visible gain.


A catch shown as a **photo** can still link out to a clip: set `media.videoId`
alongside `media.src` and the card gains a "Watch the video" link under the
notes. The photo stays — the video does not replace it. That only applies when
`media.type` is `"image"`; when the catch *is* a video (`"youtube"`), the player
facade already handles it.

### Event specs

Each event carries a `specs` block rendered as a scannable strip on the card:

```json
"specs": {
  "fee":      { "fr": "600 $ / équipe (300 $ / pêcheur)", "en": "$600 / team ($300 / angler)" },
  "teamSize": { "fr": "Équipe de 2", "en": "Team of 2" },
  "maxTeams": "100",
  "hours":    { "fr": "7 h – 14 h", "en": "7 am – 2 pm" },
  "deadline": { "fr": "1er août 2026", "en": "1 August 2026" },
  "format":   { "fr": "100 % remise à l'eau", "en": "100% catch-and-release" }
}
```

**`fee` and `teamSize` always render**, even when empty — an unknown one
shows a muted *Non publié / Not published* rather than silently disappearing,
so a reader can tell "we don't know" from "it's free". The other four appear
only when filled in. Search covers the spec text too, so `910` finds every
Excellence Bass stop.

Of the 21 entries, **9 publish an entry fee and 14 publish a team format**.
The rest genuinely aren't published: the organizers' own sites don't carry
them. Don't guess — a wrong fee is worse than an honest blank. Filling these
in is a phone call, not a code change, and it is the single biggest
improvement left for the directory.

#### Registration deadline

`deadline` is human-readable prose (*"Paiement avant le 31 mai 2026"*), which
is fine to read and impossible to compute with. A second field carries the
machine-readable version:

```json
"deadline":     { "fr": "Préinscription avant le 30 septembre 2026", "en": "Pre-register before 30 September 2026" },
"deadlineDate": "2026-09-30"
```

When `deadlineDate` is present the card shows a countdown — *Inscriptions :
encore 34 jours* — which turns amber at seven days or fewer and becomes a
plain *Inscriptions fermées* once the date has passed. Four entries have one.
**Only ever fill `deadlineDate` from a date the organizer actually published**;
it drives a claim about time, so a guess is worse here than anywhere else.

#### Add to calendar

Every entry with an exact day and a status other than `cancelled` gets an
*Ajouter au calendrier* button. `events.js` builds the `.ics` in the browser
and hands it to the visitor — no server, which is what makes it work on
GitHub Pages. `DTEND` is set to the day after the end date, because an
all-day `DTEND` is exclusive. Thirteen of the 21 entries qualify; the rest
have no exact day, and an event without a date has no business in someone's
calendar.

The team is positioned throughout as a **multi-species** team — pike, bass,
walleye — rather than a bass specialist, which is what its results actually
show.

### What is real, and what is not

Everything on the site is either a verified fact or an honest blank. As of
August 2026:

| Filled in | Still open |
|---|---|
| The three anglers — bios, all six specs, roles, photos | Tournament placements and measurements |
| The two boats — Princecraft Holiday 1996 and 1995, with owner and skipper | Merch products, sizes and prices |
| Three catches, with species, water, date and photo | Entry fees for 12 of the 21 directory entries |
| The four social accounts, confirmed by the team | |
| The three Formule Brochet dates: 4 May 2024, 3 May 2025, 2 May 2026 | |

The results carry `placement: null` and empty `figures` on purpose. The
team fished all three editions; nobody has dug up the score sheets yet, and
the site says so rather than inventing a ranking.

The directory holds **21 entries for the 2026 season**, compiled from
organizer sites in August 2026. Coverage is strongest in the Montérégie and
the Southwest and thinner elsewhere, which is what the guide's own intro
says — the site claims province-wide *scope*, not province-wide *density*.
Each entry's `notes` and `link` carry its source and any caveat: an
unconfirmed date, an organizer page that contradicts itself, a cancelled
circuit. It is rounded out with links to continuously-updated calendars
(Pêcheur Québec, Sur Le Spot, FédéCP, Coteau-du-Lac).

Tournament dates change. Keep this file current, and always tell readers to
confirm with the organizer.

### The sponsor kit

`tools/build-sponsor-kit.py` reads `data/i18n.json` and
`data/team-members.json` and writes one letter-size HTML page per language;
`tools/render-sponsor-kit.js` renders each to PDF with Chromium. The output
lives in `assets/docs/` and is linked from `sponsors.html` — the download
button swaps to the right language through `data-i18n-href`.

```bash
python3 tools/build-sponsor-kit.py
node  tools/render-sponsor-kit.js
```

Because the kit is generated from the same JSON as the website, fixing a
fact in one place fixes it in both. Regenerate after any change to the
roster or the sponsor copy, and update the season label in
`tools/build-sponsor-kit.py` when the season turns.

`data/sponsors.json` is an empty array. The *Nos partenaires* section on
`sponsors.html` hides itself while it stays that way — an empty grid under
that heading would say the opposite of what the page is for.

## Running locally

No build step needed — just serve the folder over HTTP (fetching the JSON
data files requires `http://`, not `file://`):

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Analytics

`assets/js/analytics.js` holds one constant:

```js
const GOATCOUNTER_SITE = "";
```

Empty, the file does nothing at all — no script loaded, no request, no
visitor counted. Fill in a GoatCounter site code and the pageview beacon
starts on every page. That is the entire configuration.

GoatCounter was chosen over Cloudflare Web Analytics for two reasons that
matter to a seasonal team: it keeps data for as long as the account is
active, so May 2027 can be compared against May 2026, and it parses UTM
tags, so a link posted on Instagram can be told apart from one posted on
Facebook. Cloudflare keeps six months and logs no query strings.

It sets no cookie and stores no persistent identifier, which is what keeps
the site clear of a consent banner under Québec's Law 25 — that law applies
to technologies that identify or profile a person. Adding Google Analytics
here would change that, and would also break the site's one privacy
promise: nothing reaches a third party until a visitor presses play on the
video.

Ad blockers will stop the beacon for some visitors, so treat the numbers as
a floor, not a census.

## Deployment

The site is **live** at <https://piedmarinfishing.com>, served by GitHub Pages
from the `main` branch, root folder. There is nothing to compile: pushing to
`main` publishes.

### Custom domain: piedmarinfishing.com

The repo root holds a `CNAME` file containing `piedmarinfishing.com`. **Do not
delete it** — GitHub Pages reads that file to know which domain to serve, and
losing it drops the site back to the `github.io` URL.

DNS lives at Porkbun and is already pointed correctly. Verified against
public resolvers:

```
piedmarinfishing.com       ->  185.199.108-111.153        (GitHub Pages)
www.piedmarinfishing.com   ->  kevincaron28.github.io
MX                         ->  fwd1/fwd2.porkbun.com      (email forwarding)
TXT                        ->  v=spf1 include:_spf.porkbun.com ~all
```

Porkbun's `ALIAS` at the apex is what points at `kevincaron28.github.io`; it
survives GitHub changing its IPs, so prefer it over hard-coding the four A
records. Two of Porkbun's defaults were removed and should stay removed: the
`ALIAS` to `uixie.porkbun.com` (their parking page) and the wildcard
`CNAME *.piedmarinfishing.com`. GitHub explicitly advises against wildcard DNS
on a Pages domain — it lets anyone claim an unregistered subdomain.

The `MX` and SPF `TXT` records carry email forwarding for
`info@piedmarinfishing.com`, which the whole site uses as its contact address.
They don't conflict with Pages — leave them alone.

**Enforce HTTPS** is on in the repo's Pages settings.
