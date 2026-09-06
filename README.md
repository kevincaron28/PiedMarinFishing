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
| `tools/build-catch-pages.py` | writes `prises/*.html` for the catches that clear the threshold, from `data/catches.json` |
| `tools/build-structured-data.py` | refreshes the JSON-LD blocks in the hand-written pages |
| `tools/build-sitemap.py` | rewrites `sitemap.xml`, with `lastmod` taken from git per page **and its data dependencies** |
| `tools/sync-html-fallbacks.py` | copies the French from `data/i18n.json` into the hard-coded HTML, and regenerates the `og:`/`twitter:` tags — `--check` exits 1 on drift |
| `tools/check-private.py` | refuses to let a registration number, plate or serial reach `data/` or a generated page; exits 1 on a hit |
| `tools/check-stale.py` | lists what has gone by, what has no date, and what sits below the page threshold |
| `tools/build-image-variants.py` | writes the 160/400/800px versions of every photo and the `data/image-variants.json` map that `srcset` is built from |
| `tools/build-sponsor-kit.py` | builds the sponsor-kit HTML from `data/i18n.json` |
| `tools/build-angler-sheets.py` | writes one Letter-size pro-staff sheet per angler per language, from `data/team-members.json` and the results/catches logs |
| `tools/render-angler-sheets.js` | renders those to `assets/docs/pro-staff-<id>-<lang>.pdf` |
| `tools/render-sponsor-kit.js` | renders that HTML to PDF with Chromium |

The usual order after a content change:

```bash
python3 tools/build-image-variants.py     # if a photo was added
python3 tools/build-tournament-pages.py   # if a tournament changed
python3 tools/build-profile-pages.py      # if a member or a boat changed
python3 tools/build-structured-data.py
python3 tools/sync-html-fallbacks.py
python3 tools/build-sitemap.py            # last — it reads git for lastmod
```

`build-profile-pages.py` imports its template — nav, footer, the `data-en`
helpers — from `build-tournament-pages.py` rather than copying it, so the two
families of generated pages cannot drift apart.

### Responsive photos

Every photo under `assets/img/{catches,team,boats}` is also written at 160,
400 and 800px wide, next to the original. `data/image-variants.json` records
which widths exist, and both the renderers (`PMF_IMG` in `util.js`) and
`build-profile-pages.py` build a `srcset` from it.

A photo that is **not** in the map is served at full size with no `srcset` —
adding a photo without re-running the tool costs bytes, never a broken image.
The `sizes` attribute is measured, not guessed: a hall-of-fame thumbnail is
72px at every breakpoint, a catch card is 346px, the featured catch 583px.

Before this, the 72px thumbnail was downloading the 1200px original — 16.7x
too much — and `catches.html` weighed 1.27 MB.

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
- **La relève / next generation** → `data/next-gen.json` (see **La relève**).
- **Shop products** → `data/merch.json`.
- **Federations and associations** → `data/organizations.json` (see
  **Fédérations et associations**).
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

**Mobile length.** The guide was **40 279 px — 48.5 phone screens** at 390×830,
and 79 % of that was the cards themselves (736 px each). Three options bring
it to 19.4 screens without removing anything:

- `trimWhenPaged: true` drops the specs block, the region and the organizer
  name from a card **when that tournament has its own page** — 250 px per card
  that `tournois/<id>.html` repeats verbatim. The 15 entries with no page keep
  everything, since there would be nowhere else to read it. Same idea as
  `lean` (our calendar), different motive, so it is a separate flag.
- Month blocks render as `<details>`, collapsed when **every** event in them
  is past. Nothing is removed: the content stays in the DOM (crawlers and
  in-page search still see it) and one tap opens it. A filter or a search
  suspends collapsing entirely — hiding a result somebody just asked for
  would be absurd.
- `monthNavSelector` renders the sticky month strip. It is rebuilt on every
  render, so it can never point at a month the filters removed; it scrolls
  itself to the current month; and it is hidden in calendar view, where its
  anchors would lead into a hidden list.

Two details worth keeping: the month `<h2>` lives **inside** the `<summary>`
(the spec allows it) because without it the page jumped h1 → h3 and screen
readers lost the months from their heading list. And `#ev-<id>` card anchors
reopen their collapsed month before scrolling, so a shared link never lands
on a closed block.

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

