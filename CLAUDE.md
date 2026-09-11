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

### 5. Écrire un message de commit : deux pièges, pas un

`git commit` avec un heredoc est bloqué. Le contournement est d'écrire le
message avec Python puis `git commit -F`, mais **pas** avec `python3 -c "…"` :
entre guillemets **doubles**, bash substitue encore les accents graves. Un
message qui citait deux noms de champs entre accents graves est parti en ligne
avec la sortie de la commande `date` à la place du mot, et un
`published: command not found` dans la foulée.

Un heredoc **entre apostrophes** ne substitue rien — ni accents graves, ni
`$`, ni `!` :

```bash
python3 - <<'FIN_DU_SCRIPT'
import io
io.open('.../msg.txt', 'w', encoding='utf-8').write('''…''')
FIN_DU_SCRIPT
git commit -F .../msg.txt
```

Deuxième piège, celui-là attrapé en écrivant le premier : **le marqueur de fin
ne doit apparaître nulle part dans le contenu.** Un texte qui montre un
heredoc et son marqueur de fermeture coupe le heredoc extérieur à cette
ligne-là. Choisis un marqueur qui ne peut pas se retrouver dans le texte — et
quand tu documentes un heredoc, prends-en deux différents.

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

### Les records d'une espèce : deux ou trois lignes, jamais le relevé

`records` sur une espèce, rendu par `records_html()` et gardé par
`record_ok()` — **la même règle que `claim_ok`** : vérifié, sourcé, et la
source elle-même vérifiée. Un record est une affirmation comme une autre.

**La base des records de l'IGFA est leur propriété**, et les relevés viennent
de leur espace membre. On en reprend **deux ou trois lignes** par espèce, avec
la source et le lien — une citation factuelle. Recopier les 35 catégories de
ligne d'une espèce, ce serait republier leur base. Ne le fais pas.

Trois précautions qui sont dans les données, pas dans le code :

- **La catégorie est toujours nommée.** Ce sont des records *par classe de
  ligne*, pas « le plus gros jamais pris ». « 15,19 kg au Manitoba » sans
  « soie 6 kg » serait faux dans le sens impressionnant.
- **Le Québec n'a pas de programme officiel de records** — rien à citer. Le
  site ne dit donc jamais « record du Québec », seulement le mondial et le
  plus proche, avec le lieu exact.
- **Les catégories « Junior » ne portent pas de nom de pêcheur** : elles
  désignent quelqu'un qui était mineur au moment de la prise. Le relevé est
  cité, qui veut le nom l'y trouvera.

`cited()` doit voir les records **autant que** les affirmations : sans ça leur
renvoi numéroté pointe vers une entrée absente de la liste des sources, et
`order.index` lève une erreur.

Deux espèces sur 47 en portent (grand brochet, maskinongé). Les 45 autres
n'en ont pas, et c'est normal : pas de source, pas de record.

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
forcée à toutes les largeurs, la rangée tient jusqu'à **1045 px en français**
et 1007 px en anglais. Le français est toujours la langue contraignante.

Ces chiffres étaient 967 et 929 avant que le bouton de recherche n'entre dans
`.nav-actions` : **il a coûté 78 px de marge**, qui est passée de 133 à 55.
C'est encore positif, mais c'est mince. **Un dixième onglet, ou un deuxième
bouton dans les actions, veut dire remesurer** — pas pousser le chiffre.

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

### `date` et `published` ne disent PAS la même chose

| | | |
|---|---|---|
| `date` | quand la **sortie** a eu lieu | écrite à la main, souvent partielle (« 2025 »), souvent inconnue |
| `published` | quand **YouTube a reçu** la vidéo | écrite par le robot, jamais retouchée ensuite |

La première version confondait les deux et « précisait » un `date: "2025"`
avec la date du flux. **Le garde-fou des années contradictoires l'a rattrapée
au premier vrai passage** : les deux vidéos de la saison 2025 ont été mises en
ligne les 26 et 28 août 2026. Si les années avaient concordé, la sortie aurait
silencieusement pris la date du montage.

Le robot ne remplit donc que `published`, et seulement s'il est vide. Une
nouveauté arrive avec `date: ""` — le flux ne connaît pas la date de sortie,
et vide vaut mieux que faux.

Côté rendu, les deux sens ne se croisent pas :
`videoOrder()` **classe** sur `published` (« notre dernière vidéo » parle de
mise en ligne), `videoWhen()` **affiche** `date` en premier. L'inverse mettait
« Kevin Caron · 28 août 2026 » sous une vidéo de la saison 2025.

