// Pied Marin Fishing — « Ce qu'on pêche avec ».
//
// Les marques que l'équipe utilise, et RIEN D'AUTRE. Ce n'est pas la page des
// commanditaires et ça ne doit pas y ressembler : TFO a ouvert un compte guide
// à l'équipe, ce qui n'est pas une commandite. Écrire « commanditaire » sous
// le logo d'une vraie compagnie affirmerait une entente que personne n'a dite.
//
// D'où un fichier à part — data/brands.json, pas data/sponsors.json. Le jour
// où une vraie commandite arrive, elle a déjà sa place ailleurs, et les deux
// ne se confondent pas.
//
// La section se retire d'elle-même quand le fichier est vide : une rubrique
// « ce qu'on pêche avec » sans rien dedans se lit comme un aveu.

async function initBrands(options) {
  const { gridSelector, sectionSelector } = options;
  const grid = document.querySelector(gridSelector);
  const section = sectionSelector ? document.querySelector(sectionSelector) : grid;
  if (!grid) return;

  await PMF_I18N.ready;
  const { tr } = PMF_I18N;

  let brands = [];
  try {
    brands = await (await fetch("data/brands.json", DATA_FETCH)).json();
  } catch (e) {
    brands = [];
  }
  brands = (brands || []).filter((b) => b && (b.name || b.short));

  if (!brands.length) {
    if (section) section.hidden = true;
    return;
  }
  if (section) section.hidden = false;

  await PMF_IMG.load();

  function draw() {
    grid.innerHTML = brands.map((b) => {
      const name = b.name || b.short;
      // Le logo porte le nom en texte alternatif. Une marque reconnue par son
      // dessin reste illisible pour un lecteur d'écran sans ça.
      const logo = b.logo
        ? `<img class="brand-logo-img" src="${escapeHTML(b.logo)}"${
            PMF_IMG.attrs(b.logo, "(max-width: 620px) 60vw, 220px")}
            alt="${escapeHTML(name)}" loading="lazy">`
        : `<span class="brand-name">${escapeHTML(name)}</span>`;
      const note = tr(b.note);
      const inner = logo + (note ? `<p class="brand-note">${escapeHTML(note)}</p>` : "");
      // Pas d'adresse, pas de lien. Un lien mort sous le logo d'une marque est
      // pire que pas de lien du tout.
      return b.url
        ? `<a class="brand-card" href="${escapeHTML(b.url)}" target="_blank" rel="noopener">${
            inner}</a>`
        : `<div class="brand-card">${inner}</div>`;
    }).join("");
  }

  draw();
  PMF_I18N.onChange(draw);
}
