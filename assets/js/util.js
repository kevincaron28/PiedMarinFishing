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

// Reads a filter value out of the query string, e.g. history.html?member=bobe
function queryParam(name) {
  try {
    return new URLSearchParams(location.search).get(name) || "";
  } catch (e) {
    return "";
  }
}
