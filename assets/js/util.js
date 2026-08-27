// Pied Marin Fishing — shared helpers used by the event and results renderers

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

function months(lang) {
  return MONTHS[lang] || MONTHS.fr;
}

function parseISODate(value) {
  if (!value) return null;
  const [y, m, d] = String(value).split("-").map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}

// Dates may be partial: "2024", "2024-05" or "2024-05-03". Use this when the
// year is known but the exact day isn't, rather than inventing one.
function dateParts(value) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  const [y, m, d] = raw.split("-").map(Number);
  if (!Number.isFinite(y)) return null;
  return {
    year: y,
    month: Number.isFinite(m) ? m - 1 : null,
    day: Number.isFinite(d) ? d : null,
  };
}

function escapeHTML(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// 1re / 2e in French, 1st / 2nd / 3rd / 4th in English.
function ordinal(n, lang) {
  if (!Number.isFinite(n)) return "";
  if (lang === "fr") return n === 1 ? "1re" : `${n}e`;
  const suffixes = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}

// « 99e sur 237 ». Un rang seul ne dit rien : sans le peloton, 99e peut
// aussi bien être excellent que quelconque.
function placementOf(placement, fieldSize, lang, ofLabel) {
  if (!Number.isFinite(placement)) return "";
  const rank = ordinal(placement, lang);
  return Number.isFinite(fieldSize) ? `${rank} ${ofLabel}` : rank;
}

// The last moment a partial date could still refer to: "2026" -> 31 Dec 2026,
// "2026-05" -> 31 May 2026. Used to decide whether an event has passed.
function endOfPeriod(value) {
  const p = dateParts(value);
  if (!p) return null;
  if (p.month === null) return new Date(p.year, 11, 31);
  if (p.day === null) return new Date(p.year, p.month + 1, 0);
  return new Date(p.year, p.month, p.day);
}

// Undated (recurring, date-TBC) events are never treated as past.
function isPastEvent(ev) {
  const end = endOfPeriod(ev.endDate || ev.startDate);
  if (!end) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return end < today;
}

// Date badge showing only as much as the data actually knows.
function dateBadgeHTML(value, lang, tbdLabel) {
  const m = months(lang);
  const p = dateParts(value);
  if (!p) return `<span class="day date-tbd">${escapeHTML(tbdLabel)}</span>`;
  if (p.month !== null && p.day !== null) {
    return `<span class="month">${escapeHTML(m.abbr[p.month])}</span>`
      + `<span class="day">${p.day}</span>`
      + `<span class="year">${p.year}</span>`;
  }
  if (p.month !== null) {
    return `<span class="month">${escapeHTML(m.abbr[p.month])}</span>`
      + `<span class="day year-only">${p.year}</span>`;
  }
  return `<span class="day year-only">${p.year}</span>`;
}

// Reads a filter value out of the query string, e.g. history.html?member=bobe
function queryParam(name) {
  try {
    return new URLSearchParams(location.search).get(name) || "";
  } catch (e) {
    return "";
  }
}
