// Pied Marin Fishing — le moteur de saison, verifie sans navigateur
//
// assets/js/season.js decide si une espece s'affiche comme OUVERTE. C'est la
// seule affirmation legale que le site produise par calcul, et la seule qui
// puisse nuire a quelqu'un si elle se trompe. Elle merite donc un controle
// qu'on peut rejouer en une seconde, sans lancer Chromium.
//
// Ce qui est verifie ici, et pourquoi :
//   - les periodes qui NE DOIVENT PAS s'analyser (annee absente, date
//     impossible, bornes inversees) tombent bien dans « on ne sait pas »;
//   - les bascules a la veille, au jour meme et au lendemain de chaque
//     ouverture et de chaque fermeture;
//   - le brochet, dont la fermeture est inconnue, ne dit JAMAIS « ouvert »,
//     a aucune date, jamais;
//   - « peche interdite » l'emporte sur n'importe quelle periode.
//
//     node tools/test-season.js     # sort en code 1 au premier echec

const fs = require('fs');
const src = fs.readFileSync(require('path').join(__dirname, '..', 'assets', 'js', 'season.js'), 'utf8');
// On n'exécute que la partie PMF_SEASON (le reste dépend de PMF_I18N).
const engine = src.slice(0, src.indexOf('// L’ordre de lecture'));
eval(engine.replace('const PMF_SEASON', 'globalThis.PMF_SEASON'));

const fr = (v) => (v && typeof v === 'object' ? v.fr || v.en : v) || '';
const D = (s) => { const d = new Date(s + 'T00:00:00'); d.setHours(0,0,0,0); return d; };
let pass = 0, fail = 0;
function eq(label, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (ok) pass++; else { fail++; console.log('  ECHEC', label, '\n    obtenu', JSON.stringify(got), '\n    attendu', JSON.stringify(want)); }
}

console.log('--- analyse des periodes ---');
const cases = [
  ['15 juin 2026 au 19 décembre 2026', 'range', '2026-06-15', '2026-12-19'],
  ['1er juin 2026 au 31 mars 2027',    'range', '2026-06-01', '2027-03-31'],
  ['1er avril 2026 au 31 mars 2027',   'range', '2026-04-01', '2027-03-31'],
  ['10 mai 2026 au 31 mai 2026',       'range', '2026-05-10', '2026-05-31'],
  ['Ouverture le 1er mai 2026',        'openingOnly', '2026-05-01', null],
  ['Ouverture le 15 mai 2026',         'openingOnly', '2026-05-15', null],
  // ce qui DOIT tomber dans « on ne sait pas »
  ['20 décembre au 31 mars',           'unknown', null, null],   // pas d'annee
  ['du 3e vendredi de mai au 31 mars 2027', 'unknown', null, null],
  ['31 février 2026 au 1er mars 2026', 'unknown', null, null],   // date impossible
  ['31 mars 2027 au 1er avril 2026',   'unknown', null, null],   // bornes inversees
  ['',                                 'unknown', null, null],
  ['à confirmer',                      'unknown', null, null],
  ['15 juin 2026',                     'unknown', null, null],   // une seule borne, pas « ouverture »
];
const isoOf = (d) => d ? d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0') : null;
for (const [text, kind, from, to] of cases) {
  const p = PMF_SEASON.parsePeriod(text);
  eq(text || '(vide)', [p.kind, isoOf(p.from), isoOf(p.to)], [kind, from, to]);
}

console.log('--- bascules : la veille, le jour, le lendemain ---');
const maski = { period: { fr: '15 juin 2026 au 19 décembre 2026' }, limit: { fr: '1 en tout' } };
for (const [day, want] of [['2026-06-14','soon'],['2026-06-15','open'],['2026-06-16','open'],
                           ['2026-12-18','open'],['2026-12-19','open'],['2026-12-20','closed']]) {
  eq('maskinonge ' + day, PMF_SEASON.stateOf(maski, D(day), fr).state, want);
}
eq('maskinonge 2026-12-19 jours restants', PMF_SEASON.stateOf(maski, D('2026-12-19'), fr).days, 0);
eq('maskinonge 2026-06-14 jours avant',    PMF_SEASON.stateOf(maski, D('2026-06-14'), fr).days, 1);

console.log('--- le brochet ne doit JAMAIS dire « ouvert » ---');
const brochet = { period: { fr: 'Ouverture le 1er mai 2026' }, limit: { fr: '6 en tout' } };
for (const day of ['2026-04-30','2026-05-01','2026-09-10','2027-03-31','2028-01-01']) {
  eq('brochet ' + day, PMF_SEASON.stateOf(brochet, D(day), fr).state, 'unknown');
}

console.log('--- interdit l\'emporte sur la periode ---');
const bar = { period: { fr: '1er avril 2026 au 31 mars 2027' }, limit: { fr: 'Pêche interdite' } };
eq('bar raye en pleine periode', PMF_SEASON.stateOf(bar, D('2026-09-10'), fr).state, 'banned');
const chev = { period: { fr: '1er avril 2026 au 31 mars 2027' }, rule: { fr: 'Pêche interdite' } };
eq('interdit via rule', PMF_SEASON.stateOf(chev, D('2026-09-10'), fr).state, 'banned');

console.log('--- une periode illisible ne devient pas « ouvert » ---');
eq('periode vide', PMF_SEASON.stateOf({ limit: { fr: '6' } }, D('2026-09-10'), fr).state, 'unknown');
eq('periode floue', PMF_SEASON.stateOf({ period: { fr: 'toute l\'année' }, limit: { fr: '6' } }, D('2026-09-10'), fr).state, 'unknown');

console.log('\n' + pass + ' verifications passees, ' + fail + ' echec(s)');
process.exit(fail ? 1 : 0);
