// Pied Marin Fishing — shared site behavior

// Le tiroir de navigation, en menu qui se comporte comme un menu.
//
// Il n'était qu'une classe CSS qu'on posait et qu'on enlevait. Mesuré sur un
// téléphone, cinq comportements attendus manquaient : Échap ne fermait rien,
// un geste à côté non plus, le focus ne revenait pas au bouton, la tabulation
// sortait du menu ouvert vers la page derrière, et surtout **le fond défilait
// sous le tiroir** — on ouvre le menu, on glisse le pouce, et c'est la page
// qui bouge. Le bouton ne disait pas non plus ce qu'il contrôlait.
//
// Rien ici n'est spécifique au format de l'écran : le tiroir n'existe que
// sous 1100 px (voir la requête média de style.css), donc au-dessus ces
// écouteurs ne coûtent rien — `links.classList.contains("open")` y est faux.
function initNavDrawer() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector(".nav-links");
  const nav = document.querySelector(".nav");
  if (!toggle || !links || !nav) return;

  const isOpen = () => links.classList.contains("open");

  function setOpen(open, { focusToggle = false } = {}) {
    links.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
    // Le verrou du défilement vit dans la CSS, sous la requête média : poser
    // un overflow en ligne l'aurait aussi appliqué sur écran large, où le
    // tiroir n'existe pas.
    document.documentElement.classList.toggle("nav-open", open);
    if (!open && focusToggle) toggle.focus();
  }

  toggle.addEventListener("click", () => setOpen(!isOpen()));

  // Un lien choisi ferme le tiroir. La navigation le ferait de toute façon —
  // sauf pour une ancre de la même page, où il resterait ouvert par-dessus la
  // cible qu'on vient de demander.
  links.addEventListener("click", (ev) => {
    if (ev.target.closest("a")) setOpen(false);
  });

  document.addEventListener("keydown", (ev) => {
    if (!isOpen()) return;

    if (ev.key === "Escape") {
      setOpen(false, { focusToggle: true });
      return;
    }

    if (ev.key !== "Tab") return;

    // Tant que le tiroir est ouvert, la tabulation tourne dans l'en-tête.
    // Le commutateur de langue en fait partie : on ne veut pas qu'ouvrir le
    // menu empêche de changer de langue.
    const focusables = [...nav.querySelectorAll("a[href], button:not([disabled])")]
      .filter((el) => el.offsetParent !== null);
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (ev.shiftKey && document.activeElement === first) {
      ev.preventDefault();
      last.focus();
    } else if (!ev.shiftKey && document.activeElement === last) {
      ev.preventDefault();
      first.focus();
    }
  });

  // Un geste hors de l'en-tête referme.
  document.addEventListener("click", (ev) => {
    if (isOpen() && !nav.contains(ev.target)) setOpen(false);
  });

  // Passer en mode barre avec le tiroir ouvert laissait `open`, `nav-open` et
  // aria-expanded dans un état que plus rien n'affichait.
  const wide = window.matchMedia("(min-width: 1101px)");
  const onWide = (e) => { if (e.matches && isOpen()) setOpen(false); };
  if (wide.addEventListener) wide.addEventListener("change", onWide);
  else if (wide.addListener) wide.addListener(onWide);       // Safari ancien
}

document.addEventListener("DOMContentLoaded", () => {
  initNavDrawer();

  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = String(new Date().getFullYear());
  });
});
