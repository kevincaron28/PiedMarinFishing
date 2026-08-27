// Pied Marin Fishing — season-at-a-glance calendar for the tournament guide
//
// A twelve-month overview rather than a one-month-at-a-time calendar: the
// season clusters into May–October, so paging through empty winter months
// would hide the shape of it. Seeing the whole year at once is also what
// surfaces weekend collisions between circuits.

const WEEKDAY_INITIALS = {
  fr: ["D", "L", "M", "M", "J", "V", "S"],
  en: ["S", "M", "T", "W", "T", "F", "S"],
};

function initCalendarView(options) {
  const { calendarSelector, detailSelector } = options;
  const calEl = document.querySelector(calendarSelector);
  const detailEl = detailSelector ? document.querySelector(detailSelector) : null;
  if (!calEl) return null;

  let selectedKey = null;

  function isoKey(y, m, d) {
    return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  }

  // Every day an event covers, so a multi-day event marks its whole run.
  function eachDay(ev) {
    const s = dateParts(ev.startDate);
    if (!s || s.month === null || s.day === null) return [];
    const end = dateParts(ev.endDate || ev.startDate);
    const start = new Date(s.year, s.month, s.day);
    const last = end && end.month !== null && end.day !== null
      ? new Date(end.year, end.month, end.day)
      : start;
    const out = [];
    for (let d = new Date(start); d <= last; d.setDate(d.getDate() + 1)) {
      out.push(isoKey(d.getFullYear(), d.getMonth(), d.getDate()));
    }
    return out;
  }

  function render({ filtered, renderCard }) {
    const { t, tr, plural } = PMF_I18N;
    const lang = PMF_I18N.lang;
    const m = months(lang);
    const initials = WEEKDAY_INITIALS[lang] || WEEKDAY_INITIALS.fr;

    const byDay = new Map();      // exact day  -> events
    const byMonth = new Map();    // month-only -> events
    const undated = [];
    const years = new Set();

    // A circuit whose stops are already on the grid doesn't belong in the
    // undated strip — only genuinely date-less entries do.
    const datedCircuits = new Set(
      filtered.filter((e) => e.kind === "stop" && e.circuit && dateParts(e.startDate)).map((e) => e.circuit)
    );

    filtered.forEach((ev) => {
      const p = dateParts(ev.startDate);
      if (!p) {
        if (!(ev.kind === "circuit" && datedCircuits.has(ev.id))) undated.push(ev);
        return;
      }
      years.add(p.year);
      if (p.month === null) return;
      if (p.day === null) {
        const key = `${p.year}-${String(p.month + 1).padStart(2, "0")}`;
        if (!byMonth.has(key)) byMonth.set(key, []);
        byMonth.get(key).push(ev);
        return;
      }
      eachDay(ev).forEach((key) => {
        if (!byDay.has(key)) byDay.set(key, []);
        byDay.get(key).push(ev);
      });
    });

    if (!years.size && !undated.length) {
      calEl.innerHTML = `<div class="empty-state">${escapeHTML(t("filters.empty"))}</div>`;
      if (detailEl) detailEl.innerHTML = "";
      return;
    }

    const today = new Date();
    const todayKey = isoKey(today.getFullYear(), today.getMonth(), today.getDate());

    const yearBlocks = Array.from(years).sort().map((year) => {
      const monthGrids = m.full.map((label, monthIdx) => {
        const monthKey = `${year}-${String(monthIdx + 1).padStart(2, "0")}`;
        const monthOnly = byMonth.get(monthKey) || [];

        const firstWeekday = new Date(year, monthIdx, 1).getDay();
        const daysInMonth = new Date(year, monthIdx + 1, 0).getDate();

        const cells = [];
        for (let i = 0; i < firstWeekday; i++) cells.push(`<span class="cal-day cal-blank"></span>`);
        let monthHasEvent = monthOnly.length > 0;

        for (let day = 1; day <= daysInMonth; day++) {
          const key = isoKey(year, monthIdx, day);
          const evs = byDay.get(key) || [];
          const classes = ["cal-day"];
          const anyPro = evs.some((e) => e.tier === "pro");
          const anyRegional = evs.some((e) => e.tier !== "pro");
          if (evs.length) { classes.push("cal-has-event"); monthHasEvent = true; }
          // Pro stops read purple; a day holding both is split.
          if (anyPro) classes.push("cal-pro");
          if (anyPro && anyRegional) classes.push("cal-mixed");
          else if (evs.length > 1) classes.push("cal-multi");
          if (key === todayKey) classes.push("cal-today");
          if (key === selectedKey) classes.push("cal-selected");

          if (evs.length) {
            const title = evs.map((e) => tr(e.name)).join(" · ");
            cells.push(
              `<button type="button" class="${classes.join(" ")}" data-day="${key}" title="${escapeHTML(title)}">${day}</button>`
            );
          } else {
            cells.push(`<span class="${classes.join(" ")}">${day}</span>`);
          }
        }

        const monthNote = monthOnly.length
          ? `<div class="cal-month-note" title="${escapeHTML(monthOnly.map((e) => tr(e.name)).join(" · "))}">${escapeHTML(plural("calendarView.monthOnly", monthOnly.length))}</div>`
          : "";

        return `
          <div class="cal-month${monthHasEvent ? "" : " cal-month-empty"}">
            <div class="cal-month-name">${escapeHTML(label)}</div>
            <div class="cal-weekdays">${initials.map((w) => `<span>${escapeHTML(w)}</span>`).join("")}</div>
            <div class="cal-grid">${cells.join("")}</div>
            ${monthNote}
          </div>
        `;
      }).join("");

      return `
        <div class="cal-year">
          ${years.size > 1 ? `<h3 class="cal-year-label">${year}</h3>` : ""}
          <div class="cal-months">${monthGrids}</div>
        </div>
      `;
    }).join("");

    const undatedBlock = undated.length
      ? `<div class="cal-undated">
           <h4>${escapeHTML(t("calendarView.undatedTitle"))}</h4>
           <p>${escapeHTML(t("calendarView.undatedBody"))}</p>
           <div class="cal-undated-chips">
             ${undated.map((ev) => `<button type="button" class="angler-chip" data-event="${escapeHTML(ev.id || "")}">${escapeHTML(tr(ev.name))}</button>`).join("")}
           </div>
         </div>`
      : "";

    calEl.innerHTML = `
      <div class="cal-legend">
        <span><i class="cal-swatch cal-swatch-event"></i>${escapeHTML(t("calendarView.legendEvent"))}</span>
        <span><i class="cal-swatch cal-swatch-multi"></i>${escapeHTML(t("calendarView.legendMulti"))}</span>
        <span><i class="cal-swatch cal-swatch-today"></i>${escapeHTML(t("calendarView.legendToday"))}</span>
      </div>
      ${yearBlocks}
      ${undatedBlock}
    `;

    function showEvents(list, heading) {
      if (!detailEl) return;
      if (!list.length) { detailEl.innerHTML = ""; return; }
      detailEl.innerHTML = `
        <div class="cal-detail-head">${escapeHTML(heading)}</div>
        <div class="event-list">${list.map(renderCard).join("")}</div>
      `;
      detailEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    calEl.querySelectorAll("[data-day]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.getAttribute("data-day");
        selectedKey = key === selectedKey ? null : key;
        calEl.querySelectorAll(".cal-selected").forEach((el) => el.classList.remove("cal-selected"));
        if (!selectedKey) { if (detailEl) detailEl.innerHTML = ""; return; }
        btn.classList.add("cal-selected");
        const p = dateParts(key);
        const heading = `${p.day} ${m.full[p.month].toLowerCase()} ${p.year}`;
        showEvents(byDay.get(key) || [], heading);
      });
    });

    calEl.querySelectorAll("[data-event]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-event");
        const ev = undated.find((e) => e.id === id);
        if (ev) showEvents([ev], tr(ev.name));
      });
    });

    // A selection can disappear when filters change.
    if (selectedKey && !byDay.has(selectedKey)) {
      selectedKey = null;
      if (detailEl) detailEl.innerHTML = "";
    }
  }

  return { render };
}

// List / calendar toggle. The two are views of the same filtered set, so the
// filters above them keep working unchanged.
function initViewToggle({ toggleSelector, listSelector, calendarSelector, onChange }) {
  const toggle = document.querySelector(toggleSelector);
  if (!toggle) return;
  const listWrap = document.querySelector(listSelector);
  const calWrap = document.querySelector(calendarSelector);

  function apply(view) {
    toggle.querySelectorAll("[data-view]").forEach((btn) => {
      const active = btn.getAttribute("data-view") === view;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", String(active));
    });
    if (listWrap) listWrap.hidden = view !== "list";
    if (calWrap) calWrap.hidden = view !== "calendar";
    try { localStorage.setItem("pmf-guide-view", view); } catch (e) { /* ignore */ }
    if (onChange) onChange(view);
  }

  toggle.querySelectorAll("[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => apply(btn.getAttribute("data-view")));
  });

  let initial = "list";
  try {
    const stored = localStorage.getItem("pmf-guide-view");
    if (stored === "list" || stored === "calendar") initial = stored;
  } catch (e) { /* ignore */ }
  apply(initial);
}
