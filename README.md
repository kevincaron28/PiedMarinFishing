# Pied Marin Fishing

Pied Marin Fishing - Fishing Team Quebec

A static website for the team: landing page, roster, socials, our tournament
schedule, and a community-maintained guide to fishing tournaments across
Québec.

## Pages

| File | Purpose |
|---|---|
| `index.html` | Landing page |
| `team.html` | Team roster |
| `social.html` | Social media links |
| `calendar.html` | Our team's own tournament schedule |
| `tournaments.html` | Region-wide Québec tournament directory (for any angler, not just the team) |

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
`assets/js/events.js`, and add a button to the `.lang-switch` in each page.

## Editing content

- **Team roster** → `data/team-members.json`. Each entry supports `name`,
  `role`, `initials` (used as the placeholder photo), `bio`, `quote`. Swap
  `initials` for a real headshot by editing the `member-photo` markup in
  `team.html` if you add photo files under `assets/img/`.
- **Social links** → `data/socials.json`. `icon` must be one of
  `instagram`, `facebook`, `youtube`, `tiktok`, `mail` (see `social.html`),
  or add a new SVG to the `ICONS` map there.
- **Our schedule** → `data/team-schedule.json`.
- **Québec tournament directory** → `data/quebec-tournaments.json`.

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

**The current roster, social handles, and team schedule are placeholders** —
replace them with your real team's info before publishing. The Québec
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
