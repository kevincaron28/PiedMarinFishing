// Pied Marin Fishing — péremption de la réglementation affichée sur les fiches
//
// La réglementation vit maintenant sur chaque fiche d'espèce, et ces fiches
// sont GÉNÉRÉES : rien ne peut expirer au moment du build, puisque le build a
// eu lieu le jour où on a écrit les règles. Sans ce fichier, déplacer la
// réglementation depuis une page rendue en JavaScript vers des pages statiques
// perdait la seule garantie qui compte : qu'une règle périmée disparaisse
// d'elle-même si personne ne repasse dessus.
//
// « Je vais la mettre à jour chaque année » est une promesse. Ceci est le
// mécanisme.
//
// Le bloc est REMPLACÉ, pas surmonté d'un avertissement : une règle périmée
// sous un avis reste une règle périmée à l'écran.

(function () {
  function monthsSince(iso) {
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return Infinity;
    const now = new Date();
    return (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth());
  }

  function guard() {
    document.querySelectorAll("[data-reg-updated]").forEach((block) => {
      const stamp = block.getAttribute("data-reg-updated");
      const limit = Number(block.getAttribute("data-reg-months")) || 12;
      if (!stamp || monthsSince(stamp) <= limit) return;
      const link = block.querySelector(".reg-note a");
      const title = PMF_I18N.t("reg.staleTitle");
      const body = PMF_I18N.t("reg.staleBody", { date: stamp });
      const warn = document.createElement("div");
      warn.className = "reg-stale";
      warn.setAttribute("role", "status");
      const h = document.createElement("p");
      h.className = "reg-stale-head";
      h.textContent = title;
      const p = document.createElement("p");
      p.textContent = body;
      warn.append(h, p);
      if (link) {
        const wrap = document.createElement("p");
        wrap.appendChild(link.cloneNode(true));
        warn.appendChild(wrap);
      }
      block.replaceChildren(warn);
    });
  }

  // typeof et non window.PMF_I18N : i18n.js expose un « const » global, qui
  // est visible comme identifiant mais n'est PAS une propriété de window.
  // Le test sur window echouait silencieusement et le garde-fou ne tournait
  // jamais — un mecanisme de securite qui ne s'execute pas est pire qu'aucun,
  // parce qu'on croit l'avoir.
  if (typeof PMF_I18N !== "undefined" && PMF_I18N.ready) {
    PMF_I18N.ready.then(function () { guard(); PMF_I18N.onChange(guard); });
  }
})();
