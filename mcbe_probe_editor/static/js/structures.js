(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);
  let rows = [];

  function fvTag(v) {
    if (v === 2) return '<span class="tag warn">2</span>';
    if (v === 1) return '<span class="tag item">1</span>';
    return '<span class="tag">' + esc(v == null ? "?" : v) + "</span>";
  }

  function render() {
    const tbody = $("#st-table tbody");
    tbody.innerHTML = rows.map((r, i) => {
      const size = r.size && r.size.join ? r.size.join("×") : "-";
      const op = r.format_version === 2
        ? `<button class="btn small primary" data-dg="${i}">${esc(t("struct.downgrade", "降版本"))}</button>`
        : `<span class="muted small">${esc(t("struct.noNeed", "无需处理"))}</span>`;
      const err = r.error ? ` <span class="tag warn">${esc(r.error)}</span>` : "";
      return `<tr>
        <td>${esc(r.pack)}</td>
        <td><code>${esc(r.path)}</code>${err}</td>
        <td>${fvTag(r.format_version)}</td>
        <td class="muted">${esc(size)}</td>
        <td>${r.layers == null ? "-" : r.layers}</td>
        <td>${r.palette == null ? "-" : r.palette}</td>
        <td>${r.void_cells == null ? "-" : r.void_cells}</td>
        <td>${op}</td>
      </tr>`;
    }).join("") || `<tr><td colspan="8" class="muted">${esc(t("struct.none", "没有结构文件"))}</td></tr>`;

    tbody.querySelectorAll("[data-dg]").forEach((btn) => {
      btn.onclick = () => doDowngrade([rows[parseInt(btn.dataset.dg, 10)]]);
    });
    const need = rows.filter((r) => r.format_version === 2).length;
    $("#st-count").textContent =
      tf("struct.count", { n: rows.length, k: need }, "");
  }

  async function load() {
    try {
      const r = await api(base + "/structures");
      rows = r.structures || [];
      render();
    } catch (e) { toast(e.message, true); }
  }

  async function doDowngrade(list) {
    const backup = $("#st-backup").checked;
    const targets = list.filter((r) => r.format_version === 2);
    if (!targets.length) { toast(t("struct.nothing", "没有需要转换的文件")); return; }
    if (!confirm(tf("struct.confirm", { n: targets.length }, ""))) return;

    for (const tgt of targets) {
      try {
        const r = await api(base + "/structure/downgrade", {
          method: "POST",
          body: { pack: tgt.pack, path: tgt.path, backup },
        });
        const res = (r.results || [])[0] || {};
        if (res.skipped) toast(tf("struct.skipped", { p: tgt.path }));
        else if (res.ok) toast(tf("struct.ok", { p: tgt.path }));
        else toast(tf("struct.fail", { p: tgt.path, e: res.error || "" }), true);
      } catch (e) { toast(e.message, true); }
    }
    await load();
  }

  $("#st-refresh").onclick = load;
  $("#st-all").onclick = () => doDowngrade(rows);
  load();
})();