(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);

  let allFiles = [];

  function renderList() {
    const q = $("#br-q").value.trim().toLowerCase();
    const pack = $("#br-pack").value;
    const list = $("#file-list");
    const rows = allFiles.filter((f) => {
      if (pack && f.pack !== pack) return false;
      if (q && !f.path.toLowerCase().includes(q)) return false;
      return true;
    });
    list.innerHTML = rows.map((f) => {
      const cls = ["file-row"];
      if (f.changed) cls.push("changed");
      if (f.special) cls.push("special");
      return `<div class="${cls.join(" ")}" data-pack="${esc(f.pack)}" data-path="${esc(f.path)}">
        <span class="dot"></span>
        <span class="path" title="${esc(f.path)}">${esc(f.path)}</span>
        ${f.special ? '<span class="tag">' + esc(f.special) + '</span>' : ''}
      </div>`;
    }).join("") || `<p class="empty" style="padding:12px">${esc(t("browser.noMatch", "无匹配文件"))}</p>`;

    list.querySelectorAll(".file-row").forEach((row) => {
      row.onclick = () => {
        list.querySelectorAll(".file-row").forEach((r) => r.classList.remove("active"));
        row.classList.add("active");
        openFile(row.dataset.pack, row.dataset.path);
      };
    });
  }

  async function openFile(pack, path) {
    const view = $("#file-view");
    view.innerHTML = `<p class="muted">${esc(t("common.loading", "加载中…"))}</p>`;
    try {
      const url = base + "/file?pack=" + encodeURIComponent(pack) +
                  "&path=" + encodeURIComponent(path);
      const r = await api(url);
      const info = r.info;
      let body = "";
      if (r.kind === "text") {
        body = `<pre class="code">${esc(r.content)}</pre>`;
      } else if (r.kind === "image") {
        const raw = base + "/raw?pack=" + encodeURIComponent(pack) +
                    "&path=" + encodeURIComponent(path) + "&t=" + Date.now();
        body = `<div><img src="${raw}" style="max-width:100%;image-rendering:pixelated;border:1px solid #2e323c"></div>`;
      } else {
        body = `<pre class="code">${esc(r.head_hex)}\n\n(${esc(t("browser.binary", "二进制"))}, ${r.length} ${esc(t("browser.bytes", "字节"))})</pre>`;
      }
      view.innerHTML = `
        <div class="muted small">${esc(pack)}/${esc(path)} · ${info.size} ${esc(t("browser.bytes", "字节"))} · ${esc(info.mtime || "")}</div>
        <div class="toolbar">
          <a class="btn small" href="${base}/raw?pack=${encodeURIComponent(pack)}&path=${encodeURIComponent(path)}&download=1">${esc(t("common.download", "下载"))}</a>
        </div>
        ${body}`;
    } catch (e) {
      view.innerHTML = `<p class="muted">${esc(e.message)}</p>`;
    }
  }

  async function load() {
    try {
      const r = await api(base + "/files");
      allFiles = [];
      Object.keys(r.packs).forEach((pack) => {
        r.packs[pack].forEach((f) => allFiles.push(Object.assign({ pack }, f)));
      });
      renderList();
    } catch (e) { toast(e.message, true); }
  }

  $("#br-q").oninput = renderList;
  $("#br-pack").onchange = renderList;
  load();
})();