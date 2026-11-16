# -*- coding: utf-8 -*-
"""项目 / 工作区路由。

页面:
    GET  /projects                     项目列表
    GET  /project/<pid>                项目总览(进入索引)

API:
    GET  /api/projects                 列表
    POST /api/projects                 由目录创建
    POST /api/projects/upload          上传 mcaddon/zip 创建
    POST /api/projects/<pid>/probe     重新探测
    DELETE /api/projects/<pid>         删除项目
"""

import os
import shutil
import tempfile

from flask import (Blueprint, jsonify, render_template, request,
                   send_file, url_for, redirect)

from services import workspace as ws
from services import pipeline
from services import database as db

bp = Blueprint("project", __name__)

UPLOAD_DIR = os.path.join(ws.WORKSPACE_ROOT, "_uploads")


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    return UPLOAD_DIR


def _dir_or_none(value):
    if not value:
        return None
    value = str(value).strip()
    if not value:
        return None
    if not os.path.isdir(value):
        return None
    return value


# ---------------------------------------------------------------- 页面


@bp.route("/projects")
def projects_page():
    return render_template("projects.html", projects=ws.list_projects(),
                           workspace_root=ws.WORKSPACE_ROOT)


@bp.route("/project/<project_id>")
def project_overview(project_id):
    return redirect(url_for("index.index_page", project_id=project_id))


# ---------------------------------------------------------------- 列表 / 创建


@bp.route("/api/projects")
def api_list():
    return jsonify({"ok": True, "projects": ws.list_projects(),
                    "workspace_root": ws.WORKSPACE_ROOT})


@bp.route("/api/projects", methods=["POST"])
def api_create():
    """由本地目录创建项目。

    body: {"name": "...", "behavior": "D:/...", "resource": "D:/...", "copy": true}
    """
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    behavior = _dir_or_none(body.get("behavior"))
    resource = _dir_or_none(body.get("resource"))
    copy = bool(body.get("copy", True))

    if not behavior and not resource:
        return jsonify({"ok": False, "error": "至少需要一个有效的包目录"}), 400

    pid = ws.create_project(name or "project", behavior, resource, copy=copy)
    try:
        index, inventory = pipeline.run_probe(pid)
    except Exception as exc:
        ws.delete_project(pid)
        return jsonify({"ok": False, "error": "探测失败: %s" % exc}), 500

    return jsonify({
        "ok": True,
        "project_id": pid,
        "stats": index.get("stats", {}),
        "buckets": (inventory or {}).get("buckets", []),
        "url": url_for("index.index_page", project_id=pid),
    })


@bp.route("/api/projects/upload", methods=["POST"])
def api_upload():
    """上传 mcaddon/zip 创建项目。"""
    f = request.files.get("file")
    if f is None and request.files:
        f = list(request.files.values())[0]
    if not f or not f.filename:
        ctype = request.content_type or ""
        hint = ""
        if "json" in ctype:
            hint = "：请求被当成 JSON 发送了，请 Ctrl+F5 强制刷新页面后重试"
        return jsonify({"ok": False,
                        "error": "未收到文件" + hint,
                        "content_type": ctype}), 400

    name = (request.form.get("name") or "").strip()
    if not name:
        name = os.path.splitext(os.path.basename(f.filename))[0]

    up_dir = _ensure_upload_dir()
    fd, tmp_path = tempfile.mkstemp(suffix=".zip", dir=up_dir)
    os.close(fd)
    try:
        f.save(tmp_path)
        info = ws.inspect_mcaddon(tmp_path)
        if not info.get("packs"):
            return jsonify({"ok": False,
                            "error": "压缩包内未找到 manifest.json"}), 400

        pid = ws.create_project(name or "imported", None, None, copy=False)
        ws.extract_mcaddon(tmp_path, pid, info)

        # 记录来源与包信息
        meta = ws.load_meta(pid)
        meta["imported_from"] = f.filename
        meta["pack_manifest"] = info.get("packs", [])
        ws.save_meta(pid, meta)

        try:
            index, inventory = pipeline.run_probe(pid)
        except Exception as exc:
            return jsonify({"ok": False,
                            "error": "探测失败: %s" % exc,
                            "project_id": pid}), 500

        return jsonify({
            "ok": True,
            "project_id": pid,
            "packs": info.get("packs", []),
            "stats": index.get("stats", {}),
            "buckets": (inventory or {}).get("buckets", []),
            "url": url_for("index.index_page", project_id=pid),
        })
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@bp.route("/api/projects/<project_id>", methods=["DELETE"])
def api_delete(project_id):
    ok = ws.delete_project(project_id)
    return jsonify({"ok": ok})


@bp.route("/api/projects/<project_id>/probe", methods=["POST"])
@bp.route("/api/project/<project_id>/probe", methods=["POST"])
def api_probe(project_id):
    if not os.path.isdir(ws.project_dir(project_id)):
        return jsonify({"ok": False, "error": "项目不存在"}), 404
    try:
        index, inventory = pipeline.run_probe(project_id)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({
        "ok": True,
        "stats": index.get("stats", {}),
        "buckets": (inventory or {}).get("buckets", []),
    })


@bp.route("/api/projects/<project_id>/meta")
def api_meta(project_id):
    meta = ws.load_meta(project_id)
    if not meta:
        return jsonify({"ok": False, "error": "项目不存在"}), 404
    meta["_buckets"] = db.list_temp_buckets(project_id)
    return jsonify({"ok": True, "meta": meta})