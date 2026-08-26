Drop catch photos here, then point `media.src` at them in `data/catches.json`:

    "media": { "type": "image", "src": "assets/img/catches/brochet-2026.jpg" }

For a clip instead, use a YouTube id — the tile shows a thumbnail and only
contacts YouTube once someone presses play:

    "media": { "type": "youtube", "videoId": "abc123XYZ_1" }

Resize photos to roughly 1200px on the long edge before committing. Full
camera files bloat the repository and slow the page down for no visible gain.
