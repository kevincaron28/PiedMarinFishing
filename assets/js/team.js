// Pied Marin Fishing — team roster cards
// Each card carries the angler's specs plus a record strip summarising their
// results, which deep-links into the palmarès page.

const SPEC_FIELDS = [
  { field: "homeWater", key: "team.spec.homeWater", icon: "🌊" },
  { field: "species", key: "team.spec.species", icon: "🐟" },
  { field: "technique", key: "team.spec.technique", icon: "🎯" },
  { field: "dreamCatch", key: "team.spec.dreamCatch", icon: "⭐" },
  { field: "personalBest", key: "team.spec.personalBest", icon: "🏅" },
  { field: "since", key: "team.spec.since", icon: "📅" },
];

async function initTeam(gridSelector) {
  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

  let members = [];
  let results = [];
  try {
    [members, results] = await Promise.all([
      fetch("data/team-members.json").then((r) => r.json()),
      PMF_HISTORY.load(),
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
      const bio = tr(m.bio);
      const quote = tr(m.quote);
      const specs = m.specs || {};

      // Empty fields are slots waiting to be filled, not broken cards.
      const bioBlock = bio
        ? `<p>${escapeHTML(bio)}</p>`
        : `<p class="member-bio-empty">${escapeHTML(t("team.bioPlaceholder"))}</p>`;

      // Every spec row is always shown so the card doubles as a fill-in sheet.
      const specRows = SPEC_FIELDS.map(({ field, key, icon }) => {
        const value = tr(specs[field]);
        return `
          <div class="spec-row${value ? "" : " spec-empty"}">
            <dt><span class="spec-icon" aria-hidden="true">${icon}</span>${escapeHTML(t(key))}</dt>
            <dd>${value ? escapeHTML(value) : "—"}</dd>
          </div>
        `;
      }).join("");

      const mine = m.id ? PMF_HISTORY.forMember(results, m.id) : [];
      const s = PMF_HISTORY.summarize(mine);
      const recordBits = [
        `<span><b>${s.events}</b> ${escapeHTML(plural("team.record.events", s.events))}</span>`,
      ];
      if (s.best) {
        recordBits.push(`<span><b>${escapeHTML(ordinal(s.best, lang))}</b> ${escapeHTML(t("team.record.best"))}</span>`);
      }
      if (s.top3) {
        recordBits.push(`<span><b>${s.top3}</b> ${escapeHTML(t("team.record.top3"))}</span>`);
      }

      const historyLink = m.id
        ? `<a class="member-history-link" href="history.html?member=${encodeURIComponent(m.id)}">${escapeHTML(t("team.viewResults"))}</a>`
        : "";

      return `
        <div class="member-card">
          <div class="member-photo">${escapeHTML(initials)}</div>
          <div class="member-body">
            ${role ? `<span class="member-role">${escapeHTML(role)}</span>` : ""}
            <h3>${escapeHTML(name)}</h3>
            ${bioBlock}
            <dl class="member-specs">${specRows}</dl>
            ${quote ? `<div class="member-quote">"${escapeHTML(quote)}"</div>` : ""}
            <div class="member-record">${recordBits.join("")}</div>
            ${historyLink}
          </div>
        </div>
      `;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
