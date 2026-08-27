# tools/

## Trousse de commandite

`build-sponsor-kit.py` lit `data/i18n.json` et `data/team-members.json`, puis
écrit un HTML de format lettre par langue. `render-sponsor-kit.js` le rend en
PDF avec Chromium.

La trousse se régénère donc à partir des mêmes textes que la page
`sponsors.html` : corriger un fait sur le site le corrige aussi dans le PDF.

```
python3 tools/build-sponsor-kit.py
node tools/render-sponsor-kit.js
```

Les PDF publiés sont dans `assets/docs/`.
