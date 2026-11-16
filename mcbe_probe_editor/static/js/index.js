(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);

  const tbody = $("#obj-table tbody");
  let allObjects = [];

  function renderStats(stats) {
    const box = $("#stats");
    if (!stats) { box.innerHTML = ""; return; }
    const kinds = stats.kinds || {};
    const parts = [
      [t("index.stat.objects", "对象"), stats.objects || 0],
      [t("index.stat.refs", "引用"), stats.references || 0],
      [t("index.stat.warnings", "警告"), stats.warnings || 0],
      [t("index.stat.special", "特殊文件"),
       (stats.special_files != null ? stats.special_files : (stats.__special || 0))],
    ];
    Object.keys(kinds).forEach((k) => parts.push([k, kinds[k]]));
    box.innerHTML = parts.map(([k, v]) =>
      `<div class="stat"><span class="v">${v}</span><span class="k">${esc(k)}</span></div>`
    ).join("");
  }

  function renderRows(rows) {
    tbody.innerHTML = rows.map((r) => {
      const kinds = (r.kinds || [r.kind]).join(",");
      const warn = r.warnings && r.warnings.length
        ? `<span class="tag warn">${r.warnings.length}</span>` : "";
      const primary = r.primary
        ? `<code>${esc(r.primary.pack)}/${esc(r.primary.path)}</code>`
        : `<span class="muted">${esc(t("common.missing", "缺失"))}</span>`;
      const fv = r.primary && r.primary.format_version
        ? `<span class="muted small">${esc(r.primary.format_version)}</span>` : "";
      const lang = r.lang_name
        ? `<br><span class="muted small">${esc(r.lang_name)}</span>` : "";
      return `<tr>
        <td><span class="tag ${esc(r.kind)}">${esc(kinds)}</span></td>
        <td><a href="/project/${encodeURIComponent(PID)}/object/${encodeURIComponent(r.identifier)}">${esc(r.identifier)}</a>${lang}</td>
        <td>${primary}<br>${fv}</td>
        <td>${r.ref_count}</td>
        <td>${warn}</td>
      </tr>`;
    }).join("");
    $("#obj-count").textContent =
      tf("index.shown", { a: rows.length, b: allObjects.length }, "");
  }

  function applyFilter() {
    const q = $("#flt-q").value.trim().toLowerCase();
    const kind = $("#flt-kind").value;
    const ns = $("#flt-ns").value;
    const rows = allObjects.filter((r) => {
      if (kind && r.kind !== kind) return false;
      if (ns && r.namespace !== ns) return false;
      if (q) {
        const hay = [r.identifier, r.name, r.lang_name, r.lang_text]
          .filter(Boolean).join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    renderRows(rows);
  }

  async function load() {
    try {
      const [idx, objs] = await Promise.all([
        api(base + "/index"),
        api(base + "/objects"),
      ]);
      const stats = Object.assign({}, idx.stats || {});
      if (stats.special_files == null) {
        stats.special_files = (idx.special_files || []).length;
      }
      renderStats(stats);
      allObjects = objs.objects;

      const kindSel = $("#flt-kind");
      objs.kinds.forEach((k) => {
        const o = document.createElement("option");
        o.value = k; o.textContent = k; kindSel.appendChild(o);
      });
      const nsSel = $("#flt-ns");
      objs.namespaces.forEach((n) => {
        if (!n) return;
        const o = document.createElement("option");
        o.value = n; o.textContent = n; nsSel.appendChild(o);
      });
      renderRows(allObjects);
    } catch (e) { toast(e.message, true); }
  }

  $("#flt-q").oninput = applyFilter;
  $("#flt-kind").onchange = applyFilter;
  $("#flt-ns").onchange = applyFilter;

  $("#btn-probe").onclick = async () => {
    try {
      toast(t("index.reprobing", "重新探测…"));
      const r = await api(base + "/probe", { method: "POST" });
      toast(tf("projects.done", { n: r.stats.objects }, "完成"));
      location.reload();
    } catch (e) { toast(e.message, true); }
  };

  // ---------------- 导出 ----------------
  const modal = $("#export-modal");

  $("#btn-export").onclick = () => {
    if (!modal) { toast("export modal missing", true); return; }
    modal.classList.remove("hidden");
  };
  $("#export-cancel").onclick = () => modal.classList.add("hidden");

  $("#export-ok").onclick = async () => {
    const sel = document.querySelector('input[name="exp-mode"]:checked');
    const mode = sel ? sel.value : "mcaddon";
    modal.classList.add("hidden");
    try {
      toast(t("common.loading", "处理中…"));
      const r = await api(base + "/export", { method: "POST", body: { mode } });
      toast(tf("index.exportDoneTo", { n: r.files, p: r.output }, "已导出"));
      if (r.download) {
        location.href = base + "/export/dl?name=" + encodeURIComponent(r.download);
      }
    } catch (e) { toast(e.message, true); }
  };

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });
  }

  // ---------------- 新建对象 ----------------
  const noModal = $("#new-obj-modal");
  let kindsInfo = null;

  async function openNewObject() {
    if (!noModal) return;
    try {
      if (!kindsInfo) {
        kindsInfo = await api(base + "/objects/kinds");
        const sel = $("#no-kind");
        sel.innerHTML = kindsInfo.kinds.map((k) =>
          `<option value="${esc(k)}">${esc(k)}</option>`).join("");
      }
      const kind = $("#no-kind").value || (kindsInfo.kinds[0] || "item");
      $("#no-fv").value = (kindsInfo.default_fv || {})[kind] || "";
      noModal.classList.remove("hidden");
    } catch (e) { toast(e.message, true); }
  }

  const btnNew = $("#btn-new-obj");
  if (btnNew) btnNew.onclick = openNewObject;
  const noCancel = $("#no-cancel");
  if (noCancel) noCancel.onclick = () => noModal.classList.add("hidden");

  const noKind = $("#no-kind");
  if (noKind) {
    noKind.onchange = () => {
      if (!kindsInfo) return;
      $("#no-fv").value = (kindsInfo.default_fv || {})[noKind.value] || "";
    };
  }

  const noCreate = $("#no-create");
  if (noCreate) {
    noCreate.onclick = async () => {
      const body = {
        kind: $("#no-kind").value,
        namespace: $("#no-ns").value.trim(),
        name: $("#no-name").value.trim(),
        options: {
          format_version: $("#no-fv").value.trim() || undefined,
          with_resource: $("#no-res").checked,
          with_lang: $("#no-lang").checked,
          with_texture: $("#no-tex").checked,
        },
      };
      if (!body.namespace || !body.name) {
        toast(t("index.needNsName", "请填写 namespace 与 name"), true);
        return;
      }
      try {
        const r = await api(base + "/objects/create", { method: "POST", body });
        noModal.classList.add("hidden");
        toast(tf("index.created", { id: r.identifier }, "已创建"));
        if (r.warnings && r.warnings.length) {
          setTimeout(() => toast(r.warnings.join("; "), true), 1200);
        }
        setTimeout(() => location.reload(), 900);
      } catch (e) { toast(e.message, true); }
    };
  }

  load();
})();