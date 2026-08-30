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

## Floutage des arrière-plans de prises

Le floutage se fait maintenant en amont, hors du dépôt : les photos
arrivent déjà traitées. Le script `blur-catch-backgrounds.py` qui régénérait
les images depuis les originaux a été retiré — ses fichiers sources n'étaient
pas versionnés et ses chemins de sortie ne correspondent plus à
l'arborescence (`assets/img/team/` ne contient que des portraits depuis que
les photos de prises vivent dans `assets/img/catches/`).

Le principe reste bon à connaître : une rive, une tour ou un quai suffisent
à situer un spot, et un spot à maskinongé se garde. Ce qui se trouve
directement derrière une tête reste toujours le point faible d'un floutage
automatique — recadrer plus serré à la source règle le problème mieux qu'un
masque.

## Données structurées

`build-structured-data.py` écrit le JSON-LD dans `index.html` (l'équipe) et
`tournaments.html` (la liste des tournois datés). Les moteurs de recherche
lisent ce balisage pour afficher les événements dans leurs résultats.

```
python3 tools/build-structured-data.py
```

À relancer après avoir modifié `data/quebec-tournaments.json`. Le bloc est
délimité par `<!-- structured-data:start -->` et `<!-- structured-data:end -->`;
le script le remplace en entier, il n'y a rien à éditer à la main. Le site
fonctionne sans avoir relancé le script — les données structurées seront
simplement en retard d'une édition.

Seuls les événements dont la date est complète (`2026-08-07`) sont publiés :
une date partielle ne répond pas aux exigences des moteurs.