### La relève

`data/next-gen.json` holds the team's kids, rendered by `assets/js/next-gen.js`
into the *La nouvelle génération* section of `team.html`. They are minors, so
the shape of this file is deliberately narrow: **first name only, no surname,
no age, no birth date, no photo, no page.** They are kept out of
`data/team-members.json` on purpose — everything in that file gets a public
profile page under `pecheurs/` and a `Person` JSON-LD block, and none of that
belongs to a child.

```json
{
  "id": "romy",
  "name": "Romy",
  "relation": { "fr": "Fille de Kevin Caron", "en": "Kevin Caron's daughter" },
  "parent": "kevin-caron",
  "status": "fishing",
  "catch": "perchaude-2025",
  "story": { "fr": "…", "en": "…" }
}
```

- `name` may be empty. The `relation` then becomes the card's heading, which
  is how a child is listed before there is anything to say about them.
- `parent` is a **`team-members.json` id** and is the card's only link — it
  points at the parent's profile. It is rendered only when `name` is filled,
  since otherwise the heading already says it.
- `status` is `fishing`, `growing` or `expected`; each maps to a
  `team.nextGen.status.*` label in `data/i18n.json`.
- `catch` is a **`catches.json` id**. The card reads the species and the
  **month** back out of the catch log rather than repeating them, so the two
  cannot drift — and the exact day of a child's outing stays off the page.
- Empty file, no section: it hides itself like every other block on the site.

### Two kinds of gear, and why they must not be mixed

A catch page answers "caught on what?" — but there are two possible answers and
confusing them prints something false. If the catch carries its own `gear`
array, that is what was used *that day* and it appears under **Le matériel**.
If it does not, the page falls back to the angler's kit from
`team-members.json`, under a heading that says so — **L'équipement habituel de
Kevin B.** — with a line noting it is not necessarily what was in his hands.

The 50-inch muskie is why. It was trolled on a small crankbait, while Kevin
B.'s go-to lure on his profile is a chatterbait; the page was printing
*chatterbait* under a heading that read as this catch's gear. A per-catch
`gear` entry now carries the truth:

```json
"gear": [
  { "label": {"fr": "Présentation", "en": "Presentation"},
    "value": {"fr": "À la traîne",  "en": "Trolling"} },
  { "label": {"fr": "Leurre",       "en": "Lure"},
    "value": {"fr": "Petit crankbait", "en": "Small crankbait"} }
]
```

Only what the angler actually reported goes in. No brand or model was given for
that crankbait, so none is printed.

### Approximate dates, and what the story does not say

**Rule: when a fish was landed outside its open season, the catch carries a
coarse date and the story does not name the season.** Not because anything was
done wrong — the crew fishes legally for an open species and releases anything
else at once — but a public page with a precise date next to a closed-season
species invites a fine over conduct that was lawful.

Coarsen the `date` field: `"2025-05-23"` becomes `"2025"`. Every renderer
already handles partial dates and prints only what it knows, on the card, the
page and the profile alike. The page threshold accepts a year alone for exactly
this reason — a deliberately rounded date must not delete a page.

Say less, do not say anything false. The 50-inch muskie's story still carries
what matters and what reflects well: *on était au brochet, pas au maskinongé*,
measured on the cradle, back in the water in seconds, not a hook left in it.
Only the words *hors saison* and the exact day came out. Nothing in the text
became untrue; the page simply stops dating something it has no reason to date.

This cannot be checked automatically — it needs a species-and-zone regulation
table nobody maintains here — so it lives as a rule. Québec muskie and bass in
zones 7 and 8 open 15 June; walleye opens 10 May; pike opens in early May.

### Never publish an identifying number

```bash
python3 tools/check-private.py    # exits 1 on a hit — run it before pushing
```

The repository is public. A boat registration, a plate or a serial has no place
in `data/` or in a generated page — not in a photo, and **not in the text that
describes the photo**, which is the mistake that prompted this script. The
1995's registration was masked out of the image, then written back into its
alt text, where it sat unseen until captions became visible.

