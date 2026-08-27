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

`blur-catch-backgrounds.py` régénère les photos de prises depuis les
originaux en floutant le décor : une rive, une tour ou un quai suffisent à
situer un spot, et un spot à maskinongé se garde.

Le masque est une union d'ellipses — une par pêcheur, une pour le poisson —
adoucie pour se lire comme une profondeur de champ. Une seule grande
ellipse ne marche pas : elle englobe ce qui se trouve entre les sujets, et
c'est justement là que passait une tour de communication sur une des
photos.

Limite connue : sans détourage automatique, ce qui se trouve directement
derrière une tête reste net. Pour aller plus loin il faut recadrer plus
serré à la source.

Trois de ces images servent aussi de portraits sur la page Équipe. Elles
sont partagées volontairement : flouter seulement les copies des Prises
laisserait le décor identifiable sur l'autre page.

**Les originaux ne sont pas dans le dépôt.** Garde-les de ton côté : le
floutage n'est pas réversible une fois publié.
