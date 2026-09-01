// Pied Marin Fishing — team roster cards
// Each card carries the angler's specs plus a record strip summarising their
// results, which deep-links into the palmarès page.

// Deux specs seulement : le plan d'eau et l'espèce disent qui est le pêcheur
// d'un coup d'œil, ce qui est le travail d'une carte. Les quatre autres —
// technique, prise de rêve, record personnel, depuis quand — vivent sur sa
// fiche, avec la bio. Les répéter ici rendait la fiche inutile à ouvrir.
const SPEC_FIELDS = [
  { field: "homeWater", key: "team.spec.homeWater", icon: "🌊" },
  { field: "species", key: "team.spec.species", icon: "🐟" },
];

async function initTeam(gridSelector) {
  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

  let members = [];
  let results = [];
  let catches = [];
  try {
    [members, results, catches] = await Promise.all([
      fetch("data/team-members.json", DATA_FETCH).then((r) => r.json()),
      PMF_HISTORY.load(),
      typeof PMF_CATCHES !== "undefined" ? PMF_CATCHES.load() : Promise.resolve([]),
    ]);
  } catch (e) {
    grid.innerHTML = `<div class="empty-state">${escapeHTML(t("team.loadError"))}</div>`;
    return;
  }

  function render() {
    const lang = PMF_I18N.lang;

    grid.innerHTML = members.map((m) => {
      const name = tr(m.name) || "?";
      const initials = (m.initials || name).toString().slice(0, 2).toUpperCase();
      const role = tr(m.role);
      // Une vraie photo remplace les initiales; sinon la carte garde son écusson.
      const photoAlt = tr(m.photoAlt) || name;
      const photoBlock = m.photo
        ? `<div class="member-photo has-photo">
             <img class="member-photo-img" src="${escapeHTML(m.photo)}"
                  alt="${escapeHTML(photoAlt)}" loading="lazy" width="900" height="1200">
           </div>`
        : `<div class="member-photo"><span class="member-initials">${escapeHTML(initials)}</span></div>`;

      const specs = m.specs || {};

      // Une rangée vide ne s'écrit plus : la carte est une porte d'entrée,
      // pas une feuille à remplir — c'est la fiche qui porte le détail.
      const specRows = SPEC_FIELDS.map(({ field, key, icon }) => {
        const value = tr(specs[field]);
        if (!value) return "";
        return `
          <div class="spec-row">
            <dt><span class="spec-icon" aria-hidden="true">${icon}</span>${escapeHTML(t(key))}</dt>
            <dd>${escapeHTML(value)}</dd>
          </div>
        `;
      }).join("");

      const mine = m.id ? PMF_HISTORY.forMember(results, m.id) : [];
      const s = PMF_HISTORY.summarize(mine);
      const recordBits = [
        `<span><b>${s.events}</b> ${escapeHTML(plural("team.record.events", s.events))}</span>`,
      ];
      if (s.best) {
        const place = placementOf(s.best, s.bestField, lang, t("history.of", { n: s.bestField }));
        recordBits.push(`<span><b>${escapeHTML(place)}</b> ${escapeHTML(t("team.record.best"))}</span>`);
      }
      if (s.top3) {
        recordBits.push(`<span><b>${s.top3}</b> ${escapeHTML(t("team.record.top3"))}</span>`);
      }

      // Catch count comes from the same log that drives the hall of fame.
      const mine2 = m.id && typeof PMF_CATCHES !== "undefined"
        ? PMF_CATCHES.forAngler(catches, m.id) : [];
      if (mine2.length) {
        recordBits.push(`<span><b>${mine2.length}</b> ${escapeHTML(plural("team.catchCount", mine2.length))}</span>`);
      }


      // Un seul lien : la fiche. Elle mène déjà aux résultats et aux prises,
      // alors les proposer aussi ici encombrait la carte de trois liens pour
      // deux destinations déjà atteignables d'un clic de plus.
      const profileLink = m.id
        ? `<a class="member-history-link member-profile-link" href="pecheurs/${encodeURIComponent(m.id)}.html">${escapeHTML(t("team.viewProfile"))}</a>`
        : "";

      return `
        <div class="member-card">
          ${photoBlock}
          <div class="member-body">
            ${role ? `<span class="member-role">${escapeHTML(role)}</span>` : ""}
            <h2>${escapeHTML(name)}</h2>
            <dl class="member-specs">${specRows}</dl>
            <div class="member-record">${recordBits.join("")}</div>
            ${profileLink}
          </div>
        </div>
      `;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
