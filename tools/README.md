# tools/

## Trousse de commandite

`build-sponsor-kit.py` lit `data/i18n.json` et `data/team-members.json`, puis
écrit un HTML de format lettre par langue. `render-sponsor-kit.js` le rend en
PDF avec Chromium.

La trousse se régénère donc à partir des mêmes textes que la page
`sponsors.html` : corriger un fait sur le site le corrige aussi dans le PDF.

```
python3 tools/build-sponsor-kit.py
node tools/render-sponsor-kit.js <dossier>
```

`build-sponsor-kit.py` affiche le dossier à passer en argument à la fin de son
exécution.

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

`build-structured-data.py` écrit le JSON-LD dans `index.html` (le site et
l'équipe, liés par `@id`) et `tournaments.html` (la liste des tournois
datés). Les moteurs de recherche
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

## Fiches de tournoi

`build-tournament-pages.py` écrit une page par tournoi dans `tournois/`, à
partir de `data/quebec-tournaments.json`.

```
python3 tools/build-tournament-pages.py
```

Les 34 tournois du guide vivaient sur une seule adresse : quelqu'un qui
cherche « Tournoi Destroyer 2026 inscription » n'y trouvait rien. Chaque fiche
répond maintenant à une recherche précise.

**Le seuil.** Une fiche mince nuit plus qu'elle n'aide. Un tournoi n'a droit à
sa page que s'il atteint 6 points sur les dix champs qui intéressent un
lecteur (lieu, espèce, organisateur, lien, notes, puis prix, format, horaire,
épreuve, date limite). Les étapes d'un circuit sont détaillées sur la page de
leur circuit plutôt que d'avoir chacune la leur — « Deuxième des quatre
étapes » ne fait pas une page. Une étape dont le circuit n'a pas de fiche
redevient éligible, et **tous les circuits en ont une d'office** : leur valeur
vient de ce qu'ils regroupent, pas de leurs propres champs.

Un **salon** est noté sur un barème à lui. Il n'a ni espèce ciblée, ni équipe,
ni épreuve, ni date limite : le juger sur ces dix champs revenait à le condamner
pour des cases qui ne le concernent pas. Il est donc noté sur les six qui
s'appliquent (lieu, organisateur, lien, notes, prix, horaire), avec le même
seuil proportionnel — 4 sur 6.

Le script affiche le pointage de chacun sur son propre barème, retenu ou non.
`check-stale.py` importe ce barème plutôt que d'en garder une copie.

Le script écrit aussi `data/tournament-pages.json`, la liste des identifiants
ayant une fiche. `assets/js/events.js` la lit pour ajouter le bouton « Fiche du
tournoi » aux bonnes cartes du répertoire, et supprime les fiches devenues
orphelines quand un tournoi quitte le guide.

Le français est écrit en dur dans le HTML — c'est lui que lisent les robots —
et l'anglais voyage dans des attributs `data-en` qu'`assets/js/tournament-page.js`
échange au clic. Rien n'est rendu en JavaScript. Ne modifie jamais un fichier
de `tournois/` à la main : la prochaine exécution l'écraserait. Corrige le
tournoi dans `data/quebec-tournaments.json`.

### Classement de saison sur une fiche de circuit

Un circuit peut porter un classement. Rien n'est calculé : les points viennent
de l'organisateur. Ajoute un champ `standings` au tournoi dans
`data/quebec-tournaments.json` :

```json
"standings": {
  "updated": "2026-08-30",
  "source": "https://exemple.ca/classement",
  "rows": [
    { "rank": 1, "team": "Nom de l'équipe", "points": "310" },
    { "rank": 2, "team": "Autre équipe", "points": "295" }
  ]
}
```

`updated` et `source` sont facultatifs. Sans `rows`, la section n'apparaît pas
du tout — comme le reste du site, elle se masque plutôt que de montrer un
tableau vide. `team` accepte une chaîne simple ou `{fr, en}`.

**Tous les circuits ont leur fiche**, quel que soit leur pointage : leur valeur
vient de ce qu'ils regroupent. « Programme Big Bass Québec » comptait sept
étapes sans page où les voir ensemble. Un circuit annulé garde la sienne aussi,
avec un bandeau — « est-ce que ça roule cette année? » est exactement la
question qu'on vient poser.

### « On y sera »

Un tournoi du répertoire porte la mention **On y sera** quand il figure au
calendrier de l'équipe. Le rapprochement est automatique : les identifiants
sont comparés après avoir retiré l'année finale, donc
`peche-glace-lachine-2026` et `peche-glace-lachine-2027` sont reconnus comme la
même série. Rien à saisir deux fois — ajoute l'entrée à
`data/team-schedule.json` et la mention apparaît.

