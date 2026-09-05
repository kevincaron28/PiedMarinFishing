// Pied Marin Fishing — le milieu qu'on appuie
//
// Une liste d'organismes est une invitation à s'attribuer un mérite qui n'est
// pas le sien. Ce module est écrit pour rendre ça difficile : rien ici n'est
// une affiliation, et le seul lien qu'une carte peut afficher est CALCULÉ à
// partir de nos propres données — les tournois de data/tournament-history.json
// qu'on a réellement pêchés, et ceux de data/team-schedule.json qui sont
// réellement à notre calendrier. Un organisme dont on ne pêche pas les
// événements n'affiche aucun compte, parce qu'il n'y a rien à compter.
//
// La mention « on n'est membre d'aucun » disparaît d'elle-même le jour où un
// organisme porte member: true — pour qu'elle ne devienne jamais fausse.

async function initOrganizations(sectionSelector, listSelector, disclaimerSelector) {
  const section = document.querySelector(sectionSelector);
  const list = document.querySelector(listSelector);
  if (!section || !list) return;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

  let orgs = [];
  let history = [];
  let schedule = [];
  try {
    [orgs, history, schedule] = await Promise.all([
      fetch("data/organizations.json", DATA_FETCH).then((r) => r.json()),
      fetch("data/tournament-history.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
      fetch("data/team-schedule.json", DATA_FETCH).then((r) => r.json()).catch(() => []),
    ]);
  } catch (e) {
    orgs = [];
  }

  if (!Array.isArray(orgs) || !orgs.length) {
    section.hidden = true;
    return;
  }

  // Un organisme est « le nôtre » sur un événement quand son nom apparaît dans
  // le champ organizer, dans une langue ou l'autre. La comparaison est faite
  // sans accents ni casse : « Muskies Canada Montréal » et « Muskies Canada —
  // section Montréal » sont le même monde.
  function fold(s) {
    return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }

  function organizerText(ev) {
    const o = ev.organizer;
    if (!o) return "";
    return fold(typeof o === "string" ? o : `${o.fr || ""} ${o.en || ""}`);
  }

  function matched(org, rows) {
    const needles = (org.organizerMatch || []).map(fold).filter(Boolean);
    if (!needles.length) return [];
    return rows.filter((ev) => {
      const hay = organizerText(ev);
      return needles.some((n) => hay.includes(n));
    });
  }

  function render() {
    const lang = PMF_I18N.lang;
    const anyMember = orgs.some((o) => o.member);

    const disclaimer = disclaimerSelector ? document.querySelector(disclaimerSelector) : null;
    if (disclaimer) disclaimer.hidden = anyMember;

    list.innerHTML = orgs.map((org) => {
      const name = tr(org.name);
      if (!name) return "";

      const fished = matched(org, history);
      const booked = matched(org, schedule);

      // Les liens réels, dans l'ordre où ils comptent : ce qu'on a pêché,
      // puis ce qui s'en vient. Rien quand il n'y a rien.
      const ties = [];
      if (org.member) ties.push(`<span class="org-tie org-tie-strong">${escapeHTML(t("orgs.tie.member"))}</span>`);
      if (fished.length) {
        const years = fished.map((e) => parseInt(String(e.date || "").slice(0, 4), 10)).filter(Boolean);
        const label = years.length
          ? t("orgs.tie.fishedSince", { n: fished.length, noun: plural("orgs.tournament", fished.length), y: Math.min(...years) })
          : `${fished.length} ${plural("orgs.tournament", fished.length)}`;
        ties.push(`<span class="org-tie org-tie-strong">${escapeHTML(label)}</span>`);
      }
      if (booked.length) {
        ties.push(`<span class="org-tie">${escapeHTML(
          t("orgs.tie.booked", { n: booked.length, noun: plural("orgs.tournament", booked.length) }))}</span>`);
      }
      if (!ties.length) ties.push(`<span class="org-tie org-tie-soft">${escapeHTML(t("orgs.tie.follow"))}</span>`);

      const kicker = tr(org.kicker);
      const link = org.link
        ? `<a class="org-link" href="${escapeHTML(org.link)}" target="_blank" rel="noopener">${
            escapeHTML(t("orgs.visit"))} <span aria-hidden="true">↗</span></a>`
        : "";

      return `
        <article class="org-card">
          ${kicker ? `<span class="org-kicker">${escapeHTML(kicker)}</span>` : ""}
          <h3>${escapeHTML(name)}</h3>
          <div class="org-ties">${ties.join("")}</div>
          ${tr(org.what) ? `<p class="org-what">${escapeHTML(tr(org.what))}</p>` : ""}
          ${link}
        </article>`;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
