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
  let catches = [];
  try {
    [members, results, catches] = await Promise.all([
      fetch("data/team-members.json").then((r) => r.json()),
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
      const bio = tr(m.bio);
      // Une vraie photo remplace les initiales; sinon la carte garde son écusson.
      const photoAlt = tr(m.photoAlt) || name;
      const photoBlock = m.photo
        ? `<div class="member-photo has-photo">
             <img class="member-photo-img" src="${escapeHTML(m.photo)}"
                  alt="${escapeHTML(photoAlt)}" loading="lazy" width="1200" height="900">
           </div>`
        : `<div class="member-photo"><span class="member-initials">${escapeHTML(initials)}</span></div>`;

      const quote = tr(m.quote);
      const quoteBy = tr(m.quoteBy);
      const fr = PMF_I18N.lang === "fr";
      const openQuote = fr ? "&laquo;&nbsp;" : "&ldquo;";
      const closeQuote = fr ? "&nbsp;&raquo;" : "&rdquo;";
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

      const catchLink = m.id && mine2.length
        ? `<a class="member-history-link" href="catches.html?angler=${encodeURIComponent(m.id)}">${escapeHTML(t("team.viewCatches"))}</a>`
        : "";

      const historyLink = m.id
        ? `<a class="member-history-link" href="history.html?member=${encodeURIComponent(m.id)}">${escapeHTML(t("team.viewResults"))}</a>`
        : "";

      return `
        <div class="member-card">
          ${photoBlock}
          <div class="member-body">
            ${role ? `<span class="member-role">${escapeHTML(role)}</span>` : ""}
            <h3>${escapeHTML(name)}</h3>
            ${bioBlock}
            <dl class="member-specs">${specRows}</dl>
            ${quote ? `<div class="member-quote">${openQuote}${escapeHTML(quote)}${closeQuote}${quoteBy ? `<span class="member-quote-by">&mdash; ${escapeHTML(quoteBy)}</span>` : ""}</div>` : ""}
            <div class="member-record">${recordBits.join("")}</div>
            ${historyLink}
            ${catchLink}
          </div>
        </div>
      `;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
