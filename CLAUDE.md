# Pied Marin Fishing — à lire avant de toucher au code

Site statique bilingue (FR/EN) d'une équipe de pêche québécoise, servi par
GitHub Pages depuis la racine de `main`. **Aucun cadre logiciel, aucune
dépendance, aucun build au déploiement** — ce qui est dans le dépôt est ce qui
part en ligne. C'est une force à préserver, pas une dette à rembourser.

Le README explique ce que fait chaque fichier. Celui-ci dit ce qui fait perdre
du temps, et pourquoi certaines choses sont écrites comme elles le sont.

---

## Les cinq pièges qui ont réellement coûté du temps

### 1. Le français est écrit EN DUR dans le HTML, et il dérive

Chaque page porte son texte français directement dans le balisage, avec un
attribut `data-i18n` qui dit où le retrouver dans `data/i18n.json`. Le HTML
sert les robots et le premier affichage; le JSON sert la bascule de langue.

Modifier l'un sans l'autre les fait diverger en silence.

```bash
python3 tools/sync-html-fallbacks.py            # recopie le FR du JSON vers le HTML
python3 tools/sync-html-fallbacks.py --check    # sort en code 1 si ça a dérivé
```

**Toujours écrire dans `data/i18n.json`, puis synchroniser.** Jamais l'inverse.

### 2. `PMF_I18N` est un `const` global, PAS une propriété de `window`

```js
if (window.PMF_I18N) { ... }              // FAUX — toujours undefined
if (typeof PMF_I18N !== "undefined") { }  // juste
```

Ce test raté a désactivé `reg-guard.js` — le mécanisme qui fait expirer la
réglementation périmée. Pas d'erreur, pas d'avertissement, le garde-fou ne
tournait simplement jamais. **Un mécanisme de sécurité qui ne s'exécute pas en
silence est pire qu'aucun**, parce qu'on croit l'avoir.

### 3. Les pages générées déclarent `<base href="/">`

`tournois/`, `pecheurs/`, `bateaux/`, `prises/` et `especes/` vivent un dossier
plus bas. Leur `<base>` fait marcher les chemins relatifs du menu — et casse les
ancres nues :

```html
<a href="#src-mffp">      <!-- résolu contre la BASE : renvoie à l'accueil -->
<a href="especes/x.html#src-mffp">   <!-- juste -->
```

### 4. Le navigateur saute vers une ancre AVANT que le JavaScript ait rendu

