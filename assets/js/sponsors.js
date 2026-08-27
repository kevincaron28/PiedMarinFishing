// Pied Marin Fishing — partenaires
// La section n'existe que s'il y a des partenaires. Une grille vide sous un
// titre « Nos partenaires » dirait le contraire de ce que la page cherche.

async function initSponsors(gridSelector, sectionSelector) {
  const grid = document.querySelector(gridSelector);
  const section = document.querySelector(sectionSelector);
  if (!grid || !section) return;

  await PMF_I18N.ready;
  const { tr } = PMF_I18N;

  let list = [];
  try {
    list = await (await fetch("data/sponsors.json", DATA_FETCH)).json();
  } catch (e) {
    list = [];
  }
  if (!Array.isArray(list) || !list.length) {
    section.style.display = "none";
    return;
  }

  function render() {
    section.style.display = "";
    grid.innerHTML = list.map((s) => {
      const name = tr(s.name);
      const logo = s.logo
        ? `<img src="${escapeHTML(s.logo)}" alt="${escapeHTML(name)}" class="sponsor-logo" loading="lazy">`
        : `<span class="sponsor-name">${escapeHTML(name)}</span>`;
      const blurb = tr(s.blurb);
      const inner = `${logo}${blurb ? `<p class="sponsor-blurb">${escapeHTML(blurb)}</p>` : ""}`;
      return s.url
        ? `<a class="sponsor-card" href="${escapeHTML(s.url)}" target="_blank" rel="noopener">${inner}</a>`
        : `<div class="sponsor-card">${inner}</div>`;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
