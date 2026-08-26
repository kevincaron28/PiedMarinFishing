// Pied Marin Fishing — featured YouTube video
// Set "videoId" in data/featured-video.json to swap the placeholder for the
// real clip. Nothing is requested from YouTube until the visitor hits play.

async function initFeaturedVideo(selector) {
  const host = document.querySelector(selector);
  if (!host) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  let data = {};
  try {
    data = await (await fetch("data/featured-video.json")).json();
  } catch (e) {
    data = {};
  }

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
               onerror="this.onerror=null;this.src='https://i.ytimg.com/vi/${encodeURIComponent(id)}/hqdefault.jpg'">
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
