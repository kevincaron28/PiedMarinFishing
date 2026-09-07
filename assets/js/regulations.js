// Pied Marin Fishing — réglementation par zone
//
// CE QUE CE FICHIER PROTÈGE.
//
// Une page de réglementation est le seul contenu du site qui peut coûter une
// amende à quelqu'un. Elle porte donc deux garde-fous plutôt qu'un.
//
// 1. LA DATE EST AFFICHÉE, TOUJOURS. Le visiteur voit quand le tableau a été
//    mis à jour et juge lui-même de sa fraîcheur. C'est la demande de départ,
//    et elle est juste : une information datée est honnête.
//
// 2. LE TABLEAU S'EFFACE TOUT SEUL QUAND IL VIEILLIT. « Je vais la mettre à
//    jour chaque année » est une promesse; une promesse tenue par un humain
//    occupé n'est pas un mécanisme. Passé staleAfterMonths, le tableau
//    disparaît et cède la place à un avertissement et au lien officiel. On
//    préfère ne rien afficher plutôt qu'une règle périmée — la page ne peut
//    donc pas mentir même si personne n'y touche pendant trois ans.
//
// Le tableau ne remplace jamais la réglementation officielle et ne prétend
// pas être complet : il ne porte que les règles vérifiées dans une source
// gouvernementale, pour les zones qu'on pêche.

async function initRegulations(rootSelector) {
  const root = document.querySelector(rootSelector);
  if (!root) return;

  await PMF_I18N.ready;
  // t() lit une clé d'interface (avec interpolation de {date}),
  // tr() une valeur venue d'un fichier de données. Les deux ne sont pas
  // interchangeables : tr("reg.updated") rendait la clé elle-même à l'écran.
  const { t, tr } = PMF_I18N;

  let data = null;
  try {
    data = await (await fetch("data/regulations.json", DATA_FETCH)).json();
  } catch (e) {
    data = null;
  }
  // Les fiches d'espèce ne sont générées que si elles franchissent leur seuil.
  // Sans cet index, le lien « en savoir plus » pointerait vers un 404 dès
  // qu'une règle nomme une espèce dont la fiche n'existe pas encore.
  let pages = [];
  try {
    pages = await (await fetch("data/species-pages.json", DATA_FETCH)).json();
  } catch (e) {
    pages = [];
  }
  if (!Array.isArray(pages)) pages = [];
  // Le même registre de citations que les fiches d'espèce. Une règle affichée
  // sans sa source demanderait au lecteur de nous croire sur parole — sur une
  // page qui peut lui coûter une amende, ça ne suffit pas.
  let sources = {};
  try {
    const list = await (await fetch("data/sources.json", DATA_FETCH)).json();
    (Array.isArray(list) ? list : []).forEach((x) => { if (x && x.id) sources[x.id] = x; });
  } catch (e) {
    sources = {};
  }

  function citation(id) {
    const src = sources[id];
    if (!src || !src.verified) return "";
    // Titre et éditeur seulement. Le nom complet du ministère fait 104
    // caractères : répété sous chaque règle, il noyait la règle elle-même.
    // La citation complète vit dans data/sources.json et sur les fiches
    // d'espèce, où elle a la place de s'écrire au long.
    const title = tr(src.title);
    if (!title) return "";
    const pub = tr(src.publisher);
    const text = t("reg.source") + " " + title + (pub ? ", " + pub : "") + ".";
    return src.url
      ? `<p class="reg-src"><a href="${escapeHTML(src.url)}" target="_blank" rel="noopener">${
          escapeHTML(text)}</a></p>`
      : `<p class="reg-src">${escapeHTML(text)}</p>`;
  }
  const rules = (data && Array.isArray(data.rules)) ? data.rules : [];
  // Une règle non vérifiée n'existe pas — même discipline que les fiches
  // d'espèce. Ici l'enjeu n'est plus la crédibilité, c'est une amende.
  // Deux conditions, comme claim_ok() pour les fiches d'espèce : la règle est
  // vérifiée, ET la source qu'elle cite l'est aussi. Vérifier une règle contre
  // un document dont personne n'a confirmé l'existence ne vérifie rien.
  const shown = rules.filter((r) =>
    r && r.verified && tr(r.rule) && r.source &&
    sources[r.source] && sources[r.source].verified);

  function monthsSince(iso) {
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return Infinity;
    const now = new Date();
    return (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth());
  }

  function longDate(iso) {
    const d = new Date(iso + "T00:00:00");
    if (isNaN(d)) return iso;
    return d.toLocaleDateString(PMF_I18N.lang === "en" ? "en-CA" : "fr-CA",
      { year: "numeric", month: "long", day: "numeric" });
  }

  function zoneLabel(id) {
    const z = ((data && data.zones) || []).find((x) => x.id === id);
    return z ? tr(z.name) : id;
  }

  function officialLink(label) {
    const o = (data && data.official) || {};
    if (!o.url) return escapeHTML(label);
    return `<a href="${escapeHTML(o.url)}" target="_blank" rel="noopener">${escapeHTML(label)}</a>`;
  }

  function render() {
    if (!shown.length) {
      root.innerHTML = `<p class="reg-empty">${escapeHTML(t("reg.empty"))} ${
        officialLink(t("reg.official"))}</p>`;
      return;
    }

    const age = monthsSince(data.updated);
    const limit = Number(data.staleAfterMonths) || 12;
    const stamp = t("reg.updated", { date: longDate(data.updated) });

    if (age > limit) {
      root.innerHTML =
        `<div class="reg-stale" role="status">` +
        `<p class="reg-stale-head">${escapeHTML(t("reg.staleTitle"))}</p>` +
        `<p>${escapeHTML(t("reg.staleBody", { date: longDate(data.updated) }))}</p>` +
        `<p>${officialLink(t("reg.official"))}</p>` +
        `</div>`;
      return;
    }

    const rows = shown.map((r) => {
      const zones = (r.zones || []).map(zoneLabel).join(", ");
      const detail = tr(r.detail);
      const link = (r.species_page && pages.indexOf(r.species_page) !== -1)
        ? `<a class="reg-more" href="especes/${escapeHTML(r.species_page)}.html">${
            escapeHTML(t("reg.readMore"))}</a>`
        : "";
      return `<div class="reg-row">
  <div class="reg-zone">${escapeHTML(zones)}</div>
  <div class="reg-body">
    <p class="reg-species">${escapeHTML(tr(r.species))}</p>
    <p class="reg-rule">${escapeHTML(tr(r.rule))}</p>
    ${detail ? `<p class="reg-detail">${escapeHTML(detail)}</p>` : ""}
    ${citation(r.source)}
    ${link}
  </div>
</div>`;
    }).join("");

    root.innerHTML =
      `<p class="reg-stamp">${escapeHTML(stamp)}</p>` +
      `<div class="reg-list">${rows}</div>` +
      `<p class="reg-note">${escapeHTML(t("reg.disclaimer"))} ${
        officialLink(t("reg.official"))}</p>`;
  }

  PMF_I18N.onChange(render);
  render();
}
