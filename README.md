# Pied Marin Fishing

Pied Marin Fishing - Fishing Team Quebec

A static website for the team: landing page, roster, socials, our tournament
schedule, and a community-maintained guide to fishing tournaments across
Québec.

## Pages

| File | Purpose |
|---|---|
| `index.html` | Landing page |
| `team.html` | Team roster — bios, angler specs, per-member record |
| `history.html` | Palmarès: past tournament results, filterable by member and season |
| `calendar.html` | Our team's own upcoming tournament schedule |
| `tournaments.html` | Region-wide Québec tournament directory (for any angler, not just the team) |
| `merch.html` | Shop — apparel and gear |
| `social.html` | Social media links |

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
`species`, `organizer`, `type`, `notes` on events; `role`, `bio`, `quote` on
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

Load order matters: `util.js` → `i18n.js` → renderer. `team.html` also loads
`history.js`, because the record strip on each card is computed from the
results data.

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
  placeholder photo), `bio`, `quote`, and a `specs` block. Swap `initials`
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
- **Featured video** → `data/featured-video.json`. Paste a YouTube video id
  (or a full YouTube URL — `watch?v=`, `youtu.be`, `shorts/` and `embed/`
  links are all parsed) into `videoId` and the homepage placeholder becomes
  the real clip. The homepage shows a click-to-load thumbnail rather than a
  live embed, so nothing is requested from YouTube until a visitor presses
  play, and the player then loads from `youtube-nocookie.com`.

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

### Team boats

Boats render as a section at the bottom of the team page (`#bateaux`), not
their own page. Same fill-in-sheet behaviour as the angler specs — every row
shows, empty ones show `—`:

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
angler's results. Leave `image` empty and the crest watermark stands in. Add
more boats by adding more entries; they stack vertically.

To change which spec rows appear, edit `BOAT_SPEC_FIELDS` in
`assets/js/boats.js` and add matching `boats.spec.*` labels to
`data/i18n.json`.

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

**Upcoming / Past / All.** The guide defaults to *Upcoming* so a visitor sees
what they can still fish. Past events stay in the file (dimmed, badged
"Passé") because a finished season is the best predictor of next year's
dates. This is computed from the dates — nothing to maintain by hand. An
undated entry never counts as past, and a cancelled one never counts as
upcoming.

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

Only 8 of the 19 events publish an entry fee and 11 publish a team format;
the rest genuinely aren't published by their organizers. Don't guess — a
wrong fee is worse than an honest blank.

**The roster names are real; their bios, specs, roles and photos are not
filled in yet.** The three Formule Brochet entries in the results are real
events, but their placements and measurements still need filling in. The
social handles, boats, shop products and the upcoming team schedule are
still placeholders —
sample entries are prefixed `EXEMPLE` / `SAMPLE` so they are obvious. The Québec
tournament directory holds 19 entries for the 2026 season, compiled from
organizer sites in August 2026 with close coverage of the Montérégie, the
St. Lawrence, the Richelieu and Lake Champlain — the Big Bass Québec program,
the Coteau-du-Lac Excellence Bass series, Challenge Carpe Québec, the Fête de
la pêche and more. Each entry's `notes`/`link` carries its source and any
caveat (unconfirmed dates, an organizer page that contradicts itself, a
cancelled circuit). It's rounded out with links to continuously-updated
calendars (Pêcheur Québec, Sur Le Spot, FédéCP, Coteau-du-Lac).
Tournament dates change — keep this file current, and always tell readers to
confirm with the organizer.

## Running locally

No build step needed — just serve the folder over HTTP (fetching the JSON
data files requires `http://`, not `file://`):

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploying to GitHub Pages

1. Push this repo to GitHub (already done if you're reading this from the repo).
2. In the repo settings, go to **Pages** → set source to the `main` branch, root folder.
3. The site will be live at `https://<username>.github.io/<repo>/` within a few minutes.

No further configuration needed — there's nothing to build.
