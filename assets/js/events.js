// Pied Marin Fishing — data-driven event list renderer (bilingual)
// Used by calendar.html (team schedule) and tournaments.html (regional directory)

const MONTHS = {
  fr: {
    full: ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
           "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
    abbr: ["JAN", "FÉV", "MARS", "AVR", "MAI", "JUIN",
           "JUIL", "AOÛT", "SEPT", "OCT", "NOV", "DÉC"],
  },
  en: {
    full: ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    abbr: ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
  },
};

function parseISODate(value) {
  if (!value) return null;
  const [y, m, d] = value.split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

async function initEventList(options) {
  const {
    dataUrl,
    listSelector,
    emptySelector,
    countSelector,
    monthFilterSelector,
    regionFilterSelector,
    searchSelector,
    badgeField = "type",
    linkTextKey = "events.learnMore",
  } = options;

  const listEl = document.querySelector(listSelector);
  if (!listEl) return;

  // Strings must be in place before the first render.
  await PMF_I18N.ready;

  const { t, tr, trAll, plural, key: stableKey } = PMF_I18N;

  let events = [];
  try {
    const res = await fetch(dataUrl);
    events = await res.json();
  } catch (err) {
    listEl.innerHTML = `<div class="empty-state">${escapeHTML(t("events.loadError"))}</div>`;
    return;
  }

  events.sort((a, b) => (a.startDate || "9999").localeCompare(b.startDate || "9999"));

  const monthSelect = monthFilterSelector ? document.querySelector(monthFilterSelector) : null;
  const regionSelect = regionFilterSelector ? document.querySelector(regionFilterSelector) : null;
  const searchInput = searchSelector ? document.querySelector(searchSelector) : null;

  // Option values are language-independent, so a language switch never
  // invalidates the visitor's current selection.
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
    const months = MONTHS[PMF_I18N.lang] || MONTHS.fr;
    buildOptions(
      monthSelect,
      months.full.map((label, i) => ({ value: String(i), label })),
      t("filters.allMonths")
    );

    const seen = new Map();
    events.forEach((ev) => {
      const k = stableKey(ev.region);
      if (k && !seen.has(k)) seen.set(k, tr(ev.region));
    });
    const regions = Array.from(seen, ([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label, PMF_I18N.lang));
    buildOptions(regionSelect, regions, t("filters.allRegions"));
  }

  function matchesFilters(ev) {
    if (monthSelect && monthSelect.value !== "") {
      const d = parseISODate(ev.startDate);
      if (!d || String(d.getMonth()) !== monthSelect.value) return false;
    }
    if (regionSelect && regionSelect.value !== "" && stableKey(ev.region) !== regionSelect.value) {
      return false;
    }
    if (searchInput && searchInput.value.trim() !== "") {
      const q = searchInput.value.trim().toLowerCase();
      // Search every translation so a French query still finds an English entry.
      const hay = [ev.name, ev.location, ev.organizer, ev.species, ev.notes, ev.region]
        .map(trAll)
        .join(" ")
        .toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }

  function render() {
    const months = MONTHS[PMF_I18N.lang] || MONTHS.fr;
    const filtered = events.filter(matchesFilters);
    const emptyEl = emptySelector ? document.querySelector(emptySelector) : null;
    const countEl = countSelector ? document.querySelector(countSelector) : null;

    if (countEl) countEl.textContent = plural("filters.count", filtered.length);

    if (filtered.length === 0) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";

    listEl.innerHTML = filtered.map((ev) => {
      const d = parseISODate(ev.startDate);
      const month = d ? months.abbr[d.getMonth()] : t("events.tbd");
      const day = d ? d.getDate() : "?";

      const badgeText = tr(ev[badgeField]);
      const badge = badgeText
        ? `<span class="badge${ev.status === "tentative" ? " gold" : ""}">${escapeHTML(badgeText)}</span>`
        : "";

      const metaBits = [];
      if (ev.location) metaBits.push(`<span>📍 ${escapeHTML(tr(ev.location))}</span>`);
      if (ev.region) metaBits.push(`<span>${escapeHTML(tr(ev.region))}</span>`);
      if (ev.species) metaBits.push(`<span>🎣 ${escapeHTML(tr(ev.species))}</span>`);
      if (ev.organizer) metaBits.push(`<span>${escapeHTML(tr(ev.organizer))}</span>`);

      const notes = tr(ev.notes);

      return `
        <article class="event-card">
          <div class="event-date">
            <span class="month">${escapeHTML(month)}</span>
            <span class="day">${day}</span>
          </div>
          <div>
            <div class="event-title">${escapeHTML(tr(ev.name))} ${badge}</div>
            <div class="event-meta">${metaBits.join("")}</div>
            ${notes ? `<p style="margin:8px 0 0;font-size:0.88rem;">${escapeHTML(notes)}</p>` : ""}
          </div>
          <div class="event-cta">
            ${ev.link ? `<a class="btn btn-teal" href="${escapeHTML(ev.link)}" target="_blank" rel="noopener">${escapeHTML(t(linkTextKey))}</a>` : ""}
          </div>
        </article>
      `;
    }).join("");
  }

  [monthSelect, regionSelect, searchInput].forEach((el) => {
    if (el) el.addEventListener("input", render);
  });

  PMF_I18N.onChange(() => {
    refreshFilterOptions();
    render();
  });

  refreshFilterOptions();
  render();
}
