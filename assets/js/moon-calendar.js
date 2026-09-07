// Pied Marin Fishing — le mois lunaire, rendu
//
// Un mois à la fois, avec les flèches pour se déplacer. La phase vient de
// PMF_MOON, donc rien à tenir à jour : la page sera juste en 2031 comme
// aujourd'hui, sans que personne y touche.

async function initMoonCalendar(rootSelector) {
  const root = document.querySelector(rootSelector);
  if (!root || typeof PMF_MOON === "undefined") return;

  await PMF_I18N.ready;
  const { t } = PMF_I18N;

  const today = new Date();
  today.setHours(12, 0, 0, 0);
  let shown = new Date(today.getFullYear(), today.getMonth(), 1, 12);

  function iso(d) {
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0")
      + "-" + String(d.getDate()).padStart(2, "0");
  }

  function monthName(d) {
    return d.toLocaleDateString(PMF_I18N.lang === "en" ? "en-CA" : "fr-CA",
      { month: "long", year: "numeric" });
  }

  function render() {
    const first = new Date(shown.getFullYear(), shown.getMonth(), 1, 12);
    const days = new Date(shown.getFullYear(), shown.getMonth() + 1, 0).getDate();
    // Semaine qui commence le dimanche, comme les calendriers d'ici.
    const pad = first.getDay();
    const cells = [];
    for (let i = 0; i < pad; i++) cells.push('<div class="moon-cell moon-empty"></div>');
    for (let day = 1; day <= days; day++) {
      const d = new Date(shown.getFullYear(), shown.getMonth(), day, 12);
      const ph = PMF_MOON.phase(d);
      const isToday = iso(d) === iso(today);
      const cls = "moon-cell" + (isToday ? " moon-today" : "")
        + (ph.principal ? " moon-key" : "");
      const label = t("moon." + ph.key);
      cells.push(`<div class="${cls}">
  <span class="moon-day">${day}</span>
  <span class="moon-glyph" role="img" aria-label="${escapeHTML(label)}">${PMF_MOON.glyph(ph.key)}</span>
  ${ph.principal ? `<span class="moon-name">${escapeHTML(label)}</span>` : ""}
  <span class="moon-illum">${Math.round(ph.illumination * 100)}%</span>
</div>`);
    }
    const dows = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(2026, 1, 1 + i, 12);   // 1er fevrier 2026 = dimanche
      dows.push('<div class="moon-dow">'
        + escapeHTML(d.toLocaleDateString(PMF_I18N.lang === "en" ? "en-CA" : "fr-CA",
          { weekday: "narrow" })) + "</div>");
    }
    root.innerHTML = `
<div class="moon-head">
  <button type="button" class="moon-nav" data-moon-prev aria-label="${escapeHTML(t("moon.prev"))}">←</button>
  <span class="moon-month">${escapeHTML(monthName(shown))}</span>
  <button type="button" class="moon-nav" data-moon-next aria-label="${escapeHTML(t("moon.next"))}">→</button>
</div>
<div class="moon-grid">${dows.join("")}${cells.join("")}</div>`;
    root.querySelector("[data-moon-prev]").addEventListener("click", () => {
      shown = new Date(shown.getFullYear(), shown.getMonth() - 1, 1, 12); render();
    });
    root.querySelector("[data-moon-next]").addEventListener("click", () => {
      shown = new Date(shown.getFullYear(), shown.getMonth() + 1, 1, 12); render();
    });
  }

  PMF_I18N.onChange(render);
  render();
}
