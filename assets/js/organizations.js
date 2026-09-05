// Pied Marin Fishing — fédérations et associations
//
// Une liste d'organismes est une invitation à s'attribuer un mérite qui n'est
// pas le sien. Ce module est écrit pour rendre ça difficile : rien dans
// data/organizations.json ne peut affirmer une relation. Les seuls liens
// qu'une ligne affiche sont CALCULÉS en comparant organizerMatch au champ
// organizer de trois sources :
//
//   tournament-history.json  ce qu'on a réellement pêché
//   team-schedule.json       ce qui est réellement à notre calendrier
//   quebec-tournaments.json  ce qu'ils organisent dans le répertoire
//
// C'est ce qui a rattrapé une note écrite à la main qui donnait L'Amical à
// l'APSQ : le répertoire dit « Club April Marine avec Big Bass Québec ».
// Un chiffre calculé ne peut pas vieillir tout seul; une phrase, oui.
//
// La mention « on n'est membre d'aucun » disparaît d'elle-même dès qu'un
// organisme porte member: true, pour qu'elle ne devienne jamais fausse.

async function initOrganizations(sectionSelector, listSelector, disclaimerSelector) {
  const section = document.querySelector(sectionSelector);
  const list = document.querySelector(listSelector);
  if (!section || !list) return;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

  const grab = (url) => fetch(url, DATA_FETCH).then((r) => r.json()).catch(() => []);

  let orgs = [];
  let history = [];
  let schedule = [];
  let directory = [];
  try {
    [orgs, history, schedule, directory] = await Promise.all([
      fetch("data/organizations.json", DATA_FETCH).then((r) => r.json()),
      grab("data/tournament-history.json"),
      grab("data/team-schedule.json"),
      grab("data/quebec-tournaments.json"),
    ]);
  } catch (e) {
    orgs = [];
  }

  if (!Array.isArray(orgs) || !orgs.length) {
    section.hidden = true;
    return;
  }

  // Comparaison sans accents ni casse : « Muskies Canada Montréal » et
  // « Muskies Canada — section Montréal » sont le même monde.
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

  function chip(text, cls) {
    return `<span class="org-tie${cls ? " " + cls : ""}">${escapeHTML(text)}</span>`;
  }

  function render() {
    const anyMember = orgs.some((o) => o.member);
    const disclaimer = disclaimerSelector ? document.querySelector(disclaimerSelector) : null;
    if (disclaimer) disclaimer.hidden = anyMember;

    list.innerHTML = orgs.map((org) => {
      const name = tr(org.name);
      if (!name) return "";

      const fished = matched(org, history);
      const booked = matched(org, schedule);
      const listed = matched(org, directory);

      const ties = [];
      if (org.member) ties.push(chip(t("orgs.tie.member"), "org-tie-strong"));
      if (fished.length) {
        const years = fished.map((e) => parseInt(String(e.date || "").slice(0, 4), 10)).filter(Boolean);
        const noun = plural("orgs.tournament", fished.length);
        ties.push(chip(years.length
          ? t("orgs.tie.fishedSince", { n: fished.length, noun, y: Math.min(...years) })
          : `${fished.length} ${noun}`, "org-tie-strong"));
      }
      if (booked.length) {
        ties.push(chip(t("orgs.tie.booked", { n: booked.length, noun: plural("orgs.tournament", booked.length) })));
      }
      if (listed.length) {
        ties.push(chip(t("orgs.tie.listed", { n: listed.length, noun: plural("orgs.tournament", listed.length) })));
      }
      // Aucun lien calculé : on le dit, plutôt que d'en inventer un.
      if (!ties.length) ties.push(chip(t("orgs.tie.follow"), "org-tie-soft"));

      const title = org.link
        ? `<a href="${escapeHTML(org.link)}" target="_blank" rel="noopener">${escapeHTML(name)}</a>`
        : `<b>${escapeHTML(name)}</b>`;

      return `
        <li>
          ${title}
          <div class="org-ties">${ties.join("")}</div>
          ${tr(org.what) ? `<div class="src-meta">${escapeHTML(tr(org.what))}</div>` : ""}
        </li>`;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
