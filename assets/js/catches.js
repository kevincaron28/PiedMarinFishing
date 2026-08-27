// Pied Marin Fishing — catch log / hall of fame
//
// Each catch names its angler (a member id) and optionally the event it came
// from, so the gallery links back into the roster and the palmarès instead of
// being a detached pile of photos.
// Helpers (dateParts, escapeHTML, months) come from util.js.

const PMF_CATCHES = (() => {
  let cache = null;
  function load() {
    if (!cache) {
      cache = fetch("data/catches.json", DATA_FETCH)
        .then((r) => r.json())
        .then((rows) => rows.slice().sort((a, b) => {
          // Highlights first, then most recent.
          if (!!b.highlight !== !!a.highlight) return b.highlight ? 1 : -1;
          return (b.date || "").localeCompare(a.date || "");
        }))
        .catch(() => []);
    }
    return cache;
  }
  function forAngler(rows, id) {
    return rows.filter((c) => c.angler === id);
  }
  return { load, forAngler };
})();

// Photo, YouTube clip, or the crest standing in until one exists.
function catchMediaHTML(c, t) {
  const media = c.media || {};
  if (media.type === "image" && media.src) {
    return `<img class="catch-media-img" src="${escapeHTML(media.src)}" alt="${escapeHTML(c._alt || "")}" loading="lazy">`;
  }
  if (media.type === "youtube" && media.videoId) {
    const id = encodeURIComponent(media.videoId);
    return `
      <button type="button" class="catch-facade" data-video="${escapeHTML(media.videoId)}"
              aria-label="${escapeHTML(t("catches.playVideo"))}">
        <img class="catch-media-img" alt="" loading="lazy"
             src="https://i.ytimg.com/vi/${id}/hqdefault.jpg">
        <span class="video-play" aria-hidden="true"></span>
      </button>`;
  }
  return `<div class="catch-empty-media"><span>${escapeHTML(t("catches.noMedia"))}</span></div>`;
}

