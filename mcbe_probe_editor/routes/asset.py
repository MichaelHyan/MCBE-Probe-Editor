# -*- coding: utf-8 -*-
"""资产编辑路由(对应 plan.md 4.1 / 4.2)。

API:
    GET  /api/project/<pid>/texture?pack=&path=      读取贴图(含 data_url)
    POST /api/project/<pid>/texture                  保存贴图(alpha 规则)
    POST /api/project/<pid>/texture/new              新建空白贴图
    POST /api/project/<pid>/model/associate          模型关联 + 改写命名空间
"""

import os

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import store
from services import texture as tex

bp = Blueprint("asset", __name__)


def _args():
    return (request.args.get("pack") or "",
            request.args.get("path") or "")


# ---------------------------------------------------------------- 页面


@bp.route("/project/<project_id>/paint")
def paint_page(project_id):
    return render_template("paint.html", project_id=project_id,
                           meta=ws.load_meta(project_id))


# ---------------------------------------------------------------- 贴图


@bp.route("/api/project/<project_id>/texture")
def api_texture(project_id):
    pack, rel = _args()
    if not pack or not rel:
        return jsonify({"ok": False, "error": "需要 pack 与 path"}), 400
    try:
        info = tex.load_info(project_id, pack, rel)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "texture": info,
                    "pillow": tex.pillow_ok()})


@bp.route("/api/project/<project_id>/texture", methods=["POST"])
def api_save_texture(project_id):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    rel = body.get("path")
    image = body.get("image")
    if not pack or not rel or not image:
        return jsonify({"ok": False, "error": "需要 pack/path/image"}), 400
    try:
        result = tex.save(project_id, pack, rel, image,
                          enforce=bool(body.get("enforce_alpha", True)))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    store.record_change(project_id, pack, rel, "modify")
    return jsonify(result)


@bp.route("/api/project/<project_id>/texture/new", methods=["POST"])
def api_new_texture(project_id):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack") or "resource"
    kind = body.get("kind") or "item"
    name = body.get("name")
    try:
        width = int(body.get("width") or 16)
        height = int(body.get("height") or 16)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "尺寸必须是整数"}), 400
    rel = body.get("path") or tex.suggest_path(kind, name or "texture")

    if not (1 <= width <= 256) or not (1 <= height <= 256):
        return jsonify({"ok": False,
                        "error": "画布尺寸需为 1-256"}), 400
    try:
        result = tex.create_blank(project_id, pack, rel, width, height)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    store.record_change(project_id, pack, rel, "add")
    return jsonify(result)


@bp.route("/api/project/<project_id>/texture/suggest")
def api_suggest(project_id):
    kind = request.args.get("kind", "item")
    name = request.args.get("name", "texture")
    return jsonify({"ok": True, "path": tex.suggest_path(kind, name)})


# ---------------------------------------------------------------- 模型


@bp.route("/api/project/<project_id>/model/associate", methods=["POST"])
def api_associate(project_id):
    """把模型文件与对象关联，自动改写 geometry 命名空间。"""
    body = request.get_json(silent=True) or {}
    pack = body.get("pack") or "resource"
    rel = body.get("path")
    ident = body.get("identifier")
    if not rel or not ident:
        return jsonify({"ok": False, "error": "需要 path 与 identifier"}), 400
    try:
        result = tex.associate_model(project_id, pack, rel, ident)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify(result)