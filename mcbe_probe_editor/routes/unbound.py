# -*- coding: utf-8 -*-
"""未绑定项视图（对应 plan.md 1.3 / 1.4 的探测产物侧展示）。

展示无法归属到对象的文件与键：
  * recipe / spawn_rules / feature / loot_table / trading / 动画等未关联文件
  * 未绑定语言键（含包级文本、组件内引用）

API:
    GET /api/project/<pid>/unbound          已有（在 index.py 中），此处提供页面
    GET /api/project/<pid>/unbound/detail   分页 + 搜索
"""

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import pipeline

bp = Blueprint("unbound", __name__)


@bp.route("/project/<project_id>/unbound")
def unbound_page(project_id):
    return render_template("unbound.html", project_id=project_id,
                           meta=ws.load_meta(project_id))


@bp.route("/api/project/<project_id>/unbound/detail")
def api_unbound_detail(project_id):
    index = pipeline.ensure_index(project_id)
    items = index.get("unbound") or []

    kind = (request.args.get("kind") or "").strip()
    q = (request.args.get("q") or "").strip().lower()
    try:
        offset = max(0, int(request.args.get("offset") or 0))
        limit = min(500, max(1, int(request.args.get("limit") or 100)))
    except ValueError:
        offset, limit = 0, 100

    counts = {}
    for x in items:
        k = x.get("kind")
        counts[k] = counts.get(k, 0) + 1

    rows = items
    if kind:
        rows = [x for x in rows if x.get("kind") == kind]
    if q:
        rows = [x for x in rows
                if q in str(x.get("path", "")).lower()
                or q in str(x.get("key", "")).lower()
                or q in str(x.get("identifier", "")).lower()]

    total = len(rows)
    page = rows[offset:offset + limit]
    return jsonify({
        "ok": True,
        "counts": counts,
        "all_total": len(items),
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": page,
        "vanilla_recipes": index.get("vanilla_recipes") or [],
    })