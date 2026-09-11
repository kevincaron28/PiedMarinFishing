// Pied Marin Fishing — la recherche du site.
//
// Il y avait deux recherches qui ne se parlaient pas : une sur l'index des
// espèces, une sur le guide des tournois. Chacune ne voyait que sa propre
// liste, et les 104 pages générées n'étaient trouvables par aucune des deux.
// Celle-ci couvre les 111 pages, depuis n'importe laquelle.
//
// L'index (data/search-index.json, 17 Ko) n'est PAS chargé avec la page : il
// arrive au premier clic sur la loupe. Une page qui ne sert jamais à chercher
// ne paie rien.
//
// Le bouton et le panneau sont construits ici plutôt qu'écrits dans les 116
// pages : le menu, lui, est du contenu et vit dans le balisage; une boîte de
// recherche ne sert à rien sans JavaScript, alors autant qu'elle n'existe
// que quand il tourne.

function initSearch() {
  const nav = document.querySelector(".nav");
  const actions = document.querySelector(".nav-actions");
  const header = document.querySelector(".site-header");
  if (!nav || !actions || !header) return;
  // PMF_I18N est un const global, PAS une propriété de window.
  if (typeof PMF_I18N === "undefined") return;

  const { t, plural } = PMF_I18N;
  let rows = null;              // l'index, une fois chargé
  let failed = false;
  let active = -1;              // le résultat surligné au clavier

  // --- le balisage ------------------------------------------------------
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "nav-search";
  btn.setAttribute("aria-expanded", "false");
  btn.setAttribute("aria-controls", "site-search");
  btn.innerHTML = '<span aria-hidden="true">⌕</span>';

  const panel = document.createElement("div");
  panel.className = "search-panel";
  panel.id = "site-search";
  panel.hidden = true;
  panel.innerHTML =
    '<div class="container">' +
    '<label class="search-label" for="search-input"></label>' +
    '<input id="search-input" class="search-input" type="search" autocomplete="off" ' +
    'spellcheck="false" aria-describedby="search-status">' +
    '<p class="search-status" id="search-status" role="status" aria-live="polite"></p>' +
    '<ul class="search-results"></ul>' +
    "</div>";

  actions.insertBefore(btn, actions.firstChild);
  header.appendChild(panel);

  const input = panel.querySelector(".search-input");
  const status = panel.querySelector(".search-status");
  const list = panel.querySelector(".search-results");
  const label = panel.querySelector(".search-label");

  function applyLabels() {
    btn.setAttribute("aria-label", t("search.open"));
    btn.title = t("search.open");
    label.textContent = t("search.title");
    input.placeholder = t("search.placeholder");
  }
  applyLabels();

  // --- la comparaison ---------------------------------------------------
  // Sans accent ni casse : « éperlan » doit se trouver en tapant « eperlan »,
  // et « DORÉ » en tapant « dore ».
  const fold = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  function score(row, q) {
    const hay = [row.f, row.e, row.k];
    let best = 0;
    for (const raw of hay) {
      if (!raw) continue;
      const s = fold(raw);
      const at = s.indexOf(q);
      if (at < 0) continue;
      // Un nom qui COMMENCE par ce qu'on tape passe avant un nom qui le
      // contient au milieu : « doré jaune » avant « festival du doré ».
      const weight = at === 0 ? 3 : /\s|^/.test(s[at - 1] || "") ? 2 : 1;
      if (weight > best) best = weight;
    }
    return best;
  }

  const GROUPS = ["site", "especes", "tournois", "prises", "equipe"];
  const GROUP_KEY = {
    site: "nav.home", especes: "nav.species", tournois: "nav.guide",
    prises: "nav.catches", equipe: "nav.team",
  };

  function render() {
    const q = fold(input.value.trim());
    list.innerHTML = "";
    active = -1;

    if (failed) { status.textContent = t("search.failed"); return; }
    if (q.length < 2) { status.textContent = t("search.hint"); return; }
    if (!rows) { status.textContent = ""; return; }

    const hits = rows
      .map((r) => ({ r, s: score(r, q) }))
      .filter((x) => x.s > 0)
      .sort((a, b) =>
        b.s - a.s ||
        GROUPS.indexOf(a.r.g) - GROUPS.indexOf(b.r.g) ||
        (a.r.f || "").localeCompare(b.r.f || "", "fr"))
      .slice(0, 12);

    if (!hits.length) { status.textContent = t("search.empty"); return; }
    status.textContent = plural("search.count", hits.length);

    list.innerHTML = hits.map(({ r }) => {
      const name = PMF_I18N.lang === "en" && r.e ? r.e : r.f;
      return '<li><a href="' + escapeHTML(r.u) + '">' +
        '<span class="search-hit-name">' + escapeHTML(name) + "</span>" +
        '<span class="search-hit-group">' + escapeHTML(t(GROUP_KEY[r.g] || "")) + "</span>" +
        "</a></li>";
    }).join("");
  }

  async function load() {
    if (rows || failed) return;
    try {
      rows = await (await fetch("data/search-index.json", DATA_FETCH)).json();
    } catch (e) {
      failed = true;                       // le panneau le dit, il ne ment pas
    }
    render();
  }

  // --- ouvrir et fermer -------------------------------------------------
  function setOpen(open, { focusBtn = false } = {}) {
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
    document.documentElement.classList.toggle("search-open", open);
    if (open) {
      // Les deux panneaux se disputeraient l'écran : le menu cède la place.
      const links = document.querySelector(".nav-links");
      if (links && links.classList.contains("open")) {
        links.classList.remove("open");
        const toggle = document.querySelector(".nav-toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
        document.documentElement.classList.remove("nav-open");
      }
      load();
      render();
      input.focus();
      input.select();
    } else if (focusBtn) {
      btn.focus();
    }
  }

  btn.addEventListener("click", () => setOpen(panel.hidden));
  input.addEventListener("input", render);

  document.addEventListener("click", (ev) => {
    if (!panel.hidden && !panel.contains(ev.target) && ev.target !== btn
        && !btn.contains(ev.target)) {
      setOpen(false);
    }
  });

  document.addEventListener("keydown", (ev) => {
    // Ouvrir avec « / », comme partout ailleurs — mais pas quand on est déjà
    // en train d'écrire dans un champ.
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (ev.key === "/" && panel.hidden && !typing) {
      ev.preventDefault();
      setOpen(true);
      return;
    }
    if (panel.hidden) return;

    if (ev.key === "Escape") {
      setOpen(false, { focusBtn: true });
      return;
    }

    const items = [...list.querySelectorAll("a")];
    if (!items.length) return;

    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      active = ev.key === "ArrowDown"
        ? (active + 1) % items.length
        : (active <= 0 ? items.length - 1 : active - 1);
      items.forEach((a, i) => a.classList.toggle("is-active", i === active));
      items[active].scrollIntoView({ block: "nearest" });
    } else if (ev.key === "Enter" && active >= 0) {
      ev.preventDefault();
      items[active].click();
    }
  });

  PMF_I18N.onChange(() => { applyLabels(); render(); });
}

document.addEventListener("DOMContentLoaded", initSearch);
