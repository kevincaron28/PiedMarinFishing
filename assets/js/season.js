// Pied Marin Fishing — qu'est-ce qui est ouvert aujourd'hui
//
// CE QUE CETTE PAGE PROMET, ET CE QU'ELLE REFUSE DE PROMETTRE
//
// Une pastille qui dit « ouvert » est une affirmation légale. Si elle se
// trompe, quelqu'un garde un poisson hors saison sur notre parole. C'est la
// pire erreur que ce site puisse commettre, et tout ce qui suit existe pour
// l'empêcher.
//
// Trois garde-fous, dans l'ordre où ils mordent :
//
//   1. TROIS ÉTATS, JAMAIS DEUX. Ouvert, fermé, et « on ne sait pas ». Une
//      période qui ne s'analyse pas ENTIÈREMENT tombe dans le troisième, et
//      jamais dans « ouvert ». La règle du brochet en est la preuve vivante :
//      le document officiel coupe sa date de fermeture par un saut de page,
//      on a refusé de la reproduire de mémoire, alors la page dit qu'on ne
//      sait pas. C'est l'espèce phare, et elle affiche un aveu d'ignorance.
//
//   2. LA DATE FRANÇAISE FAIT FOI. On n'analyse que le texte français, et on
//      rend les deux langues à partir des dates obtenues. Analyser les deux
//      textes séparément laisserait l'anglais dire « ouvert » pendant que le
//      français dit « fermé », et personne ne le verrait avant longtemps.
//
//   3. LA PAGE SE PÉRIME. Même horloge que reg-guard.js : passé le délai de
//      regulations.json, tout le calcul disparaît et cède la place au lien
//      officiel. Un « OUVERT » périmé est exactement le scénario qu'on refuse.
//
// Et une règle de langue : on écrit « la saison est ouverte », jamais « tu
// peux le garder ». On rapporte une date, on n'accorde pas une permission.

const PMF_SEASON = (() => {
  const MOIS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
    "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
  };

  // « 15 juin 2026 », « 1er mai 2026 ». L'année est obligatoire : sans elle on
  // devrait deviner de quelle saison il s'agit, et deviner est ce qu'on refuse.
  const DATE_RX = /(\d{1,2})\s*(?:er)?\s+([a-zA-Zéèêûîàç]+)\s+(\d{4})/;

  function oneDate(text) {
    const m = DATE_RX.exec(text || "");
    if (!m) return null;
    const mois = MOIS[m[2].toLowerCase()];
    if (!mois) return null;
    const day = Number(m[1]);
    const d = new Date(Number(m[3]), mois - 1, day);
    // Un 31 février deviendrait le 3 mars en silence. On refuse plutôt.
    if (d.getDate() !== day || d.getMonth() !== mois - 1) return null;
    d.setHours(0, 0, 0, 0);
    return d;
  }

  // Renvoie { kind, from, to }. kind vaut "range" seulement quand les DEUX
  // bornes sont lues; tout le reste est "unknown" ou "openingOnly".
  function parsePeriod(fr) {
    const text = (fr || "").trim();
    if (!text) return { kind: "unknown" };
    const halves = text.split(/\s+au\s+/);
    if (halves.length === 2) {
      const from = oneDate(halves[0]);
      const to = oneDate(halves[1]);
      if (from && to && to >= from) return { kind: "range", from, to };
      return { kind: "unknown" };
    }
    if (/ouvertur/i.test(text)) {
      const from = oneDate(text);
      if (from) return { kind: "openingOnly", from };
    }
    return { kind: "unknown" };
  }

  function days(a, b) {
    return Math.round((b - a) / 86400000);
  }

  // L'état d'une règle à une date donnée. `today` est un paramètre et non
  // new Date() : c'est ce qui rend les bascules testables — la veille et le
  // lendemain de chaque ouverture, de chaque fermeture.
  function stateOf(rule, today, frOf) {
    const limit = frOf(rule.limit) || "";
    const ruleText = frOf(rule.rule) || "";
    if (/interdit/i.test(limit) || /p[eê]che interdite/i.test(ruleText)) {
      return { state: "banned" };
    }
    const p = parsePeriod(frOf(rule.period));
    if (p.kind === "range") {
      if (today < p.from) return { state: "soon", days: days(today, p.from), from: p.from, to: p.to };
      if (today > p.to) return { state: "closed", days: days(p.to, today), from: p.from, to: p.to };
      return { state: "open", days: days(today, p.to), from: p.from, to: p.to };
    }
    if (p.kind === "openingOnly") {
      // Ouverte depuis une date connue, fermeture inconnue. On NE conclut pas
      // qu'elle est ouverte aujourd'hui : une saison a une fin, et ne pas la
      // connaître n'est pas la même chose que ne pas en avoir.
      return { state: "unknown", from: p.from };
    }
    return { state: "unknown" };
  }

  function monthsSince(iso) {
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return Infinity;
    const now = new Date();
    return (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth());
  }

  // La dernière date écrite dans un texte. Sert à lire la fin de saison dans
  // « Saison 2026-2027 — du 1er avril 2026 au 31 mars 2027 ». Renvoie null si
  // aucune date complète n'y figure, et l'appelant se tait alors plutôt que
  // de supposer une fin.
  function lastDateOf(text) {
    const rx = new RegExp(DATE_RX.source, "g");
    let m, last = null;
    while ((m = rx.exec(text || ""))) last = m[0];
    return last ? oneDate(last) : null;
  }

  return { parsePeriod, stateOf, monthsSince, oneDate, lastDateOf };
})();

