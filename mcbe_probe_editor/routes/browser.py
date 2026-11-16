# -*- coding: utf-8 -*-
"""文件浏览视图(对应 plan.md 3.4)。

特殊文件(tick.json / lines/ / pack_icon 等)只能在这里查看。
"""

import os

from flask import (Blueprint, jsonify, render_template, request,
                   send_file)

from services import workspace as ws
from services import store
from services import pipeline

bp = Blueprint("browser", __name__)

TEXT_EXT = (".json", ".lang", ".md", ".txt", ".mcfunction",
            ".material", ".html", ".css", ".js", ".py")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".tga")


def _walk(root, prefix=""):
    """递归列出目录，返回扁平文件列表(rel 路径)。"""
    out = []
    if not root or not os.path.isdir(root):
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in (".git", "__pycache__"))
        for fn in sorted(filenames):
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, root).replace("\\", "/")
            out.append({
                "path": rel,
                "size": os.path.getsize(ap),
                "ext": os.path.splitext(fn)[1].lower(),
            })
    return out


# ---------------------------------------------------------------- 页面


@bp.route("/project/<project_id>/browser")
def browser_page(project_id):
    meta = ws.load_meta(project_id)
    return render_template("browser.html", project_id=project_id, meta=meta)


# ---------------------------------------------------------------- API


@bp.route("/api/project/<project_id>/files")
def api_files(project_id):
    """列出工作区文件(可按 pack 过滤)。"""
    pack = (request.args.get("pack") or "").strip()
    packs = ["behavior", "resource"] if not pack else [pack]

    index = pipeline.ensure_index(project_id)
    special = {}
    for x in index.get("special_files") or []:
        special[(x.get("pack"), x.get("path"))] = x.get("reason")

    changed = store.changed_files(project_id)

    out = {}
    for p in packs:
        root = ws.resolve_pack_dir(project_id, p)
        files = _walk(root)
        for f in files:
            key = (p, f["path"])
            f["special"] = special.get(key)
            f["changed"] = key in changed
            f["editable"] = (f["ext"] in (".json", ".lang")
                             and not f["special"])
        out[p] = files

    return jsonify({"ok": True, "packs": out,
                    "special_files": index.get("special_files") or [],
                    "structures": index.get("structures") or []})


@bp.route("/api/project/<project_id>/file")
def api_file(project_id):
    """读取单个文件内容(文本返回内容，二进制返回元信息)。"""
    pack = request.args.get("pack", "")
    rel = request.args.get("path", "")
    try:
        info = store.file_info(project_id, pack, rel)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    ext = os.path.splitext(rel)[1].lower()
    if ext in IMAGE_EXT:
        return jsonify({"ok": True, "info": info, "kind": "image"})

    if ext in TEXT_EXT:
        try:
            text = store.read_text(project_id, pack, rel)
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "info": info, "kind": "text",
                        "content": text})

    data = store.read_bytes(project_id, pack, rel)
    preview = data[:64].hex()
    return jsonify({"ok": True, "info": info, "kind": "binary",
                    "head_hex": preview, "length": len(data)})


@bp.route("/api/project/<project_id>/raw")
def api_raw(project_id):
    """原始文件下载 / 图片直出。"""
    pack = request.args.get("pack", "")
    rel = request.args.get("path", "")
    try:
        full = store.resolve_file(project_id, pack, rel)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    if not os.path.isfile(full):
        return jsonify({"ok": False, "error": "文件不存在"}), 404

    as_attach = request.args.get("download")
    kwargs = {"conditional": True}
    if as_attach:
        kwargs["as_attachment"] = True
        kwargs["download_name"] = os.path.basename(full)
    return send_file(full, **kwargs)