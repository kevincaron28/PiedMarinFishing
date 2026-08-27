// Pied Marin Fishing — team boats
// Rendered as a section on the team page. A boat's `skipper` holds a member
// id, which links the card back to that angler.

const BOAT_SPEC_FIELDS = [
  { field: "model", key: "boats.spec.model" },
  { field: "year", key: "boats.spec.year" },
  { field: "length", key: "boats.spec.length" },
  { field: "engine", key: "boats.spec.engine" },
  { field: "trolling", key: "boats.spec.trolling" },
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
      fetch("data/boats.json").then((r) => r.json()),
      fetch("data/team-members.json").then((r) => r.json()).catch(() => []),
    ]);
  } catch (e) {
    host.innerHTML = `<div class="empty-state">${escapeHTML(t("boats.loadError"))}</div>`;
    return;
  }

  const memberById = new Map(members.map((m) => [m.id, m]));

  function render() {
    host.innerHTML = boats.map((b) => {
      const name = tr(b.name) || "—";
      const description = tr(b.description);
      const specs = b.specs || {};

      const specRows = BOAT_SPEC_FIELDS.map(({ field, key }) => {
        const value = tr(specs[field]);
        return `
          <div class="spec-row${value ? "" : " spec-empty"}">
            <dt>${escapeHTML(t(key))}</dt>
            <dd>${value ? escapeHTML(value) : "—"}</dd>
          </div>
        `;
      }).join("");

      // Un bateau peut appartenir à un membre et être barré par un autre.
      const skipper = memberById.get(b.skipper);
      const owner = memberById.get(b.owner);
      const crewLink = (m) =>
        `<a href="history.html?member=${encodeURIComponent(m.id)}">${escapeHTML(tr(m.name))}</a>`;
      let skipperRow = "";
      if (skipper && owner && skipper.id === owner.id) {
        skipperRow = `<div class="boat-skipper">${escapeHTML(t("boats.skipperOwner"))} ${crewLink(skipper)}</div>`;
      } else {
        const parts = [];
        if (skipper) parts.push(`${escapeHTML(t("boats.skipper"))} ${crewLink(skipper)}`);
        if (owner) parts.push(`${escapeHTML(t("boats.owner"))} ${crewLink(owner)}`);
        if (parts.length) skipperRow = `<div class="boat-skipper">${parts.join("<br>")}</div>`;
      }

      const photo = b.image
        ? `<img src="${escapeHTML(b.image)}" alt="${escapeHTML(t("boats.photoAlt", { name }))}" class="boat-photo-img">`
        : "";

      return `
        <article class="boat-card">
          <div class="boat-photo">${photo}</div>
          <div class="boat-body">
            <h3>${escapeHTML(name)}</h3>
            ${description
              ? `<p>${escapeHTML(description)}</p>`
              : `<p class="member-bio-empty">${escapeHTML(t("boats.descPlaceholder"))}</p>`}
            <dl class="member-specs boat-specs">${specRows}</dl>
            ${skipperRow}
          </div>
        </article>
      `;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