**Le titre est nettoyé.** La traînée finale de mots-clés
(« #musky #pêchequébec ») est de la métadonnée YouTube, pas un titre : elle
déborde de la légende et n'apprend rien. Seule la traînée **finale** est
coupée — un « #1 » au milieu d'une phrase reste — et le test de `#shorts` se
fait sur le titre brut, avant la coupe.

**`channelId` se trouve tout seul.** Le flux veut un `UC…` et rien d'autre :
ni le `@handle`, ni l'adresse de la chaîne. Le lire à la main demande
d'ouvrir le code source d'une page — impossible sur un téléphone. Le script
va donc chercher la page de `channelUrl`, en extrait l'identifiant et
**l'écrit dans `data/videos.json`**. C'est fait une fois; ensuite le champ est
rempli et la page de la chaîne n'est plus jamais lue. Quatre motifs sont
essayés, le lien canonique d'abord — le seul qui soit du HTML et non du
JavaScript embarqué.

**Les garde-fous, tous testés dans `tools/test-youtube.py` (51 contrôles) :**

| | |
|---|---|
| `channelId` et `channelUrl` absents | le script dit quoi remplir et sort en 0 — rien n'est deviné |
| page de chaîne sans identifiant | code non nul, et il dit de le mettre à la main |
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

## Le tiroir est un menu, pas une classe CSS

`initNavDrawer()` dans `assets/js/main.js`. Il n'était qu'un `classList.toggle`.
Mesuré sur un téléphone, **cinq comportements attendus manquaient** :

| | |
|---|---|
| Échap | ne fermait rien |
| un geste à côté | ne fermait rien |
| le focus | ne revenait pas au bouton après fermeture |
| la tabulation | sortait du menu ouvert vers la page derrière |
| **le fond** | **défilait sous le tiroir** — on ouvre, on glisse le pouce, c'est la page qui bouge |

Plus `aria-controls` absent : le bouton annonçait « replié » sans jamais
nommer ce qu'il repliait. Il exige un `id`, donc `id="nav-menu"` est sur la
liste dans les 116 pages **et** dans `NAV`.

Deux détails qui se paient si on les oublie :

- **Le verrou du défilement est en CSS**, sous la requête média
  (`html.nav-open { overflow: hidden }`), pas en JavaScript. Un `overflow` posé
  en ligne se serait aussi appliqué sur écran large, où le tiroir n'existe pas.
- **La tabulation tourne dans `.nav`, pas dans `.nav-links`** — le
  commutateur de langue est dans `.nav-actions`, et ouvrir le menu ne doit pas
  empêcher de changer de langue.

`matchMedia` remet tout à zéro en repassant au-dessus de 1100 px : sans ça,
`open`, `nav-open` et `aria-expanded` restaient dans un état que plus rien
n'affichait.

**Cibles tactiles : 44 px, pas 24.** WCAG 2.5.8 (AA) demande 24 px et était
respecté — c'est pourquoi `taps.js` ne signalait rien. Mais les liens
faisaient 42 px, le bouton ☰ 39 et les boutons de langue **32**. 2.5.5 vise
44, et c'est la vraie cible au pouce.

**Pas de « retour en haut », et c'est réglé.** L'en-tête est `sticky` :
mesuré tout en bas du guide (11,7 écrans sur téléphone), il est encore à
`y=0` et le bouton ☰ reste atteignable. Le menu est à deux gestes de
n'importe quel point de n'importe quelle page.

**Un seul site, responsive.** Pas de version mobile séparée : le menu est
écrit en dur dans 116 pages et un gabarit, et le dédoubler ferait 232 endroits
à tenir, deux sitemaps, et couperait en deux le référencement d'une page que
Google vient d'indexer.

---

## Se repérer dans les 104 pages générées

### Le fil d'Ariane

`breadcrumb(famille, feuille, url)` dans `tools/build-tournament-pages.py`,
appelé par les cinq générateurs. Une fiche d'espèce ne disait nulle part
qu'elle appartenait à « Espèces » : le seul retour était le menu.

Les deux premiers échelons réutilisent **les clés du menu** (`nav.species`,
`nav.guide`…) — renomme un onglet et le fil suit. La feuille est une donnée
bilingue, donc `data-en`. Le helper émet aussi un `BreadcrumbList` JSON-LD,
**dans le corps** et non dans `<head>` : c'est valide, et ça évite de faire
passer les données du fil à travers `head()` dans cinq générateurs.

Rappel du piège 3 : ces pages déclarent `<base href="/">`, donc `href="especes.html"`
vise bien la racine. Il ne faut **pas** écrire `../especes.html`.

### « Précédente / suivante »

`siblings(prev, nxt)`, même module. Chaque famille décide de son ordre, et
**cet ordre doit être celui de l'index correspondant**, sinon la flèche mène
ailleurs que ce que le lecteur vient de voir :

| Famille | Ordre |
|---|---|
| espèces | alphabétique sur le nom français, **accents repliés** (`fold()`) |
| tournois | calendrier; une date absente vaut `9999` et passe en dernier |
| prises | de la plus récente à la plus ancienne, comme le mur |
| pêcheurs, bateaux | l'ordre du fichier de données, celui des index |

Au bout de la série, `siblings()` ne rend qu'un seul lien — jamais une flèche
morte. `.sib-next:only-child` le renvoie à droite, sinon il se collerait là où
« précédente » aurait dû être.

### La recherche

`assets/js/search.js` + `data/search-index.json`, construit par
`tools/build-search-index.py` (111 pages, 17 Ko).

Il y avait **deux** recherches qui ne se parlaient pas — une sur l'index des
espèces, une sur le guide — et les 104 pages générées n'étaient trouvables par
aucune des deux.

- **L'index n'est pas chargé avec la page.** Il arrive au premier clic sur la
  loupe. Vérifié : 0 requête au chargement, 1 au premier usage.
- **Le bouton est dans `.nav-actions`, pas dans la rangée d'onglets.** La
  barre était pleine à 77 px près; un dixième onglet aurait forcé à remonter
  le point de bascule.
- **Le bouton et le panneau sont construits en JavaScript**, pas écrits dans
  les 116 pages : une boîte de recherche ne sert à rien sans JavaScript. Le
  menu, lui, est du contenu et reste dans le balisage.
- L'index ne contient **aucun texte de corps** : on cherche des pages, pas des
  phrases. Il vit dans `data/`, donc `check-private.py` le contrôle comme le
  reste.
- `PMF_I18N` est un `const` (piège 2) : `search.js` teste
  `typeof PMF_I18N === "undefined"` et sort, il ne lit jamais `window`.

Après toute modification de `data/`, relancer `tools/build-search-index.py` —
sinon la recherche pointe sur une page qui n'existe plus.

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

### `released` : la remise à l'eau se calcule, elle ne s'écrit pas

Le champ est **obligatoire** sur chaque prise, comme `showcase` :

| | |
|---|---|
| `released: true` | pastille « Remis à l'eau » sur la carte et sur la fiche |
| `released: false` | pastille « Gardé » |
| champ absent | `check-links.py` sort en code 1 |

La phrase du haut du mur des prises est **dérivée** de ce champ : « On remet
nos prises à l'eau… » tant que tout est à `true`, « …sauf indication contraire
sur la fiche » dès qu'une prise passe à `false`. Une phrase figée serait
devenue fausse en silence le jour où un doré est gardé — et fausse dans le
sens qui rassure, ce qui est le pire.

**Le calcul se fait sur `PMF_CATCHES.loadAll()`, pas sur `load()`.** `load()`
retire les prises en `showcase: false`, qui ne montent pas sur le mur. La
première version comptait dessus : simulée, **un doré gardé et laissé hors du
mur ne faisait PAS changer la phrase**, et le site continuait d'affirmer qu'on
remet tout. La phrase décrit la pratique de l'équipe, pas le contenu du mur —
elle doit voir les dix prises, pas les sept affichées.

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
python3 tools/build-search-index.py            # après toute modif de data/
python3 tools/test-youtube.py                  # 51 contrôles du lecteur de flux
```

Puis, si le rendu a changé, la suite Playwright du bac à sable
(`NODE_PATH=/opt/node22/lib/node_modules`) : chaque page dans les deux langues,
les parcours interactifs, les cibles tactiles, le contraste.

**Mesurer avant de recommander.** Les décisions de ce dépôt viennent de
chiffres pris dans un navigateur — 425 px avant le premier chiffre d'une fiche,
19,1 écrans pour le guide, 14,6 pour l'index des espèces — pas d'impressions.
Et simuler l'horloge quand une page dépend de la date : `addInitScript` avec un
`Date` figé révèle les bascules qu'aucune lecture du code ne montre.
