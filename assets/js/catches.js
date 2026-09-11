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
  let everything = null;

  function fetchAll() {
    if (!everything) {
      everything = fetch("data/catches.json", DATA_FETCH)
        .then((r) => r.json())
        .then((rows) => rows.filter(Boolean))
        .catch(() => []);
    }
    return everything;
  }

  function load() {
    if (!cache) {
      cache = fetchAll()
        // showcase === false : la photo vit sur la fiche de son espèce et
        // nulle part ailleurs. Le mur des prises est une sélection — les gros,
        // les beaux, ceux qui ont une histoire — et pas un journal de sorties.
        // Sans ce filtre, chaque photo envoyée finissait sur le mur et le
        // diluait; c'est ce qui arrive à tous les sites d'équipe.
        .then((rows) => rows.filter((c) => c.showcase !== false))
        .then((rows) => rows.slice().sort((a, b) => {
          // La prise vedette d'abord, ensuite la plus récente.
          if (!!b.featured !== !!a.featured) return b.featured ? 1 : -1;
          return (b.date || "").localeCompare(a.date || "");
        }));
    }
    return cache;
  }

  // TOUTES les prises, y compris celles qui ne montent pas sur le mur.
  //
  // La phrase « on remet nos prises à l'eau » décrit la pratique de l'équipe,
  // pas le contenu du mur. En la calculant sur la liste filtrée, un doré gardé
  // et marqué showcase:false n'aurait PAS fait changer la phrase — le site
  // aurait continué d'affirmer qu'on remet tout. Vérifié en simulant le cas :
  // c'est exactement ce qui se produisait.
  function loadAll() {
    return fetchAll();
  }

  function forAngler(rows, id) {
    return rows.filter((c) => c.angler === id);
  }
  return { load, loadAll, forAngler };
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

// La visionneuse vit maintenant dans assets/js/lightbox.js : les fiches
// generees en avaient besoin aussi, et deux copies auraient derive.
// Cette page doit donc charger lightbox.js AVANT catches.js.

