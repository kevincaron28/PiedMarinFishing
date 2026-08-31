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
  const { sectionSelector, gridSelector, socialSelector } = options;
  const section = document.querySelector(sectionSelector);
  const grid = document.querySelector(gridSelector);
  if (!section || !grid) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  const json = (url) => fetch(url, DATA_FETCH).then((r) => r.json()).catch(() => []);
  const [catches, schedule, history, socials] = await Promise.all([
    json("data/catches.json"),
    json("data/team-schedule.json"),
    json("data/tournament-history.json"),
    json("data/socials.json"),
  ]);

  const today = new Date().toISOString().slice(0, 10);
  // Une date partielle ("2027", "2027-05") se compare bien en texte tant qu'on
  // la complète : "2027" devient "2027-99" pour trier après les mois connus.
  const sortable = (d) => (d || "").padEnd(10, "9");
  const newest = (rows, key) =>
    rows.filter((r) => r[key]).sort((a, b) => sortable(b[key]).localeCompare(sortable(a[key])))[0];

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
  const next = schedule
    .filter((e) => e.startDate && sortable(e.endDate || e.startDate) >= today)
    .sort((a, b) => sortable(a.startDate).localeCompare(sortable(b.startDate)))[0];
  if (next) {
    cards.push({
      kicker: t("new.next"),
      title: tr(next.name),
      meta: [longDate(next.startDate, PMF_I18N.lang), tr(next.location)].filter(Boolean).join(" · "),
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
