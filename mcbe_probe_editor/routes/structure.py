# -*- coding: utf-8 -*-
"""结构降版本路由(对应 plan.md 4.3)。

API:
    GET  /api/project/<pid>/structures           列出结构 + 版本信息
    POST /api/project/<pid>/structure/inspect    单文件版本检查
    POST /api/project/<pid>/structure/downgrade  执行降版本(fv2->fv1)
"""

import os

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import pipeline
from services import structure as st

bp = Blueprint("structure", __name__)


@bp.route("/project/<project_id>/structures")
def structures_page(project_id):
    return render_template("structures.html", project_id=project_id,
                           meta=ws.load_meta(project_id))


@bp.route("/api/project/<project_id>/structures")
def api_structures(project_id):
    index = pipeline.ensure_index(project_id)
    rows = []
    for item in index.get("structures") or []:
        pack = item.get("pack")
        rel = item.get("path")
        try:
            info = st.inspect(project_id, pack, rel)
        except Exception as exc:
            info = {"pack": pack, "path": rel, "error": str(exc)}
        info["size"] = item.get("size")
        rows.append(info)
    return jsonify({"ok": True, "structures": rows})


@bp.route("/api/project/<project_id>/structure/inspect", methods=["POST"])
def api_inspect(project_id):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    rel = body.get("path")
    if not pack or not rel:
        return jsonify({"ok": False, "error": "需要 pack/path"}), 400
    try:
        info = st.inspect(project_id, pack, rel)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "info": info})


@bp.route("/api/project/<project_id>/structure/downgrade", methods=["POST"])
def api_downgrade(project_id):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    rel = body.get("path")
    backup = bool(body.get("backup", True))

    targets = []
    if pack and rel:
        targets.append((pack, rel))
    else:
        index = pipeline.ensure_index(project_id)
        for item in index.get("structures") or []:
            targets.append((item.get("pack"), item.get("path")))

    if not targets:
        return jsonify({"ok": False, "error": "没有可处理的结构文件"}), 404

    results = []
    for p, r in targets:
        try:
            res = st.downgrade(project_id, p, r, backup=backup)
            res.update({"pack": p, "path": r})
        except Exception as exc:
            res = {"ok": False, "pack": p, "path": r, "error": str(exc)}
        results.append(res)

    done = sum(1 for x in results if x.get("ok") and not x.get("skipped"))
    skip = sum(1 for x in results if x.get("skipped"))
    fail = sum(1 for x in results if not x.get("ok"))
    return jsonify({"ok": fail == 0, "converted": done,
                    "skipped": skip, "failed": fail, "results": results})