async function initCatches(options) {
  const {
    gridSelector,
    emptySelector,
    countSelector,
    featuredSelector,
    releaseSelector,
    hallSelector,
    anglerFilterSelector,
    speciesFilterSelector,
  } = options;

  const grid = document.querySelector(gridSelector);
  if (!grid) return;

  await PMF_I18N.ready;
  // La carte des largeurs d'image, pour que srcset soit prêt au premier
  // rendu. Elle avale ses propres erreurs : sans elle, les photos sont
  // simplement servies en taille d'origine.
  await PMF_IMG.load();
  const { t, tr, plural, key: stableKey } = PMF_I18N;

  let catches = [];
  let members = [];
  let events = [];
  // Les prises assez documentées ont leur propre fiche dans prises/. La liste
  // est écrite par tools/build-catch-pages.py; si elle manque, les cartes
  // s'affichent simplement sans le lien.
  let pageIds = [];
  let allCatches = [];
  try {
    [catches, members, events, pageIds, allCatches] = await Promise.all([
      PMF_CATCHES.load(),
      fetch("data/team-members.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
      fetch("data/tournament-history.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
      fetch("data/catch-pages.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
      PMF_CATCHES.loadAll(),
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
  const hallEl = hallSelector ? document.querySelector(hallSelector) : null;
  const releaseEl = releaseSelector ? document.querySelector(releaseSelector) : null;

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
    // Un pêcheur hors roster porte son nom sur la prise elle-même : c'est le
    // cas de la relève, qui n'a volontairement pas de fiche (voir
    // data/next-gen.json). Sa vignette reste alors du texte, sans lien.
    const anglerName = angler ? tr(angler.name) : (tr(c.anglerName) || c.angler || "");
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
  function mediaHTML(c, d, sizes) {
    const photos = catchPhotos(c);
    if (photos.length) {
      const badge = photos.length > 1
        ? `<span class="catch-photo-count" aria-hidden="true">1/${photos.length}</span>`
        : "";
      return `
        <button type="button" class="catch-media-btn" data-catch="${escapeHTML(c.id)}" data-photo="0"
                aria-label="${escapeHTML(t("catches.openPhoto"))}">
          <img class="catch-media-img" src="${escapeHTML(photos[0].src)}"${
            PMF_IMG.attrs(photos[0].src, sizes || "(max-width: 760px) 92vw, 346px")}
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

  // Remise a l'eau, prise par prise.
  //
  // Le champ `released` est OBLIGATOIRE (check-links.py) et vaut true sur les
  // dix prises actuelles. Le jour ou un dore est garde, on met false sur cette
  // fiche-la et tout le site suit — y compris la phrase du haut de page, qui
  // est calculee et non ecrite en dur. Une phrase figee « toutes nos prises
  // repartent a l'eau » serait devenue fausse en silence.
  function releaseChipHTML(c) {
    if (typeof c.released !== "boolean") return "";
    const key = c.released ? "catch.released" : "catch.kept";
    const cls = c.released ? "catch-release" : "catch-release is-kept";
    return `<span class="${cls}">${escapeHTML(t(key))}</span>`;
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
      ${releaseChipHTML(c)}
      ${d.facts.length ? `<div class="catch-facts">${d.facts.map((f) => `<span>${escapeHTML(f)}</span>`).join("")}</div>` : ""}
      ${d.notes ? `<p class="catch-notes">${escapeHTML(d.notes)}</p>` : ""}
      ${storyLinkHTML(c)}
      ${videoLinkHTML(c)}`;
  }

  // Le récit complet vit sur la fiche de la prise quand elle en a une. La
  // carte n'en montre rien : elle garde sa note courte, et le lien mène au
  // reste plutôt que d'allonger une liste de sept prises.
  function storyLinkHTML(c) {
    if (!pageIds.includes(c.id)) return "";
    return `
      <a class="catch-story-link" href="prises/${escapeHTML(c.id)}.html">
        ${escapeHTML(t("catches.readStory"))}
      </a>`;
  }

  // Une prise illustrée par une photo peut quand même avoir été filmée : le
  // champ media.videoId sert alors de renvoi vers le clip, sans remplacer la
  // photo. Quand la prise EST une vidéo (media.type === "youtube"), c'est
  // mediaHTML qui s'en charge et il n'y a rien à ajouter ici.
  function videoLinkHTML(c) {
    const media = c.media || {};
    if (media.type === "youtube" || !media.videoId) return "";
    const id = encodeURIComponent(media.videoId);
    return `
      <a class="catch-video-link" href="https://www.youtube.com/watch?v=${id}"
         target="_blank" rel="noopener">
        <span aria-hidden="true">▶</span> ${escapeHTML(t("catches.watchVideo"))}
      </a>`;
  }

  function cardHTML(c) {
    const d = describe(c);
    return `
      <article class="catch-card" id="c-${escapeHTML(c.id || "")}">
        <div class="catch-media">${mediaHTML(c, d)}</div>
        <div class="catch-body">${bodyHTML(c, d, "h3")}</div>
      </article>`;
  }

  function featuredHTML(c) {
    const d = describe(c);
    // Pas de bouton « voir en grand » : la photo elle-même ouvre la visionneuse.
    return `
      <article class="featured-catch" id="c-${escapeHTML(c.id || "")}">
        <div class="catch-media featured-media">
          ${mediaHTML(c, d, "(max-width: 760px) 92vw, 583px")}
          <span class="featured-flag">${escapeHTML(t("catches.featured"))}</span>
        </div>
        <div class="catch-body featured-body">
          ${bodyHTML(c, d, "h2")}
        </div>
      </article>`;
  }

  // Temple de la renommée — le plus gros poisson par espèce.
  //
  // Rien n'est saisi à la main : le tableau se recalcule à partir des prises.
  // Une prise sans mesure ne peut pas détenir de record, et deux mesures ne se
  // comparent que si elles portent la même unité — 50 po et 11 lb ne se
  // classent pas l'un contre l'autre.
  function records(rows) {
    const best = new Map();
    rows.forEach((c) => {
      const parsed = parseMeasure(tr(c.measure));
      if (!parsed) return;
      const key = stableKey(c.species);
      if (!key) return;
      const held = best.get(key);
      // À unité différente, on garde le premier plutôt que de comparer
      // des pouces à des livres.
      if (!held || (held.parsed.unit === parsed.unit && parsed.value > held.parsed.value)) {
        best.set(key, { catch: c, parsed });
      }
    });
    return [...best.values()].sort((a, b) => {
      const sa = tr(a.catch.species) || "";
      return sa.localeCompare(tr(b.catch.species) || "", PMF_I18N.lang);
    });
  }

  function hallHTML(rows) {
    return rows.map(({ catch: c }) => {
      const d = describe(c);
      const photo = catchPhotos(c)[0];
      const angler = d.anglerName;
      return `
        <!-- Pas d'aria-label : il remplacerait le texte visible du bouton par une
             version plus courte, sans le nom du pêcheur. Le contenu fait le nom
             accessible, et il correspond exactement à ce qui est à l'écran.
             La vignette reste en alt="" — décorative à côté de ce texte. -->
        <button type="button" class="hall-item" data-catch="${escapeHTML(c.id)}" data-photo="0">
          ${photo ? `<img class="hall-thumb" src="${escapeHTML(photo.src)}"${PMF_IMG.attrs(photo.src, "72px")} alt="" loading="lazy" width="120" height="90">` : ""}
          <span class="hall-body">
            <span class="hall-species">${escapeHTML(tr(c.species))}</span>
            <span class="hall-measure">${escapeHTML(tr(c.measure))}</span>
            ${angler ? `<span class="hall-angler">${escapeHTML(angler)}</span>` : ""}
          </span>
        </button>`;
    }).join("");
  }

  function render() {
    const rows = catches.filter(matches);
    slides = slidesFor(rows);

    if (countEl) countEl.textContent = plural("catches.count", rows.length);
    if (releaseEl) {
      // Sur TOUTES les prises — ni la selection du filtre, ni meme celles du
      // mur. La phrase decrit la pratique de l'equipe; une prise gardee mais
      // laissee hors du mur (showcase:false) doit la faire changer quand meme.
      const kept = allCatches.filter((c) => c.released === false).length;
      releaseEl.textContent = t(kept ? "catches.releaseSome" : "catches.releaseAll");
    }

    // La vedette ne sort que sur la page complète : dès qu'un filtre est actif,
    // toutes les prises retenues retournent dans la grille.
    const featured = !filtering() ? rows.find((c) => c.featured) : null;
    if (featuredEl) featuredEl.innerHTML = featured ? featuredHTML(featured) : "";

    // Le temple ne s'affiche que sur la page complète, comme la vedette, et
    // seulement s'il compte au moins deux records — un seul ne fait pas un
    // palmarès.
    const hall = !filtering() ? records(rows) : [];
    if (hallEl) {
      const show = hall.length >= 2;
      hallEl.innerHTML = show ? hallHTML(hall) : "";
      const section = hallEl.closest("[data-hall-section]") || hallEl;
      section.hidden = !show;
    }

    const gridRows = featured ? rows.filter((c) => c !== featured) : rows;
    grid.innerHTML = gridRows.map(cardHTML).join("");

    if (emptyEl) emptyEl.style.display = rows.length ? "none" : "block";

    const scope = [featuredEl, hallEl, grid].filter(Boolean);
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

  // Lien profond vers UNE prise : catches.html#c-maskinonge-kevin-b. Les
  // cartes n'existent pas au chargement, alors le navigateur a déjà renoncé
  // à sauter quand elles apparaissent — on refait le saut ici. Un filtre
  // actif peut avoir écarté la cible : on le lève plutôt que de rester sur
  // une page qui n'a pas ce qu'on est venu voir.
  function jumpToCatch() {
    const id = (location.hash || "").slice(1);
    if (!/^c-/.test(id)) return;
    if (!document.getElementById(id) && anglerSelect && anglerSelect.value) {
      anglerSelect.value = "";
      render();
    }
    const el = document.getElementById(id);
    if (!el) return;
    const header = document.querySelector(".site-header");
    const offset = (header ? header.getBoundingClientRect().height : 0) + 12;
    window.scrollTo({ top: Math.max(0, el.getBoundingClientRect().top + window.scrollY - offset),
                      behavior: "smooth" });
    // Un repère visuel : sur une page de sept prises, « laquelle déjà? »
    el.classList.add("catch-targeted");
    setTimeout(() => el.classList.remove("catch-targeted"), 2600);
  }
  window.addEventListener("hashchange", jumpToCatch);
  jumpToCatch();
}
