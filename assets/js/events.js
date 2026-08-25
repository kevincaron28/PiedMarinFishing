// Pied Marin Fishing — data-driven event list renderer
// Used by calendar.html (team schedule) and tournaments.html (regional directory)

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function parseISODate(value) {
  if (!value) return null;
  const [y, m, d] = value.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function formatDateRange(startISO, endISO) {
  const start = parseISODate(startISO);
  if (!start) return "Date TBD";
  const end = endISO ? parseISODate(endISO) : null;
  const startLabel = `${MONTH_NAMES[start.getMonth()].slice(0, 3)} ${start.getDate()}`;
  if (!end || end.getTime() === start.getTime()) return startLabel;
  const sameMonth = end.getMonth() === start.getMonth();
  return sameMonth
    ? `${startLabel}–${end.getDate()}`
    : `${startLabel} – ${MONTH_NAMES[end.getMonth()].slice(0, 3)} ${end.getDate()}`;
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
    linkText = "Details",
  } = options;

  const listEl = document.querySelector(listSelector);
  if (!listEl) return;

  let events = [];
  try {
    const res = await fetch(dataUrl);
    events = await res.json();
  } catch (err) {
    listEl.innerHTML = `<div class="empty-state">Could not load event data. (${escapeHTML(String(err))})</div>`;
    return;
  }

  events.sort((a, b) => (a.startDate || "9999").localeCompare(b.startDate || "9999"));

  const monthSelect = monthFilterSelector ? document.querySelector(monthFilterSelector) : null;
  const regionSelect = regionFilterSelector ? document.querySelector(regionFilterSelector) : null;
  const searchInput = searchSelector ? document.querySelector(searchSelector) : null;

  if (regionSelect) {
    const regions = Array.from(new Set(events.map((e) => e.region).filter(Boolean))).sort();
    regions.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      regionSelect.appendChild(opt);
    });
  }

  function matchesFilters(ev) {
    if (monthSelect && monthSelect.value !== "") {
      const d = parseISODate(ev.startDate);
      if (!d || String(d.getMonth()) !== monthSelect.value) return false;
    }
    if (regionSelect && regionSelect.value !== "" && ev.region !== regionSelect.value) return false;
    if (searchInput && searchInput.value.trim() !== "") {
      const q = searchInput.value.trim().toLowerCase();
      const hay = [ev.name, ev.location, ev.organizer, ev.species, ev.notes].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }

  function render() {
    const filtered = events.filter(matchesFilters);
    const emptyEl = emptySelector ? document.querySelector(emptySelector) : null;
    const countEl = countSelector ? document.querySelector(countSelector) : null;

    if (countEl) {
      countEl.textContent = `${filtered.length} event${filtered.length === 1 ? "" : "s"}`;
    }

    if (filtered.length === 0) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";

    listEl.innerHTML = filtered.map((ev) => {
      const d = parseISODate(ev.startDate);
      const month = d ? MONTH_NAMES[d.getMonth()].slice(0, 3).toUpperCase() : "TBD";
      const day = d ? d.getDate() : "?";
      const badge = ev[badgeField] ? `<span class="badge${ev.status === "tentative" ? " gold" : ""}">${escapeHTML(ev[badgeField])}</span>` : "";
      const metaBits = [];
      if (ev.location) metaBits.push(`<span>📍 ${escapeHTML(ev.location)}</span>`);
      if (ev.region) metaBits.push(`<span>${escapeHTML(ev.region)}</span>`);
      if (ev.species) metaBits.push(`<span>🎣 ${escapeHTML(ev.species)}</span>`);
      if (ev.organizer) metaBits.push(`<span>${escapeHTML(ev.organizer)}</span>`);

      return `
        <article class="event-card">
          <div class="event-date">
            <span class="month">${month}</span>
            <span class="day">${day}</span>
          </div>
          <div>
            <div class="event-title">${escapeHTML(ev.name)} ${badge}</div>
            <div class="event-meta">${metaBits.join("")}</div>
            ${ev.notes ? `<p style="margin:8px 0 0;font-size:0.88rem;">${escapeHTML(ev.notes)}</p>` : ""}
          </div>
          <div class="event-cta">
            ${ev.link ? `<a class="btn btn-teal" href="${escapeHTML(ev.link)}" target="_blank" rel="noopener">${linkText}</a>` : ""}
          </div>
        </article>
      `;
    }).join("");
  }

  [monthSelect, regionSelect, searchInput].forEach((el) => {
    if (el) el.addEventListener("input", render);
  });

  render();
}