The word `registration` is deliberately *not* a trigger: in tournament English
it means *inscription* and appears throughout the directory. A check that cries
wolf gets ignored. The named-number rule fires on `immatriculation`, `plaque
d'immatriculation`, `licence plate`, `numéro de série`, `serial number`, `hull
id` and `VIN`, and only when what follows actually looks like an identifier —
six or more digits, or letters mixed with digits.

Verified both ways: it blocks the exact sentence that went live, the same with
a space, the English wording, a trailer plate and an engine serial; it passes
`Inscription jusqu'au 14 août`, `Pre-registration rate ran until 14 August`
and `un maskinongé de 50 po`.

### Galleries: captions and the lightbox

`assets/js/lightbox.js` holds `PMF_LIGHTBOX` — swipe, arrows, Esc, focus trap,
counter, neighbour preloading. It used to live inside `catches.js`, so only
`catches.html` had it. The generated pages showed their galleries with no way
to open them, and that was a real defect rather than a missing luxury: the boat
grid crops every photo to 4:3 with `object-fit: cover`, so **three of the ten
restoration photos could not be seen in full anywhere on the site.**

One definition, several consumers. `catches.html` must load `lightbox.js`
*before* `catches.js`; the generated pages load it from the shared footer in
`build-tournament-pages.py` and call `initGalleryLightbox("[data-gallery]")`.
On a tournament page, which has no gallery, that call returns immediately.

**Captions.** Every photo in `boats.json` and `catches.json` already carried a
rich bilingual description — but only in `alt`, where it reached screen readers
and nobody else. It is now a visible `<figcaption>`, and the img drops to
`alt=""`: the caption sits directly below and repeating the text would have it
announced twice. `seo.js` accepts an empty alt inside a `<button>`, which is
exactly where these live. The gain is measurable — the catch page went from 236
to 336 words, the boat page to 422, all of it text that was already written.

`initGalleryLightbox` rebuilds its slide list on every open rather than caching
it. On a generated page French and English live in the same DOM and the visible
caption changes when the language does; ten photos make that free.

One fix came out of this. The backdrop was `rgba(7, 23, 38, 0.92)` — at 8%
the page's own text showed through and landed directly on the lightbox
caption, making both unreadable. It is opaque now. That was pre-existing on
`catches.html`; making more galleries clickable is what exposed it.

### Catch pages, and the threshold that decides them

Every catch card on `catches.html` carries an `id="c-<id>"`, so a single catch
has an address. That is what the angler profiles link to: a thumbnail on
`pecheurs/kevin-b.html` goes to `catches.html#c-maskinonge-kevin-b`, not to the
filtered list. Three things make that anchor actually work:

- The cards are rendered by JavaScript, so the browser has already given up
  scrolling by the time they exist — `catches.js` redoes the jump itself, and
  clears the header height so the card is not hidden under it.
- If a filter is active and excludes the target, the filter is lifted rather
  than leaving the visitor on a page that lacks what they came for.
- The card gets `.catch-targeted` for 2.6 s. On a page of seven catches,
  "which one?" is a real question; a permanent highlight would read as state
  rather than as an answer.

`tools/build-catch-pages.py` then writes a full page per catch — but only for
catches that deserve one:

| Requirement | Why |
|---|---|
| a date (year and month at least) | |
| a body of water | |
| **1 photo** | |
| **a 120-word story** (`story`, bilingual) | below that the page fails `seo.js` |

The first cut of this threshold asked for three photos and a 60-word story.
That was the wrong balance: a catch page's substance is the story, not the
photo count. One good photo and 120 words earn an address; three photos and
two sentences do not. The word count is calibrated, not guessed — `seo.js`
rejects a page under 120 words, and the resulting page comes in at 223 words
in French, 219 in English. A generated page passes our own audit, or it is not
generated.

The script prints what each catch is missing, so the next one to clear the bar
is obvious:

```
malachigan-2025          récit (0/120 mots)
```

**Inbound links matter as much as the page.** A generated page nobody links to
is the orphan problem this repo already fixed once. So the generator also
writes `data/catch-pages.json`, and two readers use it: the card on
`catches.html` grows a *Lire le récit →* link, and the thumbnail on the
angler's profile points at the page instead of the `#c-` anchor. Catches
without a page keep the anchor.

A catch that later drops back below the threshold has its page deleted on the
next run — otherwise an orphan would stay served while absent from the sitemap.

