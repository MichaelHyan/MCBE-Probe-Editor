# -*- coding: utf-8 -*-
"""导出路由。

导出产物统一落到工程根的 output/<project_id>/ 下（便于查找与归档）。

模式:
    zip      行为包 + 资源包打包为一个 zip
    mcaddon  同内容，后缀改为 .mcaddon
    changes  仅导出改动过的文件（保持相对位置）

API:
    POST /api/project/<pid>/export          执行导出
    GET  /api/project/<pid>/exports         列出历史导出
    GET  /api/project/<pid>/export/dl       下载导出文件
    GET  /api/project/<pid>/output-path     查看输出目录
"""

import json
import os
import time
import zipfile

from flask import Blueprint, jsonify, request, send_file

from services import workspace as ws
from services import store

bp = Blueprint("export", __name__)

# 工程根下的 output/（与 workspaces/ 同级）
# workspaces 在 mcbe_probe_editor/ 下，工程根还要再上一层
OUTPUT_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(ws.WORKSPACE_ROOT)), "output")


def output_dir(project_id):
    path = os.path.join(OUTPUT_ROOT, project_id)
    os.makedirs(path, exist_ok=True)
    return path


def _pack_top(project_id, pack):
    """导出时包目录的顶层名。

    优先级:
      1. meta.sources 原始目录名(目录创建的项目)
      2. meta.pack_manifest 中对应 type 的 root(mcaddon 导入的项目)
      3. 默认 behavior_pack / resource_pack
    """
    meta = ws.load_meta(project_id)
    src = (meta.get("sources") or {}).get(pack)
    if src:
        base = os.path.basename(os.path.normpath(src))
        if base:
            return base
    want = "data" if pack == "behavior" else "resources"
    for m in (meta.get("pack_manifest") or []):
        if not isinstance(m, dict) or m.get("type") != want:
            continue
        root = (m.get("root") or "").replace("\\", "/").rstrip("/")
        base = os.path.basename(root)
        if base:
            return base
    return "behavior_pack" if pack == "behavior" else "resource_pack"


def _iter_pack_files(project_id, pack):
    root = ws.resolve_pack_dir(project_id, pack)
    if not root or not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "__pycache__", "_fv2_backup")]
        for fn in filenames:
            if fn.lower().endswith((".tmp",)):
                continue
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, root).replace("\\", "/")
            yield ap, rel


def _write_zip(project_id, dest):
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for pack in ("behavior", "resource"):
            top = _pack_top(project_id, pack)
            for ap, rel in _iter_pack_files(project_id, pack):
                zf.write(ap, "%s/%s" % (top, rel))
                count += 1
    return count


def _write_changes(project_id, dest_dir):
    data = store.load_changes(project_id)
    manifest = {"project_id": project_id,
                "exported": time.strftime("%Y-%m-%d %H:%M:%S"),
                "files": []}
    for entry in data.get("changes") or []:
        pack = entry.get("pack")
        rel = entry.get("path")
        if not pack or not rel:
            continue
        try:
            full = store.resolve_file(project_id, pack, rel)
        except Exception:
            continue
        if not os.path.isfile(full):
            manifest["files"].append({"pack": pack, "path": rel,
                                      "op": entry.get("op"),
                                      "status": "missing"})
            continue
        top = _pack_top(project_id, pack)
        target = os.path.join(dest_dir, top, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(full, "rb") as src, open(target, "wb") as out:
            out.write(src.read())
        manifest["files"].append({"pack": pack, "path": rel,
                                  "op": entry.get("op"),
                                  "status": "ok"})
    with open(os.path.join(dest_dir, "_changes.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return len([x for x in manifest["files"] if x["status"] == "ok"])


# ---------------------------------------------------------------- API


@bp.route("/api/project/<project_id>/output-path")
def api_output_path(project_id):
    return jsonify({"ok": True, "path": output_dir(project_id),
                    "root": OUTPUT_ROOT})


@bp.route("/api/project/<project_id>/export", methods=["POST"])
def api_export(project_id):
    body = request.get_json(silent=True) or {}
    mode = (body.get("mode") or "zip").lower()
    if mode not in ("zip", "mcaddon", "changes"):
        return jsonify({"ok": False, "error": "未知导出模式"}), 400

    if not os.path.isdir(ws.project_dir(project_id)):
        return jsonify({"ok": False, "error": "项目不存在"}), 404

    out_dir = output_dir(project_id)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    name = (body.get("name") or project_id).strip() or project_id

    try:
        if mode == "changes":
            dest = os.path.join(out_dir, "%s_changes_%s" % (name, stamp))
            os.makedirs(dest, exist_ok=True)
            count = _write_changes(project_id, dest)
            return jsonify({"ok": True, "mode": mode, "files": count,
                            "output": dest, "download": None,
                            "output_root": out_dir})
        suffix = ".mcaddon" if mode == "mcaddon" else ".zip"
        dest = os.path.join(out_dir, "%s_%s%s" % (name, stamp, suffix))
        count = _write_zip(project_id, dest)
        return jsonify({"ok": True, "mode": mode, "files": count,
                        "output": dest, "download": os.path.basename(dest),
                        "output_root": out_dir})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@bp.route("/api/project/<project_id>/exports")
def api_list_exports(project_id):
    out_dir = output_dir(project_id)
    rows = []
    for fn in sorted(os.listdir(out_dir), reverse=True):
        full = os.path.join(out_dir, fn)
        rows.append({
            "name": fn,
            "is_dir": os.path.isdir(full),
            "size": None if os.path.isdir(full) else os.path.getsize(full),
            "mtime": time.strftime("%Y-%m-%d %H:%M:%S",
                                   time.localtime(os.path.getmtime(full))),
        })
    return jsonify({"ok": True, "exports": rows, "root": out_dir})


@bp.route("/api/project/<project_id>/export/dl")
def api_download(project_id):
    name = request.args.get("name", "")
    if not name or "/" in name or "\\" in name or ".." in name:
        return jsonify({"ok": False, "error": "非法文件名"}), 400
    full = os.path.join(output_dir(project_id), name)
    if not os.path.isfile(full):
        return jsonify({"ok": False, "error": "文件不存在"}), 404
    return send_file(full, as_attachment=True, download_name=name)