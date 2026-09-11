// Pied Marin Fishing — le journal des sorties.
//
// Le site avait deux endroits pour un poisson : le mur des prises, qui ne
// garde que les records et le spécial, et la fiche de son espèce. Aucun pour
// une JOURNÉE. Le 4 juillet 2025 le montrait bien — quatre espèces, deux
// records personnels, un Short, un coucher de soleil — éparpillés en quatre
// morceaux que rien ne rassemblait.
//
// Une sortie ne recopie rien : elle porte des identifiants et va chercher les
// prises, les pêcheurs, le bateau et les vidéos dans leurs propres fichiers.
// Un nom recopié aurait dérivé le jour où quelqu'un corrige une mesure.

async function initTrips(options) {
  const { listSelector, countSelector, limit = 0 } = options;
  const list = document.querySelector(listSelector);
  if (!list) return;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

  const json = (url) => fetch(url, DATA_FETCH).then((r) => r.json()).catch(() => null);
  const [trips, catches, members, boats, videoData, pageIds] = await Promise.all([
    json("data/trips.json"),
    // Le fichier complet, lu directement : une sortie peut compter une prise
    // qui ne monte pas sur le mur (showcase:false) — le brochet du 4 juillet
    // est dans ce cas, et l'oublier serait raconter la journée à moitié.
    //
    // On ne passe PAS par PMF_CATCHES : ce module vit dans catches.js, qui
    // porte tout le rendu du mur. Charger 400 lignes de code pour un fetch
    // ferait payer à cette page une fonctionnalité qu'elle n'affiche pas.
    json("data/catches.json"),
    json("data/team-members.json"),
    json("data/boats.json"),
    json("data/videos.json"),
    json("data/catch-pages.json"),
  ]);

  if (!Array.isArray(trips) || !trips.length) {
    list.innerHTML = `<div class="empty-state">${escapeHTML(t("trips.empty"))}</div>`;
    return;
  }

  await PMF_IMG.load();

  const byId = (rows, k) => new Map((rows || []).map((r) => [r[k || "id"], r]));
  const catchById = byId(catches);
  const memberById = byId(members);
  const boatById = byId(boats);
  const videoById = new Map(((videoData || {}).videos || []).map((v) => [v.videoId, v]));
  const sheets = Array.isArray(pageIds) ? pageIds : [];

  // De la plus récente à la plus ancienne. Une date de sortie est toujours
  // complète — c'est une journée, pas une année.
  const ordered = trips.slice().sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  const shown = limit > 0 ? ordered.slice(0, limit) : ordered;

  function crewHTML(ids) {
    const chips = (ids || []).map((id) => {
      const m = memberById.get(id);
      if (!m) return "";
      return `<a class="angler-chip" href="pecheurs/${escapeHTML(id)}.html">${
        escapeHTML(tr(m.name))}</a>`;
    }).filter(Boolean).join("");
    return chips ? `<div class="trip-crew">${chips}</div>` : "";
  }

  function catchHTML(id) {
    const c = catchById.get(id);
    if (!c) return "";
    const photo = (c.media && c.media.src) || "";
    const who = memberById.get(c.angler);
    const bits = [tr(c.measure), who ? tr(who.name) : ""].filter(Boolean).join(" · ");
    const inner =
      (photo ? `<img class="trip-catch-thumb" src="${escapeHTML(photo)}"${
        PMF_IMG.attrs(photo, "(max-width: 700px) 45vw, 160px")} alt="" loading="lazy"
        width="160" height="120">` : "") +
      `<span class="trip-catch-body"><span class="trip-catch-species">${
        escapeHTML(tr(c.species))}</span>${
        bits ? `<span class="trip-catch-meta">${escapeHTML(bits)}</span>` : ""}</span>`;
    // Le lien ne mène quelque part que si la prise a vraiment sa fiche.
    // Pointer sur prises/<id>.html « au cas où » donnerait un 404 que
    // check-links.py ne peut pas voir depuis les données.
    return sheets.includes(id)
      ? `<a class="trip-catch" href="prises/${escapeHTML(id)}.html">${inner}</a>`
      : `<figure class="trip-catch trip-catch-flat">${inner}</figure>`;
  }

  function videoHTML(id) {
    const v = videoById.get(id);
    if (!v) return "";
    // Même prudence qu'ailleurs : rien n'est demandé à YouTube avant le clic.
    return `<a class="trip-video" href="https://www.youtube.com/watch?v=${
      encodeURIComponent(id)}" target="_blank" rel="noopener">
      <img class="trip-video-thumb" loading="lazy" width="320" height="180" alt=""
           src="https://i.ytimg.com/vi/${encodeURIComponent(id)}/mqdefault.jpg">
      <span>${escapeHTML(tr(v.title))}</span></a>`;
  }

  function block(key, body) {
    return body ? `<div class="trip-block"><h3 class="trip-block-title">${
      escapeHTML(t(key))}</h3>${body}</div>` : "";
  }

  function tripHTML(trip) {
    const boat = boatById.get(trip.boat);
    const caught = (trip.catches || []).map(catchHTML).filter(Boolean).join("");
    const vids = (trip.videos || []).map(videoHTML).filter(Boolean).join("");
    const story = tr(trip.story);
    const conditions = tr(trip.conditions);
    return `
      <article class="trip" id="t-${escapeHTML(trip.id || "")}">
        <header class="trip-head">
          <p class="trip-when">${escapeHTML(longDate(trip.date, PMF_I18N.lang))}</p>
          <h2>${escapeHTML(tr(trip.title))}</h2>
          ${tr(trip.water) ? `<p class="trip-water">${escapeHTML(tr(trip.water))}</p>` : ""}
          ${(trip.catches || []).length
            ? `<p class="trip-tally">${escapeHTML(
                plural("trips.catchCount", trip.catches.length))}</p>` : ""}
        </header>
        ${block("trips.crew", crewHTML(trip.members) +
          (boat ? `<p class="trip-boat"><a href="bateaux/${escapeHTML(boat.id)}.html">${
            escapeHTML(tr(boat.name))}</a></p>` : ""))}
        ${block("trips.conditions", conditions ? `<p>${escapeHTML(conditions)}</p>` : "")}
        ${story ? `<div class="trip-story"><p>${escapeHTML(story)}</p></div>` : ""}
        ${block("trips.caught", caught ? `<div class="trip-catches">${caught}</div>` : "")}
        ${block("trips.video", vids)}
      </article>`;
  }

  function draw() {
    list.innerHTML = shown.map(tripHTML).join("");
    const countEl = countSelector ? document.querySelector(countSelector) : null;
    if (countEl) countEl.textContent = plural("trips.count", ordered.length);
  }

  draw();
  PMF_I18N.onChange(draw);
}
