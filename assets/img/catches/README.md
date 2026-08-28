Drop catch photos here, then point `media.src` at them in `data/catches.json`:

    "media": { "type": "image", "src": "assets/img/catches/brochet-2026.jpg" }

For a clip instead, use a YouTube id — the tile shows a thumbnail and only
contacts YouTube once someone presses play:

    "media": { "type": "youtube", "videoId": "abc123XYZ_1" }

Several photos of the same fish? Keep the best one in `media` — it is the cover
on the card — and list the rest in `gallery`. They follow the cover in the
lightbox and the card picks up a `1/3` badge:

    "media":   { "type": "image", "src": "assets/img/catches/brochet-2026.jpg" },
    "gallery": [
      { "src": "assets/img/catches/brochet-2026-b.jpg",
        "alt": { "fr": "Le brochet de profil", "en": "The pike in profile" } },
      "assets/img/catches/brochet-2026-c.jpg"
    ]

An entry is either a plain path or an object with its own bilingual `alt`.
Without one, the photo reuses the catch's description.

Resize photos to roughly 1200px on the long edge before committing. Full
camera files bloat the repository and slow the page down for no visible gain.
