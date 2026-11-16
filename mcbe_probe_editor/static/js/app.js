/* 通用工具 */
(function () {
  const toastEl = document.getElementById("toast");

  window.toast = function (msg, isError) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.toggle("error", !!isError);
    toastEl.classList.add("show");
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => {
      toastEl.classList.remove("show");
    }, 2600);
  };

  window.api = async function (url, options) {
    const opts = Object.assign({ headers: {} }, options || {});
    const isForm = (typeof FormData !== "undefined") && (opts.body instanceof FormData);
    if (opts.body && !isForm && typeof opts.body !== "string") {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(url, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok || (data && data.ok === false)) {
      const msg = (data && data.error) ||
        ((window.t ? window.t("common.failed", "请求失败") : "请求失败") + ": " + res.status);
      throw new Error(msg);
    }
    return data;
  };

  window.esc = function (s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  };

  // 通用文本截断（用于超长组件值）
  window.shortText = function (v, max) {
    max = max || 220;
    const s = (typeof v === "string") ? v : JSON.stringify(v);
    if (s == null) return "";
    return s.length > max ? s.slice(0, max) + "…" : s;
  };
})();