// Pied Marin Fishing — catch log / hall of fame
//
// Each catch names its angler (a member id) and optionally the event it came
// from, so the gallery links back into the roster and the palmarès instead of
// being a detached pile of photos.
//
// A catch carries one cover photo in "media" and, optionally, more photos of
// the same fish in "gallery". Clicking any photo opens the lightbox, which
// walks every photo of every catch currently on screen — nothing moves on its
// own, the visitor drives.
//
// Helpers (longDate, escapeHTML, queryParam) come from util.js.

const PMF_CATCHES = (() => {
  let cache = null;
  function load() {
    if (!cache) {
      cache = fetch("data/catches.json", DATA_FETCH)
        .then((r) => r.json())
        .then((rows) => rows.slice().sort((a, b) => {
          // La prise vedette d'abord, ensuite la plus récente.
          if (!!b.featured !== !!a.featured) return b.featured ? 1 : -1;
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

// Toutes les photos d'une prise : la couverture, puis les photos additionnelles.
// Une prise vidéo n'en a aucune — elle garde son lecteur sur la carte.
function catchPhotos(c) {
  const media = c.media || {};
  const photos = [];
  if (media.type === "image" && media.src) photos.push({ src: media.src, alt: media.alt || null });
  (c.gallery || []).forEach((g) => {
    const src = typeof g === "string" ? g : g && g.src;
    if (src) photos.push({ src, alt: (g && g.alt) || null });
  });
  return photos;
}

const PMF_LIGHTBOX = (() => {
  let root = null;
  let slides = [];
  let index = 0;
  let opener = null;
  let els = {};

  function build(t) {
    root = document.createElement("div");
    root.className = "lightbox";
    root.hidden = true;
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-label", t("catches.gallery"));
    root.innerHTML = `
      <div class="lightbox-backdrop" data-close></div>
      <button type="button" class="lightbox-btn lightbox-close" data-close></button>
      <button type="button" class="lightbox-btn lightbox-prev" data-prev></button>
      <button type="button" class="lightbox-btn lightbox-next" data-next></button>
      <figure class="lightbox-figure">
        <img class="lightbox-img" alt="">
        <figcaption class="lightbox-caption">
          <span class="lightbox-title"></span>
          <span class="lightbox-meta"></span>
          <span class="lightbox-counter"></span>
        </figcaption>
      </figure>
      <p class="visually-hidden" aria-live="polite"></p>`;
    document.body.appendChild(root);

    els = {
      img: root.querySelector(".lightbox-img"),
      title: root.querySelector(".lightbox-title"),
      meta: root.querySelector(".lightbox-meta"),
      counter: root.querySelector(".lightbox-counter"),
      status: root.querySelector("[aria-live]"),
      close: root.querySelector(".lightbox-close"),
      prev: root.querySelector(".lightbox-prev"),
      next: root.querySelector(".lightbox-next"),
    };

    root.addEventListener("click", (e) => {
      if (e.target.closest("[data-close]")) close();
      else if (e.target.closest("[data-prev]")) step(-1);
      else if (e.target.closest("[data-next]")) step(1);
    });

    // Balayage sur mobile.
    let startX = null;
    root.addEventListener("touchstart", (e) => { startX = e.changedTouches[0].clientX; }, { passive: true });
    root.addEventListener("touchend", (e) => {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      startX = null;
      if (Math.abs(dx) > 45) step(dx < 0 ? 1 : -1);
    }, { passive: true });

    document.addEventListener("keydown", (e) => {
      if (root.hidden) return;
      if (e.key === "Escape") { close(); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); step(1); }
      else if (e.key === "Tab") trapFocus(e);
    });
  }

  // Le clavier reste dans la visionneuse tant qu'elle est ouverte.
  function trapFocus(e) {
    const focusable = [els.close, els.prev, els.next].filter((el) => !el.hidden);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  function labels(t) {
    els.close.setAttribute("aria-label", t("catches.close"));
    els.prev.setAttribute("aria-label", t("catches.prevPhoto"));
    els.next.setAttribute("aria-label", t("catches.nextPhoto"));
  }

  function show(t) {
    const s = slides[index];
    if (!s) return;
    els.img.src = s.src;
    els.img.alt = s.alt || "";
    els.title.textContent = s.title || "";
    els.meta.textContent = s.meta || "";

    const many = slides.length > 1;
    els.counter.textContent = many ? `${index + 1} / ${slides.length}` : "";
    els.prev.hidden = !many;
    els.next.hidden = !many;
    els.status.textContent = t("catches.photoOf", { n: index + 1, total: slides.length });

    // Les voisines sont préchargées pour que la navigation soit immédiate.
    [slides[index - 1], slides[index + 1]].forEach((n) => {
      if (n) { const im = new Image(); im.src = n.src; }
    });
  }

  function step(delta) {
    if (slides.length < 2) return;
    index = (index + delta + slides.length) % slides.length;
    show(PMF_I18N.t);
  }

  function open(list, start, t) {
    if (!list.length) return;
    if (!root) build(t);
    labels(t);
    slides = list;
    index = Math.max(0, Math.min(start, list.length - 1));
    opener = document.activeElement;
    root.hidden = false;
    document.body.classList.add("has-lightbox");
    show(t);
    els.close.focus();
  }

  function close() {
    if (!root || root.hidden) return;
    root.hidden = true;
    els.img.removeAttribute("src");
    document.body.classList.remove("has-lightbox");
    if (opener && document.contains(opener)) opener.focus();
    opener = null;
  }

  return { open, close };
})();

async function initCatches(options) {
  const {
    gridSelector,
    emptySelector,
    countSelector,
    featuredSelector,
    anglerFilterSelector,
    speciesFilterSelector,
  } = options;

  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  const { t, tr, plural, key: stableKey } = PMF_I18N;

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
  const countEl = countSelector ? document.querySelector(countSelector) : null;
  const emptyEl = emptySelector ? document.querySelector(emptySelector) : null;
  const featuredEl = featuredSelector ? document.querySelector(featuredSelector) : null;

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

  function filtering() {
    return !!((anglerSelect && anglerSelect.value) || (speciesSelect && speciesSelect.value));
  }

  function matches(c) {
    if (anglerSelect && anglerSelect.value && c.angler !== anglerSelect.value) return false;
    if (speciesSelect && speciesSelect.value && stableKey(c.species) !== speciesSelect.value) return false;
    return true;
  }

  // Tout ce qu'on répète d'une prise : le nom du pêcheur, la date lisible,
  // les faits, et le texte alternatif d'une photo.
  function describe(c) {
    const lang = PMF_I18N.lang;
    const angler = memberById.get(c.angler);
    const anglerName = angler ? tr(angler.name) : c.angler || "";
    const when = longDate(c.date, lang);

    const ev = c.event ? eventById.get(c.event) : null;
    const facts = [];
    if (when) facts.push(`📅 ${when}`);
    if (tr(c.water)) facts.push(`📍 ${tr(c.water)}`);
    if (ev) facts.push(`🏆 ${tr(ev.name)}`);

    const species = tr(c.species) || "—";
    const measure = tr(c.measure);
    return {
      angler,
      anglerName,
      when,
      facts,
      species,
      measure,
      notes: tr(c.notes),
      title: measure ? `${species} — ${measure}` : species,
      // Alt utile pour un lecteur d'écran : quoi, qui, et où.
      alt: [species, anglerName, tr(c.water)].filter(Boolean).join(" — "),
      meta: [anglerName].concat(facts).filter(Boolean).join(" · "),
    };
  }

  // La liste plate que parcourt la visionneuse : chaque photo de chaque prise
  // affichée, dans l'ordre de la page.
  function slidesFor(rows) {
    const out = [];
    rows.forEach((c) => {
      const d = describe(c);
      catchPhotos(c).forEach((photo, i) => {
        out.push({
          catchId: c.id,
          photoIndex: i,
          src: photo.src,
          alt: tr(photo.alt) || d.alt,
          title: d.title,
          meta: d.meta,
        });
      });
    });
    return out;
  }

  let slides = [];

  function openFrom(btn) {
    const id = btn.getAttribute("data-catch");
    const n = Number(btn.getAttribute("data-photo")) || 0;
    const at = slides.findIndex((s) => s.catchId === id && s.photoIndex === n);
    PMF_LIGHTBOX.open(slides, at < 0 ? 0 : at, t);
  }

  // Photo cliquable, clip YouTube, ou l'écusson en attendant une vraie photo.
  function mediaHTML(c, d) {
    const photos = catchPhotos(c);
    if (photos.length) {
      const badge = photos.length > 1
        ? `<span class="catch-photo-count" aria-hidden="true">1/${photos.length}</span>`
        : "";
      return `
        <button type="button" class="catch-media-btn" data-catch="${escapeHTML(c.id)}" data-photo="0"
                aria-label="${escapeHTML(t("catches.openPhoto"))}">
          <img class="catch-media-img" src="${escapeHTML(photos[0].src)}"
               alt="${escapeHTML(tr(photos[0].alt) || d.alt)}" loading="lazy">
          ${badge}
        </button>`;
    }
    const media = c.media || {};
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

  function bodyHTML(c, d, headingTag) {
    const chip = d.anglerName
      ? (d.angler
        ? `<a class="angler-chip" href="history.html?member=${encodeURIComponent(d.angler.id)}">${escapeHTML(d.anglerName)}</a>`
        : `<span class="angler-chip">${escapeHTML(d.anglerName)}</span>`)
      : "";
    return `
      <div class="catch-head">
        <${headingTag}>${escapeHTML(d.species)}</${headingTag}>
        ${d.measure ? `<span class="catch-measure">${escapeHTML(d.measure)}</span>` : ""}
      </div>
      ${chip ? `<div class="catch-anglers">${chip}</div>` : ""}
      ${d.facts.length ? `<div class="catch-facts">${d.facts.map((f) => `<span>${escapeHTML(f)}</span>`).join("")}</div>` : ""}
      ${d.notes ? `<p class="catch-notes">${escapeHTML(d.notes)}</p>` : ""}`;
  }

  function cardHTML(c) {
    const d = describe(c);
    return `
      <article class="catch-card">
        <div class="catch-media">${mediaHTML(c, d)}</div>
        <div class="catch-body">${bodyHTML(c, d, "h3")}</div>
      </article>`;
  }

  function featuredHTML(c) {
    const d = describe(c);
    // Pas de bouton « voir en grand » : la photo elle-même ouvre la visionneuse.
    return `
      <article class="featured-catch">
        <div class="catch-media featured-media">
          ${mediaHTML(c, d)}
          <span class="featured-flag">${escapeHTML(t("catches.featured"))}</span>
        </div>
        <div class="catch-body featured-body">
          ${bodyHTML(c, d, "h2")}
        </div>
      </article>`;
  }

  function render() {
    const rows = catches.filter(matches);
    slides = slidesFor(rows);

    if (countEl) countEl.textContent = plural("catches.count", rows.length);

    // La vedette ne sort que sur la page complète : dès qu'un filtre est actif,
    // toutes les prises retenues retournent dans la grille.
    const featured = !filtering() ? rows.find((c) => c.featured) : null;
    if (featuredEl) featuredEl.innerHTML = featured ? featuredHTML(featured) : "";

    const gridRows = featured ? rows.filter((c) => c !== featured) : rows;
    grid.innerHTML = gridRows.map(cardHTML).join("");

    if (emptyEl) emptyEl.style.display = rows.length ? "none" : "block";

    const scope = featuredEl ? [featuredEl, grid] : [grid];
    scope.forEach((el) => {
      el.querySelectorAll("[data-catch]").forEach((btn) => {
        btn.addEventListener("click", () => openFrom(btn));
      });
      // Rien n'atteint YouTube tant que personne n'appuie sur lecture.
      el.querySelectorAll("[data-video]").forEach((btn) => {
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
    });
  }

  [anglerSelect, speciesSelect].forEach((el) => {
    if (el) el.addEventListener("input", () => { PMF_LIGHTBOX.close(); render(); });
  });

  PMF_I18N.onChange(() => { PMF_LIGHTBOX.close(); refreshFilterOptions(); render(); });
  refreshFilterOptions();

  // Deep link from a team card: catches.html?angler=bobe
  const preselect = queryParam("angler");
  if (anglerSelect && preselect && memberById.has(preselect)) anglerSelect.value = preselect;

  render();
}
