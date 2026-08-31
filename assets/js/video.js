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

async function initFeaturedVideo(selector) {
  const host = document.querySelector(selector);
  if (!host) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  const all = await loadVideos();
  // La vedette, sinon la première de la liste — l'accueil montre toujours
  // quelque chose tant qu'il y a une vidéo.
  const data = Object.assign(
    { channelUrl: all.channelUrl },
    all.videos.find((v) => v.featured) || all.videos[0] || {});

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

  function renderPlaceholder() {
    const channel = data.channelUrl
      ? `<a href="${escapeHTML(data.channelUrl)}" target="_blank" rel="noopener">${escapeHTML(t("video.watchChannel"))}</a>`
      : "";
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

  function draw() {
    if (videos.length < minimum) {
      if (section) section.hidden = true;
      list.innerHTML = "";
      return;
    }
    if (section) section.hidden = false;
    list.innerHTML = videos.map((v) => {
      const id = encodeURIComponent(v.videoId);
      const title = tr(v.title) || t("videos.untitled");
      const when = v.date ? longDate(v.date, PMF_I18N.lang) : "";
      return `
        <a class="video-item" href="https://www.youtube.com/watch?v=${id}"
           target="_blank" rel="noopener">
          <img class="video-item-thumb" loading="lazy" width="320" height="180" alt=""
               src="https://i.ytimg.com/vi/${id}/mqdefault.jpg">
          <span class="video-item-body">
            <span class="video-item-title">${escapeHTML(title)}</span>
            ${when ? `<span class="video-item-date">${escapeHTML(when)}</span>` : ""}
          </span>
        </a>`;
    }).join("");
  }

  draw();
  PMF_I18N.onChange(draw);
}
