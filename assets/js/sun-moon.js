// Pied Marin Fishing — positions du Soleil et de la Lune
//
// Lever, coucher et passage au méridien, calculés. Pas d'API, pas de fichier
// de données : les séries viennent de « Astronomical Algorithms » (Meeus) en
// version courte, ce qui donne la position de la Lune à environ 0,3° près —
// soit quelques minutes sur une heure de lever. Largement assez pour décider
// à quelle heure mettre le bateau à l'eau.
//
// Le lieu de référence est MONTRÉAL, pas notre secteur de pêche. Sur les
// 100 km du corridor fluvial l'écart est de quelques minutes, et le secteur
// où on pêche ne regarde personne.

const PMF_SKY = (function () {
  const RAD = Math.PI / 180;
  const J2000 = Date.UTC(2000, 0, 1, 12) / 86400000;

  // POINTS DE RÉFÉRENCE — publics, jamais notre secteur.
  //
  // Mesuré d'un bout à l'autre de la zone 8 : l'écart sur le lever du soleil
  // est de 4 à 7 minutes, et de 0 à 4 minutes sur le passage de la Lune au
  // méridien. C'est moins que la précision de l'éphéméride elle-même, et sans
  // commune mesure avec des fenêtres solunaires d'une à deux heures.
  //
  // Coder les coordonnées de notre secteur ne gagnerait donc rien d'utile, et
  // publierait sur un dépôt public exactement ce qu'on protège depuis le
  // début. Le pêcheur qui veut ses vraies heures utilise plutôt sa propre
  // position : elle reste dans SON navigateur et ne touche jamais le site.
  const PLACES = [
    { id: "valleyfield", name: "Valleyfield", lat: 45.25, lon: -74.13 },
    { id: "montreal", name: "Montréal", lat: 45.5019, lon: -73.5674 },
    { id: "sorel", name: "Sorel-Tracy", lat: 46.04, lon: -73.11 },
    { id: "trois-rivieres", name: "Trois-Rivières", lat: 46.34, lon: -72.55 },
  ];
  const DEFAULT = PLACES[1];
  let LAT = DEFAULT.lat, LON = DEFAULT.lon;
  let placeLabel = DEFAULT.name;

  const sin = (d) => Math.sin(d * RAD), cos = (d) => Math.cos(d * RAD);
  const norm = (d) => ((d % 360) + 360) % 360;

  function days(date) { return date.getTime() / 86400000 - J2000; }

  function obliquity(d) { return 23.439 - 0.0000004 * d; }

  function sun(d) {
    const L = norm(280.460 + 0.9856474 * d);
    const g = norm(357.528 + 0.9856003 * d);
    const lam = norm(L + 1.915 * sin(g) + 0.020 * sin(2 * g));
    const e = obliquity(d);
    return { ra: Math.atan2(cos(e) * sin(lam), cos(lam)) / RAD,
             dec: Math.asin(sin(e) * sin(lam)) / RAD };
  }

  function moon(d) {
    const Lp = norm(218.316 + 13.176396 * d);   // longitude moyenne
    const M = norm(134.963 + 13.064993 * d);    // anomalie moyenne
    const F = norm(93.272 + 13.229350 * d);     // argument de latitude
    const lam = Lp + 6.289 * sin(M);
    const bet = 5.128 * sin(F);
    const e = obliquity(d);
    const x = cos(bet) * cos(lam);
    const y = cos(e) * cos(bet) * sin(lam) - sin(e) * sin(bet);
    const z = sin(e) * cos(bet) * sin(lam) + cos(e) * sin(bet);
    return { ra: Math.atan2(y, x) / RAD, dec: Math.asin(z) / RAD };
  }

  // Temps sidéral local, en degrés.
  function lst(d) { return norm(280.16 + 360.9856235 * d + LON); }

  function altitude(body, date) {
    const d = days(date);
    const p = body(d);
    const H = norm(lst(d) - p.ra);
    return Math.asin(sin(LAT) * sin(p.dec) + cos(LAT) * cos(p.dec) * cos(H)) / RAD;
  }

  // Balayage puis bissection : robuste, et il n'y a rien de plus rapide qui
  // vaille la peine ici — un mois entier tient en quelques millisecondes.
  function events(body, dayStart, h0) {
    const STEP = 10 * 60000;
    const end = dayStart.getTime() + 86400000;
    let prev = new Date(dayStart), prevAlt = altitude(body, prev) - h0;
    let rise = null, set = null, transit = null, best = -91;
    for (let t = dayStart.getTime() + STEP; t <= end; t += STEP) {
      const now = new Date(t), alt = altitude(body, now) - h0;
      if (alt + h0 > best) { best = alt + h0; transit = now; }
      if (prevAlt < 0 && alt >= 0) rise = refine(body, prev, now, h0);
      if (prevAlt >= 0 && alt < 0) set = refine(body, prev, now, h0);
      prev = now; prevAlt = alt;
    }
    // Le passage au méridien tombait sur un multiple du pas de balayage :
    // « 13 h 20 » là où la vraie valeur est 13 h 17. Recherche ternaire
    // autour du meilleur échantillon, à la seconde près.
    if (transit) {
      let lo = transit.getTime() - STEP, hi = transit.getTime() + STEP;
      for (let i = 0; i < 40; i++) {
        const a = lo + (hi - lo) / 3, b = hi - (hi - lo) / 3;
        if (altitude(body, new Date(a)) < altitude(body, new Date(b))) lo = a; else hi = b;
      }
      transit = new Date((lo + hi) / 2);
      best = altitude(body, transit);
    }
    return { rise, set, transit, maxAltitude: best };
  }

  function refine(body, a, b, h0) {
    let lo = a.getTime(), hi = b.getTime();
    for (let i = 0; i < 30; i++) {
      const mid = (lo + hi) / 2;
      if (altitude(body, new Date(mid)) - h0 < 0) lo = mid; else hi = mid;
    }
    return new Date((lo + hi) / 2);
  }

  // Le passage INFÉRIEUR : la Lune au plus bas sous l'horizon, soit environ
  // 12 h 25 après le passage supérieur. C'est la deuxième période majeure des
  // tables solunaires.
  function lowerTransit(upper) {
    return upper ? new Date(upper.getTime() + 12.421 * 3600000) : null;
  }

  // LES PÉRIODES SOLUNAIRES.
  //
  // Ce n'est pas de l'astronomie, c'est une théorie de pêche : John Alden
  // Knight, 1926. Elle pose que le poisson est plus actif quand la Lune passe
  // au méridien (au-dessus de la tête) et au méridien inférieur (sous les
  // pieds) — les périodes MAJEURES, deux heures chacune — et à son lever et
  // à son coucher — les MINEURES, une heure chacune.
  //
  // Les instants sont calculés exactement. Ce que le poisson en fait n'est
  // pas démontré, et la page le dit. On calcule ce que la théorie demande,
  // sans prétendre qu'elle a raison.
  // Tous les passages au méridien d'un intervalle, trouvés en continu.
  // Les découper par jour créait des artefacts de bord : un passage juste
  // après minuit était trouvé par la fenêtre de la veille ET par celle du
  // jour, et sortait deux fois à une journée d'écart.
  function transits(from, to) {
    const STEP = 10 * 60000;
    const out = [];
    let a = altitude(moon, new Date(from - STEP)), b = altitude(moon, new Date(from));
    for (let t = from + STEP; t <= to; t += STEP) {
      const c = altitude(moon, new Date(t));
      if (b > a && b >= c) {
        let lo = t - 2 * STEP, hi = t;
        for (let i = 0; i < 40; i++) {
          const x = lo + (hi - lo) / 3, y = hi - (hi - lo) / 3;
          if (altitude(moon, new Date(x)) < altitude(moon, new Date(y))) lo = x; else hi = y;
        }
        out.push(new Date((lo + hi) / 2));
      }
      a = b; b = c;
    }
    return out;
  }

  function solunar(dayStart) {
    const dayEnd = new Date(dayStart.getTime() + 86400000);
    const m = events(moon, dayStart, 0.125);
    const centers = [];
    for (const up of transits(dayStart.getTime() - 86400000, dayEnd.getTime() + 86400000)) {
      centers.push({ kind: "major", at: up });
      centers.push({ kind: "major", at: lowerTransit(up) });
    }
    const yest = events(moon, new Date(dayStart.getTime() - 86400000), 0.125);
    const dem = events(moon, dayEnd, 0.125);
    for (const ev of [yest, m, dem]) {
      if (ev.rise) centers.push({ kind: "minor", at: ev.rise });
      if (ev.set) centers.push({ kind: "minor", at: ev.set });
    }
    const seen = new Set(), periods = [];
    for (const c of centers) {
      if (!c.at) continue;
      const half = (c.kind === "major" ? 1 : 0.5) * 3600000;
      const from = new Date(c.at.getTime() - half), to = new Date(c.at.getTime() + half);
      if (to <= dayStart || from >= dayEnd) continue;
      const key = c.kind + Math.round(c.at.getTime() / 1800000);
      if (seen.has(key)) continue;
      seen.add(key);
      periods.push({ kind: c.kind, from: from, to: to, center: c.at });
    }
    periods.sort((a, b) => a.from - b.from);
    return { periods: periods, moon: m, sun: events(sun, dayStart, -0.833) };
  }

  function setPlace(p) {
    if (!p || typeof p.lat !== "number" || typeof p.lon !== "number") return;
    LAT = p.lat; LON = p.lon;
    placeLabel = p.name || "";
  }

  return {
    places: PLACES,
    defaultPlace: DEFAULT,
    setPlace,
    place: () => ({ lat: LAT, lon: LON, name: placeLabel }),
    solunar,
    sun: (dayStart) => events(sun, dayStart, -0.833),
    moon: (dayStart) => events(moon, dayStart, 0.125),
    lowerTransit,
    altitudeOfMoon: (date) => altitude(moon, date),
  };
})();
