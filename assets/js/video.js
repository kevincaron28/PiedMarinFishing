// Pied Marin Fishing — vidéos YouTube
//
// data/videos.json tient la liste; celle marquée "featured" passe en vedette
// sur l'accueil, et la page Réseaux les affiche toutes. Rien n'est demandé à
// YouTube tant que le visiteur n'a pas cliqué : la vignette vient d'i.ytimg,
// et l'iframe n'est créée qu'au clic. Pas de témoin avant ce geste.

async function loadVideos() {
  try {
    const data = await (await fetch("data/videos.json", DATA_FETCH)).json();
    return {
      channelUrl: data.channelUrl || "",
      videos: (data.videos || []).filter((v) => v && v.videoId),
    };
  } catch (e) {
    return { channelUrl: "", videos: [] };
  }
}

// DEUX DATES, ET ELLES NE DISENT PAS LA MÊME CHOSE.
//
//   date      — quand la sortie a eu lieu. Écrite à la main, souvent partielle
//               (« 2025 »). C'est ce qu'on affiche à côté du pêcheur.
//   published — quand YouTube a reçu la vidéo. Écrite par le robot.
//
// Les deux premières vidéos racontent la saison 2025 et ont été mises en
// ligne en août 2026 : les confondre décalait tout d'un an.
//
// « Notre dernière vidéo » parle de mise en ligne, donc on classe sur
// `published`, avec `date` en secours pour une vidéo que le flux n'a jamais
// vue. Une date partielle se compare en la complétant, comme partout ailleurs
// sur le site : elle vaut alors la fin de son année. À égalité, la DERNIÈRE
// du fichier gagne — `fetch-youtube.py` ajoute en fin de liste, donc l'ordre
// du fichier est déjà chronologique.
// Pour CLASSER : la mise en ligne d'abord — « notre dernière vidéo » parle de
// ça. `date` en secours pour une vidéo que le flux n'a jamais vue.
function videoOrder(v) {
  return (v && (v.published || v.date)) || "";
}

// Pour AFFICHER : la sortie d'abord — c'est ce que le lecteur veut savoir, et
// c'est ce que l'humain a écrit. La mise en ligne ne sert que si on ne connaît
// pas la sortie. L'inverse affichait « Kevin Caron · 28 août 2026 » sous une
// vidéo de la saison 2025.
function videoWhen(v) {
  return (v && (v.date || v.published)) || "";
}

function videosByDate(videos) {
  return (videos || [])
    .map((v, i) => ({ v, i }))
    .sort((a, b) =>
      sortableDate(videoOrder(b.v)).localeCompare(sortableDate(videoOrder(a.v))) || b.i - a.i)
    .map((x) => x.v);
}

function newestVideo(videos) {
  return videosByDate(videos)[0];
}

