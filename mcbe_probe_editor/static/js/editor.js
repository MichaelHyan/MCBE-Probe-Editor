(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const IDENT = window.IDENT;
  const base = "/api/project/" + encodeURIComponent(PID);

  const VALUE_LIMIT = 200;

  let data = null;
  let activeFile = 0;
  let activeScope = "components";
  let compEditTarget = null;
  let currentExamples = [];

  // ---------------- 工具 ----------------
  function scopeLabel(s) {
    if (s === "components") return t("editor.scopeComponents", "组件");
    if (s === "events") return t("editor.scopeEvents", "事件");
    if (s.startsWith("component_groups.")) {
      return t("editor.scopeGroup", "组件组") + ": " + s.slice("component_groups.".length);
    }
    if (s === "component_groups") return t("editor.scopeGroups", "组件组");
    return s;
  }

  function fileLabel(f) {
    const p = (f.pack || "") + "/" + (f.path || "");
    const fv = f.format_version
      ? `<span class="fv">v${esc(f.format_version)}</span>` : "";
    return `<div class="file-tab" data-i="${f.__i}">${esc(f.role)}: ${esc(p)}${fv}</div>`;
  }

  // ---------------- 主渲染 ----------------
  function render() {
    const root = $("#edit-root");
    if (!data) { root.innerHTML = '<p class="empty">-</p>'; return; }

    const obj = data.object || {};
    const files = data.files || [];
    let html = "";

    if (obj.warnings && obj.warnings.length) {
      html += `<div class="warn-box">${obj.warnings.map((w) => "⚠ " + esc(w)).join("<br>")}</div>`;
    }

    // 关联引用（固定槽位，全部可选）
    const slots = (data.object && data.object.slots) || {};
    const slotKeys = Object.keys(slots);
    if (slotKeys.length) {
      html += `<div class="editor-section"><h3>${esc(t("editor.slots", "关联引用"))}</h3>
        <table class="comp-table"><tbody>`;
      slotKeys.forEach((k) => {
        const s = slots[k] || {};
        const refs = s.refs || [];
        const st = s.state || (refs.length ? "linked" : "optional");
        const badge = st === "linked"
          ? `<span class="tag ok">${esc(t("slot.state.linked", "已关联"))}</span>`
          : (st === "pending"
              ? `<span class="tag warn">${esc(t("slot.state.pending", "待指定"))}</span>`
              : `<span class="muted small">${esc(t("slot.state.optional", "可选"))}</span>`);
        let refsHtml = "";
        refs.forEach((r, ri) => {
          const p = (r.pack ? esc(r.pack) + "/" : "") + esc(r.path || r.name || "-");
          const fv = r.format_version
            ? ` <span class="fv">v${esc(r.format_version)}</span>` : "";
          const keys = (r.keys && r.keys.length)
            ? ` <span class="muted small">[${esc(r.keys.join(", "))}]</span>` : "";
          const unresolved = (r.resolved === false);
          const open = (r.pack && r.path && !unresolved)
            ? ` <button class="btn small ghost" data-slot-open="${esc(k)}:${ri}">${esc(t("common.edit", "打开"))}</button>`
            : "";
          const mark = unresolved
            ? ` <span class="tag warn">${esc(t("editor.slotUnresolved", "未找到文件"))}</span>`
            : "";
          refsHtml += `<div><code>${p}</code>${fv}${keys}${mark}${open}</div>`;
        });
        if (!refsHtml) refsHtml = `<span class="muted small">—</span>`;
        let ops = `<button class="btn small ghost" data-slot-link="${esc(k)}">${esc(t("editor.slotLink", "关联"))}</button>`;
        if (s.can_create) {
          ops += ` <button class="btn small" data-slot-create="${esc(k)}">${esc(t("editor.slotCreate", "新建"))}</button>`;
        }
        html += `<tr>
          <td class="comp-name" style="width:18%">${esc(t("slot." + k, s.label || k))}</td>
          <td style="width:80px">${badge}</td>
          <td>${refsHtml}</td>
          <td style="width:180px">${ops}</td>
        </tr>`;
      });
      html += `</tbody></table></div>`;
    }

    html += `<div class="editor-section"><h3>${esc(t("editor.fileGroups", "文件分组"))}</h3>
      <div class="file-tabs" id="file-tabs">`;
    files.forEach((f, i) => { f.__i = i; html += fileLabel(f); });
    html += `</div><div id="file-body"></div></div>`;

    // 语言键（多 locale）
    if (data.lang_keys && data.lang_keys.length) {
      html += `<div class="editor-section"><h3>${esc(t("editor.langKeys", "语言键"))}</h3>
        <table class="comp-table"><tbody>`;
      data.lang_keys.forEach((lk) => {
        const rows = (lk.entries || []).map((ent) => `
          <div class="locale-row">
            <span class="loc">${esc(ent.locale)}</span>
            <input type="text" value="${esc(ent.value)}"
                   data-lang-key="${esc(lk.key)}"
                   data-lang-pack="${esc(ent.pack)}"
                   data-lang-path="${esc(ent.path)}">
          </div>`).join("");
        html += `<tr>
          <td class="comp-name" style="width:34%">${esc(lk.key)}</td>
          <td>${rows}</td>
        </tr>`;
      });
      html += `</tbody></table>
        <div class="toolbar"><button id="btn-save-lang" class="btn primary">${esc(t("editor.saveLang", "保存语言键"))}</button></div></div>`;
    }

    // 贴图
    if (data.textures && data.textures.length) {
      html += `<div class="editor-section"><h3>${esc(t("editor.textures", "贴图"))}</h3>
        <div style="display:flex;gap:12px;flex-wrap:wrap">`;
      data.textures.forEach((tx) => {
        if (!tx.pack || !tx.path) return;
        const raw = base + "/raw?pack=" + encodeURIComponent(tx.pack) +
                    "&path=" + encodeURIComponent(tx.path) + "&t=" + Date.now();
        html += `<div><img src="${raw}" style="width:64px;height:64px;image-rendering:pixelated;border:1px solid #2e323c;background:#0f1115"><br>
          <a class="small" href="/project/${encodeURIComponent(PID)}/paint?pack=${encodeURIComponent(tx.pack)}&path=${encodeURIComponent(tx.path)}">${esc(t("common.edit", "编辑"))}</a></div>`;
      });
      html += `</div></div>`;
    }

    // 模型关联
    if (data.geometries && data.geometries.length) {
      html += `<div class="editor-section"><h3>${esc(t("editor.models", "模型关联"))}</h3>
        <p class="muted small">${esc(t("editor.modelHint", ""))}</p>
        <table class="comp-table"><tbody>`;
      data.geometries.forEach((g, gi) => {
        html += `<tr>
          <td class="comp-name" style="width:34%">${esc(g.name || "(unnamed)")}</td>
          <td><input type="text" data-geo-input="${gi}" placeholder="${esc(t("editor.modelPathHint", "models/entity/xxx.geo.json"))}" style="width:100%"></td>
          <td style="width:110px"><button class="btn small" data-geo-link="${gi}">${esc(t("editor.link", "关联"))}</button></td>
        </tr>`;
      });
      html += `</tbody></table></div>`;
    }

    root.innerHTML = html;

    root.querySelectorAll(".file-tab").forEach((tab) => {
      tab.onclick = () => {
        activeFile = parseInt(tab.dataset.i, 10);
        activeScope = "components";
        root.querySelectorAll(".file-tab").forEach((x) => x.classList.remove("active"));
        tab.classList.add("active");
        renderFileBody();
      };
    });
    if (files.length) {
      const first = root.querySelector('.file-tab[data-i="0"]');
      if (first) first.click();
    }

    root.querySelectorAll("[data-slot-link]").forEach((btn) => {
      btn.onclick = () => openSlotModal(btn.dataset.slotLink, "link");
    });
    root.querySelectorAll("[data-slot-create]").forEach((btn) => {
      btn.onclick = () => openSlotModal(btn.dataset.slotCreate, "create");
    });
    root.querySelectorAll("[data-slot-open]").forEach((btn) => {
      btn.onclick = () => {
        const raw = btn.dataset.slotOpen || "";
        const cut = raw.lastIndexOf(":");
        const k = raw.slice(0, cut);
        const ri = parseInt(raw.slice(cut + 1), 10);
        const s = (data.object && data.object.slots && data.object.slots[k]) || {};
        const r = (s.refs || [])[ri];
        if (!r || !r.pack || !r.path) return;
        openSlotRef(r);
      };
    });

    root.querySelectorAll("[data-geo-link]").forEach((btn) => {
      btn.onclick = async () => {
        const gi = parseInt(btn.dataset.geoLink, 10);
        const input = root.querySelector('[data-geo-input="' + gi + '"]');
        const path = (input.value || "").trim();
        if (!path) { toast(t("editor.pathHint", "请填写模型文件路径"), true); return; }
        try {
          const r = await api(base + "/model/associate", {
            method: "POST",
            body: { pack: "resource", path, identifier: IDENT },
          });
          if (r.ok) toast(tf("editor.linked", { n: r.changed }));
          else toast(r.reason || t("editor.notChanged", "未改写"), true);
        } catch (e) { toast(e.message, true); }
      };
    });

    const saveLang = $("#btn-save-lang");
    if (saveLang) saveLang.onclick = saveLangKeys;
  }

  // ---------------- 关联槽位 ----------------
  let slotCtx = null;

  async function openSlotModal(key, mode) {
    slotCtx = { key: key, mode: mode };
    const slots = (data && data.object && data.object.slots) || {};
    const s = slots[key] || {};
    const modal = $("#slot-modal");
    if (!modal) return;
    $("#slot-modal-title").textContent = (s.label || t("slot." + key, key)) +
      " · " + (mode === "link" ? t("editor.slotLink", "关联")
                              : t("editor.slotCreate", "新建"));
    $("#slot-modal-hint").textContent = s.suggest
      ? (t("editor.slotSuggest", "建议路径") + ": " + s.suggest) : "";
    const linkRow = $("#slot-link-row");
    const acRow = $("#slot-ac-row");
    if (mode === "link") {
      linkRow.style.display = "";
      acRow.style.display = "none";
      $("#slot-path").value = "";
      const sel = $("#slot-candidate");
      sel.innerHTML = `<option value="">${esc(t("common.loading", "加载中…"))}</option>`;
      try {
        const r = await api(base + "/edit/" + encodeURIComponent(IDENT) + "/slots");
        const found = (r.slots || []).find((x) => x.key === key);
        const cands = (found && found.candidates) || [];
        sel.innerHTML =
          `<option value="">${esc(t("editor.slotPick", "选择候选（或手动填写）"))}</option>` +
          cands.map((c) => `<option value="${esc(c.pack)}|${esc(c.path)}">` +
            `${esc(c.pack)}/${esc(c.path)}</option>`).join("");
      } catch (e) {
        sel.innerHTML = `<option value="">${esc(e.message)}</option>`;
      }
    } else {
      linkRow.style.display = "none";
      acRow.style.display = key.indexOf("animation_controller") >= 0 ? "" : "none";
      const ac = $("#slot-ac-names");
      if (ac) ac.value = "";
    }
    modal.classList.remove("hidden");
  }

  const slotOkBtn = $("#slot-ok");
  if (slotOkBtn) slotOkBtn.onclick = async () => {
    if (!slotCtx) return;
    const key = slotCtx.key;
    const mode = slotCtx.mode;
    try {
      if (mode === "create") {
        const body = { slot: key };
        if (key.indexOf("animation_controller") >= 0) {
          const acEl = $("#slot-ac-names");
          const raw = acEl ? (acEl.value || "").trim() : "";
          if (raw) {
            body.animation_controller_names = raw.split(",")
              .map((x) => x.trim()).filter(Boolean);
          }
        }
        const r = await api(base + "/edit/" + encodeURIComponent(IDENT) +
          "/slots/create", { method: "POST", body: body });
        if (r.warnings && r.warnings.length) toast(r.warnings.join("; "), true);
        else toast(tf("editor.slotCreated", { n: (r.created || []).length }, "已创建"));
      } else {
        let pack = "";
        let path = "";
        const manual = ($("#slot-path").value || "").trim();
        if (manual) {
          const parts = manual.replace(/\\/g, "/").split("/");
          if (parts[0] === "behavior" || parts[0] === "resource") pack = parts.shift();
          else pack = "resource";
          path = parts.join("/");
        } else {
          const sel = $("#slot-candidate");
          if (sel && sel.value) {
            const cut = sel.value.indexOf("|");
            pack = sel.value.slice(0, cut);
            path = sel.value.slice(cut + 1);
          }
        }
        if (!path) { toast(t("editor.slotNeedPath", "请选择或填写文件路径"), true); return; }
        await api(base + "/edit/" + encodeURIComponent(IDENT) + "/slots/link",
          { method: "POST", body: { slot: key, pack: pack, path: path } });
        toast(t("common.saveOk", "已关联"));
      }
      $("#slot-modal").classList.add("hidden");
      await reload();
    } catch (e) { toast(e.message, true); }
  };

  // ---------------- 槽位跳转 ----------------
  // 图像 -> 像素画编辑器；JSON -> 代码区（文件标签 + 滚动）；其余 -> 文件浏览
  function openPaint(f) {
    location.href = "/project/" + encodeURIComponent(PID) +
      "/paint?pack=" + encodeURIComponent(f.pack) +
      "&path=" + encodeURIComponent(f.path);
  }

  function openInCodeArea(f) {
    const root = $("#edit-root");
    const files = (data && data.files) || [];
    for (let i = 0; i < files.length; i++) {
      if (files[i].pack === f.pack && files[i].path === f.path) {
        const tab = root.querySelector('.file-tab[data-i="' + i + '"]');
        if (tab) {
          tab.click();
          const code = $("#raw-json");
          if (code) code.scrollIntoView({ behavior: "smooth", block: "center" });
          else tab.scrollIntoView({ behavior: "smooth", block: "center" });
          return true;
        }
      }
    }
    return false;
  }

  function openSlotRef(r) {
    if (!r || !r.pack || !r.path) return;
    const low = String(r.path).toLowerCase();
    if (low.endsWith(".png") || low.endsWith(".tga")) {
      openPaint(r);
      return;
    }
    if (openInCodeArea(r)) return;
    location.href = "/project/" + encodeURIComponent(PID) +
      "/browser?pack=" + encodeURIComponent(r.pack) +
      "&path=" + encodeURIComponent(r.path);
  }

  const slotCancelBtn = $("#slot-cancel");
  if (slotCancelBtn) {
    slotCancelBtn.onclick = () => $("#slot-modal").classList.add("hidden");
  }

  // ---------------- 文件体 ----------------
  // 组件组的标准写法是「组名 -> 组件集合」，没有 components 包装层；
  // 这里同时兼容两种形态，只挑 minecraft:* 键。
  function groupItems(grp) {
    if (!grp || typeof grp !== "object") return {};
    const keys = Object.keys(grp);
    const hasMc = keys.some((k) => k.indexOf("minecraft:") === 0);
    if (!hasMc && grp.components && typeof grp.components === "object") {
      return grp.components;
    }
    const out = {};
    keys.forEach((k) => {
      if (k.indexOf("minecraft:") === 0) out[k] = grp[k];
    });
    return out;
  }

  function scopeList(f) {
    const sc = f.scopes || {};
    const out = [{ key: "components", label: scopeLabel("components"),
                   items: sc.components || {} }];
    const groups = sc.component_groups || {};
    Object.keys(groups).forEach((g) => {
      const grp = groups[g] || {};
      out.push({
        key: "component_groups." + g,
        label: scopeLabel("component_groups." + g),
        items: groupItems(grp),
      });
    });
    if (sc.events && Object.keys(sc.events).length) {
      out.push({ key: "events", label: scopeLabel("events"),
                 items: sc.events || {} });
    }
    return out;
  }

  function renderFileBody() {
    const f = data.files[activeFile];
    const body = $("#file-body");
    if (!f) { body.innerHTML = ""; return; }
    if (f.error) {
      body.innerHTML = `<div class="warn-box">${esc(t("editor.readFailed", "读取失败"))}: ${esc(f.error)}</div>`;
      return;
    }

    const scopes = scopeList(f);
    if (!scopes.some((s) => s.key === activeScope)) activeScope = "components";
    const cur = scopes.find((s) => s.key === activeScope) || scopes[0];
    const items = cur.items || {};

    let html = `<div class="muted small">${esc(f.pack)}/${esc(f.path)} · v${esc(f.format_version || "?")}</div>`;

    // scope 切换
    html += `<div class="toolbar" id="scope-tabs">`;
    scopes.forEach((s) => {
      const n = Object.keys(s.items || {}).length;
      const cls = s.key === cur.key ? "btn small primary" : "btn small ghost";
      html += `<button class="${cls}" data-scope="${esc(s.key)}">${esc(s.label)} (${n})</button>`;
    });
    html += `</div>`;

    html += `<div class="toolbar">
      <button id="btn-add-comp" class="btn small">${esc(t("editor.addFromDb", "+ 添加"))}</button>
      <button id="btn-save-raw" class="btn small ghost">${esc(t("editor.saveWhole", "保存整个文件"))}</button>
    </div>`;

    html += `<table class="comp-table"><tbody>`;
    Object.keys(items).forEach((name) => {
      const rawJson = JSON.stringify(items[name], null, 2);
      html += `<tr>
        <td class="comp-name" style="width:30%">${esc(name)}</td>
        <td>${renderValue(rawJson)}</td>
        <td style="width:130px">
          <button class="btn small" data-edit="${esc(name)}">${esc(t("common.edit", "编辑"))}</button>
          <button class="btn small danger" data-del="${esc(name)}">${esc(t("common.delete", "删除"))}</button>
        </td>
      </tr>`;
    });
    if (!Object.keys(items).length) {
      html += `<tr><td colspan="3" class="muted">${esc(t("editor.emptyScope", "（空）"))}</td></tr>`;
    }
    html += `</tbody></table>`;

    html += `<h3>${esc(t("editor.codeArea", "代码区"))}</h3>
      <textarea id="raw-json" class="code-input" rows="16" spellcheck="false">${esc(JSON.stringify(f.data, null, 2))}</textarea>`;

    body.innerHTML = html;

    body.querySelectorAll("[data-scope]").forEach((btn) => {
      btn.onclick = () => { activeScope = btn.dataset.scope; renderFileBody(); };
    });

    body.querySelectorAll(".comp-val .toggle").forEach((tg) => {
      tg.onclick = () => tg.parentElement.classList.toggle("expanded");
    });

    body.querySelectorAll("[data-edit]").forEach((btn) => {
      btn.onclick = () => openCompEdit(f, cur.key, btn.dataset.edit, items[btn.dataset.edit]);
    });
    body.querySelectorAll("[data-del]").forEach((btn) => {
      btn.onclick = () => deleteEntry(f, cur.key, btn.dataset.del);
    });
    $("#btn-add-comp").onclick = () => openAddFromDb(f, cur.key);
    $("#btn-save-raw").onclick = () => saveRaw(f);
  }

  function renderValue(rawJson) {
    let oneLine = rawJson;
    try { oneLine = JSON.stringify(JSON.parse(rawJson)); } catch (e) { /* ignore */ }
    if (oneLine.length <= VALUE_LIMIT) {
      return `<span class="comp-val">${esc(oneLine)}</span>`;
    }
    const head = oneLine.slice(0, VALUE_LIMIT);
    return `<span class="comp-val">
      <span class="short">${esc(head)}…</span>
      <span class="full">${esc(rawJson)}</span>
      <span class="toggle">${esc(t("editor.expand", "展开"))}</span>
    </span>`;
  }

  function compInfo(name) {
    const c = data.components && data.components.merged && data.components.merged[name];
    if (!c) return { cls: "temp", txt: t("editor.fromTemp", "临时库") };
    if (c.origin === "official") {
      const v = c.verified ? " ✓" : "";
      return { cls: "official", txt: t("editor.fromDb", "正式库") + v };
    }
    return { cls: "temp", txt: t("editor.fromTemp", "临时库") };
  }

  // ---------------- 示例下拉 ----------------
  function exampleSrcLabel(src) {
    if (src === "local") return t("editor.srcLocal", "本地库");
    if (src === "official") return t("editor.srcOfficial", "官方");
    return t("editor.srcProject", "本项目");
  }

  // 本项目示例标注来源对象，用于区分同版本不同对象的取值
  function exampleOrigin(ex) {
    if (!ex || ex.source !== "project" || !ex.origin) return "";
    return " · " + ex.origin;
  }

  async function loadExamples(kind, fv, name) {
    currentExamples = [];
    if (!kind || !fv || !name) return;
    try {
      const r = await api(base + "/db/examples?kind=" + encodeURIComponent(kind) +
                          "&fv=" + encodeURIComponent(fv) +
                          "&component=" + encodeURIComponent(name));
      currentExamples = r.examples || [];
    } catch (e) { currentExamples = []; }
  }

  function renderExampleSelect() {
    const sel = $("#comp-example");
    if (!sel) return;
    if (!currentExamples.length) {
      sel.innerHTML = `<option value="">${esc(t("editor.noExample", "无可用示例"))}</option>`;
      return;
    }
    sel.innerHTML = currentExamples.map((ex, i) => {
      let v = JSON.stringify(ex.value);
      if (v == null) v = "null";
      if (v.length > 80) v = v.slice(0, 80) + "…";
      const src = exampleSrcLabel(ex.source) + exampleOrigin(ex);
      return `<option value="${i}">[${esc(src)}] ${esc(v)}</option>`;
    }).join("");
  }

  // ---------------- 组件编辑 ----------------
  async function openCompEdit(f, scope, name, value, presetName) {
    const isNew = !name;
    const targetName = name || presetName || "";
    compEditTarget = { f, scope, name, isNew };
    $("#comp-modal-title").textContent =
      (isNew ? t("editor.addComponent", "添加条目") : t("editor.editComponent", "编辑")) +
      (targetName ? ": " + targetName : "");

    const kind = (f.prim_kind || (data.object && data.object.kind) || "item");
    const fv = f.format_version;
    if (targetName) await loadExamples(kind, fv, targetName);
    else currentExamples = [];
    renderExampleSelect();

    let hint = t("editor.jsonHint", "JSON 值");
    if (targetName) {
      const c = (data.components && data.components.merged &&
                 data.components.merged[targetName]) || {};
      if (c.note) hint += " · " + c.note;
    }
    $("#comp-modal-hint").textContent = hint;

    $("#comp-name-row").style.display = isNew ? "flex" : "none";
    $("#comp-name").value = targetName;
    $("#comp-value").value = JSON.stringify(value === undefined ? {} : value, null, 2);
    $("#comp-modal").classList.remove("hidden");
  }

  // ---------------- 从数据库添加（组件清单） ----------------
  let addTarget = null;
  let addMerged = {};

  function renderAddList() {
    const q = ($("#add-search").value || "").trim().toLowerCase();
    const names = Object.keys(addMerged)
      .filter((n) => !q || n.toLowerCase().indexOf(q) >= 0).sort();
    const box = $("#add-list");
    if (!names.length) {
      box.innerHTML = `<p class="muted small">${esc(t("db.none", "无匹配组件"))}</p>`;
      return;
    }
    box.innerHTML = names.map((n) => {
      const e = addMerged[n] || {};
      const ex = (e.example !== undefined) ? e.example : e.default;
      let exTxt = "";
      try { exTxt = shortText(JSON.stringify(ex), 90); } catch (err) { exTxt = String(ex); }
      const src = e.origin === "official"
        ? t("editor.fromDb", "正式库") : t("editor.fromTemp", "临时库");
      return `<div class="add-row" data-name="${esc(n)}">
        <div class="add-name">${esc(n)} <span class="muted small">${esc(e.value_type || "any")}</span></div>
        <div class="muted small">${esc(exTxt)} · ${esc(src)}</div>
      </div>`;
    }).join("");
    box.querySelectorAll(".add-row").forEach((row) => {
      row.onclick = () => {
        const n = row.dataset.name;
        const e = addMerged[n] || {};
        const initVal = (e.example !== undefined) ? e.example
          : (e.default !== undefined ? e.default : {});
        $("#add-modal").classList.add("hidden");
        openCompEdit(addTarget.f, addTarget.scope, "", initVal, n);
      };
    });
  }

  async function openAddFromDb(f, scope) {
    addTarget = { f, scope };
    addMerged = {};
    $("#add-search").value = "";
    $("#add-list").innerHTML =
      `<p class="muted small">${esc(t("common.loading", "加载中…"))}</p>`;
    $("#add-modal").classList.remove("hidden");

    const kind = f.prim_kind || (data.object && data.object.kind) || "item";
    const fv = f.format_version;
    try {
      const r = await api(base + "/components?kind=" + encodeURIComponent(kind) +
                          "&fv=" + encodeURIComponent(fv));
      addMerged = (r.components && r.components.merged) || {};
    } catch (e) {
      addMerged = (data.components && data.components.merged) || {};
    }
    renderAddList();
  }

  $("#comp-cancel").onclick = () => $("#comp-modal").classList.add("hidden");

  const addCancel = $("#add-cancel");
  if (addCancel) addCancel.onclick = () => $("#add-modal").classList.add("hidden");
  const addSearch = $("#add-search");
  if (addSearch) addSearch.oninput = renderAddList;

  $("#comp-insert-example").onclick = () => {
    const sel = $("#comp-example");
    if (!sel || !sel.value) return;
    const ex = currentExamples[parseInt(sel.value, 10)];
    if (!ex) return;
    $("#comp-value").value = JSON.stringify(ex.value, null, 2);
    toast(t("editor.exampleFilled", "已填入示例"));
  };

  $("#comp-copy").onclick = async () => {
    const txt = $("#comp-value").value;
    try {
      await navigator.clipboard.writeText(txt);
      toast(t("editor.copied", "已复制到剪贴板"));
    } catch (e) {
      $("#comp-value").select();
      document.execCommand("copy");
      toast(t("editor.copied", "已复制到剪贴板"));
    }
  };

  $("#comp-save-example").onclick = async () => {
    if (!compEditTarget || !compEditTarget.name) return;
    let val;
    try { val = JSON.parse($("#comp-value").value); }
    catch (e) { toast(t("editor.jsonError", "JSON 格式错误"), true); return; }
    try {
      await api(base + "/db/examples/add", {
        method: "POST",
        body: {
          kind: (compEditTarget.f.prim_kind ||
                 (data.object && data.object.kind) || "item"),
          fv: compEditTarget.f.format_version,
          component: compEditTarget.name,
          value: val,
          label: "manual",
          source: "local",
        },
      });
      toast(t("editor.exampleSaved", "已保存到本地库"));
      await loadExamples(
        (compEditTarget.f.prim_kind || (data.object && data.object.kind) || "item"),
        compEditTarget.f.format_version, compEditTarget.name);
      renderExampleSelect();
    } catch (e) { toast(e.message, true); }
  };

  $("#comp-save").onclick = async () => {
    if (!compEditTarget) return;
    let val;
    try { val = JSON.parse($("#comp-value").value); }
    catch (e) { toast(t("editor.jsonError", "JSON 格式错误") + ": " + e.message, true); return; }

    const tgt = compEditTarget;
    const name = tgt.isNew ? ($("#comp-name").value || "").trim() : tgt.name;
    if (!name) { toast(t("editor.needName", "请填写条目名"), true); return; }

    if (!tgt.isNew && tgt.scope === "component_groups") {
      // 整组替换
      try {
        await api(base + "/edit/" + encodeURIComponent(IDENT) + "/entry", {
          method: "POST",
          body: { pack: tgt.f.pack, path: tgt.f.path, scope: "component_groups",
                  name, value: val, op: "set_group" },
        });
        toast(t("common.saveOk", "已保存"));
        $("#comp-modal").classList.add("hidden");
        await reload();
      } catch (e) { toast(e.message, true); }
      return;
    }

    try {
      await api(base + "/edit/" + encodeURIComponent(IDENT) + "/entry", {
        method: "POST",
        body: { pack: tgt.f.pack, path: tgt.f.path, scope: tgt.scope,
                name, value: val, op: "set" },
      });
      toast(t("common.saveOk", "已保存"));
      $("#comp-modal").classList.add("hidden");
      await reload();
    } catch (e) { toast(e.message, true); }
  };

  async function deleteEntry(f, scope, name) {
    if (!confirm(t("common.delete", "删除") + " " + name + " ?")) return;
    try {
      await api(base + "/edit/" + encodeURIComponent(IDENT) + "/entry", {
        method: "POST",
        body: { pack: f.pack, path: f.path, scope, name, op: "delete" },
      });
      toast(t("common.deleteOk", "已删除"));
      await reload();
    } catch (e) { toast(e.message, true); }
  }

  // ---------------- 原始保存 ----------------
  async function saveRaw(f) {
    let obj;
    try { obj = JSON.parse($("#raw-json").value); }
    catch (e) { toast(t("editor.jsonError", "JSON 格式错误") + ": " + e.message, true); return; }
    try {
      await api(base + "/edit/" + encodeURIComponent(IDENT) + "/file", {
        method: "POST",
        body: { pack: f.pack, path: f.path, data: obj },
      });
      toast(t("common.saveOk", "已保存"));
      await reload();
    } catch (e) { toast(e.message, true); }
  }

  // ---------------- 语言键保存 ----------------
  async function saveLangKeys() {
    const inputs = document.querySelectorAll("[data-lang-key]");
    const updates = [];
    inputs.forEach((inp) => {
      updates.push({
        key: inp.dataset.langKey,
        pack: inp.dataset.langPack,
        path: inp.dataset.langPath,
        value: inp.value,
      });
    });
    if (!updates.length) return;
    try {
      await api(base + "/edit/" + encodeURIComponent(IDENT) + "/lang", {
        method: "POST", body: { updates },
      });
      toast(t("editor.langSaved", "语言键已保存"));
    } catch (e) { toast(e.message, true); }
  }

  // ---------------- 加载 ----------------
  async function reload() {
    try {
      data = await api(base + "/edit/" + encodeURIComponent(IDENT));
      const prim = (data.object || {}).primary || {};
      (data.files || []).forEach((f) => {
        f.prim_kind = prim.kind || (data.object || {}).kind;
      });
      render();
    } catch (e) {
      $("#edit-root").innerHTML = `<p class="empty">${esc(e.message)}</p>`;
    }
  }

  reload();
})();