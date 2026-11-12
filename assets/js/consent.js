// Pied Marin Fishing — consentement aux témoins publicitaires (Google AdSense)
//
// Aucun script publicitaire ne se charge avant un choix. Le choix est gardé
// dans localStorage; sans localStorage (navigation privée…), la bannière
// revient à chaque page, ce qui est le côté sûr de l'erreur.
//
//   Accepter -> annonces personnalisées
//   Refuser  -> annonces non personnalisées (requestNonPersonalizedAds = 1)
//
// Ce fichier est autonome : ses textes sont ici, pas dans data/i18n.json, parce
// que la bannière ne doit pas dépendre du chargement d'un autre fichier. La
// langue suit l'attribut lang de <html>, que i18n.js met à jour au clic FR/EN.
//
// Les unités publicitaires ne sont PAS dans le balisage : elles viennent des
// annonces automatiques, à activer dans AdSense.

(function () {
  "use strict";

  var CLIENT = "ca-pub-6948243189424271";
  var SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + CLIENT;
  var KEY = "pmf-consent";        // "granted" | "denied"
  var LANG_KEY = "pmf-lang";      // la même clé que i18n.js

  var TEXT = {
    fr: {
      label: "Témoins publicitaires",
      title: "Témoins publicitaires",
      body: "Ce site affiche de la publicité Google AdSense, qui utilise des témoins (cookies). " +
            "Si tu acceptes, les annonces peuvent être personnalisées; si tu refuses, elles ne le seront pas. " +
            "Tu peux changer d'avis en tout temps.",
      more: "En savoir plus",
      accept: "Accepter",
      decline: "Refuser",
      manage: "Témoins publicitaires"
    },
    en: {
      label: "Advertising cookies",
      title: "Advertising cookies",
      body: "This site shows Google AdSense ads, which use cookies. " +
            "If you accept, ads may be personalised; if you decline, they won't be. " +
            "You can change your mind at any time.",
      more: "Learn more",
      accept: "Accept",
      decline: "Decline",
      manage: "Advertising cookies"
    }
  };

  function store(fn) { try { return fn(); } catch (e) { return null; } }
  function readChoice() {
    var v = store(function () { return localStorage.getItem(KEY); });
    return v === "granted" || v === "denied" ? v : null;
  }
  function writeChoice(v) { store(function () { localStorage.setItem(KEY, v); }); }

  // La langue : ?lang= gagne, puis le choix mémorisé, puis <html lang>.
  function currentLang() {
    var l = store(function () { return new URLSearchParams(location.search).get("lang"); });
    if (l !== "fr" && l !== "en") l = store(function () { return localStorage.getItem(LANG_KEY); });
    if (l !== "fr" && l !== "en") l = document.documentElement.lang;
    return l === "en" ? "en" : "fr";
  }
  // Une fois i18n.js parti, <html lang> est la vérité (il suit les clics).
  var htmlLangTouched = false;
  function lang() {
    return htmlLangTouched ? (document.documentElement.lang === "en" ? "en" : "fr") : currentLang();
  }

  // --- publicité --------------------------------------------------------
  var adsLoaded = false;
  function loadAds(personalised) {
    if (adsLoaded) return;
    adsLoaded = true;
    var q = (window.adsbygoogle = window.adsbygoogle || []);
    if (!personalised) q.requestNonPersonalizedAds = 1;
    var s = document.createElement("script");
    s.async = true;
    s.src = SRC;
    s.crossOrigin = "anonymous";
    // Un bloqueur de pub peut l'empêcher de charger; ce n'est pas une erreur.
    s.onerror = function () {};
    document.head.appendChild(s);
  }

  // --- bannière ---------------------------------------------------------
  var banner = null;

  function paint() {
    if (!banner) return;
    var t = TEXT[lang()];
    banner.setAttribute("aria-label", t.label);
    banner.querySelector(".consent-title").textContent = t.title;
    banner.querySelector(".consent-text").textContent = t.body;
    var more = banner.querySelector(".consent-more");
    more.textContent = t.more;
    banner.querySelector('[data-choice="granted"]').textContent = t.accept;
    banner.querySelector('[data-choice="denied"]').textContent = t.decline;
  }

  function choose(value) {
    var hadLoaded = adsLoaded;
    writeChoice(value);
    if (banner) { banner.remove(); banner = null; }
    // Des annonces déjà chargées ne se « déchargent » pas : on repart à neuf.
    if (hadLoaded) { location.reload(); return; }
    loadAds(value === "granted");
  }

  function show() {
    if (banner) return;
    banner = document.createElement("div");
    banner.className = "consent-banner";
    banner.setAttribute("role", "dialog");
    banner.innerHTML =
      '<div class="consent-inner">' +
        '<div class="consent-copy">' +
          '<strong class="consent-title"></strong>' +
          '<p class="consent-text"></p>' +
          '<a class="consent-more" href="privacy.html"></a>' +
        '</div>' +
        '<div class="consent-actions">' +
          '<button type="button" class="consent-btn" data-choice="granted"></button>' +
          '<button type="button" class="consent-btn" data-choice="denied"></button>' +
        '</div>' +
      '</div>';
    banner.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("[data-choice]") : null;
      if (b) choose(b.getAttribute("data-choice"));
    });
    document.body.appendChild(banner);
    paint();
  }

  // --- lien « changer mon choix » ---------------------------------------
  function addFooterLink() {
    var host = document.querySelector(".footer-legal") ||
               document.querySelector(".site-footer .footer-bottom");
    if (!host || host.querySelector("[data-consent-open]")) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "consent-link";
    b.setAttribute("data-consent-open", "");
    b.textContent = TEXT[lang()].manage;
    if (host.firstChild) host.appendChild(document.createTextNode(" · "));
    host.appendChild(b);
  }

  function paintLinks() {
    var t = TEXT[lang()];
    document.querySelectorAll(".consent-link").forEach(function (b) { b.textContent = t.manage; });
  }

  function init() {
    addFooterLink();
    document.addEventListener("click", function (e) {
      var o = e.target.closest ? e.target.closest("[data-consent-open]") : null;
      if (o) { e.preventDefault(); show(); }
    });
    // Suit le commutateur FR/EN : i18n.js réécrit <html lang>.
    new MutationObserver(function () {
      htmlLangTouched = true;
      paint();
      paintLinks();
    }).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });

    var c = readChoice();
    if (c) loadAds(c === "granted");
    else show();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