async function initCatches(options) {
  const {
    gridSelector,
    emptySelector,
    countSelector,
    anglerFilterSelector,
    speciesFilterSelector,
    highlightFilterSelector,
  } = options;

  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  const { t, tr, trAll, plural, key: stableKey } = PMF_I18N;

  let catches = [];
  let members = [];
  let events = [];
  try {
    [catches, members, events] = await Promise.all([
      PMF_CATCHES.load(),
      fetch("data/team-members.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
      fetch("data/tournament-history.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
    ]);
  } catch (e) {
    grid.innerHTML = `<div class="empty-state">${escapeHTML(t("catches.loadError"))}</div>`;
    return;
  }

  const memberById = new Map(members.map((m) => [m.id, m]));
  const eventById = new Map(events.map((e) => [e.id, e]));

  const anglerSelect = anglerFilterSelector ? document.querySelector(anglerFilterSelector) : null;
  const speciesSelect = speciesFilterSelector ? document.querySelector(speciesFilterSelector) : null;
  const highlightToggle = highlightFilterSelector ? document.querySelector(highlightFilterSelector) : null;
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
      anglerSelect,
      members.map((m) => ({ value: m.id, label: tr(m.name) })),
      t("catches.allAnglers")
    );
    const seen = new Map();
    catches.forEach((c) => {
      const k = stableKey(c.species);
      if (k && !seen.has(k)) seen.set(k, tr(c.species));
    });
    buildOptions(
      speciesSelect,
      Array.from(seen, ([value, label]) => ({ value, label }))
        .sort((a, b) => a.label.localeCompare(b.label, PMF_I18N.lang)),
      t("catches.allSpecies")
    );
  }

  function matches(c) {
    if (anglerSelect && anglerSelect.value && c.angler !== anglerSelect.value) return false;
    if (speciesSelect && speciesSelect.value && stableKey(c.species) !== speciesSelect.value) return false;
    if (highlightToggle && highlightToggle.checked && !c.highlight) return false;
    return true;
  }

  function render() {
    const lang = PMF_I18N.lang;
    const m = months(lang);
    const rows = catches.filter(matches);

    if (countEl) countEl.textContent = plural("catches.count", rows.length);

    if (!rows.length) {
      grid.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
      return;
    }
    if (emptyEl) emptyEl.style.display = "none";

    grid.innerHTML = rows.map((c) => {
      const angler = memberById.get(c.angler);
      const anglerName = angler ? tr(angler.name) : c.angler || "";
      // Alt utile pour un lecteur d'écran : quoi, qui, et où.
      c._alt = [tr(c.species), anglerName, tr(c.water)].filter(Boolean).join(" — ");

      const p = dateParts(c.date);
      let when = "";
      if (p) {
        when = p.month !== null && p.day !== null
          ? `${p.day} ${m.full[p.month].toLowerCase()} ${p.year}`
          : p.month !== null ? `${m.full[p.month]} ${p.year}` : String(p.year);
      }

      const ev = c.event ? eventById.get(c.event) : null;
      const meta = [];
      if (anglerName) {
        meta.push(angler
          ? `<a class="angler-chip" href="history.html?member=${encodeURIComponent(angler.id)}">${escapeHTML(anglerName)}</a>`
          : `<span class="angler-chip">${escapeHTML(anglerName)}</span>`);
      }

      const facts = [];
      if (when) facts.push(`<span>📅 ${escapeHTML(when)}</span>`);
      if (tr(c.water)) facts.push(`<span>📍 ${escapeHTML(tr(c.water))}</span>`);
      if (ev) facts.push(`<span>🏆 ${escapeHTML(tr(ev.name))}</span>`);

      const notes = tr(c.notes);

      return `
        <article class="catch-card${c.highlight ? " catch-highlight" : ""}">
          <div class="catch-media">
            ${catchMediaHTML(c, t)}
            ${c.highlight ? `<span class="catch-ribbon">${escapeHTML(t("catches.featured"))}</span>` : ""}
          </div>
          <div class="catch-body">
            <div class="catch-head">
              <h3>${escapeHTML(tr(c.species) || "—")}</h3>
              ${tr(c.measure) ? `<span class="catch-measure">${escapeHTML(tr(c.measure))}</span>` : ""}
            </div>
            ${meta.length ? `<div class="catch-anglers">${meta.join("")}</div>` : ""}
            ${facts.length ? `<div class="catch-facts">${facts.join("")}</div>` : ""}
            ${notes ? `<p class="catch-notes">${escapeHTML(notes)}</p>` : ""}
          </div>
        </article>
      `;
    }).join("");

    // Nothing reaches YouTube until someone presses play.
    grid.querySelectorAll("[data-video]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = encodeURIComponent(btn.getAttribute("data-video"));
        const wrap = btn.closest(".catch-media");
        const iframe = document.createElement("iframe");
        iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
        iframe.title = t("catches.playVideo");
        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
        iframe.allowFullscreen = true;
        wrap.innerHTML = "";
        wrap.appendChild(iframe);
      });
    });
  }

  [anglerSelect, speciesSelect, highlightToggle].forEach((el) => {
    if (el) el.addEventListener("input", render);
  });

  // Sans aucune prise marquée, la case ne pourrait que vider la grille.
  if (highlightToggle && !catches.some((c) => c.highlight)) {
    const wrap = highlightToggle.closest("label") || highlightToggle;
    wrap.style.display = "none";
    highlightToggle.checked = false;
  }

  PMF_I18N.onChange(() => { refreshFilterOptions(); render(); });
  refreshFilterOptions();

  // Deep link from a team card: catches.html?angler=bobe
  const preselect = queryParam("angler");
  if (anglerSelect && preselect && memberById.has(preselect)) anglerSelect.value = preselect;

  render();
}
