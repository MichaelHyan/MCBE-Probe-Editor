# -*- coding: utf-8 -*-
"""组件数据库路由（对应 plan.md 2.1 / 2.2）。

提供临时库 / 正式库浏览、临时条目提升、核实标记与文档读写。

API:
    GET  /api/project/<pid>/db/buckets          临时 + 正式桶列表
    GET  /api/project/<pid>/db/bucket           单桶组件(合并视图)
    POST /api/project/<pid>/db/promote          临时条目提升到正式库
    POST /api/project/<pid>/db/verify           标记已核实
    GET  /api/project/<pid>/db/doc              读取组件文档
    POST /api/project/<pid>/db/doc              写入组件文档
"""

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import database as db
from services import pipeline

bp = Blueprint("db", __name__)


@bp.route("/project/<project_id>/database")
def database_page(project_id):
    return render_template("database.html", project_id=project_id,
                           meta=ws.load_meta(project_id))


@bp.route("/api/project/<project_id>/db/buckets")
def api_buckets(project_id):
    return jsonify({
        "ok": True,
        "temp": db.list_temp_buckets(project_id),
        "official": db.list_official_buckets(),
        "official_root": db.OFFICIAL_ROOT,
    })


@bp.route("/api/project/<project_id>/db/bucket")
def api_bucket(project_id):
    kind = request.args.get("kind", "")
    fv = request.args.get("fv", "")
    if not kind or not fv:
        return jsonify({"ok": False, "error": "需要 kind 与 fv"}), 400
    data = db.query_components(project_id, kind, fv)
    return jsonify({"ok": True, "bucket": data})


@bp.route("/api/project/<project_id>/db/promote", methods=["POST"])
def api_promote(project_id):
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    fv = body.get("fv")
    names = body.get("names") or None
    if not kind or not fv:
        return jsonify({"ok": False, "error": "需要 kind 与 fv"}), 400
    try:
        result = db.promote_to_official(project_id, kind, fv, names=names)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify(result)


@bp.route("/api/project/<project_id>/db/verify", methods=["POST"])
def api_verify(project_id):
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    fv = body.get("fv")
    name = body.get("name")
    content = body.get("doc")
    if not kind or not fv or not name:
        return jsonify({"ok": False, "error": "需要 kind/fv/name"}), 400

    doc_rel = None
    if content is not None:
        path = db.write_doc(kind, name, content)
        doc_rel = path.replace(db.OFFICIAL_ROOT, "").lstrip("\\/").replace("\\", "/")

    ok = db.mark_verified(kind, fv, name, doc_rel=doc_rel)
    return jsonify({"ok": ok, "doc_ref": doc_rel})


@bp.route("/api/project/<project_id>/db/doc")
def api_get_doc(project_id):
    kind = request.args.get("kind", "")
    name = request.args.get("name", "")
    if not kind or not name:
        return jsonify({"ok": False, "error": "需要 kind 与 name"}), 400
    content = db.read_doc(kind, name)
    return jsonify({"ok": True, "content": content})

# ---------------------------------------------------------------- 示例库


@bp.route("/api/project/<project_id>/db/examples")
def api_examples(project_id):
    """列出某组件的可用示例（本地库 + 本项目）。"""
    kind = request.args.get("kind", "")
    fv = request.args.get("fv", "")
    name = request.args.get("component", "")
    if not kind or not fv or not name:
        return jsonify({"ok": False, "error": "需要 kind/fv/component"}), 400
    items = db.list_examples(project_id, kind, fv, name)
    return jsonify({"ok": True, "component": name, "examples": items})


@bp.route("/api/project/<project_id>/db/examples/add", methods=["POST"])
def api_example_add(project_id):
    """把一条示例保存到本地库（跨项目共享）。"""
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    fv = body.get("fv")
    name = body.get("component")
    if not kind or not fv or not name or "value" not in body:
        return jsonify({"ok": False, "error": "需要 kind/fv/component/value"}), 400
    res = db.record_example(
        kind, fv, name, body.get("value"),
        label=body.get("label") or "manual",
        source=body.get("source") or "local",
        origin=body.get("origin") or project_id,
    )
    return jsonify(res)