La mention ne s'affiche que sur une édition **à venir** : le répertoire tient
encore les éditions 2026 alors que l'équipe vise les 2027, et « on y sera » sur
une date passée serait faux. Elle réapparaîtra d'elle-même sur les entrées 2027.

### Vidéos

`data/videos.json` tient la liste et l'adresse de la chaîne. Celle marquée
`"featured": true` passe en vedette sur l'accueil; la page Réseaux les affiche
toutes, mais **la section se retire sous deux vidéos** — une chaîne d'un seul
clip n'en est pas une, et l'accueil le montre déjà.

```json
{
  "channelUrl": "https://youtube.com/@piedmarinfishing",
  "videos": [
    { "id": "…", "videoId": "PXwFXozk-5c", "orientation": "portrait",
      "title": { "fr": "…", "en": "…" }, "angler": "kevin-b",
      "date": "2026-07-04", "featured": true }
  ]
}
```

`orientation: "portrait"` pour un Short, sinon le cadre 16:9 le réduit à une
bande. `videoId` accepte l'identifiant seul ou une URL YouTube complète.
`angler` est un identifiant de `data/team-members.json`, jamais un nom recopié —
le nom affiché suit la fiche d'équipe. `date` et `angler` sont facultatifs.

## Chiffres de l'accueil

`build-stats.py` écrit `data/site-stats.json` — quelques octets, régénérés avec
le reste.

```
python3 tools/build-stats.py
```

Le répertoire pèse 74 Ko : le charger sur la page d'accueil pour afficher
« 45 tournois » serait absurde. Les autres chiffres du bandeau (saisons,
records) se calculent dans le navigateur, à partir de fichiers qu'il charge
déjà. Un tournoi annulé n'est pas compté : il est au répertoire pour prévenir,
pas pour gonfler un chiffre.

## Après avoir modifié `data/i18n.json`

Chaque page HTML porte une copie française du texte, visible avant que
`i18n.js` s'exécute. C'est cette copie que lisent Google, Facebook et les
aperçus de lien — pas la version chargée en JavaScript. Elle doit donc suivre.

```
python3 tools/sync-html-fallbacks.py --check   # ce qui a dérivé
python3 tools/sync-html-fallbacks.py           # le corriger
```

Le script recopie aussi le `<title>` et la `<meta name="description">` vers les
balises `og:` et `twitter:`, qui figeaient sinon d'anciennes phrases dans les
aperçus partagés. Les clés à accolades (`{year}`, `{count}`) sont laissées de
côté : leur version HTML est volontairement différente.

C'est l'oubli le plus facile du dépôt — le site s'affiche parfaitement pendant
que les moteurs indexent une phrase périmée. `--check` sort en code 1 s'il
trouve une divergence.

## Sitemap

`build-sitemap.py` régénère `sitemap.xml`. La date `<lastmod>` de chaque page
vient de git : le dernier commit qui a touché la page **ou** une des données
qu'elle affiche (`tournaments.html` suit `data/quebec-tournaments.json`, et
toutes suivent `data/i18n.json`). Une page modifiée mais pas encore commitée
est datée d'aujourd'hui.

```
python3 tools/build-sitemap.py
```

À relancer juste après un commit de contenu, pour que les dates soient celles
du commit et non celles de la journée. `merch.html` et `404.html` en sont
absentes : elles portent `noindex`. Les fiches de `tournois/` y sont ajoutées
automatiquement.

## Ce qui demande une vérification

`check-stale.py` lit le répertoire et dit par où commencer une séance de
recherche, au lieu de relire les 42 entrées.

```
python3 tools/check-stale.py            # rapport complet
python3 tools/check-stale.py --brief    # juste les totaux
```

Quatre paquets : les éditions **passées** (à reporter sur la saison suivante),
celles **sans date publiée**, celles **sous le seuil de fiche** avec la liste
exacte des champs manquants, et celles **encore à venir** (rien à faire). Le
script avertit aussi quand aucune date de la saison suivante n'est au
répertoire — c'est ce qui donne au guide un air abandonné au printemps.

Il ne va sur aucun site et ne modifie rien : la recherche reste manuelle, et
c'est voulu. Une date inventée coûte plus cher au répertoire qu'une date
manquante.

## L'ordre des scripts

Après une modification de `data/quebec-tournaments.json` :

```
python3 tools/build-tournament-pages.py   # 1. les fiches
python3 tools/build-stats.py              # 2. les chiffres de l'accueil
python3 tools/build-structured-data.py    # 3. le JSON-LD du guide
python3 tools/sync-html-fallbacks.py      # 4. les textes FR figés
python3 tools/build-sitemap.py            # 5. le sitemap (après le commit)
```
