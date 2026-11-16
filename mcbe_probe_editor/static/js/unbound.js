(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);

  const LIMIT = 100;
  let offset = 0;
  let total = 0;

  async function load() {
    const kind = $("#ub-kind").value;
    const q = $("#ub-q").value.trim();
    const url = base + "/unbound/detail?offset=" + offset + "&limit=" + LIMIT +
                (kind ? "&kind=" + encodeURIComponent(kind) : "") +
                (q ? "&q=" + encodeURIComponent(q) : "");
    try {
      const r = await api(url);
      total = r.total;
      renderRows(r.items);
      renderCounts(r.counts, r.all_total);
      $("#ub-count").textContent =
        tf("unbound.count",
           { a: offset + 1, b: Math.min(offset + LIMIT, total),
             t: total, all: r.all_total }, "");
    } catch (e) { toast(e.message, true); }
  }

  function renderCounts(counts, all) {
    const sel = $("#ub-kind");
    const current = sel.value;
    sel.innerHTML = `<option value="">${esc(t("common.all", "全部"))}</option>`;
    Object.keys(counts).sort().forEach((k) => {
      const o = document.createElement("option");
      o.value = k;
      o.textContent = k + " (" + counts[k] + ")";
      sel.appendChild(o);
    });
    sel.value = current;
  }

  function renderRows(items) {
    const tbody = $("#ub-table tbody");
    tbody.innerHTML = items.map((x) => {
      const extra = [];
      if (x.key) extra.push("key: " + x.key);
      if (x.identifier) extra.push("id: " + x.identifier);
      if (x.target) extra.push("target: " + x.target);
      if (x.result_item) extra.push("result: " + x.result_item);
      if (x.line) extra.push("L" + x.line);
      if (x.format_version) extra.push("v" + x.format_version);
      return `<tr>
        <td><span class="tag">${esc(x.kind || "")}</span></td>
        <td class="muted">${esc(x.pack || "")}</td>
        <td><code>${esc(x.path || x.key || "")}</code></td>
        <td class="muted small">${esc(extra.join(" · "))}</td>
      </tr>`;
    }).join("") || `<tr><td colspan="4" class="muted">${esc(t("unbound.noMatch", "无匹配项"))}</td></tr>`;
  }

  $("#ub-kind").onchange = () => { offset = 0; load(); };
  $("#ub-q").oninput = () => { offset = 0; load(); };
  $("#ub-refresh").onclick = () => { offset = 0; load(); };
  $("#ub-prev").onclick = () => {
    if (offset <= 0) return;
    offset = Math.max(0, offset - LIMIT);
    load();
  };
  $("#ub-next").onclick = () => {
    if (offset + LIMIT >= total) return;
    offset += LIMIT;
    load();
  };

  load();
})();