// Pied Marin Fishing — index des fiches d'espèce
//
// Les fiches sont générées par tools/build-species-pages.py, qui écrit aussi
// data/species-pages.json. Cet index lit CET INDEX plutôt que data/species.json :
// une espèce qui n'a pas franchi son seuil n'a pas de page, et une carte qui
// pointerait vers elle serait un 404. Les deux fichiers ne peuvent donc pas
// diverger.

async function initSpecies(gridSelector, countSelector) {
  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  const { t, tr, key } = PMF_I18N;

  let species = [];
  let published = [];
  try {
    [species, published] = await Promise.all([
      (await fetch("data/species.json", DATA_FETCH)).json(),
      (await fetch("data/species-pages.json", DATA_FETCH)).json(),
    ]);
  } catch (e) {
    species = [];
    published = [];
  }
  const live = new Set(Array.isArray(published) ? published : []);
  const list = (Array.isArray(species) ? species : []).filter((s) => s && live.has(s.id));

  function render() {
    const count = document.querySelector(countSelector);
    if (count) count.textContent = t("sp.indexCount", { n: list.length });
    if (!list.length) {
      grid.innerHTML = "";
      return;
    }
    grid.innerHTML = list.map((s) => {
      const status = tr(s.status);
      // Deux repères en aperçu : la taille et ce qui vient après. Toute la
      // grille tiendrait sur la carte, mais on ne lit pas une carte, on la
      // balaie — et la fiche est à un clic.
      const marks = (s.marks || []).filter((m) => tr(m.value)).slice(0, 2);
      const rows = marks.map((m) =>
        `<div class="sp-card-mark"><span>${escapeHTML(tr(m.label))}</span>${
          escapeHTML(tr(m.value))}</div>`).join("");
      return `<a class="sp-card" href="especes/${escapeHTML(s.id)}.html">
  <span class="sp-card-name">${escapeHTML(tr(s.name))}</span>
  ${s.scientificName ? `<em class="sp-card-sci">${escapeHTML(s.scientificName)}</em>` : ""}
  ${status ? `<span class="sp-card-status">${escapeHTML(status)}</span>` : ""}
  ${rows}
</a>`;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
