// Pied Marin Fishing — tournament results (palmarès)
// Shared by history.html and the record strip on the team cards.
// Helpers (months, parseISODate, escapeHTML, ordinal, queryParam) come from util.js.

const PMF_HISTORY = (() => {
  let cache = null;

  function load() {
    if (!cache) {
      cache = fetch("data/tournament-history.json", DATA_FETCH)
        .then((r) => r.json())
        .then((rows) => rows.slice().sort((a, b) => (b.date || "").localeCompare(a.date || "")))
        .catch(() => []);
    }
    return cache;
  }

  // Compare des mesures écrites pour l'oeil (« 55,25 po ») : on isole le nombre.
  function figureValue(v) {
    const txt = (typeof v === "object" && v) ? (v.fr || v.en || "") : (v || "");
    const n = parseFloat(String(txt).replace(",", ".").replace(/[^\d.]/g, ""));
    return Number.isFinite(n) ? n : null;
  }

  function bestFigure(rows) {
    let best = null;
    rows.forEach((r) => {
      const f = (r.figures || [])[0];
      if (!f) return;
      const n = figureValue(f.value);
      if (n !== null && (best === null || n > best.n)) best = { n, figure: f };
    });
    return best;
  }

  function bestFieldSize(rows) {
    let best = null;
    rows.forEach((r) => {
      if (!Number.isFinite(r.placement)) return;
      if (best === null || r.placement < best.placement) best = r;
    });
    return best && Number.isFinite(best.fieldSize) ? best.fieldSize : null;
  }

  // Aggregate stats for a set of results — the whole team, or one angler.
  function summarize(rows) {
    const placements = rows.map((r) => r.placement).filter((p) => Number.isFinite(p));
    const seasons = new Set(rows.map((r) => (r.date || "").slice(0, 4)).filter(Boolean));
    return {
      events: rows.length,
      best: placements.length ? Math.min(...placements) : null,
      // Le peloton du meilleur résultat : un rang sans son dénominateur
      // ne veut rien dire.
      bestField: bestFieldSize(rows),
      top3: placements.filter((p) => p <= 3).length,
      wins: placements.filter((p) => p === 1).length,
      seasons: seasons.size,
      // La première mesure d'une sortie est celle qui a servi au pointage.
      bestFigure: bestFigure(rows),
    };
  }

  function forMember(rows, memberId) {
    return rows.filter((r) => Array.isArray(r.members) && r.members.includes(memberId));
  }

  return { load, summarize, forMember };
})();

// Podium finishes get a colour; everything else stays neutral.
// Un rang brut ne se lit pas sans son peloton : 99e est excellent sur 329,
// médiocre sur 120. Le centile le dit d'un coup d'œil, et c'est la façon dont
// les circuits présentent leurs résultats.
function topPercent(placement, fieldSize) {
  if (!Number.isFinite(placement) || !Number.isFinite(fieldSize) || fieldSize < 1) return null;
  return Math.max(1, Math.ceil((placement / fieldSize) * 100));
}

function placementClass(placement) {
  if (placement === 1) return "gold";
  if (placement === 2) return "silver";
  if (placement === 3) return "bronze";
  return "";
}

