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

  function zonesHtml() {
    // Les cartes officielles, servies depuis le site : sur le fleuve le
    // signal tombe, et une carte de zone en PDF sur le telephone marche
    // sans reseau. Le lien vers la page du gouvernement reste a cote, parce
    // que c'est elle qui fait foi.
    const zones = (data.zones || []).filter((z) => z.map);
    if (!zones.length) return "";
    return `<div class="reg-maps">` + zones.map((z) => `
  <a class="reg-map" href="${escapeHTML(z.map)}" download>
    <span class="reg-map-name">${escapeHTML(tr(z.name))}</span>
    <span class="reg-map-kind">${escapeHTML(t("reg.mapKind"))}</span>
    ${tr(z.note) ? `<span class="reg-map-note">${escapeHTML(tr(z.note))}</span>` : ""}
  </a>`).join("") + `</div>`;
  }

  function render() {
    const stale = monthsSince(data.updated) > (Number(data.staleAfterMonths) || 12);
    const link = (data.official && data.official.url)
      ? `<a href="${escapeHTML(data.official.url)}" target="_blank" rel="noopener">${
          escapeHTML(t("reg.official"))}</a>`
      : "";
    if (stale) {
      // Les cartes de zone survivent a la peremption : les limites d'une zone
      // ne changent pas d'une saison a l'autre, contrairement aux dates.
      root.innerHTML = `<div class="reg-stale" role="status"><p class="reg-stale-head">${
        escapeHTML(t("reg.staleTitle"))}</p><p>${
        escapeHTML(t("reg.staleBody", { date: data.updated }))}</p><p>${link}</p></div>`
        + zonesHtml();
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
      zonesHtml() +
      `<p class="reg-note">${escapeHTML(t("reg.disclaimer"))} ${link}</p>`;
  }

  PMF_I18N.onChange(render);
  render();
}

// Le statut officiel range les 47 fiches en trois familles sans qu'on ait à
// juger quoi que ce soit : le gouvernement l'a déjà écrit. On lit la valeur
// FRANÇAISE plutôt que la traduite — la carte doit tomber dans le même groupe
// dans les deux langues, et « invasive » ne contient pas « envahissant ».
function frValue(v) {
  return (v && typeof v === "object" ? v.fr || v.en : v) || "";
}

const SPECIES_GROUPS = [
  { id: "sportive", key: "sp.groupSport", openByDefault: true,
    match: (s) => !frValue(s.status) },
  { id: "statut", key: "sp.groupStatus",
    match: (s) => frValue(s.status) && !/envahissant/i.test(frValue(s.status)) },
  { id: "envahissante", key: "sp.groupInvasive",
    match: (s) => /envahissant/i.test(frValue(s.status)) },
];

async function initSpecies(gridSelector, countSelector, searchSelector, navSelector) {
  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

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

  const search = searchSelector ? document.querySelector(searchSelector) : null;
  const nav = navSelector ? document.querySelector(navSelector) : null;

  // « walleye », « doré jaune » et « Sander vitreus » doivent tous mener au
  // doré, quelle que soit la langue affichée. tr() ne rend que la langue
  // courante : chercher « walleye » en français ne trouvait rien. On aplatit
  // donc les DEUX côtés de chaque champ bilingue.
  function bothLangs(v) {
    if (!v) return [];
    if (typeof v === "object") return [v.fr || "", v.en || ""];
    return [String(v)];
  }
  function haystack(s) {
    return [s.name, s.status]
      .concat(s.otherNames || [])
      .map(bothLangs)
      .flat()
      .concat([s.scientificName || ""])
      .join(" ")
      .toLowerCase();
  }

  function card(s) {
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
  }

  function render() {
    const q = (search ? search.value : "").trim().toLowerCase();
    const shown = q ? list.filter((s) => haystack(s).indexOf(q) !== -1) : list;

    const count = document.querySelector(countSelector);
    if (count) count.textContent = t("sp.indexCount", { n: list.length });

    if (nav) {
      // Les liens rapides suivent le filtre : pointer vers un groupe vide
      // ferait défiler vers rien, ce qui se lit comme un lien cassé.
      const chips = SPECIES_GROUPS
        .map((g) => [g, shown.filter(g.match).length])
        .filter(([, n]) => n > 0)
        .map(([g, n]) => `<a class="sp-chip" href="especes.html#sp-${g.id}">${
          escapeHTML(t(g.key))} <span class="sp-chip-n">${n}</span></a>`);
      nav.innerHTML = chips.join("");
      nav.hidden = chips.length < 2;
    }

    if (!shown.length) {
      grid.innerHTML = `<p class="empty-state">${escapeHTML(t("sp.empty"))}</p>`;
      return;
    }

    // Trois titres et trois intros ajoutaient 1,4 écran à une page dont le
    // reproche était justement la longueur. Repliés comme les mois du guide,
    // les deux groupes qu'on ne parcourt pas la ramènent sous la moitié. Une
    // recherche rouvre tout ce qu'elle touche, sinon ses résultats seraient
    // cachés derrière un titre fermé.
    // Changer de langue reconstruit la grille : sans ça, un groupe qu'on vient
    // d'ouvrir se refermait au clic sur EN, ce qui se lit comme un bogue.
    const openNow = new Set([...grid.querySelectorAll(".sp-group[open]")]
      .map((el) => el.id.replace(/^sp-/, "")));

    grid.innerHTML = SPECIES_GROUPS.map((g) => {
      const members = shown.filter(g.match);
      if (!members.length) return "";
      const wasOpen = openNow.has(g.id);
      const open = q || (openNow.size ? wasOpen : g.openByDefault) ? " open" : "";
      return `<details class="sp-group" id="sp-${g.id}"${open}>
  <summary class="sp-group-head">
    <h2>${escapeHTML(t(g.key))}</h2>
    <span class="sp-group-count">${escapeHTML(plural("sp.groupCount", members.length))}</span>
  </summary>
  <p class="tp-notes sp-group-note">${escapeHTML(t(g.key + "Note"))}</p>
  <div class="sp-grid">${members.map(card).join("")}</div>
</details>`;
    }).join("");
  }

  // Une pastille qui mène à un groupe replié dépose le visiteur sur un titre
  // fermé — il croit que le groupe est vide. On l'ouvre avant d'y aller.
  if (nav) {
    nav.addEventListener("click", (e) => {
      const chip = e.target.closest(".sp-chip");
      if (!chip) return;
      const box = document.getElementById(chip.getAttribute("href").split("#")[1]);
      if (box) box.open = true;
    });
  }

  // Un lien partagé vers #sp-statut arrive avant que la grille existe : le
  // navigateur ne trouve rien, puis la grille se construit et le groupe reste
  // fermé. On refait le saut une fois le rendu fait, sans animation au
  // chargement puisque le visiteur n'a encore rien vu bouger.
  function openHashGroup(atLoad) {
    const id = (location.hash || "").slice(1);
    if (!/^sp-/.test(id)) return;
    const box = document.getElementById(id);
    if (!box) return;
    box.open = true;
    const header = document.querySelector(".site-header");
    const offset = (header ? header.getBoundingClientRect().height : 0) + 10;
    window.scrollTo({
      top: Math.max(0, box.getBoundingClientRect().top + window.scrollY - offset),
      behavior: atLoad ? "auto" : "smooth",
    });
  }
  window.addEventListener("hashchange", () => openHashGroup(false));

  if (search) search.addEventListener("input", render);
  PMF_I18N.onChange(render);
  render();
  openHashGroup(true);
}
