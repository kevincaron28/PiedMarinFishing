// Pied Marin Fishing — la relève
//
// Les enfants de l'équipe sont mineurs : cette section les nomme par leur
// prénom seulement, sans âge, sans date de naissance, sans nom de famille et
// sans photo. C'est délibéré, et c'est la raison pour laquelle ils vivent ici
// plutôt que dans data/team-members.json — le reste du site génère une fiche
// publique et un JSON-LD Person pour chaque membre de ce fichier-là, et aucun
// enfant n'a besoin de ça.
//
// Une entrée sans prénom est normale : la relation ("Fille de Kevin B.") sert
// alors de titre, ce qui laisse ajouter les prochains sans rien dévoiler.

async function initNextGen(sectionSelector, listSelector) {
  const section = document.querySelector(sectionSelector);
  const list = document.querySelector(listSelector);
  if (!section || !list) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  let kids = [];
  let catches = [];
  try {
    [kids, catches] = await Promise.all([
      fetch("data/next-gen.json", DATA_FETCH).then((r) => r.json()),
      typeof PMF_CATCHES !== "undefined" ? PMF_CATCHES.load() : Promise.resolve([]),
    ]);
  } catch (e) {
    kids = [];
  }

  // Section vide, section absente : comme partout ailleurs sur le site.
  if (!Array.isArray(kids) || !kids.length) {
    section.hidden = true;
    return;
  }

  const catchById = new Map(catches.map((c) => [c.id, c]));

  function render() {
    const lang = PMF_I18N.lang;

    list.innerHTML = kids.map((k) => {
      const name = tr(k.name);
      const relation = tr(k.relation);
      const title = name || relation;
      if (!title) return "";

      // Un prénom donne son initiale; une entrée encore anonyme garde la
      // pousse, qui dit « ça s'en vient » sans rien révéler.
      const badge = name
        ? `<span class="nextgen-initial">${escapeHTML(name.slice(0, 1).toUpperCase())}</span>`
        : `<span class="nextgen-initial nextgen-sprout" aria-hidden="true">🌱</span>`;

      // Le lien vers le parent est le seul lien de la carte : l'enfant, lui,
      // n'a pas de page.
      const parent = k.parent
        ? `<a class="nextgen-parent" href="pecheurs/${encodeURIComponent(k.parent)}.html">${escapeHTML(relation)}</a>`
        : (relation ? `<span class="nextgen-parent">${escapeHTML(relation)}</span>` : "");

      const status = k.status ? t(`team.nextGen.status.${k.status}`) : "";

      // La première prise se lit dans data/catches.json plutôt que d'être
      // recopiée ici : l'espèce et le mois ne peuvent pas dériver. On s'en
      // tient au mois — le jour exact d'un enfant ne regarde personne.
      const first = k.catch ? catchById.get(k.catch) : null;
      const firstLine = first
        ? `<p class="nextgen-first"><b>${escapeHTML(t("team.nextGen.firstCatch"))}</b> ${
            escapeHTML([tr(first.species), longDate((first.date || "").slice(0, 7), lang)]
              .filter(Boolean).join(" — "))}</p>`
        : "";

      return `
        <article class="nextgen-card">
          <div class="nextgen-badge">${badge}</div>
          <div class="nextgen-body">
            ${status ? `<span class="nextgen-status">${escapeHTML(status)}</span>` : ""}
            <h3>${escapeHTML(title)}</h3>
            ${name && relation ? parent : ""}
            ${tr(k.story) ? `<p class="nextgen-story">${escapeHTML(tr(k.story))}</p>` : ""}
            ${firstLine}
          </div>
        </article>`;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
