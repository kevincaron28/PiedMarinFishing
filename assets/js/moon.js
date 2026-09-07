// Pied Marin Fishing — calendrier lunaire
//
// CE QUI EST UN FAIT ET CE QUI N'EN EST PAS UN.
//
// La phase de la Lune est de l'astronomie : elle se calcule, elle ne
// s'estime pas. Ce fichier la calcule à partir d'une nouvelle lune de
// référence et de la durée du mois synodique (29,530588853 jours). Aucune
// donnée à tenir à jour, aucune API, rien qui puisse se périmer — c'est le
// seul contenu du site qui n'a pas besoin de garde-fou.
//
// Ce que la Lune fait pour la pêche, par contre, est beaucoup moins établi
// que ce que racontent les tables « solunaires » vendues partout. La marée
// du fleuve, la lumière nocturne et le comportement de fraie de certaines
// espèces sont réels; « les gros poissons mordent à la pleine lune » ne
// l'est pas. La page dit donc la phase, et laisse le pêcheur en faire ce
// qu'il veut. On ne vend pas de prédiction qu'on ne peut pas soutenir.

const PMF_MOON = (function () {
  const SYNODIC = 29.530588853;
  // Nouvelle lune du 6 janvier 2000, 18 h 14 UTC.
  const EPOCH = Date.UTC(2000, 0, 6, 18, 14) / 86400000;

  function age(date) {
    const days = date.getTime() / 86400000;
    let a = (days - EPOCH) % SYNODIC;
    if (a < 0) a += SYNODIC;
    return a;
  }

  function illumination(date) {
    return (1 - Math.cos((2 * Math.PI * age(date)) / SYNODIC)) / 2;
  }

  // Huit phases, la principale n'etant reconnue que dans une fenetre d'un
  // jour autour de son instant exact — sinon « pleine lune » resterait
  // affiche trois jours de suite.
  const PHASES = [
    { key: "new", at: 0 }, { key: "waxingCrescent", at: 3.7 },
    { key: "firstQuarter", at: 7.4 }, { key: "waxingGibbous", at: 11.1 },
    { key: "full", at: 14.8 }, { key: "waningGibbous", at: 18.5 },
    { key: "lastQuarter", at: 22.1 }, { key: "waningCrescent", at: 25.8 },
  ];

  const PRINCIPAL = ["new", "firstQuarter", "full", "lastQuarter"];

  function nearest(a) {
    let best = PHASES[0], dist = SYNODIC;
    for (const p of PHASES) {
      const d = Math.min(Math.abs(a - p.at), SYNODIC - Math.abs(a - p.at));
      if (d < dist) { dist = d; best = p; }
    }
    return { phase: best, dist: dist };
  }

  function phase(date) {
    const a = age(date);
    const here = nearest(a);
    // Une phase principale n'est marquee que sur LE jour le plus proche de
    // son instant exact. Une simple fenetre de tolerance affichait
    // « nouvelle lune » deux jours de suite quand l'instant tombait vers
    // midi — un calendrier ne peut pas avoir deux nouvelles lunes.
    let principal = false;
    if (PRINCIPAL.includes(here.phase.key)) {
      const before = nearest(age(new Date(date.getTime() - 86400000)));
      const after = nearest(age(new Date(date.getTime() + 86400000)));
      principal = here.dist <= 1
        && !(before.phase.key === here.phase.key && before.dist < here.dist)
        && !(after.phase.key === here.phase.key && after.dist < here.dist);
    }
    return { key: here.phase.key, age: a, illumination: illumination(date), principal };
  }

  const GLYPH = { new: "🌑", waxingCrescent: "🌒", firstQuarter: "🌓",
                  waxingGibbous: "🌔", full: "🌕", waningGibbous: "🌖",
                  lastQuarter: "🌗", waningCrescent: "🌘" };

  return { age, illumination, phase, glyph: (k) => GLYPH[k] || "", SYNODIC };
})();
