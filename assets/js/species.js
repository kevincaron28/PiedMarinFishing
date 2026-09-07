// Pied Marin Fishing — index des fiches d'espèce
//
// Les fiches sont générées par tools/build-species-pages.py, qui écrit aussi
// data/species-pages.json. Cet index lit CET INDEX plutôt que data/species.json :
// une espèce qui n'a pas franchi son seuil n'a pas de page, et une carte qui
// pointerait vers elle serait un 404. Les deux fichiers ne peuvent donc pas
// diverger.

// Les règles qui ne visent aucune espèce en particulier — transport de
// poissons vivants, signalement, nombre de lignes l'hiver — n'ont pas de fiche
// où atterrir. Elles vivent donc ici, sur l'index, plutôt que sur une page de
// réglementation à part que Kevin ne voulait pas.
async function initGeneralRules(selector) {
  const root = document.querySelector(selector);
  if (!root) return;
  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  let data = null;
  try {
    data = await (await fetch("data/regulations.json", DATA_FETCH)).json();
  } catch (e) {
    data = null;
  }
  const rules = ((data && data.rules) || []).filter((r) => r && r.general && r.verified);
  if (!rules.length) {
    root.hidden = true;
    return;
  }

  function monthsSince(iso) {
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return Infinity;
    const now = new Date();
    return (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth());
  }

  function render() {
    const stale = monthsSince(data.updated) > (Number(data.staleAfterMonths) || 12);
    const link = (data.official && data.official.url)
      ? `<a href="${escapeHTML(data.official.url)}" target="_blank" rel="noopener">${
          escapeHTML(t("reg.official"))}</a>`
      : "";
    if (stale) {
      root.innerHTML = `<div class="reg-stale" role="status"><p class="reg-stale-head">${
        escapeHTML(t("reg.staleTitle"))}</p><p>${
        escapeHTML(t("reg.staleBody", { date: data.updated }))}</p><p>${link}</p></div>`;
      return;
    }
    root.innerHTML =
      `<p class="reg-stamp">${escapeHTML(t("reg.updated", { date: data.updated }))}</p>` +
      `<div class="reg-list">` + rules.map((r) => `<div class="reg-row">
  <div class="reg-body">
    <p class="reg-species">${escapeHTML(tr(r.species))}</p>
    <p class="reg-rule">${escapeHTML(tr(r.rule) || tr(r.limit))}</p>
    ${tr(r.period) ? `<p class="reg-detail">${escapeHTML(tr(r.period))}</p>` : ""}
    ${tr(r.detail) ? `<p class="reg-detail">${escapeHTML(tr(r.detail))}</p>` : ""}
  </div>
</div>`).join("") + `</div>` +
      `<p class="reg-note">${escapeHTML(t("reg.disclaimer"))} ${link}</p>`;
  }

  PMF_I18N.onChange(render);
  render();
}

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
