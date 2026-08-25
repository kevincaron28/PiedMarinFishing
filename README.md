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

All schedule/directory entries share this shape:

```json
{
  "id": "unique-id",
  "name": "Tournament name",
  "startDate": "2026-08-28",
  "endDate": "2026-08-30",
  "region": "Montérégie",
  "location": "Lake / venue",
  "species": "Bass",
  "organizer": "Who runs it",
  "type": "Circuit Stop",
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