async function initHistory(options) {
  const {
    listSelector,
    emptySelector,
    statsSelector,
    tableSelector,
    countSelector,
    memberFilterSelector,
    yearFilterSelector,
    searchSelector,
  } = options;

  const listEl = document.querySelector(listSelector);
  if (!listEl) return;

  await PMF_I18N.ready;
  const { t, tr, trAll, plural } = PMF_I18N;

  let results = [];
  let members = [];
  try {
    [results, members] = await Promise.all([
      PMF_HISTORY.load(),
      fetch("data/team-members.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
    ]);
  } catch (e) {
    listEl.innerHTML = `<div class="empty-state">${escapeHTML(t("history.loadError"))}</div>`;
    return;
  }

  const memberById = new Map(members.map((m) => [m.id, m]));

  const memberSelect = memberFilterSelector ? document.querySelector(memberFilterSelector) : null;
  const yearSelect = yearFilterSelector ? document.querySelector(yearFilterSelector) : null;
  const searchInput = searchSelector ? document.querySelector(searchSelector) : null;
  const statsEl = statsSelector ? document.querySelector(statsSelector) : null;
  const tableEl = tableSelector ? document.querySelector(tableSelector) : null;
  const countEl = countSelector ? document.querySelector(countSelector) : null;
  const emptyEl = emptySelector ? document.querySelector(emptySelector) : null;

  function buildOptions(select, entries, allLabel) {
    if (!select) return;
    const previous = select.value;
    select.innerHTML = "";
    const all = document.createElement("option");
    all.value = "";
    all.textContent = allLabel;
    select.appendChild(all);
    entries.forEach(({ value, label }) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = label;
      select.appendChild(opt);
    });
    select.value = previous;
  }

  function refreshFilterOptions() {
    buildOptions(
      memberSelect,
      members.map((m) => ({ value: m.id, label: tr(m.name) })),
      t("history.allMembers")
    );
    const years = Array.from(new Set(results.map((r) => (r.date || "").slice(0, 4)).filter(Boolean)))
      .sort((a, b) => b.localeCompare(a));
    buildOptions(yearSelect, years.map((y) => ({ value: y, label: y })), t("history.allSeasons"));
  }

  function matches(r) {
    if (memberSelect && memberSelect.value && !(r.members || []).includes(memberSelect.value)) return false;
    if (yearSelect && yearSelect.value && (r.date || "").slice(0, 4) !== yearSelect.value) return false;
    if (searchInput && searchInput.value.trim()) {
      const q = searchInput.value.trim().toLowerCase();
      const hay = [r.name, r.location, r.region, r.species, r.organizer, r.notes]
        .map(trAll).join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }

  function renderStats(rows) {
    if (!statsEl) return;
    const s = PMF_HISTORY.summarize(rows);
    const lang = PMF_I18N.lang;
    const tiles = [
      { num: s.events, label: plural("history.stat.events", s.events) },
      { num: s.best ? placementOf(s.best, s.bestField, lang, t("history.of", { n: s.bestField })) : "—",
        label: t("history.stat.best") },
      // Un « 0 podium » en évidence ne dit rien; la meilleure mesure, oui.
      // La tuile podium revient d'elle-même au premier top 3.
      s.top3 > 0
        ? { num: s.top3, label: plural("history.stat.top3", s.top3) }
        : (s.bestFigure
            ? { num: PMF_I18N.tr(s.bestFigure.figure.value), label: t("history.stat.bestScore") }
            : { num: s.top3, label: plural("history.stat.top3", s.top3) }),
      { num: s.seasons, label: plural("history.stat.seasons", s.seasons) },
    ];
    statsEl.innerHTML = tiles.map((x) => `
      <div class="stat-card">
        <div class="num">${escapeHTML(String(x.num))}</div>
        <div class="label">${escapeHTML(x.label)}</div>
      </div>
    `).join("");
  }

  function renderTable(rows) {
    if (!tableEl) return;
    const section = tableEl.closest("[data-table-section]") || tableEl;
    if (rows.length < 2) {
      section.hidden = true;
      tableEl.innerHTML = "";
      return;
    }
    section.hidden = false;
    const lang = PMF_I18N.lang;
    const head = ["history.col.season", "history.col.event",
                  "history.col.place", "history.col.score"]
      .map((k) => `<th>${escapeHTML(t(k))}</th>`).join("");
    const body = rows.map((r) => {
      const season = String(r.date || "").slice(0, 4) || "—";
      const pct = topPercent(r.placement, r.fieldSize);
      const place = Number.isFinite(r.placement)
        ? `${escapeHTML(ordinal(r.placement, lang))}${
            Number.isFinite(r.fieldSize) ? " " + escapeHTML(t("history.of", { n: r.fieldSize })) : ""}`
        : "—";
      const first = (r.figures || [])[0];
      const score = first ? tr(first.value) : (r.weight ? tr(r.weight) : "—");
      return `
        <tr>
          <td>${escapeHTML(season)}</td>
          <td>${escapeHTML(tr(r.name))}</td>
          <td>${place}${pct ? ` <span class="table-pct">${escapeHTML(t("history.topPercent", { n: pct }))}</span>` : ""}</td>
          <td>${escapeHTML(score)}</td>
        </tr>`;
    }).join("");
    tableEl.innerHTML =
      `<table class="record-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }

  function render() {
    const lang = PMF_I18N.lang;
    const m = months(lang);
    const rows = results.filter(matches);

    renderStats(rows);
    renderTable(rows);
    if (countEl) countEl.textContent = plural("history.count", rows.length);

    if (!rows.length) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";

    listEl.innerHTML = rows.map((r) => {
      // Show exactly as much of the date as the data actually knows.
      const p = dateParts(r.date);
      let dateBadge;
      if (!p) {
        dateBadge = `<span class="month">${escapeHTML(t("events.tbd"))}</span><span class="day">?</span>`;
      } else if (p.month !== null && p.day !== null) {
        dateBadge = `<span class="month">${escapeHTML(m.abbr[p.month])}</span>`
          + `<span class="day">${p.day}</span>`
          + `<span class="year">${p.year}</span>`;
      } else if (p.month !== null) {
        dateBadge = `<span class="month">${escapeHTML(m.abbr[p.month])}</span>`
          + `<span class="day year-only">${p.year}</span>`;
      } else {
        dateBadge = `<span class="day year-only">${p.year}</span>`;
      }

      const place = Number.isFinite(r.placement)
        ? `<span class="placement ${placementClass(r.placement)}">${escapeHTML(ordinal(r.placement, lang))}</span>`
        : `<span class="placement placement-unknown" title="${escapeHTML(t("history.resultPending"))}">—</span>`;
      const pct = topPercent(r.placement, r.fieldSize);
      const pctHTML = pct
        ? `<span class="placement-pct">${escapeHTML(t("history.topPercent", { n: pct }))}</span>`
        : "";
      const field = Number.isFinite(r.fieldSize)
        ? `<span class="placement-of">${escapeHTML(t("history.of", { n: r.fieldSize }))}</span>`
        : "";

      const meta = [];
      if (r.location) meta.push(`<span>📍 ${escapeHTML(tr(r.location))}</span>`);
      if (r.region) meta.push(`<span>${escapeHTML(tr(r.region))}</span>`);
      if (r.species) meta.push(`<span>🎣 ${escapeHTML(tr(r.species))}</span>`);
      if (r.organizer) meta.push(`<span>${escapeHTML(tr(r.organizer))}</span>`);

      // Weight events use weight/bigFish; length events (catch-photo-release)
      // supply their own labelled figures. Empty values simply don't render.
      const figures = [];
      if (r.weight) figures.push(`<span><b>${escapeHTML(r.weight)}</b> ${escapeHTML(t("history.weight"))}</span>`);
      if (r.bigFish) figures.push(`<span><b>${escapeHTML(r.bigFish)}</b> ${escapeHTML(t("history.bigFish"))}</span>`);
      (r.figures || []).forEach((f) => {
        const value = tr(f.value);
        if (value) figures.push(`<span><b>${escapeHTML(value)}</b> ${escapeHTML(tr(f.label))}</span>`);
      });

      const anglers = (r.members || []).map((id) => {
        const mem = memberById.get(id);
        const label = mem ? tr(mem.name) : id;
        return `<a class="angler-chip" href="?member=${encodeURIComponent(id)}">${escapeHTML(label)}</a>`;
      }).join("");

      const notes = tr(r.notes);

      return `
        <article class="result-card">
          <div class="event-date">${dateBadge}</div>
          <div class="result-main">
            <div class="event-title">${escapeHTML(tr(r.name))}</div>
            <div class="event-meta">${meta.join("")}</div>
            ${figures.length ? `<div class="result-figures">${figures.join("")}</div>` : ""}
            ${anglers ? `<div class="angler-chips"><span class="angler-label">${escapeHTML(t("history.anglers"))}</span>${anglers}</div>` : ""}
            ${notes ? `<p class="result-notes">${escapeHTML(notes)}</p>` : ""}
          </div>
          <div class="result-place">
            ${place}
            ${field}
            ${pctHTML}
          </div>
        </article>
      `;
    }).join("");
  }

  [memberSelect, yearSelect, searchInput].forEach((el) => {
    if (el) el.addEventListener("input", render);
  });

  PMF_I18N.onChange(() => {
    refreshFilterOptions();
    render();
  });

  refreshFilterOptions();

  // Allow deep links from the team cards: history.html?member=bobe
  const preselect = queryParam("member");
  if (memberSelect && preselect && memberById.has(preselect)) {
    memberSelect.value = preselect;
  }

  render();
}
