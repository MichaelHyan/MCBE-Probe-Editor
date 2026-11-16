/* 前端 i18n 运行时：字典由服务端注入到 window.I18N_DICT */
(function () {
  const DICT = window.I18N_DICT || {};

  window.t = function (key, fallback) {
    if (DICT && Object.prototype.hasOwnProperty.call(DICT, key)) {
      return DICT[key];
    }
    return fallback != null ? fallback : key;
  };

  window.tf = function (key, vars, fallback) {
    let s = window.t(key, fallback);
    if (vars && typeof s === "string") {
      Object.keys(vars).forEach((k) => {
        s = s.split("{" + k + "}").join(String(vars[k]));
      });
    }
    return s;
  };

  window.applyI18n = function (root) {
    root = root || document;

    root.querySelectorAll("[data-i18n]").forEach((el) => {
      const v = window.t(el.getAttribute("data-i18n"), null);
      if (v != null) el.textContent = v;
    });
    root.querySelectorAll("[data-i18n-ph]").forEach((el) => {
      const v = window.t(el.getAttribute("data-i18n-ph"), null);
      if (v != null) el.setAttribute("placeholder", v);
    });
    root.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const v = window.t(el.getAttribute("data-i18n-title"), null);
      if (v != null) el.setAttribute("title", v);
    });
  };

  // 语言切换器
  async function switchLang(lang) {
    try {
      await fetch("/api/ui-lang", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lang }),
      });
      location.reload();
    } catch (e) {
      location.reload();
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    window.applyI18n(document);
    const sel = document.getElementById("ui-lang-select");
    if (sel) sel.onchange = () => switchLang(sel.value);
  });
})();