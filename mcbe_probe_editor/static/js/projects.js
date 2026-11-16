(function () {
  const $ = (s) => document.querySelector(s);

  const createForm = $("#create-form");
  const uploadForm = $("#upload-form");

  function show(el) { el.classList.remove("hidden"); }
  function hide(el) { el.classList.add("hidden"); }

  $("#btn-create").onclick = () => { show(createForm); hide(uploadForm); };
  $("#btn-upload").onclick = () => { show(uploadForm); hide(createForm); };
  $("#btn-refresh").onclick = () => location.reload();

  $("#btn-create-cancel").onclick = () => hide(createForm);
  $("#btn-upload-cancel").onclick = () => hide(uploadForm);

  $("#btn-create-submit").onclick = async () => {
    const body = {
      name: $("#f-name").value.trim(),
      behavior: $("#f-behavior").value.trim(),
      resource: $("#f-resource").value.trim(),
      copy: $("#f-copy").checked,
    };
    if (!body.behavior && !body.resource) {
      toast(t("projects.needPack", "至少填一个包目录"), true);
      return;
    }
    try {
      toast(t("projects.creating", "创建并探测中…"));
      const r = await api("/api/projects", { method: "POST", body });
      toast(tf("projects.done", { n: r.stats.objects }, "完成"));
      location.href = r.url;
    } catch (e) { toast(e.message, true); }
  };

  $("#btn-upload-submit").onclick = async () => {
    const fileInput = $("#f-up-file");
    if (!fileInput.files.length) {
      toast(t("projects.pleaseSelectFile", "请选择文件"), true);
      return;
    }
    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    fd.append("name", $("#f-up-name").value.trim());
    try {
      toast(t("projects.uploading", "上传并探测中…"));
      const r = await api("/api/projects/upload", { method: "POST", body: fd });
      toast(tf("projects.done", { n: r.stats.objects }, "完成"));
      location.href = r.url;
    } catch (e) { toast(e.message, true); }
  };

  document.querySelectorAll("[data-del]").forEach((btn) => {
    btn.onclick = async () => {
      const pid = btn.dataset.del;
      if (!confirm(tf("projects.confirmDelete", { id: pid }, "确认删除？"))) return;
      try {
        await api("/api/projects/" + encodeURIComponent(pid), { method: "DELETE" });
        toast(t("common.deleteOk", "已删除"));
        location.reload();
      } catch (e) { toast(e.message, true); }
    };
  });
})();