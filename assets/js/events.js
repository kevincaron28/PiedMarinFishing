// Pied Marin Fishing — data-driven event list renderer (bilingual)
// Used by calendar.html (team schedule) and tournaments.html (regional directory)
// Shared helpers (MONTHS, parseISODate, escapeHTML) come from util.js.

async function initEventList(options) {
  const {
    dataUrl,
    listSelector,
    emptySelector,
    countSelector,
    monthFilterSelector,
    regionFilterSelector,
    whenFilterSelector,
    kindFilterSelector,
    yearFilterSelector,
    searchSelector,
    badgeField = "type",
    linkTextKey = "events.learnMore",
    onRender = null,
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
  const whenSelect = whenFilterSelector ? document.querySelector(whenFilterSelector) : null;
  const kindSelect = kindFilterSelector ? document.querySelector(kindFilterSelector) : null;
  const yearSelect = yearFilterSelector ? document.querySelector(yearFilterSelector) : null;

  // A circuit is a series; its stops point back at it by id.
  const circuitById = new Map(events.filter((e) => e.kind === "circuit").map((e) => [e.id, e]));
  const stopsOf = new Map();
  events.forEach((e) => {
    if (e.kind !== "stop" || !e.circuit) return;
    if (!stopsOf.has(e.circuit)) stopsOf.set(e.circuit, []);
    stopsOf.get(e.circuit).push(e);
  });
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
    const m = months(PMF_I18N.lang);
    buildOptions(
      monthSelect,
      m.full.map((label, i) => ({ value: String(i), label })),
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

    if (whenSelect) {
      const previous = whenSelect.value || "upcoming";
      whenSelect.innerHTML = "";
      [["upcoming", "filters.when.upcoming"], ["past", "filters.when.past"], ["all", "filters.when.all"]]
        .forEach(([value, key]) => {
          const opt = document.createElement("option");
          opt.value = value;
          opt.textContent = t(key);
          whenSelect.appendChild(opt);
        });
      whenSelect.value = previous;
    }

    if (yearSelect) {
      const years = Array.from(new Set(
        events.map((ev) => (dateParts(ev.startDate) || {}).year).filter(Boolean)
      )).sort((a, b) => b - a);
      buildOptions(
        yearSelect,
        years.map((y) => ({ value: String(y), label: String(y) })),
        t("filters.allYears")
      );
    }

    if (kindSelect) {
      const previous = kindSelect.value || "";
      kindSelect.innerHTML = "";
      [["", "filters.kind.all"], ["single", "filters.kind.single"],
       ["circuit", "filters.kind.circuit"]]
        .forEach(([value, key]) => {
          const opt = document.createElement("option");
          opt.value = value;
          opt.textContent = t(key);
          kindSelect.appendChild(opt);
        });
      kindSelect.value = previous;
    }
  }

  function matchesKind(ev) {
    if (!kindSelect || !kindSelect.value) return true;
    const v = kindSelect.value;
    if (v === "pro") return ev.tier === "pro";
    if (v === "circuit") return ev.tier !== "pro" && (ev.kind === "circuit" || ev.kind === "stop");
    if (v === "single") return ev.tier !== "pro" && ev.kind === "single";
    return true;
  }

  function matchesFilters(ev) {
    if (!matchesKind(ev)) return false;
    // A circuit carries no date of its own — it is judged by its stops.
    if (ev.kind === "circuit") {
      const stops = stopsOf.get(ev.id) || [];
      if (stops.length) return stops.some((st) => matchesDateAndPlace(st));
      return matchesDateAndPlace(ev);
    }
    return matchesDateAndPlace(ev);
  }

  function matchesDateAndPlace(ev) {
    if (whenSelect && whenSelect.value !== "all") {
      const past = isPastEvent(ev);
      // A cancelled event is never something you can still go and fish.
      if (whenSelect.value === "upcoming" && (past || ev.status === "cancelled")) return false;
      if (whenSelect.value === "past" && !past) return false;
    }
    if (yearSelect && yearSelect.value !== "") {
      const p = dateParts(ev.startDate);
      // Recurring / date-TBC entries aren't tied to a season, so they stay.
      if (p && String(p.year) !== yearSelect.value) return false;
    }
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
      const specValues = Object.values(ev.specs || {});
      const hay = [ev.name, ev.location, ev.organizer, ev.species, ev.notes, ev.region, ...specValues]
        .map(trAll)
        .join(" ")
        .toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }

  // Building a card is separate from listing them, so other views (the
  // calendar) can render the same card for a selected day.
  function renderCard(ev) {
    const dateBadge = dateBadgeHTML(ev.startDate, PMF_I18N.lang, t("events.tbd"));
    const past = isPastEvent(ev);
    const cancelled = ev.status === "cancelled";

    const badgeText = tr(ev[badgeField]);
    const badge = badgeText
      ? `<span class="badge${ev.status === "tentative" ? " gold" : ""}">${escapeHTML(badgeText)}</span>`
      : "";
    const stateBadge = cancelled
      ? `<span class="badge red">${escapeHTML(t("events.cancelled"))}</span>`
      : past ? `<span class="badge navy">${escapeHTML(t("events.past"))}</span>` : "";
    // A stop names its parent series, so it never reads as a standalone event.
    const parent = ev.kind === "stop" && ev.circuit ? circuitById.get(ev.circuit) : null;
    const parentTag = parent
      ? `<span class="event-parent">${escapeHTML(tr(parent.name))}</span>`
      : "";

    const metaBits = [];
    if (ev.location) metaBits.push(`<span>📍 ${escapeHTML(tr(ev.location))}</span>`);
    if (ev.region) metaBits.push(`<span>${escapeHTML(tr(ev.region))}</span>`);
    if (ev.species) metaBits.push(`<span>🎣 ${escapeHTML(tr(ev.species))}</span>`);
    if (ev.organizer) metaBits.push(`<span>${escapeHTML(tr(ev.organizer))}</span>`);

    // Entry fee and team format always show — an unpublished one says so
    // rather than leaving the reader guessing. The rest appear when known.
    const specs = ev.specs || {};
    const specRows = [
      { field: "fee", key: "spec.fee", icon: "💵", always: true },
      { field: "teamSize", key: "spec.teamSize", icon: "👥", always: true },
      { field: "maxTeams", key: "spec.maxTeams", icon: "🚩" },
      { field: "hours", key: "spec.hours", icon: "⏱" },
      { field: "deadline", key: "spec.deadline", icon: "📋" },
      { field: "format", key: "spec.format", icon: "🎯" },
    ].reduce((out, { field, key, icon, always }) => {
      const value = tr(specs[field]);
      if (!value && !always) return out;
      const shown = value || t("spec.notPublished");
      out.push(`
        <div class="event-spec${value ? "" : " spec-empty"}">
          <span class="event-spec-label"><span aria-hidden="true">${icon}</span> ${escapeHTML(t(key))}</span>
          <span class="event-spec-value">${escapeHTML(shown)}</span>
        </div>
      `);
      return out;
    }, []).join("");

    const notes = tr(ev.notes);

    return `
      <article class="event-card${past || cancelled ? " event-inactive" : ""}${ev.tier === "pro" ? " event-pro" : ""}" id="ev-${escapeHTML(ev.id || "")}">
        <div class="event-date">${dateBadge}</div>
        <div>
          ${parentTag}
          <div class="event-title">${escapeHTML(tr(ev.name))} ${badge}${stateBadge}</div>
          <div class="event-meta">${metaBits.join("")}</div>
          ${specRows ? `<div class="event-specs">${specRows}</div>` : ""}
          ${notes ? `<p class="event-notes">${escapeHTML(notes)}</p>` : ""}
        </div>
        <div class="event-cta">
          ${ev.link ? `<a class="btn btn-teal" href="${escapeHTML(ev.link)}" target="_blank" rel="noopener">${escapeHTML(t(linkTextKey))}</a>` : ""}
        </div>
      </article>
    `;
  }

  // Stops nest inside their circuit so a series reads as one thing rather
  // than as N unrelated rows.
  function groupByCircuit(filtered) {
    const shownIds = new Set(filtered.map((e) => e.id));
    const out = [];
    const consumed = new Set();

    filtered.forEach((ev) => {
      if (consumed.has(ev.id)) return;

      if (ev.kind === "circuit") {
        consumed.add(ev.id);
        const stops = (stopsOf.get(ev.id) || [])
          .filter((st) => shownIds.has(st.id))
          .sort((a, b) => (a.startDate || "9999").localeCompare(b.startDate || "9999"));
        stops.forEach((st) => consumed.add(st.id));
        out.push(`
          <section class="circuit-block${ev.tier === "pro" ? " circuit-pro" : ""}">
            ${renderCard(ev)}
            ${stops.length ? `
              <div class="circuit-stops">
                <div class="circuit-stops-head">${escapeHTML(plural("events.stopCount", stops.length))}</div>
                <div class="event-list">${stops.map(renderCard).join("")}</div>
              </div>` : ""}
          </section>
        `);
        return;
      }

      // A stop whose circuit was filtered out still stands on its own.
      if (ev.kind === "stop" && ev.circuit && shownIds.has(ev.circuit)) return;
      consumed.add(ev.id);
      out.push(renderCard(ev));
    });

    return out.join("");
  }

  function render() {
    const filtered = events.filter(matchesFilters);
    const emptyEl = emptySelector ? document.querySelector(emptySelector) : null;
    const countEl = countSelector ? document.querySelector(countSelector) : null;

    if (countEl) countEl.textContent = plural("filters.count", filtered.length);

    if (filtered.length === 0) {
      listEl.innerHTML = "";
      if (emptyEl) emptyEl.style.display = "block";
    } else {
      if (emptyEl) emptyEl.style.display = "none";
      listEl.innerHTML = groupByCircuit(filtered);
    }

    if (onRender) onRender({ filtered, renderCard });
  }

  [monthSelect, regionSelect, whenSelect, kindSelect, yearSelect, searchInput].forEach((el) => {
    if (el) el.addEventListener("input", render);
  });

  PMF_I18N.onChange(() => {
    refreshFilterOptions();
    render();
  });

  refreshFilterOptions();
  render();
}
