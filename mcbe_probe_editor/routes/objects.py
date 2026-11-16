# -*- coding: utf-8 -*-
"""新建对象路由。

API:
    GET  /api/project/<pid>/objects/kinds      支持的 kind 与默认版本
    POST /api/project/<pid>/objects/create     创建对象
"""

from flask import Blueprint, jsonify, request

from services import objects as objs
from services import pipeline
from services import workspace as ws

bp = Blueprint("objects", __name__)


@bp.route("/api/project/<project_id>/objects/kinds")
def api_kinds(project_id):
    return jsonify({
        "ok": True,
        "kinds": list(objs.KINDS),
        "default_fv": dict(objs.DEFAULT_FV),
    })


@bp.route("/api/project/<project_id>/objects/create", methods=["POST"])
def api_create(project_id):
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    ns = body.get("namespace")
    name = body.get("name")
    options = body.get("options") or {}

    if not ws.valid_project_id(project_id):
        return jsonify({"ok": False, "error": "项目 ID 非法"}), 400

    try:
        res = objs.create(project_id, kind, ns, name, options)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    try:
        index, _ = pipeline.run_probe(project_id)
        res["stats"] = index.get("stats", {})
    except Exception as exc:
        res["warnings"] = (res.get("warnings") or []) + ["探测失败: %s" % exc]

    return jsonify(res)