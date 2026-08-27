// Pied Marin Fishing — merchandise
// There is no checkout here on purpose: a product either links out to a real
// store, or falls back to an email order link. Nothing pretends to take money.

async function initMerch(selector) {
  const host = document.querySelector(selector);
  if (!host) return;

  await PMF_I18N.ready;
  const { t, tr } = PMF_I18N;

  let data = {};
  try {
    data = await (await fetch("data/merch.json")).json();
  } catch (e) {
    host.innerHTML = `<div class="empty-state">${escapeHTML(t("merch.loadError"))}</div>`;
    return;
  }

  const products = Array.isArray(data.products) ? data.products : [];

  const STATUS_KEYS = {
    available: "merch.available",
    soon: "merch.soon",
    soldout: "merch.soldOut",
  };

  function statusBadge(status) {
    const key = STATUS_KEYS[status] || STATUS_KEYS.soon;
    const tone = status === "available" ? "" : status === "soldout" ? " navy" : " gold";
    return `<span class="badge${tone}">${escapeHTML(t(key))}</span>`;
  }

  function callToAction(p) {
    // Seul un produit réellement disponible se commande.
    if (p.status !== "available") return "";
    // A product's own link wins; then a shop-wide store; then email.
    const href = p.url || data.storeUrl || "";
    if (href) {
      return `<a class="btn btn-teal" href="${escapeHTML(href)}" target="_blank" rel="noopener">${escapeHTML(t("merch.order"))}</a>`;
    }
    if (data.orderEmail) {
      const subject = encodeURIComponent(`${t("merch.emailSubject")} — ${tr(p.name)}`);
      return `<a class="btn btn-teal" href="mailto:${escapeHTML(data.orderEmail)}?subject=${subject}">${escapeHTML(t("merch.orderEmail"))}</a>`;
    }
    return "";
  }

  function render() {
    if (!products.length) {
      host.innerHTML = `<div class="empty-state">${escapeHTML(t("merch.empty"))}</div>`;
      return;
    }

    host.innerHTML = products.map((p) => {
      const name = tr(p.name) || "—";
      const price = tr(p.price);
      const sizes = Array.isArray(p.sizes) && p.sizes.length
        ? `<div class="merch-sizes">${p.sizes.map((s) => `<span>${escapeHTML(s)}</span>`).join("")}</div>`
        : "";
      const photo = p.image
        ? `<img src="${escapeHTML(p.image)}" alt="${escapeHTML(t("merch.photoAlt", { name }))}" class="merch-photo-img">`
        : "";

      return `
        <article class="merch-card">
          <div class="merch-photo">${photo}</div>
          <div class="merch-body">
            <div class="merch-head">
              <h3>${escapeHTML(name)}</h3>
              ${statusBadge(p.status)}
            </div>
            <div class="merch-price">${price ? escapeHTML(price) : escapeHTML(t("merch.priceTBD"))}</div>
            <p>${escapeHTML(tr(p.description))}</p>
            ${sizes}
            ${callToAction(p)}
          </div>
        </article>
      `;
    }).join("");
  }

  PMF_I18N.onChange(render);
  render();
}
