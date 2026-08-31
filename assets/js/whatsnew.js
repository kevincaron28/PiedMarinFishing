// Pied Marin Fishing — « Quoi de neuf » sur la page d'accueil.
//
// L'accueil avait l'air figé entre deux visites : rien n'y bougeait sauf la
// vidéo, changée à la main. Ce bloc lit les mêmes fichiers que le reste du
// site et affiche les trois choses les plus récentes — la dernière prise, le
// prochain tournoi au calendrier, le dernier résultat. Il se met donc à jour
// tout seul chaque fois qu'une prise ou un tournoi est ajouté, sans qu'on ait
// à toucher à l'accueil.
//
// Aucun flux de réseaux sociaux ici : Instagram exige un jeton d'accès depuis
// la fin de l'API Basic Display, et le greffon de Facebook dépose des témoins
// qui obligeraient à un bandeau de consentement (Loi 25). Le bloc social plus
// bas se contente de liens — c'est honnête et ça ne coûte rien au visiteur.
async function initWhatsNew(options) {
  const { sectionSelector, gridSelector, socialSelector, statsSelector } = options;
  const section = document.querySelector(sectionSelector);
  const grid = document.querySelector(gridSelector);
  if (!section || !grid) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  const json = (url) => fetch(url, DATA_FETCH).then((r) => r.json()).catch(() => []);
  const [catches, schedule, history, socials, stats] = await Promise.all([
    json("data/catches.json"),
    json("data/team-schedule.json"),
    json("data/tournament-history.json"),
    json("data/socials.json"),
    // Écrit par tools/build-stats.py. Le répertoire lui-même pèse 74 Ko :
    // le charger ici pour afficher un nombre serait absurde.
    json("data/site-stats.json"),
  ]);

  const today = new Date().toISOString().slice(0, 10);
  // Une date partielle ("2027", "2027-05") se compare bien en texte tant qu'on
  // la complète : "2027" devient "2027-99" pour trier après les mois connus.
  const sortable = (d) => (d || "").padEnd(10, "9");
  const newest = (rows, key) =>
    rows.filter((r) => r[key]).sort((a, b) => sortable(b[key]).localeCompare(sortable(a[key])))[0];

  // ---- Les chiffres du bandeau d'accueil ------------------------------
  // Le côté droit de l'en-tête était vide. Trois chiffres, tous calculés :
  // rien à tenir à jour à la main, et rien qui puisse devenir faux.
  const statsHost = statsSelector ? document.querySelector(statsSelector) : null;
  if (statsHost) {
    const seasons = new Set(
      history.map((r) => String(r.date || "").slice(0, 4)).filter(Boolean)).size;

    // Un record par espèce, et seulement pour une prise mesurée — même règle
    // que le temple de la renommée, via parseMeasure de util.js.
    const measured = new Set();
    catches.forEach((c) => {
      if (parseMeasure(tr(c.measure))) measured.add(PMF_I18N.key(c.species));
    });

    const tiles = [
      [seasons, "hero.stat.seasons"],
      [Number(stats && stats.tournaments) || 0, "hero.stat.guide"],
      [measured.size, "hero.stat.records"],
    ].filter(([n]) => n > 0);

    statsHost.innerHTML = tiles.map(([n, key]) => `
      <div class="hero-stat">
        <span class="hero-stat-n">${escapeHTML(String(n))}</span>
        <span class="hero-stat-label">${escapeHTML(PMF_I18N.plural(key, n))}</span>
      </div>`).join("");
    statsHost.hidden = !tiles.length;
  }

  const cards = [];

  const catch_ = newest(catches, "date");
  if (catch_) {
    const parts = [tr(catch_.species), tr(catch_.measure)].filter(Boolean).join(" — ");
    cards.push({
      kicker: t("new.catch"),
      title: parts || tr(catch_.species),
      meta: [longDate(catch_.date, PMF_I18N.lang), tr(catch_.water)].filter(Boolean).join(" · "),
      href: "catches.html",
      cta: t("new.catchCta"),
    });
  }

  // Le prochain tournoi : le premier qui n'est pas encore passé. Une entrée
  // datée à l'année seule ("2027") reste candidate — c'est bien à venir.
  //
  // Mais elle ne peut pas être triée sur "2027" seul : la pêche blanche de
  // janvier se retrouverait après l'ouverture du brochet de mai. Quand
  // l'organisateur n'a pas encore publié sa date, on ordonne sur le mois et le
  // jour de l'édition précédente (previousDate). C'est une estimation, et elle
  // ne sert qu'au classement — jamais affichée comme si c'était la date 2027.
  const orderKey = (e) => {
    const start = e.startDate || "";
    if (/^\d{4}$/.test(start) && /^\d{4}-\d{2}-\d{2}$/.test(e.previousDate || "")) {
      return start + e.previousDate.slice(4);
    }
    return sortable(start);
  };
  const next = schedule
    .filter((e) => e.startDate && sortable(e.endDate || e.startDate) >= today)
    .sort((a, b) => orderKey(a).localeCompare(orderKey(b)))[0];
  if (next) {
    // "2027" tout court ne dit rien d'utile : on l'annonce comme à confirmer.
    const when = /^\d{4}$/.test(next.startDate)
      ? `${next.startDate} — ${t("new.dateTBC")}`
      : longDate(next.startDate, PMF_I18N.lang);
    cards.push({
      kicker: t("new.next"),
      title: tr(next.name),
      meta: [when, tr(next.location)].filter(Boolean).join(" · "),
      href: "calendar.html",
      cta: t("new.nextCta"),
    });
  }

  const last = newest(history, "date");
  if (last) {
    const rank = Number.isFinite(last.placement)
      ? (PMF_I18N.lang === "en"
          ? `${last.placement}${last.fieldSize ? " / " + last.fieldSize : ""}`
          : `${last.placement}e${last.fieldSize ? " sur " + last.fieldSize : ""}`)
      : t("history.resultPending");
    cards.push({
      kicker: t("new.result"),
      title: tr(last.name),
      meta: [longDate(last.date, PMF_I18N.lang), rank].filter(Boolean).join(" · "),
      href: "history.html",
      cta: t("new.resultCta"),
    });
  }

  // Rien à montrer : la section se retire plutôt que d'afficher un cadre vide.
  if (!cards.length) {
    section.style.display = "none";
    return;
  }
  section.style.display = "";

  grid.innerHTML = cards.map((c) => `
    <article class="news-card">
      <span class="news-kicker">${escapeHTML(c.kicker)}</span>
      <h3 class="news-title">${escapeHTML(c.title)}</h3>
      ${c.meta ? `<p class="news-meta">${escapeHTML(c.meta)}</p>` : ""}
      <a class="news-link" href="${escapeHTML(c.href)}">${escapeHTML(c.cta)}</a>
    </article>
  `).join("");

  const socialHost = socialSelector ? document.querySelector(socialSelector) : null;
  if (socialHost) {
    const links = socials.filter((s) => (s.url || "").startsWith("http"));
    socialHost.innerHTML = links.length
      ? links.map((s) => `
          <a class="news-social" href="${escapeHTML(s.url)}" target="_blank" rel="noopener"
             style="--dot:${escapeHTML(s.color || "#157a76")}">
            <span class="news-social-name">${escapeHTML(tr(s.name))}</span>
            <span class="news-social-handle">${escapeHTML(s.handle || "")}</span>
          </a>`).join("")
      : "";
    socialHost.hidden = !links.length;
  }
}
