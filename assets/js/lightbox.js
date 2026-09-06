// Pied Marin Fishing — la visionneuse photo
//
// Elle vivait dans catches.js, donc seule la page Prises l'avait. Les fiches
// generees — bateaux/, prises/ — affichaient leurs galeries sans pouvoir les
// ouvrir : la grille recadre les photos en 4:3, et il n'existait aucun endroit
// ou voir le cadre complet. Une seule definition, plusieurs consommateurs.
//
// Depend de escapeHTML et PMF_IMG (util.js) et de PMF_I18N (i18n.js).

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
    // La visionneuse occupe presque tout l'écran : sur un téléphone, 96vw en
    // double densité demande environ 750px, pas les 1200 de l'original.
    const ss = PMF_IMG.srcset(s.src);
    if (ss) { els.img.srcset = ss; els.img.sizes = "96vw"; }
    else { els.img.removeAttribute("srcset"); els.img.removeAttribute("sizes"); }
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

// Rend cliquable une galerie deja rendue en HTML — c'est le cas des fiches
// generees, ou le serveur a ecrit les <figure> et le JS n'a rien a construire.
//
// La liste des diapositives est rebatie a chaque ouverture plutot que mise en
// cache : sur une fiche generee, le francais et l'anglais vivent dans le meme
// DOM et la legende visible change quand on bascule la langue. Dix photos,
// c'est gratuit.
async function initGalleryLightbox(selector) {
  const root = document.querySelector(selector);
  if (!root) return;

  await PMF_I18N.ready;
  // La carte des largeurs, pour que la visionneuse serve la bonne taille.
  // Elle avale ses propres erreurs : sans elle, on sert l'original.
  await PMF_IMG.load();
  const { t } = PMF_I18N;

  const figures = [...root.querySelectorAll("figure")];
  if (!figures.length) return;

  figures.forEach((fig, i) => {
    const img = fig.querySelector("img");
    if (!img) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "gal-btn";
    btn.setAttribute("aria-label", t("catches.openPhoto"));
    img.parentNode.insertBefore(btn, img);
    btn.appendChild(img);
    // La legende visible decrit deja la photo juste en dessous : repeter le
    // texte dans alt le ferait annoncer deux fois.
    if (fig.querySelector("figcaption")) img.setAttribute("alt", "");
    btn.addEventListener("click", () => {
      const slides = figures.map((f) => {
        const im = f.querySelector("img");
        const cap = f.querySelector("figcaption");
        return im ? { src: im.getAttribute("src"),
                      alt: cap ? cap.textContent.trim() : (im.getAttribute("alt") || ""),
                      meta: cap ? cap.textContent.trim() : "" } : null;
      }).filter(Boolean);
      PMF_LIGHTBOX.open(slides, i, t);
    });
  });
}
