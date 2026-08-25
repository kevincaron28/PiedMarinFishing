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
the ordinal is written correctly per language (1re/2e vs 1st/2nd). `weight`
and `bigFish` are free-text strings, so use whatever unit you actually weigh
in.

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

Leave `startDate`/`endDate` as an empty string `""` for a "date TBD" entry.
`status: "tentative"` renders a gold badge instead of teal.

**The roster names are real; their bios, specs, roles and photos are not
filled in yet.** The social handles, team schedule and past results are all
still placeholders — replace them with your real info before publishing.
Sample entries are prefixed `EXEMPLE` / `SAMPLE` so they are obvious. The Québec
tournament directory was seeded with a few tournaments verified against
organizer sites in August 2026 (see the `notes`/`link` field on each entry
for the source) plus links out to a few live, continuously-updated calendars
(Pêcheur Québec, Sur Le Spot, etc.) for anything not yet in our own list.
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
