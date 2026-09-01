// Fiches de tournoi — bascule FR/EN.
//
// Ces pages sont écrites en dur par tools/build-tournament-pages.py : le
// français est dans le HTML (c'est lui que lisent les moteurs de recherche) et
// l'anglais voyage dans un attribut data-en. On échange les deux au moment du
// clic plutôt que de tout reconstruire en JavaScript — la page reste lisible
// sans script, ce qui est tout l'intérêt de la générer.
//
// Le reste de la page (menu, pied de page) passe par PMF_I18N comme partout
// ailleurs; ici on ne s'occupe que du contenu propre au tournoi.
(function () {
  function swap(lang) {
    const en = lang === "en";

    document.querySelectorAll("[data-en]").forEach((el) => {
      // Le français d'origine est mémorisé au premier passage : sans ça, un
      // aller-retour FR→EN→FR laisserait la page en anglais.
      if (!el.hasAttribute("data-fr")) el.setAttribute("data-fr", el.textContent);
      el.textContent = el.getAttribute(en ? "data-en" : "data-fr");
    });

    document.querySelectorAll("[data-en-content]").forEach((el) => {
      if (!el.hasAttribute("data-fr-content")) {
        el.setAttribute("data-fr-content", el.getAttribute("content") || "");
      }
      el.setAttribute("content", el.getAttribute(en ? "data-en-content" : "data-fr-content"));
    });

    document.querySelectorAll("[data-en-alt]").forEach((el) => {
      if (!el.hasAttribute("data-fr-alt")) {
        el.setAttribute("data-fr-alt", el.getAttribute("alt") || "");
      }
      el.setAttribute("alt", el.getAttribute(en ? "data-en-alt" : "data-fr-alt"));
    });

    document.querySelectorAll("[data-en-href]").forEach((el) => {
      if (!el.hasAttribute("data-fr-href")) {
        el.setAttribute("data-fr-href", el.getAttribute("href") || "");
      }
      el.setAttribute("href", el.getAttribute(en ? "data-en-href" : "data-fr-href"));
    });
  }

  if (typeof PMF_I18N === "undefined") return;
  PMF_I18N.ready.then(() => swap(PMF_I18N.lang));
  PMF_I18N.onChange(swap);
})();
