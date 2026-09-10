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

## Les seuils, et pourquoi ils existent

Une page mince nuit plus qu'elle n'aide. Chaque générateur porte un seuil.

| Ce qui est généré | Ce qu'il faut |
|---|---|
| Fiche de prise | une photo, un récit, une date, un plan d'eau |
| Fiche d'espèce | une source vérifiée, `MARKS_MIN` repères, `BLOCKS_MIN` blocs |
| Fiche de tournoi | `SCORE_MIN` sur dix champs, **et** de quoi lire au-delà du nom |

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
```

Puis, si le rendu a changé, la suite Playwright du bac à sable
(`NODE_PATH=/opt/node22/lib/node_modules`) : chaque page dans les deux langues,
les parcours interactifs, les cibles tactiles, le contraste.

**Mesurer avant de recommander.** Les décisions de ce dépôt viennent de
chiffres pris dans un navigateur — 425 px avant le premier chiffre d'une fiche,
19,1 écrans pour le guide, 14,6 pour l'index des espèces — pas d'impressions.
Et simuler l'horloge quand une page dépend de la date : `addInitScript` avec un
`Date` figé révèle les bascules qu'aucune lecture du code ne montre.
