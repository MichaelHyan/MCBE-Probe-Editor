# -*- coding: utf-8 -*-
"""新建对象路由。

API:
    GET  /api/project/<pid>/objects/kinds      支持的 kind、默认版本、模板列表
    GET  /api/project/<pid>/objects/template   取空模板代码(kind + fv)
    POST /api/project/<pid>/objects/create     创建对象
"""

from flask import Blueprint, jsonify, request

from services import objects as objs
from services import templates as tpl_mod
from services import pipeline
from services import workspace as ws

bp = Blueprint("objects", __name__)


@bp.route("/api/project/<project_id>/objects/kinds")
def api_kinds(project_id):
    try:
        tpl_mod.ensure_templates()
    except Exception:
        pass
    return jsonify({
        "ok": True,
        "kinds": list(objs.KINDS),
        "default_fv": dict(objs.DEFAULT_FV),
        "templates": tpl_mod.list_templates(),
    })


@bp.route("/api/project/<project_id>/objects/template")
def api_template(project_id):
    kind = (request.args.get("kind") or "").strip()
    fv = (request.args.get("fv") or "").strip()
    if kind not in objs.KINDS or not fv:
        return jsonify({"ok": False, "error": "需要 kind 与 fv"}), 400
    data = tpl_mod.load_template(kind, fv)
    if data is None:
        data = tpl_mod.materialize(kind, fv, "%s:name" % kind)
    return jsonify({"ok": True, "kind": kind, "format_version": fv,
                    "template": data})


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