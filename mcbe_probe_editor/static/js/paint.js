(function () {
  const $ = (s) => document.querySelector(s);
  const PID = window.PROJECT_ID;
  const base = "/api/project/" + encodeURIComponent(PID);

  const canvas = $("#p-canvas");
  const ctx = canvas.getContext("2d");

  const RECENT_KEY = "mcpe_recent_colors";
  const MAX_RECENT = 20;
  const MAX_UNDO = 40;

  let img = null;
  let drawing = false;
  let strokeDirty = false;
  const undoStack = [];
  const redoStack = [];

  const swatchColors = [
    "#000000", "#ffffff", "#7f7f7f", "#c0c0c0",
    "#ff0000", "#ff7f00", "#ffff00", "#7fff00",
    "#00ff00", "#00ff7f", "#00ffff", "#007fff",
    "#0000ff", "#7f00ff", "#ff00ff", "#ff007f",
  ];

  // ---------------- 画布 ----------------
  function applyCanvasSize(w, h, keep) {
    w = Math.max(1, Math.min(256, parseInt(w, 10) || 16));
    h = Math.max(1, Math.min(256, parseInt(h, 10) || 16));
    $("#p-width").value = w;
    $("#p-height").value = h;

    let old = null;
    if (keep && img) {
      old = ctx.getImageData(0, 0, canvas.width, canvas.height);
    }

    canvas.width = w;
    canvas.height = h;
    const zoom = Math.max(1, Math.min(32, Math.floor(480 / Math.max(w, h))));
    canvas.style.width = (w * zoom) + "px";
    canvas.style.height = (h * zoom) + "px";
    ctx.imageSmoothingEnabled = false;

    img = ctx.createImageData(w, h);
    for (let i = 0; i < img.data.length; i += 4) img.data[i + 3] = 0;

    if (old) {
      const ox = Math.min(old.width, w);
      const oy = Math.min(old.height, h);
      for (let y = 0; y < oy; y++) {
        for (let x = 0; x < ox; x++) {
          const si = (y * old.width + x) * 4;
          const di = (y * w + x) * 4;
          img.data[di] = old.data[si];
          img.data[di + 1] = old.data[si + 1];
          img.data[di + 2] = old.data[si + 2];
          img.data[di + 3] = old.data[si + 3];
        }
      }
    }
    ctx.putImageData(img, 0, 0);
  }

  // ---------------- 撤回 / 重做 ----------------
  function snapshot() {
    if (!img) return null;
    return {
      w: canvas.width,
      h: canvas.height,
      data: new Uint8ClampedArray(img.data),
    };
  }

  function restore(snap) {
    if (!snap) return;
    if (canvas.width !== snap.w || canvas.height !== snap.h) {
      canvas.width = snap.w;
      canvas.height = snap.h;
      $("#p-width").value = snap.w;
      $("#p-height").value = snap.h;
      const zoom = Math.max(1, Math.min(32, Math.floor(480 / Math.max(snap.w, snap.h))));
      canvas.style.width = (snap.w * zoom) + "px";
      canvas.style.height = (snap.h * zoom) + "px";
      ctx.imageSmoothingEnabled = false;
    }
    img = ctx.createImageData(snap.w, snap.h);
    img.data.set(snap.data);
    ctx.putImageData(img, 0, 0);
  }

  function pushUndo() {
    const snap = snapshot();
    if (!snap) return;
    undoStack.push(snap);
    if (undoStack.length > MAX_UNDO) undoStack.shift();
    redoStack.length = 0;
  }

  function doUndo() {
    if (!undoStack.length) return;
    redoStack.push(snapshot());
    restore(undoStack.pop());
    if ($("#p-recent")) refreshRecent();
  }

  function doRedo() {
    if (!redoStack.length) return;
    undoStack.push(snapshot());
    restore(redoStack.pop());
  }

  // ---------------- 最近颜色 ----------------
  function loadRecent() {
    try {
      const raw = localStorage.getItem(RECENT_KEY);
      const arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr.slice(0, MAX_RECENT) : [];
    } catch (e) { return []; }
  }

  function saveRecent(arr) {
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(arr.slice(0, MAX_RECENT))); }
    catch (e) { /* ignore */ }
  }

  function rememberColor(hex) {
    if (!hex) return;
    hex = hex.toLowerCase();
    const arr = loadRecent().filter((c) => c.toLowerCase() !== hex);
    arr.unshift(hex);
    saveRecent(arr);
    refreshRecent();
  }

  function refreshRecent() {
    const box = $("#p-recent");
    if (!box) return;
    const arr = loadRecent();
    box.innerHTML = arr.map((c) =>
      `<div class="swatch" data-c="${esc(c)}" style="background:${esc(c)}" title="${esc(c)}"></div>`
    ).join("");
    box.querySelectorAll(".swatch").forEach((s) => {
      s.onclick = () => { $("#p-color").value = s.dataset.c; };
    });
  }

  // ---------------- 色板 ----------------
  function renderSwatches() {
    const box = $("#p-swatch");
    box.innerHTML = swatchColors
      .map((c) => `<div class="swatch" data-c="${c}" style="background:${c}"></div>`)
      .join("");
    box.querySelectorAll(".swatch").forEach((s) => {
      s.onclick = () => { $("#p-color").value = s.dataset.c; };
    });
  }

  // ---------------- 绘制 ----------------
  function paintAt(px, py) {
    if (!img || px < 0 || py < 0 || px >= img.width || py >= img.height) return;
    const i = (py * img.width + px) * 4;
    if ($("#p-eraser").checked) {
      img.data[i] = 0; img.data[i + 1] = 0; img.data[i + 2] = 0; img.data[i + 3] = 0;
    } else {
      const hex = $("#p-color").value;
      let r = parseInt(hex.slice(1, 3), 16);
      let g = parseInt(hex.slice(3, 5), 16);
      let b = parseInt(hex.slice(5, 7), 16);
      if ($("#p-gray").checked) {
        const avg = Math.round((r + g + b) / 3);
        r = g = b = avg;
      }
      img.data[i] = r; img.data[i + 1] = g; img.data[i + 2] = b; img.data[i + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    strokeDirty = true;
  }

  function pick(e) {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left) / (rect.width / canvas.width));
    const y = Math.floor((e.clientY - rect.top) / (rect.height / canvas.height));
    return { x, y };
  }

  canvas.addEventListener("mousedown", (e) => {
    pushUndo();
    drawing = true;
    strokeDirty = false;
    const p = pick(e); paintAt(p.x, p.y);
  });
  canvas.addEventListener("mousemove", (e) => {
    if (!drawing) return;
    const p = pick(e); paintAt(p.x, p.y);
  });
  window.addEventListener("mouseup", () => {
    if (drawing && strokeDirty && !$("#p-eraser").checked) {
      rememberColor($("#p-color").value);
    }
    drawing = false;
  });

  // ---------------- 载入 ----------------
  async function loadTexture() {
    const pack = $("#p-pack").value;
    const path = $("#p-path").value.trim();
    if (!path) { toast(t("paint.enterPath", "请输入路径"), true); return; }
    try {
      const r = await api(base + "/texture?pack=" + encodeURIComponent(pack) +
                          "&path=" + encodeURIComponent(path));
      const tx = r.texture;
      const im = new Image();
      im.onload = () => {
        canvas.width = im.width;
        canvas.height = im.height;
        const zoom = Math.max(1, Math.min(32, Math.floor(480 / Math.max(im.width, im.height))));
        canvas.style.width = (im.width * zoom) + "px";
        canvas.style.height = (im.height * zoom) + "px";
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(im, 0, 0);
        img = ctx.getImageData(0, 0, canvas.width, canvas.height);
        $("#p-width").value = im.width;
        $("#p-height").value = im.height;
        undoStack.length = 0;
        redoStack.length = 0;
        $("#p-info").textContent = tf("paint.loaded",
          { w: im.width, h: im.height, n: tx.semi_transparent }, "");
      };
      im.src = tx.data_url;
    } catch (e) { toast(e.message, true); }
  }

  // ---------------- 事件 ----------------
  $("#p-load").onclick = loadTexture;

  $("#p-new").onclick = () => {
    const w = $("#p-width").value;
    const h = $("#p-height").value;
    pushUndo();
    applyCanvasSize(w, h, false);
    $("#p-info").textContent = tf("paint.created", { w: canvas.width, h: canvas.height }, "");
  };

  $("#p-undo").onclick = doUndo;
  $("#p-redo").onclick = doRedo;

  $("#p-save").onclick = async () => {
    const pack = $("#p-pack").value;
    const path = $("#p-path").value.trim();
    if (!path) { toast(t("paint.savePath", "请填写保存路径"), true); return; }
    const dataUrl = canvas.toDataURL("image/png");
    try {
      const r = await api(base + "/texture", {
        method: "POST",
        body: { pack, path, image: dataUrl },
      });
      if (r.fixed_pixels) {
        toast(tf("paint.savedFixed", { n: r.fixed_pixels }));
      } else {
        toast(t("paint.saved", "已保存"));
      }
    } catch (e) { toast(e.message, true); }
  };

  // Ctrl+Z / Ctrl+Y
  document.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey)) return;
    const k = e.key.toLowerCase();
    if (k === "z" && !e.shiftKey) { e.preventDefault(); doUndo(); }
    else if (k === "y" || (k === "z" && e.shiftKey)) { e.preventDefault(); doRedo(); }
  });

  // ---------------- 初始化 ----------------
  renderSwatches();
  refreshRecent();
  applyCanvasSize(16, 16, false);

  (function autoLoadFromUrl() {
    const params = new URLSearchParams(location.search);
    const pack = params.get("pack");
    const path = params.get("path");
    if (!pack || !path) return;
    $("#p-pack").value = pack;
    $("#p-path").value = path;
    loadTexture();
  })();
})();