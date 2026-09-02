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

// Une date en toutes lettres, dans la forme de la langue : « 23 mai 2025 » en
// français, "May 23, 2025" en anglais. Rend seulement ce que la date connaît —
// « Octobre 2024 » ou « 2024 » quand le jour ou le mois manquent.
function longDate(value, lang) {
  const p = dateParts(value);
  if (!p) return "";
  const m = months(lang);
  if (p.month === null) return String(p.year);
  // En français les mois s'écrivent en minuscule, y compris sans le jour :
  // « mai 2027 », pas « Mai 2027 ». La branche avec jour le faisait déjà.
  if (p.day === null) {
    return lang === "en"
      ? `${m.full[p.month]} ${p.year}`
      : `${m.full[p.month].toLowerCase()} ${p.year}`;
  }
  return lang === "en"
    ? `${m.full[p.month]} ${p.day}, ${p.year}`
    : `${p.day} ${m.full[p.month].toLowerCase()} ${p.year}`;
}

// Lit une mesure de prise : « 50 po », « 11 lb », « 45" ». Renvoie la valeur et
// son unité, ou null si rien n'est mesurable. Deux mesures ne se comparent que
// si leur unité est la même — des pouces contre des livres ne veulent rien dire.
// Partagé par la page Prises (temple de la renommée) et l'accueil (compteur).
function parseMeasure(text) {
  const m = String(text || "").match(/([\d]+(?:[.,][\d]+)?)\s*(po|lb|kg|cm|in|"|″)/i);
  if (!m) return null;
  return { value: parseFloat(m[1].replace(",", ".")), unit: m[2].toLowerCase().replace(/["″]/, "po") };
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

// Une date partielle se compare en la complétant : « 2027 » devient
// « 2027999999 », donc après tout ce qui est daté dans l'année.
function sortableDate(d) {
  return (d || "").padEnd(10, "9");
}

// Le classement d'un événement dont la date n'est pas encore publiée.
// Une entrée « 2027 » toute seule n'a pas de mois, alors six d'entre elles
// se retrouvaient à égalité et s'affichaient dans l'ordre du fichier — un
// gala de mai avant un salon de février. Quand previousDate donne la date de
// la dernière édition, on emprunte son mois et son jour pour classer, sans
// jamais prétendre connaître la date à venir : previousDate ne sert qu'ici.
function eventOrderKey(ev) {
  const start = ev.startDate || "";
  if (/^\d{4}$/.test(start) && /^\d{4}-\d{2}-\d{2}$/.test(ev.previousDate || "")) {
    return start + ev.previousDate.slice(4);
  }
  return sortableDate(start);
}

// Les photos existent en plusieurs largeurs, écrites par
// tools/build-image-variants.py et listées dans data/image-variants.json.
// On donne la liste au navigateur et c'est lui qui choisit : une vignette de
// 72px n'a aucune raison de télécharger 1200px.
//
// Une photo absente de la carte est servie telle quelle, sans srcset — donc
// ajouter une photo sans relancer l'outil dégrade le poids, jamais l'affichage.
const PMF_IMG = (() => {
  let map = null;

  async function load() {
    if (map) return map;
    try {
      map = await (await fetch("data/image-variants.json", DATA_FETCH)).json();
    } catch (e) {
      map = {};
    }
    return map;
  }

  function srcset(src) {
    const widths = map && map[src];
    if (!widths || widths.length < 2) return "";
    const dot = src.lastIndexOf(".");
    const stem = src.slice(0, dot);
    const ext = src.slice(dot);
    // La plus grande largeur, c'est le fichier d'origine sous son propre nom.
    const max = Math.max(...widths);
    return widths
      .map((w) => `${w === max ? src : stem + "-" + w + ext} ${w}w`)
      .join(", ");
  }

  // Prêt à coller dans une balise : vide si aucune variante n'est connue.
  function attrs(src, sizes) {
    const ss = srcset(src);
    return ss ? ` srcset="${escapeHTML(ss)}" sizes="${escapeHTML(sizes)}"` : "";
  }

  return { load, srcset, attrs };
})();
