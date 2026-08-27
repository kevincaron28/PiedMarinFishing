const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const lang of ['fr','en']) {
    const p = await (await b.newContext()).newPage();
    const errs=[]; p.on('pageerror',e=>errs.push(e.message));
    await p.goto('file://' + __dirname + `/kit-${lang}.html`, { waitUntil: 'networkidle' });
    await p.waitForTimeout(500);
    await p.pdf({ path: `${lang}.pdf`, format: 'Letter', printBackground: true,
                  margin: {top:'0',right:'0',bottom:'0',left:'0'} });
    // aperçu image pour vérification visuelle
    await p.setViewportSize({ width: 816, height: 1056 });
    await p.screenshot({ path: `preview-${lang}.png`, fullPage: true });
    console.log(`${lang} : pdf rendu, erreurs: ${errs.length?errs:'aucune'}`);
    await p.context().close();
  }
  await b.close();
})();
