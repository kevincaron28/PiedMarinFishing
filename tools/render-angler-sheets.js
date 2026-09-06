// Rend chaque sheet-<id>-<lang>.html en PDF Letter, plus un aperçu image.
// Le dossier de travail est celui que build-angler-sheets.py vient d'écrire :
// passe-le en argument.
//
//   node tools/render-angler-sheets.js <dossier>
//
// Les PDF finaux vont dans assets/docs/, sous le nom que les fiches web
// pointent : pro-staff-<id>-<lang>.pdf.
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const DIR = path.resolve(process.argv[2] || __dirname);
const DOCS = path.resolve(__dirname, '..', 'assets', 'docs');

(async () => {
  const files = fs.readdirSync(DIR).filter(f => /^sheet-.+-(fr|en)\.html$/.test(f)).sort();
  if (!files.length) { console.error('aucun sheet-*.html dans ' + DIR); process.exit(1); }
  fs.mkdirSync(DOCS, { recursive: true });

  const b = await chromium.launch();
  for (const f of files) {
    const m = f.match(/^sheet-(.+)-(fr|en)\.html$/);
    const [, id, lang] = m;
    const p = await (await b.newContext()).newPage();
    const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto('file://' + path.join(DIR, f), { waitUntil: 'networkidle' });
    await p.waitForTimeout(300);

    // Une fiche pro staff qui déborde se lit comme un brouillon — et .sheet
    // est en overflow:hidden, donc scrollHeight n'y montre rien : le contenu
    // en trop est simplement coupé, sans bruit. On compare donc le bas du
    // dernier bloc au haut du pied de page, ce qui voit aussi bien ce qui
    // dépasse que ce qui se fait recouvrir.
    const over = await p.evaluate(() => {
      const sheet = document.querySelector('.sheet').getBoundingClientRect();
      const last = document.querySelector('.contact').getBoundingClientRect();
      const foot = document.querySelector('.foot').getBoundingClientRect();
      return { under: Math.round(last.bottom - foot.top),
               reste: Math.round(foot.top - last.bottom),
               hauteur: Math.round(sheet.height) };
    });

    const out = path.join(DOCS, `pro-staff-${id}-${lang}.pdf`);
    await p.pdf({ path: out, format: 'Letter', printBackground: true,
                  margin: { top: '0', right: '0', bottom: '0', left: '0' } });
    await p.setViewportSize({ width: 816, height: 1056 });
    await p.screenshot({ path: path.join(DIR, `preview-${id}-${lang}.png`), fullPage: true });

    const ko = (fs.statSync(out).size / 1024).toFixed(0);
    console.log(`${id.padEnd(13)} ${lang}  ${String(ko).padStart(4)} Ko  ` +
      (over.under > 0 ? `DÉBORDE de ${over.under}px` : `ok, ${over.reste}px de marge`) +
      (errs.length ? `  erreurs: ${errs}` : ''));
    await p.context().close();
  }
  await b.close();
})();