Sur les pages dont le contenu est construit en JS (le guide, le calendrier,
l'index des espèces), un lien `page.html#cible` atterrit dans le vide : le
navigateur cherche la cible, ne la trouve pas, puis la liste se construit et
pousse la cible 1 400 px plus bas.

Chacune de ces pages refait donc le saut après le rendu, sans animation au
chargement. Voir `openHashTarget()` dans `events.js`, `openHashGroup()` dans
`species.js`. Si tu ajoutes une page rendue en JS avec des ancres, refais-le.

### 5. `git commit` avec un heredoc est bloqué

```bash
python3 -c "import io; io.open('/tmp/msg.txt','w',encoding='utf-8').write('''...''')"
git commit -F /tmp/msg.txt
```

---

## Ce qui ne se négocie pas

### La vie privée

`tools/check-private.py` refuse qu'un numéro d'immatriculation, une plaque, un
numéro de série **ou le prénom d'une mineure** parte en ligne. Il sort en code 1
et nomme le fichier et la ligne.

La relève de l'équipe se désigne par ses initiales — « R.C. » — et rien
d'autre : pas de nom, pas d'âge, pas de date de naissance, pas de page.

Le contrôle existe parce qu'un numéro masqué sur une photo avait été réécrit
dans son texte alternatif, où il est resté invisible jusqu'à ce que les
descriptions deviennent des légendes affichées. **Le texte alternatif est le
meilleur endroit pour cacher une fuite.**

Le secteur de pêche de l'équipe ne doit jamais être identifiable. Les points de
référence solunaires sont quatre villes publiques, jamais les coordonnées de
l'équipe. C'est délibéré.

### On ne publie jamais une affirmation non vérifiée

`tools/build-species-pages.py` ne sort une affirmation que si elle porte
`verified` **et** que toutes ses sources le portent aussi. Une affirmation non
vérifiée n'est pas signalée sur la page : elle n'existe pas. Un « à confirmer »
publié est encore une publication.

La règle vient d'une recherche qui avait retourné « le maskinongé du
Saint-Laurent est entièrement interdit de pêche » — faux, et
auto-incriminant sur notre propre site.

### Trois états, jamais deux

`assets/js/season.js` calcule ce qui est ouvert. Une période qui ne s'analyse
pas **entièrement** tombe dans « on ne sait pas », jamais dans « ouvert ». Une
pastille « ouvert » est une affirmation légale : si elle se trompe, quelqu'un
garde un poisson hors saison sur notre parole.

Le troisième état a servi : le brochet l'a affiché deux jours, parce que le PDF
officiel coupait sa date de fermeture par un saut de page. Le trou s'est
refermé quand quelqu'un est allé chercher la fiche. **C'est le troisième état
qui a rendu le trou visible au lieu de le combler.**

Corollaire : une espèce qu'aucune règle ne couvre apparaît dans un bloc « ce
qu'on n'a pas ». Le silence d'une page qui s'appelle « Qu'est-ce qui est
ouvert » se lit comme une absence de contrainte.

### Deux péremptions

`regulations.json` porte `updated` et `staleAfterMonths`. Passé le délai,
`reg-guard.js` **remplace** le bloc de règles — il ne met pas un avertissement
au-dessus, parce qu'une règle périmée sous un avis reste une règle périmée à
l'écran. `saison.html` s'éteint en plus dès que la saison décrite est finie,
même si le délai n'est pas atteint.

Ne repousse jamais `updated` sur la foi d'une relecture partielle : cette date
arme la péremption de **toutes** les règles. Une relecture d'une seule règle se
consigne dans son propre champ `verified`.

---

## La navigation : neuf dans la barre, onze dans le tiroir

Le menu est écrit **à la main dans les 13 pages racine** et **une fois** dans
`NAV`, au haut de `tools/build-tournament-pages.py`, d'où sortent les 103
pages générées. Un changement se fait donc à deux endroits, puis on régénère.

Deux items — « Notre histoire » et « Réseaux » — portent la classe
`nav-extra` : masqués dans la barre, visibles dans le tiroir sous un filet.
La barre n'a pas la place, le tiroir en a 484 px de reste.

Le point de bascule est **1100 px**, mesuré, pas estimé : disposition « barre »
forcée à toutes les largeurs, la rangée tient jusqu'à 967 px en français et
929 px en anglais. Le français est toujours la langue contraignante.
**Un dixième item veut dire remesurer**, pas pousser le chiffre.

`nav_for(current)` dans `tools/build-profile-pages.py` déplace
`aria-current="page"` sur l'onglet de la page. Il ne cherche qu'à partir du
`<ul>` : l'écusson pointe lui aussi sur `index.html` et vient avant. Toutes
les fiches sortaient marquées sur « Équipe » — une fiche d'espèce annonçait
« Équipe » comme page courante au lecteur d'écran.

L'onglet « Ouvert ? » (`nav-live`) porte un accent doré **statique**. Il
n'annonce aucun état de saison, et c'est voulu : une pastille calculée dans la
barre obligerait les 116 pages à charger `season.js` et `regulations.json`
(45 Ko) pour dessiner un point — et un point qui dérive de la page qu'il
annonce vaut moins que pas de point.

Le bandeau « Ce qui presse » de l'accueil et de l'index des espèces est le
seul autre chemin vers `saison.html`, et **il se masque quand rien ne bouge
dans les 60 jours** (`root.hidden = true` dans `season.js`). C'est pour ça que
la page a besoin d'une place permanente dans le menu : son seul lien entrant
était saisonnier.

---

## Le seul automate du dépôt : le flux YouTube

`.github/workflows/youtube.yml` appelle `tools/fetch-youtube.py` une fois par
jour, qui ajoute les nouvelles vidéos dans `data/videos.json` et commite.

**Pourquoi pas dans le navigateur.** Le flux Atom de YouTube est public et
sans jeton, mais il ne porte aucun en-tête CORS — une page ne peut pas le
lire. Passer par un relais tiers ferait transiter nos visiteurs par un service
qu'on ne contrôle pas, pour un fichier qui change une fois par mois. On le lit
donc dans l'action et on écrit le résultat dans le dépôt : le site continue de
lire un fichier local, et la position d'`analytics.js` — un seul script tiers,
sans témoin, pas de bandeau de consentement — tient toujours.

**Ce que le robot ne fait jamais.** Il n'écrase aucune entrée existante. Le
titre bilingue, `orientation`, `angler`, `catch` et `featured` sont écrits à
la main; le flux ne donne qu'un titre, dans une seule langue. Une vidéo déjà
connue est laissée telle quelle.

**La seule exception**, et elle ne porte pas sur de l'éditorial : une `date`
d'année seule (« 2025 ») est complétée par la date exacte du flux. La date de
publication appartient à YouTube. Une date déjà précise au jour n'est jamais
retouchée, et une année qui **contredit** le flux est signalée, pas corrigée.

**Les garde-fous, tous testés dans `tools/test-youtube.py` (34 contrôles) :**

| | |
|---|---|
| `channelId` absent | le script explique où le trouver et sort en 0 — rien n'est deviné |
| `channelId` mal formé | refus (il faut `UC` + 22 caractères) |
| identifiant de vidéo ≠ 11 caractères | l'entrée est ignorée — `video.js` retomberait sans bruit sur le bloc « bientôt » |
| `#shorts` dans le titre | `orientation: "portrait"`, seule indication fiable de verticalité |
| flux illisible ou vide | code de sortie non nul, rien n'est écrit |

**L'accueil suit la plus récente, plus « la première du tableau ».** Le robot
ajoute en fin de liste : « la première » serait devenue la plus vieille, alors
que la section s'appelle « Notre dernière vidéo ». `videosByDate()` dans
`video.js` trie par date, et **à égalité c'est la dernière du fichier qui
gagne** — l'ordre du fichier est déjà chronologique. Sans cette règle de
départage, deux vidéos datées « 2025 » se classaient à l'envers.

`featured: true` reste une épingle manuelle et **court-circuite** le tri.

---

## Les seuils, et pourquoi ils existent

Une page mince nuit plus qu'elle n'aide. Chaque générateur porte un seuil.

| Ce qui est généré | Ce qu'il faut |
|---|---|
| Fiche de prise | une photo, un récit, une date, un plan d'eau |
| Photo sur une fiche d'espèce | une photo et un `speciesId` — pas de récit exigé |
| Fiche d'espèce | une source vérifiée, `MARKS_MIN` repères, `BLOCKS_MIN` blocs |
| Fiche de tournoi | `SCORE_MIN` sur dix champs, **et** de quoi lire au-delà du nom |

`showcase` décide où une prise apparaît, et le champ est OBLIGATOIRE :

| | Mur des prises | Fiche d'espèce |
|---|---|---|
| `showcase: true` | oui | oui |
| `showcase: false` | non | oui |
| champ absent | `check-links.py` sort en code 1 |

Le mur est une sélection — les gros, les beaux, ceux qui ont une histoire — et
pas un journal de sorties. Une photo en `false` n'a AUCUN lien : sa vignette
est un `<figure>`, pas un `<a>`. L'ancre `catches.html#c-<id>` d'une prise
retirée du mur menait à l'index et n'y trouvait rien — un lien mort que
`check-links.py` ne peut pas voir, puisque la page, elle, existe.

**Le compte de mots juge mal une fiche-tableau.** Un audit avait recommandé de
couper de 34 fiches de tournoi à 16 sur ce critère; en les lisant, deux
seulement ne répondaient à rien. Une fiche de 150 mots qui donne le prix,
l'horaire, le format et la date limite fait son travail.

---

## Avant de pousser

```bash
python3 tools/sync-html-fallbacks.py --check   # 0 divergence
python3 tools/check-private.py                 # 0 identifiant, 0 prénom de mineure
python3 tools/check-links.py                   # 0 lien cassé, 0 speciesId orphelin
node    tools/test-season.js                   # 30 contrôles du moteur de saison
python3 tools/test-youtube.py                  # 34 contrôles du lecteur de flux
```

Puis, si le rendu a changé, la suite Playwright du bac à sable
(`NODE_PATH=/opt/node22/lib/node_modules`) : chaque page dans les deux langues,
les parcours interactifs, les cibles tactiles, le contraste.

**Mesurer avant de recommander.** Les décisions de ce dépôt viennent de
chiffres pris dans un navigateur — 425 px avant le premier chiffre d'une fiche,
19,1 écrans pour le guide, 14,6 pour l'index des espèces — pas d'impressions.
Et simuler l'horloge quand une page dépend de la date : `addInitScript` avec un
`Date` figé révèle les bascules qu'aucune lecture du code ne montre.
