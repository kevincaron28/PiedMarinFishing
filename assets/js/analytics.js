// Pied Marin Fishing — mesure d'audience
//
// GoatCounter : sans témoin, sans identifiant persistant, sans donnée
// personnelle. C'est ce qui permet de mesurer sans bandeau de consentement,
// la Loi 25 ne l'exigeant que pour les technologies qui identifient ou
// profilent une personne.
//
// POUR L'ACTIVER : crée un compte sur goatcounter.com, choisis un code de
// site, et colle-le ci-dessous. Rien d'autre à faire.
//
//   const GOATCOUNTER_SITE = "piedmarinfishing";
//
// Laissé vide, ce fichier ne fait rien du tout : aucun script chargé,
// aucune requête, aucun visiteur mesuré.

const GOATCOUNTER_SITE = "piedmarinfishing";

(function () {
  if (!GOATCOUNTER_SITE) return;

  const s = document.createElement("script");
  s.async = true;
  s.src = "https://gc.zgo.at/count.js";
  s.setAttribute("data-goatcounter",
    `https://${GOATCOUNTER_SITE}.goatcounter.com/count`);
  // Un bloqueur de pub peut l'empêcher de charger; ce n'est pas une erreur.
  s.onerror = function () {};
  document.head.appendChild(s);
})();
