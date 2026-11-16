(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);

  let packs = {};
  let activePack = "behavior";

  function renderStatus(res) {
    const box = $("#mf-status");
    const errs = res.errors || [];
    const warns = res.warnings || [];
    let html = "";
    if (!res.exists) {
      html += `<div class="warn-box">${esc(t("mf.notFound", "该包暂无 manifest.json"))}</div>`;
    }
    if (errs.length) {
      html += `<div class="warn-box">${errs.map((e) => "✖ " + esc(e)).join("<br>")}</div>`;
    }
    if (warns.length) {
      html += `<div class="warn-box">${warns.map((w) => "⚠ " + esc(w)).join("<br>")}</div>`;
    }
    if (!errs.length && res.exists) {
      html += `<p class="muted small">${esc(t("mf.valid", "校验通过"))}</p>`;
    }
    box.innerHTML = html;
  }

  function render() {
    const res = packs[activePack] || {};
    $("#mf-editor").value = res.data
      ? JSON.stringify(res.data, null, 2)
      : "";
    renderStatus(res);
    document.querySelectorAll("[data-pack]").forEach((b) => {
      b.className = b.dataset.pack === activePack
        ? "btn small primary" : "btn small ghost";
    });
  }

  async function load() {
    try {
      const r = await api(base + "/manifest");
      packs = r.packs || {};
      render();
    } catch (e) { toast(e.message, true); }
  }

  document.querySelectorAll("[data-pack]").forEach((btn) => {
    btn.onclick = () => { activePack = btn.dataset.pack; render(); };
  });

  $("#mf-validate").onclick = async () => {
    let data;
    try { data = JSON.parse($("#mf-editor").value); }
    catch (e) { toast(t("editor.jsonError", "JSON 格式错误"), true); return; }
    try {
      const r = await api(base + "/manifest/validate", {
        method: "POST", body: { data },
      });
      packs[activePack] = Object.assign({}, packs[activePack], {
        data, exists: true,
        errors: r.errors || [], warnings: r.warnings || [],
      });
      renderStatus(packs[activePack]);
      toast(r.ok ? t("mf.valid", "校验通过") : t("mf.invalid", "校验未通过"),
            !r.ok);
    } catch (e) { toast(e.message, true); }
  };

  $("#mf-save").onclick = async () => {
    let data;
    try { data = JSON.parse($("#mf-editor").value); }
    catch (e) { toast(t("editor.jsonError", "JSON 格式错误"), true); return; }
    try {
      await api(base + "/manifest", {
        method: "POST", body: { pack: activePack, data },
      });
      toast(t("common.saveOk", "已保存"));
      await load();
    } catch (e) { toast(e.message, true); }
  };

  $("#mf-template").onclick = async () => {
    try {
      const r = await api(base + "/manifest/template", {
        method: "POST", body: { pack: activePack },
      });
      $("#mf-editor").value = JSON.stringify(r.data, null, 2);
      toast(t("mf.templateReady", "已生成模板，保存后生效"));
    } catch (e) { toast(e.message, true); }
  };

  load();
})();