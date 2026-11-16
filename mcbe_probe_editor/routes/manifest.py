# -*- coding: utf-8 -*-
"""manifest 编辑路由（项目级，不计入对象索引）。

页面:
    GET /project/<pid>/manifest

API:
    GET  /api/project/<pid>/manifest            读取双包 manifest
    POST /api/project/<pid>/manifest            保存（pack + data）
    POST /api/project/<pid>/manifest/validate   仅校验
    POST /api/project/<pid>/manifest/template   生成模板
"""

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import manifest as mf
from services import pipeline

bp = Blueprint("manifest", __name__)


@bp.route("/project/<project_id>/manifest")
def manifest_page(project_id):
    return render_template("manifest.html", project_id=project_id,
                           meta=ws.load_meta(project_id))


@bp.route("/api/project/<project_id>/manifest")
def api_get(project_id):
    out = {}
    for pack in ("behavior", "resource"):
        out[pack] = mf.describe(project_id, pack)
    return jsonify({"ok": True, "packs": out})


@bp.route("/api/project/<project_id>/manifest", methods=["POST"])
def api_save(project_id):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    data = body.get("data")
    if pack not in ("behavior", "resource"):
        return jsonify({"ok": False, "error": "pack 必须是 behavior/resource"}), 400
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "data 必须是对象"}), 400

    errors, warnings = mf.validate(data)
    if errors:
        return jsonify({"ok": False, "error": "校验未通过",
                        "errors": errors, "warnings": warnings}), 400

    try:
        mf.save(project_id, pack, data)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    # manifest 影响包识别，重新探测一次
    try:
        pipeline.run_probe(project_id)
    except Exception:
        pass

    return jsonify({"ok": True, "warnings": warnings})


@bp.route("/api/project/<project_id>/manifest/validate", methods=["POST"])
def api_validate(project_id):
    body = request.get_json(silent=True) or {}
    data = body.get("data")
    errors, warnings = mf.validate(data)
    return jsonify({"ok": not errors, "errors": errors, "warnings": warnings})


@bp.route("/api/project/<project_id>/manifest/template", methods=["POST"])
def api_template(project_id):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    if pack not in ("behavior", "resource"):
        return jsonify({"ok": False, "error": "pack 不合法"}), 400
    name = body.get("name") or ""
    return jsonify({"ok": True, "data": mf.template(pack, name)})