async function initFeaturedVideo(selector) {
  const host = document.querySelector(selector);
  if (!host) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  const all = await loadVideos();
  // La vedette si quelqu'un en a choisi une, sinon LA PLUS RÉCENTE.
  //
  // C'était « la première de la liste », ce qui marchait tant que la liste
  // était tenue à la main. tools/fetch-youtube.py ajoute maintenant les
  // nouveautés à la FIN : « la première » serait devenue la plus vieille, et
  // la section s'appelle « Notre dernière vidéo ». Le titre doit rester vrai
  // tout seul.
  const data = Object.assign(
    { channelUrl: all.channelUrl },
    all.videos.find((v) => v.featured) || newestVideo(all.videos) || {});

  // Accept a bare id or a full YouTube URL, whichever got pasted in.
  function extractId(value) {
    const raw = (value || "").trim();
    if (!raw) return "";
    const match = raw.match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([A-Za-z0-9_-]{11})/);
    if (match) return match[1];
    return /^[A-Za-z0-9_-]{11}$/.test(raw) ? raw : "";
  }

  // A Short is vertical; a 16:9 frame would letterbox it into a thin strip.
  function frameClass() {
    return data.orientation === "portrait" ? " video-portrait" : "";
  }

  // Le lien vers la chaîne, en bouton. Réservé au substitut : quand une vidéo
  // est en vedette, le hero de l'accueil porte déjà le lien vers YouTube, et
  // le redonner ici n'aurait fait que le répéter.
  function channelBtn(label, cls) {
    return data.channelUrl
      ? `<a class="btn ${cls}" href="${escapeHTML(data.channelUrl)}" target="_blank" rel="noopener">${escapeHTML(t(label))}</a>`
      : "";
  }

  function renderPlaceholder() {
    const channel = channelBtn("video.watchChannel", "btn-teal");
    host.innerHTML = `
      <div class="video-frame${frameClass()}">
        <div class="video-placeholder">
          <span class="video-play" aria-hidden="true"></span>
          <h3>${escapeHTML(t("video.placeholderTitle"))}</h3>
          <p>${escapeHTML(t("video.placeholderBody"))}</p>
          ${channel}
        </div>
      </div>
    `;
  }

  function renderVideo(id) {
    const title = tr(data.title);
    host.innerHTML = `
      <div class="video-frame${frameClass()}">
        <button type="button" class="video-facade" aria-label="${escapeHTML(t("video.playLabel"))}">
          <img class="video-thumb" alt=""
               src="https://i.ytimg.com/vi/${encodeURIComponent(id)}/maxresdefault.jpg"
               onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/${encodeURIComponent(id)}/hqdefault.jpg';this.onerror=function(){this.style.display='none';}">
          <span class="video-play" aria-hidden="true"></span>
        </button>
      </div>
      ${title ? `<div class="video-caption">${escapeHTML(title)}</div>` : ""}
    `;

    host.querySelector(".video-facade").addEventListener("click", (ev) => {
      const frame = ev.currentTarget.closest(".video-frame");
      const iframe = document.createElement("iframe");
      // nocookie host + autoplay, since the click is the consent to load it.
      iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&rel=0`;
      iframe.title = tr(data.title) || t("video.playLabel");
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;
      frame.innerHTML = "";
      frame.appendChild(iframe);
    });
  }

  function render() {
    const id = extractId(data.videoId);
    if (id) renderVideo(id);
    else renderPlaceholder();
  }

  PMF_I18N.onChange(render);
  render();
}

// Liste des vidéos — page Réseaux.
//
// Sous deux vidéos, la section se retire : une « chaîne » d'un seul clip
// n'en est pas une, et l'accueil le montre déjà en vedette.
async function initVideoList(options) {
  const { listSelector, sectionSelector, minimum = 2 } = options;
  const list = document.querySelector(listSelector);
  const section = sectionSelector ? document.querySelector(sectionSelector) : list;
  if (!list) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;
  const { videos } = await loadVideos();

  // Le nom du pêcheur vient de la fiche d'équipe, comme pour les prises :
  // un identifiant dans les données, jamais un nom recopié.
  let memberById = new Map();
  if (videos.some((v) => v.angler)) {
    try {
      const members = await (await fetch("data/team-members.json", DATA_FETCH)).json();
      memberById = new Map(members.map((m) => [m.id, m]));
    } catch (e) { /* sans les noms, la liste reste utilisable */ }
  }

  function draw() {
    if (videos.length < minimum) {
      if (section) section.hidden = true;
      list.innerHTML = "";
      return;
    }
    if (section) section.hidden = false;
    list.innerHTML = videosByDate(videos).map((v) => {
      const id = encodeURIComponent(v.videoId);
      const title = tr(v.title) || t("videos.untitled");
      // La date de sortie si on la connaît; sinon celle de mise en ligne,
      // qui reste une date vraie au sujet de la vidéo.
      const when = videoWhen(v) ? longDate(videoWhen(v), PMF_I18N.lang) : "";
      const member = v.angler ? memberById.get(v.angler) : null;
      const who = member ? tr(member.name) : "";
      const line = [who, when].filter(Boolean).join(" · ");
      return `
        <a class="video-item" href="https://www.youtube.com/watch?v=${id}"
           target="_blank" rel="noopener">
          <img class="video-item-thumb" loading="lazy" width="320" height="180" alt=""
               src="https://i.ytimg.com/vi/${id}/mqdefault.jpg">
          <span class="video-item-body">
            <span class="video-item-title">${escapeHTML(title)}</span>
            ${line ? `<span class="video-item-date">${escapeHTML(line)}</span>` : ""}
          </span>
        </a>`;
    }).join("");
  }

  draw();
  PMF_I18N.onChange(draw);
}
