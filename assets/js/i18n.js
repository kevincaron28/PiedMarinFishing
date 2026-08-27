// Pied Marin Fishing — bilingual (FR/EN) engine
// French is the default; the visitor's choice is remembered in localStorage.

const PMF_I18N = (() => {
  const SUPPORTED = ["fr", "en"];
  const DEFAULT_LANG = "fr";
  const STORAGE_KEY = "pmf-lang";

  let strings = {};
  let lang = DEFAULT_LANG;
  const listeners = [];

  function readStoredLang() {
    // Explicit ?lang= wins (useful for sharing a link in one language),
    // then a previously remembered choice, then French.
    try {
      const fromUrl = new URLSearchParams(location.search).get("lang");
      if (SUPPORTED.includes(fromUrl)) return fromUrl;
    } catch (e) { /* ignore */ }
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (SUPPORTED.includes(stored)) return stored;
    } catch (e) { /* localStorage can throw in private mode */ }
    return DEFAULT_LANG;
  }

  function persistLang(value) {
    try { localStorage.setItem(STORAGE_KEY, value); } catch (e) { /* ignore */ }
  }

  function interpolate(str, vars) {
    if (!vars) return str;
    return str.replace(/\{(\w+)\}/g, (match, name) =>
      Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : match
    );
  }

  // Look up a UI string by key, falling back across languages then to the key.
  function t(key, vars) {
    const table = strings[lang] || {};
    const fallback = strings[DEFAULT_LANG] || {};
    const raw = table[key] != null ? table[key] : fallback[key];
    if (raw == null) return key;
    return interpolate(raw, vars);
  }

  // Plural helper: French treats 0 and 1 as singular, English only 1.
  function plural(baseKey, n) {
    const isOne = lang === "fr" ? n < 2 : n === 1;
    return t(`${baseKey}.${isOne ? "one" : "other"}`, { n });
  }

  // Translate a value coming from a data file. Accepts either a plain string
  // (same in both languages) or an object like { fr: "…", en: "…" }.
  function tr(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    return value[lang] || value[DEFAULT_LANG] || value.en || "";
  }

  // Every translation of a data value, for language-agnostic searching.
  function trAll(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    return Object.values(value).filter((v) => typeof v === "string").join(" ");
  }

  // A stable identifier for a data value, so filter <option> values survive a
  // language switch. Always keyed off the French text.
  function key(value) {
    if (value == null) return "";
    if (typeof value === "string") return value;
    return value[DEFAULT_LANG] || value.en || "";
  }

  function applyTo(root) {
    const scope = root || document;

    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      el.innerHTML = t(el.getAttribute("data-i18n"), { year: new Date().getFullYear() });
    });
    scope.querySelectorAll("[data-i18n-text]").forEach((el) => {
      el.textContent = t(el.getAttribute("data-i18n-text"));
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
    });
    scope.querySelectorAll("[data-i18n-content]").forEach((el) => {
      el.setAttribute("content", t(el.getAttribute("data-i18n-content")));
    });
    // La trousse de commandite existe en deux versions : le lien lui-même change.
    scope.querySelectorAll("[data-i18n-href]").forEach((el) => {
      el.setAttribute("href", t(el.getAttribute("data-i18n-href")));
    });
    scope.querySelectorAll("[data-i18n-alt]").forEach((el) => {
      el.setAttribute("alt", t(el.getAttribute("data-i18n-alt")));
    });
    scope.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria-label")));
    });
  }

  function syncSwitcher() {
    document.querySelectorAll(".lang-switch [data-lang]").forEach((btn) => {
      const isActive = btn.getAttribute("data-lang") === lang;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-pressed", String(isActive));
    });
  }

  function apply() {
    document.documentElement.lang = lang;
    applyTo(document);
    syncSwitcher();
    listeners.forEach((fn) => {
      try { fn(lang); } catch (e) { console.error(e); }
    });
  }

  function setLang(value) {
    if (!SUPPORTED.includes(value) || value === lang) return;
    lang = value;
    persistLang(value);
    apply();
  }

  function bindSwitcher() {
    document.querySelectorAll(".lang-switch [data-lang]").forEach((btn) => {
      btn.addEventListener("click", () => setLang(btn.getAttribute("data-lang")));
    });
  }

  const ready = fetch("data/i18n.json")
    .then((r) => r.json())
    .then((data) => {
      strings = data;
      lang = readStoredLang();
      apply();
    })
    .catch((err) => {
      // Markup ships with French copy inline, so a failure here degrades to French.
      console.error("i18n load failed:", err);
    })
    .finally(() => {
      bindSwitcher();
      syncSwitcher();
    });

  return {
    ready,
    t,
    tr,
    trAll,
    plural,
    key,
    setLang,
    onChange: (fn) => listeners.push(fn),
    get lang() { return lang; },
  };
})();