// L'ordre de lecture, et il n'est pas alphabétique. Ce qui ferme bientôt vient
// d'abord parce que c'est ce qui coûte une occasion manquée; ce qui est
// interdit vient avant « on ne sait pas » parce qu'une interdiction est une
// information certaine, et l'incertitude se lit mieux à la fin.
const SEASON_ORDER = ["closingSoon", "openingSoon", "open", "banned", "closed", "unknown"];
const SEASON_SOON_DAYS = 60;

async function initSeason(rootSelector, options) {
  const root = document.querySelector(rootSelector);
  if (!root) return;
  const opts = options || {};
  // Le mode « aperçu » sert le bandeau d'especes.html : les deux ou trois
  // lignes qui pressent, sans le tableau complet.
  const preview = Number(opts.preview) || 0;

  await PMF_I18N.ready;
  const { t, tr, plural } = PMF_I18N;

  let regs = null;
  let species = [];
  let published = [];
  try {
    [regs, species, published] = await Promise.all([
      (await fetch("data/regulations.json", DATA_FETCH)).json(),
      (await fetch("data/species.json", DATA_FETCH)).json(),
      (await fetch("data/species-pages.json", DATA_FETCH)).json(),
    ]);
  } catch (e) {
    regs = null;
  }
  if (!regs || !Array.isArray(regs.rules)) {
    root.hidden = true;
    return;
  }

  const live = new Set(Array.isArray(published) ? published : []);
  const byId = new Map((Array.isArray(species) ? species : [])
    .filter((s) => s && live.has(s.id)).map((s) => [s.id, s]));
  const zoneName = new Map((regs.zones || []).map((z) => [z.id, z.name]));

  function frOf(v) {
    return (v && typeof v === "object" ? v.fr || v.en : v) || "";
  }

  // Seules les règles qui VISENT une espèce entrent ici. Les règles générales
  // — transport de poissons vivants, nombre de lignes l'hiver — n'ont pas de
  // saison et vivent déjà sur l'index des espèces.
  const rules = regs.rules.filter((r) => r && r.verified && !r.general
    && (r.speciesPages || []).some((id) => byId.has(id)));

  function bucket(info) {
    if (info.state === "open") {
      return info.days <= SEASON_SOON_DAYS ? "closingSoon" : "open";
    }
    if (info.state === "soon") {
      return info.days <= SEASON_SOON_DAYS ? "openingSoon" : "closed";
    }
    return info.state;
  }

  function dayLabel(n) {
    return plural("season.days", n);
  }

  function noteFor(key, info) {
    if (key === "closingSoon") return t("season.closesIn", { n: dayLabel(info.days) });
    if (key === "openingSoon") return t("season.opensIn", { n: dayLabel(info.days) });
    if (key === "open") return t("season.closesOn", { date: longDate(iso(info.to), PMF_I18N.lang) });
    if (key === "closed") {
      if (info.state === "soon") return t("season.opensOn", { date: longDate(iso(info.from), PMF_I18N.lang) });
      return t("season.closedSince", { date: longDate(iso(info.to), PMF_I18N.lang) });
    }
    if (key === "banned") return "";
    // « on ne sait pas » : dire CE QU'ON SAIT quand même vaut mieux que rien.
    if (info.from) return t("season.openedNoClose", { date: longDate(iso(info.from), PMF_I18N.lang) });
    return t("season.unparsed");
  }

  function iso(d) {
    if (!d) return "";
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function zonesHtml(r) {
    return (r.zones || []).map((z) => `<span class="season-zone">${
      escapeHTML(tr(zoneName.get(z)) || z)}</span>`).join("");
  }

  function sheetsHtml(r) {
    return (r.speciesPages || []).filter((id) => byId.has(id)).map((id) =>
      `<a class="season-sheet" href="especes/${escapeHTML(id)}.html">${
        escapeHTML(tr(byId.get(id).name))}</a>`).join("");
  }

  function rowHtml(r, key, info) {
    const note = noteFor(key, info);
    const limit = tr(r.limit) || tr(r.rule);
    const length = tr(r.length);
    return `<div class="season-row season-${key}">
  <div class="season-head">
    <span class="season-badge season-badge-${key}">${escapeHTML(t("season.state." + key))}</span>
    <span class="season-species">${escapeHTML(tr(r.species))}</span>
    ${zonesHtml(r)}
  </div>
  ${note ? `<p class="season-note">${escapeHTML(note)}</p>` : ""}
  ${limit ? `<p class="season-limit">${escapeHTML(t("season.limit"))} ${escapeHTML(limit)}${
      length ? ` · ${escapeHTML(t("season.length"))} ${escapeHTML(length)}` : ""}</p>` : ""}
  <div class="season-sheets">${sheetsHtml(r)}</div>
</div>`;
  }

  function render() {
    // Le garde-fou d'abord : périmé, on n'affiche AUCUN état. Pas un
    // avertissement au-dessus d'un tableau encore lisible — le tableau
    // disparaît, sinon la règle périmée reste à l'écran sous un avis.
    const stale = PMF_SEASON.monthsSince(regs.updated) > (Number(regs.staleAfterMonths) || 12);
    const official = (regs.official && regs.official.url)
      ? `<a href="${escapeHTML(regs.official.url)}" target="_blank" rel="noopener">${
          escapeHTML(t("reg.official"))}</a>`
      : "";
    if (stale) {
      root.innerHTML = `<div class="reg-stale" role="status">
  <p class="reg-stale-head">${escapeHTML(t("reg.staleTitle"))}</p>
  <p>${escapeHTML(t("reg.staleBody", { date: regs.updated }))}</p>
  <p>${official}</p>
</div>`;
      return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // La péremption de 12 mois ne suffit pas. Le 1er avril 2027, nos dates
    // 2026-2027 sont encore « fraîches » au sens du délai, mais la saison
    // qu'elles décrivent est finie : la page basculait alors TOUT dans
    // « fermé ». C'est faux — ces saisons ne sont pas fermées, c'est une
    // nouvelle année dont on n'a pas les dates. Le sens de l'erreur est le
    // moins dangereux des deux, mais une page qui se trompe reste une page
    // qui se trompe. On se tait jusqu'à ce que la réglementation suivante
    // arrive.
    const seasonEnd = PMF_SEASON.lastDateOf(frOf(regs.season));
    if (seasonEnd && today > seasonEnd) {
      const label = (frOf(regs.season).match(/\d{4}\s*[-–]\s*\d{4}/) || [""])[0]
        || tr(regs.season);
      root.innerHTML = `<div class="reg-stale" role="status">
  <p class="reg-stale-head">${escapeHTML(t("season.overTitle", { season: label }))}</p>
  <p>${escapeHTML(t("season.overBody"))}</p>
  <p>${official}</p>
</div>`;
      return;
    }

    const scored = rules.map((r) => {
      const info = PMF_SEASON.stateOf(r, today, frOf);
      return { r, key: bucket(info), info };
    });

    // Le doré porte DEUX règles en zone 8 : du 10 au 31 mai avec une limite de
    // 6, puis du 1er juin au 31 mars avec « 6 en tout ». La première est une
    // sous-période, pas une saison séparée — mais en septembre elle tombait
    // dans « fermé », et la page affichait « Doré jaune : FERMÉ » trois lignes
    // sous « Doré jaune et doré noir : OUVERT ». Un lecteur pressé y lit que
    // le doré est fermé, ce qui est faux et dangereux dans ce sens-là.
    // Une règle échue s'efface donc quand une autre garde les MÊMES espèces
    // ouvertes dans la MÊME zone. Si elle n'en couvre qu'une partie, elle
    // reste : l'information partielle compte.
    const ouvertes = new Set();
    scored.forEach(({ r, key }) => {
      if (key !== "open" && key !== "closingSoon") return;
      (r.speciesPages || []).forEach((sid) =>
        (r.zones || []).forEach((z) => ouvertes.add(sid + "@" + z)));
    });
    const visibles = scored.filter(({ r, key }) => {
      if (key !== "closed") return true;
      const paires = [];
      (r.speciesPages || []).forEach((sid) =>
        (r.zones || []).forEach((z) => paires.push(sid + "@" + z)));
      return !paires.length || !paires.every((k) => ouvertes.has(k));
    });

    const groups = new Map(SEASON_ORDER.map((k) => [k, []]));
    visibles.forEach((row) => groups.get(row.key).push(row));
    // À l'intérieur d'un groupe, le plus pressant en premier.
    groups.get("closingSoon").sort((a, b) => a.info.days - b.info.days);
    groups.get("openingSoon").sort((a, b) => a.info.days - b.info.days);

    if (preview) {
      const urgent = groups.get("closingSoon").concat(groups.get("openingSoon"));
      const pick = urgent.slice(0, preview);
      if (!pick.length) {
        root.hidden = true;
        return;
      }
      root.hidden = false;
      root.innerHTML = `<div class="season-strip">
  <p class="season-strip-lead">${escapeHTML(t("season.stripLead"))}</p>
  <div class="season-strip-rows">${pick.map(({ r, key, info }) =>
    `<span class="season-chip season-badge-${key}">${escapeHTML(tr(r.species))} — ${
      escapeHTML(noteFor(key, info))}</span>`).join("")}</div>
  <a class="cross-link" href="saison.html">${escapeHTML(t("season.stripLink"))}</a>
</div>`;
      return;
    }

    const blocks = SEASON_ORDER.map((key) => {
      const rows = groups.get(key);
      if (!rows.length) return "";
      return `<section class="season-group">
  <div class="section-head"><h2>${escapeHTML(t("season.group." + key))}</h2></div>
  <p class="tp-notes season-group-note">${escapeHTML(t("season.groupNote." + key))}</p>
  <div class="season-rows">${rows.map(({ r, key: k, info }) => rowHtml(r, k, info)).join("")}</div>
</section>`;
    }).join("");

    root.innerHTML = `<p class="reg-stamp">${
      escapeHTML(t("reg.updated", { date: regs.updated }))}</p>${blocks}
<p class="reg-note">${escapeHTML(t("season.disclaimer"))} ${official}</p>`;
  }

  PMF_I18N.onChange(render);
  render();
}
