// Rend kit-fr.html et kit-en.html en PDF Letter, plus un aperçu image.
// Le dossier de travail est celui que build-sponsor-kit.py vient d'écrire :
// passe-le en argument, sinon on prend celui du script.
//
//   node tools/render-sponsor-kit.js <dossier>
const path = require('path');
const { chromium } = require('playwright');

const DIR = path.resolve(process.argv[2] || __dirname);

(async () => {
  const b = await chromium.launch();
  for (const lang of ['fr', 'en']) {
    const p = await (await b.newContext()).newPage();
    const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto('file://' + path.join(DIR, `kit-${lang}.html`), { waitUntil: 'networkidle' });
    await p.waitForTimeout(500);
    await p.pdf({ path: path.join(DIR, `${lang}.pdf`), format: 'Letter', printBackground: true,
                  margin: { top: '0', right: '0', bottom: '0', left: '0' } });
    // aperçu image pour vérification visuelle
    await p.setViewportSize({ width: 816, height: 1056 });
    await p.screenshot({ path: path.join(DIR, `preview-${lang}.png`), fullPage: true });
    console.log(`${lang} : pdf rendu dans ${DIR}, erreurs: ${errs.length ? errs : 'aucune'}`);
    await p.context().close();
  }
  await b.close();
})();
