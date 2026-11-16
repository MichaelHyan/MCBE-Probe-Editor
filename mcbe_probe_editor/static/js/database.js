(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);

  let buckets = { temp: [], official: [] };
  let docTarget = null;

  async function loadBuckets() {
    try {
      const r = await api(base + "/db/buckets");
      buckets = { temp: r.temp || [], official: r.official || [] };
      fillSelectors();
      $("#db-info").textContent = t("db.root", "正式库目录：") + r.official_root;
    } catch (e) { toast(e.message, true); }
  }

  function fillSelectors() {
    const kindSel = $("#db-kind");
    const fvSel = $("#db-fv");
    const kinds = new Set();
    buckets.temp.forEach((b) => kinds.add(b.kind));
    buckets.official.forEach((b) => kinds.add(b.kind));

    kindSel.innerHTML = `<option value="">${esc(t("db.kind", "选择 kind"))}</option>`;
    Array.from(kinds).sort().forEach((k) => {
      const o = document.createElement("option");
      o.value = k; o.textContent = k;
      kindSel.appendChild(o);
    });
    fvSel.innerHTML = `<option value="">${esc(t("db.fv", "选择版本"))}</option>`;
  }

  function fillVersions() {
    const kind = $("#db-kind").value;
    const fvSel = $("#db-fv");
    fvSel.innerHTML = `<option value="">${esc(t("db.fv", "选择版本"))}</option>`;
    if (!kind) return;

    const map = new Map();
    buckets.temp.filter((b) => b.kind === kind).forEach((b) => {
      map.set(b.format_version, { fv: b.format_version, temp: b.count, off: 0 });
    });
    buckets.official.filter((b) => b.kind === kind).forEach((b) => {
      const cur = map.get(b.format_version) || { fv: b.format_version, temp: 0, off: 0 };
      cur.off = b.count;
      map.set(b.format_version, cur);
    });

    Array.from(map.values())
      .sort((a, b) => String(a.fv).localeCompare(String(b.fv)))
      .forEach((v) => {
        const o = document.createElement("option");
        o.value = v.fv;
        o.textContent = v.fv + " (" +
          tf("db.tempCount", { a: v.temp, b: v.off }, "") + ")";
        fvSel.appendChild(o);
      });
  }

  function exampleText(e) {
    const ex = (e.example !== undefined) ? e.example : e.default;
    if (ex === undefined || ex === null) return "";
    return (typeof ex === "object") ? JSON.stringify(ex) : String(ex);
  }

  function renderBucket(data) {
    const merged = data.merged || {};
    const names = Object.keys(merged).sort();
    const tbody = $("#db-table tbody");

    tbody.innerHTML = names.map((name) => {
      const e = merged[name];
      const origin = e.origin === "official"
        ? `<span class="origin-official">${esc(t("editor.fromDb", "正式库"))}${e.verified ? " ✓" : ""}</span>`
        : `<span class="origin-temp">${esc(t("editor.fromTemp", "临时库"))}</span>`;
      const usage = e.in_use ? ' <span class="tag item">In use</span>' : "";
      const verifyBtn = e.origin === "official"
        ? `<button class="btn small" data-doc="${esc(name)}">${esc(t("db.doc", "文档/核实"))}</button>`
        : `<button class="btn small" data-promote="${esc(name)}">${esc(t("db.promote", "提升"))}</button>`;
      const exTxt = exampleText(e);
      const note = e.note || e.description || "";
      return `<tr>
        <td class="comp-name">${esc(name)}${usage}</td>
        <td class="muted">${esc(e.value_type || "any")}</td>
        <td class="comp-val">${esc(exTxt)}${note ? '<br><span class="muted small">' + esc(note) + '</span>' : ''}</td>
        <td>${origin}</td>
        <td>${verifyBtn}</td>
      </tr>`;
    }).join("") || `<tr><td colspan="5" class="muted">${esc(t("db.none", "该版本暂无组件"))}</td></tr>`;

    tbody.querySelectorAll("[data-promote]").forEach((btn) => {
      btn.onclick = () => promote([btn.dataset.promote]);
    });
    tbody.querySelectorAll("[data-doc]").forEach((btn) => {
      btn.onclick = () => openDoc(btn.dataset.doc);
    });
  }

  async function loadBucket() {
    const kind = $("#db-kind").value;
    const fv = $("#db-fv").value;
    if (!kind || !fv) { toast(t("db.needSelect", "请选择 kind 与版本"), true); return; }
    try {
      const r = await api(base + "/db/bucket?kind=" + encodeURIComponent(kind) +
                          "&fv=" + encodeURIComponent(fv));
      renderBucket(r.bucket);
      $("#db-info").textContent = tf("db.info", {
        k: kind, v: fv,
        a: Object.keys(r.bucket.temp).length,
        b: Object.keys(r.bucket.official).length,
      }, "");
    } catch (e) { toast(e.message, true); }
  }

  async function promote(names) {
    const kind = $("#db-kind").value;
    const fv = $("#db-fv").value;
    try {
      const r = await api(base + "/db/promote", {
        method: "POST",
        body: { kind, fv, names },
      });
      toast(tf("db.promoted", { a: r.added, u: r.updated, t: r.total }, ""));
      await loadBuckets();
      await loadBucket();
    } catch (e) { toast(e.message, true); }
  }

  function openDoc(name) {
    docTarget = { kind: $("#db-kind").value, name, fv: $("#db-fv").value };
    $("#doc-title").textContent = tf("db.docTitle", { n: name }, "");
    $("#doc-content").value = "";
    api(base + "/db/doc?kind=" + encodeURIComponent(docTarget.kind) +
        "&name=" + encodeURIComponent(name))
      .then((r) => { $("#doc-content").value = r.content || ""; })
      .catch(() => {});
    $("#doc-modal").classList.remove("hidden");
  }

  $("#doc-cancel").onclick = () => $("#doc-modal").classList.add("hidden");
  $("#doc-save").onclick = async () => {
    if (!docTarget) return;
    try {
      const r = await api(base + "/db/verify", {
        method: "POST",
        body: {
          kind: docTarget.kind, fv: docTarget.fv,
          name: docTarget.name, doc: $("#doc-content").value,
        },
      });
      if (r.ok) {
        toast(t("db.docSaved", "已保存并标记核实"));
        $("#doc-modal").classList.add("hidden");
        await loadBucket();
      } else {
        toast(t("db.docFailed", "标记失败"), true);
      }
    } catch (e) { toast(e.message, true); }
  };

  $("#db-kind").onchange = fillVersions;
  $("#db-load").onclick = loadBucket;
  $("#db-promote-all").onclick = () => promote(null);

  loadBuckets();
})();