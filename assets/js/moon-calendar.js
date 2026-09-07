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

  const TZ = "America/Toronto";
  const hhmm = (d) => d ? d.toLocaleTimeString(PMF_I18N.lang === "en" ? "en-CA" : "fr-CA",
    { timeZone: TZ, hour: "2-digit", minute: "2-digit" }) : "—";

  const today = new Date();
  today.setHours(12, 0, 0, 0);
  let shown = new Date(today.getFullYear(), today.getMonth(), 1, 12);
  let picked = new Date(today);

  // LE LIEU. Quatre points publics du corridor, plus la position du visiteur
  // s'il l'accorde. Sa position n'est ni envoyée ni enregistrée ailleurs que
  // dans son propre navigateur — le site n'a aucun serveur, et de toute façon
  // ce n'est pas notre affaire de savoir d'où quelqu'un pêche.
  const PLACE_KEY = "pmf-sky-place";
  let custom = null;
  function restorePlace() {
    if (typeof PMF_SKY === "undefined") return;
    try {
      const raw = localStorage.getItem(PLACE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (saved && saved.mine && typeof saved.lat === "number") {
        custom = { lat: saved.lat, lon: saved.lon, name: t("sky.mine") };
        PMF_SKY.setPlace(custom);
        return;
      }
      const p = PMF_SKY.places.find((x) => x.id === saved.id);
      if (p) PMF_SKY.setPlace(p);
    } catch (e) { /* navigation privée, ou stockage bloqué */ }
  }
  function rememberPlace(value) {
    try { localStorage.setItem(PLACE_KEY, JSON.stringify(value)); } catch (e) { /* ignore */ }
  }

  function placeHtml() {
    if (typeof PMF_SKY === "undefined") return "";
    const now = PMF_SKY.place();
    const opts = PMF_SKY.places.map((p) =>
      `<option value="${escapeHTML(p.id)}"${p.name === now.name ? " selected" : ""}>${
        escapeHTML(p.name)}</option>`).join("");
    const mine = custom
      ? `<option value="__mine" selected>${escapeHTML(t("sky.mine"))}</option>` : "";
    return `<div class="sky-place">
  <label class="sky-place-label" for="sky-place">${escapeHTML(t("sky.placeLabel"))}</label>
  <select id="sky-place" data-sky-place>${opts}${mine}</select>
  <button type="button" class="btn btn-ghost sky-locate" data-sky-locate>${
    escapeHTML(t("sky.locate"))}</button>
</div>`;
  }

  function bindPlace() {
    const sel = root.querySelector("[data-sky-place]");
    if (sel) sel.addEventListener("change", () => {
      const p = PMF_SKY.places.find((x) => x.id === sel.value);
      if (p) { custom = null; PMF_SKY.setPlace(p); rememberPlace({ id: p.id }); render(); }
    });
    const btn = root.querySelector("[data-sky-locate]");
    if (btn) btn.addEventListener("click", () => {
      if (!navigator.geolocation) { btn.textContent = t("sky.locateNo"); return; }
      btn.disabled = true;
      btn.textContent = t("sky.locating");
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          custom = { lat: pos.coords.latitude, lon: pos.coords.longitude, name: t("sky.mine") };
          PMF_SKY.setPlace(custom);
          rememberPlace({ mine: true, lat: custom.lat, lon: custom.lon });
          render();
        },
        () => { btn.disabled = false; btn.textContent = t("sky.locateNo"); },
        { timeout: 8000, maximumAge: 600000 });
    });
  }

  function iso(d) {
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0")
      + "-" + String(d.getDate()).padStart(2, "0");
  }

  function monthName(d) {
    return d.toLocaleDateString(PMF_I18N.lang === "en" ? "en-CA" : "fr-CA",
      { month: "long", year: "numeric" });
  }

  // Les periodes solunaires du jour choisi. Ce n'est pas de l'astronomie mais
  // une theorie de peche : les instants sont exacts, ce que le poisson en fait
  // ne l'est pas. La note sous le calendrier le dit en toutes lettres.
  function detailHtml(day) {
    if (typeof PMF_SKY === "undefined") return "";
    const start = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 0, 0, 0);
    const r = PMF_SKY.solunar(start);
    const row = (icon, label, value) => value
      ? `<div class="event-spec"><span class="event-spec-label"><span aria-hidden="true">${icon}</span> ${
          escapeHTML(label)}</span><span class="event-spec-value">${escapeHTML(value)}</span></div>` : "";
    // « 18 h 26 → 06 h 39 » se lisait comme une plage, alors que ce jour-là
    // la lune se couche AVANT de se lever. Deux valeurs nommées, pas une
    // flèche.
    const pair = (a, b) => t("sky.rise") + " " + hhmm(a) + " · " + t("sky.set") + " " + hhmm(b);
    const specs = [
      row("🌅", t("sky.sun"), pair(r.sun.rise, r.sun.set)),
      row("🌙", t("sky.moon"), pair(r.moon.rise, r.moon.set)),
    ].join("");
    const periods = r.periods.map((p) => `<li class="sol-${p.kind}">
  <span class="sol-kind">${escapeHTML(t(p.kind === "major" ? "sky.major" : "sky.minor"))}</span>
  <span class="sol-time">${escapeHTML(hhmm(p.from) + " → " + hhmm(p.to))}</span>
</li>`).join("");
    return `<h3 class="moon-detail-title">${escapeHTML(
      day.toLocaleDateString(PMF_I18N.lang === "en" ? "en-CA" : "fr-CA",
        { weekday: "long", day: "numeric", month: "long" }))}</h3>
<div class="event-specs tp-specs">${specs}</div>
<p class="sol-head">${escapeHTML(t("sky.periods"))}</p>
<ul class="sol-list">${periods}</ul>
<p class="sol-place">${escapeHTML(
      t("sky.placeNote", { place: PMF_SKY.place().name }))}</p>`;
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
        + (ph.principal ? " moon-key" : "")
        + (iso(d) === iso(picked) ? " moon-picked" : "");
      const label = t("moon." + ph.key);
      cells.push(`<button type="button" class="${cls}" data-day="${day}"
    aria-pressed="${iso(d) === iso(picked)}">
  <span class="moon-day">${day}</span>
  <span class="moon-glyph" role="img" aria-label="${escapeHTML(label)}">${PMF_MOON.glyph(ph.key)}</span>
  ${ph.principal ? `<span class="moon-name">${escapeHTML(label)}</span>` : ""}
  <span class="moon-illum">${Math.round(ph.illumination * 100)}%</span>
</button>`);
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
<div class="moon-grid">${dows.join("")}${cells.join("")}</div>
<div class="moon-detail">${detailHtml(picked)}</div>
${placeHtml()}`;
    bindPlace();
    root.querySelectorAll("[data-day]").forEach((btn) => {
      btn.addEventListener("click", () => {
        picked = new Date(shown.getFullYear(), shown.getMonth(),
                          Number(btn.getAttribute("data-day")), 12);
        render();
      });
    });
    root.querySelector("[data-moon-prev]").addEventListener("click", () => {
      shown = new Date(shown.getFullYear(), shown.getMonth() - 1, 1, 12); render();
    });
    root.querySelector("[data-moon-next]").addEventListener("click", () => {
      shown = new Date(shown.getFullYear(), shown.getMonth() + 1, 1, 12); render();
    });
  }

  restorePlace();
  PMF_I18N.onChange(render);
  render();
}