The page itself pulls the gear straight from `team-members.json` rather than
copying it into the catch: "caught on what?" is the question a reader and a
brand both ask, and there should be one answer, not two. JSON-LD is `Article`
— a catch report is an illustrated story, not an event or a product — and it
declares only what is true: no invented publication date, and no author unless
the angler is on the roster.

### Pro-staff sheets

A pro-staff application is handled angler by angler — a rod brand wants to
know what *this* angler holds, not what the crew averages. So each angler
gets a one-page Letter PDF, in both languages, to send alongside the
sponsorship kit:

```bash
python3 tools/build-angler-sheets.py          # writes sheet-<id>-<lang>.html
node tools/render-angler-sheets.js <dir>      # → assets/docs/pro-staff-<id>-<lang>.pdf
```

Nothing is typed into the builder. The bio, the six spec rows, the gear, the
tournament results and the catches all come from `data/`, so a sheet and the
angler's web page at `pecheurs/<id>.html` cannot drift apart. An angler with
no gear entries gets no gear section rather than an empty one — a half-filled
list hurts the application.

Both PDFs are linked from the angler's own page, side by side regardless of
the displayed language: an English-speaking brand should not have to switch
the interface to find theirs.

Two things the renderer checks, because both bit once:

- **Overflow.** `.sheet` is `overflow: hidden`, so a block that runs past the
  page is silently clipped and `scrollHeight` reports nothing wrong. The
  renderer instead compares the bottom of the last block against the top of
  the footer, which catches content that is *covered* as well as content that
  spills. It prints the remaining margin for every sheet; Kevin Caron's is the
  tightest at 21 px, because he has five gear rows to the others' two.
- **Whose boat.** BOBE owns the 1996 and Kevin B. skippers it. Labelling both
  "his boat" is true but vague, so the sheet names the actual role — *Aux
  commandes de* for the skipper, *Propriétaire de* for the owner.

The "what I can't offer yet" block reuses `sponsors.honestBody` rather than a
second copy, so the sheets and the kit make the same admission about having no
audience numbers.

### Fédérations et associations

`data/organizations.json` feeds the *Fédérations et associations* block at the
bottom of `tournaments.html` through `assets/js/organizations.js`. The guide is
its home for a reason: it is the page anglers already read as a reference, and
keeping the list in one place is what stops two copies from drifting apart.
`sponsors.html` links here rather than repeating it.

A list like this is an easy place to imply a relationship nobody granted, so
the module is built to make that hard: **nothing in the JSON can assert one.**
Every tie shown is *computed* by matching `organizerMatch` against the
`organizer` field of three files:

| Source | Chip |
|---|---|
| `tournament-history.json` | *N tournois pêchés depuis YYYY* |
| `team-schedule.json` | *N tournois à notre calendrier* |
| `quebec-tournaments.json` | *N tournois au répertoire* |
| nothing matched | *On suit leur travail* |

```json
{
  "id": "muskies-canada",
  "name": "Muskies Canada — section Montréal",
  "what": { "fr": "…", "en": "…" },
  "link": "https://muskiescanada.ca/montreal/",
  "organizerMatch": ["Muskies Canada"]
}
```

- Matching ignores case and accents, so `Muskies Canada Montréal` and
  `Muskies Canada — section Montréal` are the same organization. An empty
  array, or no match, falls back to *On suit leur travail* — never to a number.
- The *fished since* year is the earliest matching result's year. Nothing is
  written by hand, so a line cannot outrun the record. This replaced three
  hand-written notes, one of which had already gone stale: it credited
  L'Amical to the APSQ, while the directory says *Club April Marine avec Big
  Bass Québec*.
- `member: true` is the **only** way to claim membership, and setting it on
  any organization hides the *we belong to none of them* line under the list —
  so that sentence can never turn into a lie.
- Empty file: the heading, the list and the note all disappear together.

The external links here cannot be reached from a sandboxed session (the egress
proxy blocks every outside host), so they are transcribed from search results
and should be clicked by hand once before anyone leans on them.

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
- A catch landed by someone who is **not** on the roster leaves `angler`
  empty and names them in `anglerName` (bilingual) instead. The card then
  shows a plain chip rather than a link, and the catch stays out of every
  member's count. That is how the kids' catches are logged — they have no
  profile page by design.
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
