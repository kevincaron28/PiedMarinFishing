// Pied Marin Fishing — team boats
// Rendered as a section on the team page. A boat's `skipper` holds a member
// id, which links the card back to that angler.

// Le modèle et l'année sont déjà dans le nom du bateau, et la longueur ne
// distingue pas deux coques identiques : la carte garde donc ce qui les
// sépare vraiment — le moteur et l'électronique. Le reste est sur la fiche.
const BOAT_SPEC_FIELDS = [
  { field: "engine", key: "boats.spec.engine" },
  { field: "electronics", key: "boats.spec.electronics" },
];

async function initBoats(selector) {
  const host = document.querySelector(selector);
  if (!host) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  let boats = [];
  let members = [];
  try {
    [boats, members] = await Promise.all([
      fetch("data/boats.json", DATA_FETCH).then((r) => r.json()),
      fetch("data/team-members.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
    ]);
  } catch (e) {
    host.innerHTML = `<div class="empty-state">${escapeHTML(t("boats.loadError"))}</div>`;
    return;
  }

  const memberById = new Map(members.map((m) => [m.id, m]));

  function render() {
    host.innerHTML = boats.map((b) => {
      const name = tr(b.name) || "—";
      const specs = b.specs || {};

      const specRows = BOAT_SPEC_FIELDS.map(({ field, key }) => {
        const value = tr(specs[field]);
        if (!value) return "";
        return `
          <div class="spec-row">
            <dt>${escapeHTML(t(key))}</dt>
            <dd>${escapeHTML(value)}</dd>
          </div>
        `;
      }).join("");

      // Un bateau peut appartenir à un membre et être barré par un autre.
      const skipper = memberById.get(b.skipper);
      const owner = memberById.get(b.owner);
      const crewLink = (m) =>
        `<a href="pecheurs/${encodeURIComponent(m.id)}.html">${escapeHTML(tr(m.name))}</a>`;
      let skipperRow = "";
      if (skipper && owner && skipper.id === owner.id) {
        skipperRow = `<div class="boat-skipper">${escapeHTML(t("boats.skipperOwner"))} ${crewLink(skipper)}</div>`;
      } else {
        const parts = [];
        if (skipper) parts.push(`${escapeHTML(t("boats.skipper"))} ${crewLink(skipper)}`);
        if (owner) parts.push(`${escapeHTML(t("boats.owner"))} ${crewLink(owner)}`);
        if (parts.length) skipperRow = `<div class="boat-skipper">${parts.join("<br>")}</div>`;
      }

      // Un bateau en chantier le dit sur sa carte : c'est ce qui donne envie
      // d'ouvrir sa fiche, où le journal de restauration se tient.
      const status = (b.restoration || {}).status || "";
      const statusBadge = status === "restoration"
        ? `<span class="boat-status">${escapeHTML(t("boats.restoring"))}</span>`
        : (status === "restored" || status === "done")
          ? `<span class="boat-status is-done">${escapeHTML(t("boats.restored"))}</span>`
          : "";

      const pageLink = b.id
        ? `<a class="member-history-link" href="bateaux/${encodeURIComponent(b.id)}.html">${escapeHTML(t("boats.viewPage"))}</a>`
        : "";

      const photo = b.image
        ? `<img src="${escapeHTML(b.image)}" alt="${escapeHTML(t("boats.photoAlt", { name }))}" class="boat-photo-img">`
        : "";

      return `
        <article class="boat-card">
          <div class="boat-photo">${photo}</div>
          <div class="boat-body">
            ${statusBadge}
            <h3>${escapeHTML(name)}</h3>
            <dl class="member-specs boat-specs">${specRows}</dl>
            ${skipperRow}
            ${pageLink}
          </div>
        </article>
      `;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
