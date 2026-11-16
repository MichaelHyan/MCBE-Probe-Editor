# -*- coding: utf-8 -*-
"""索引 / 对象浏览路由。

页面:
    GET /project/<pid>/index           对象列表(可按 kind/namespace 过滤)
    GET /project/<pid>/object/<ident>  对象详情(引用树)

API:
    GET /api/project/<pid>/index                索引总览
    GET /api/project/<pid>/objects              对象列表(过滤/分页)
    GET /api/project/<pid>/object/<ident>       单对象
    GET /api/project/<pid>/unbound              未绑定项
"""

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import pipeline

bp = Blueprint("index", __name__)


def _load(project_id):
    if not ws.valid_project_id(project_id):
        raise ValueError("非法项目 id")
    return pipeline.ensure_index(project_id)


# ---------------------------------------------------------------- 页面


@bp.route("/project/<project_id>/index")
def index_page(project_id):
    index = _load(project_id)
    return render_template("index.html", project_id=project_id,
                           meta=ws.load_meta(project_id),
                           stats=index.get("stats", {}))


@bp.route("/project/<project_id>/object/<path:ident>")
def object_page(project_id, ident):
    index = _load(project_id)
    obj = pipeline.find_object(index, ident)
    return render_template("object.html", project_id=project_id,
                           ident=ident, obj=obj, meta=ws.load_meta(project_id))


# ---------------------------------------------------------------- API


@bp.route("/api/project/<project_id>/index")
def api_index(project_id):
    index = _load(project_id)
    return jsonify({
        "ok": True,
        "project_id": project_id,
        "packs": index.get("packs", {}),
        "stats": index.get("stats", {}),
        "special_files": index.get("special_files", []),
        "structures": index.get("structures", []),
        "file_errors": index.get("file_errors", []),
        "generated": index.get("generated"),
    })


@bp.route("/api/project/<project_id>/objects")
def api_objects(project_id):
    index = _load(project_id)
    objects = index.get("objects") or {}

    kind = (request.args.get("kind") or "").strip()
    namespace = (request.args.get("namespace") or "").strip()
    q = (request.args.get("q") or "").strip().lower()

    rows = []
    namespaces = set()
    kinds = set()
    for ident, obj in objects.items():
        k = obj.get("kind")
        ns = obj.get("namespace")
        kinds.add(k)
        namespaces.add(ns)
        if kind and k != kind:
            continue
        if namespace and ns != namespace:
            continue
        if q and q not in ident.lower() and \
                q not in (obj.get("name") or "").lower() and \
                q not in (obj.get("lang_text") or "").lower() and \
                not any(q in str(k).lower()
                        for ref in (obj.get("references") or [])
                        if ref.get("role") == "lang"
                        for k in (ref.get("keys") or [])):
            continue
        rows.append({
            "identifier": ident,
            "kind": k,
            "kinds": obj.get("kinds") or [k],
            "namespace": ns,
            "name": obj.get("name"),
            "primary": obj.get("primary"),
            "ref_count": len(obj.get("references") or []),
            "warnings": obj.get("warnings") or [],
            "notes_count": len(obj.get("notes") or []),
            "lang_name": obj.get("lang_name"),
            "lang_text": obj.get("lang_text"),
        })

    rows.sort(key=lambda r: (r["kind"] or "", r["namespace"] or "",
                             r["name"] or ""))

    return jsonify({
        "ok": True,
        "total": len(objects),
        "filtered": len(rows),
        "kinds": sorted(kinds),
        "namespaces": sorted(namespaces),
        "objects": rows,
    })


@bp.route("/api/project/<project_id>/object/<path:ident>")
def api_object(project_id, ident):
    index = _load(project_id)
    obj = pipeline.find_object(index, ident)
    if not obj:
        return jsonify({"ok": False, "error": "对象不存在: %s" % ident}), 404
    return jsonify({"ok": True, "identifier": ident, "object": obj})


@bp.route("/api/project/<project_id>/unbound")
def api_unbound(project_id):
    index = _load(project_id)
    kind = (request.args.get("kind") or "").strip()
    items = index.get("unbound") or []
    if kind:
        items = [x for x in items if x.get("kind") == kind]

    counts = {}
    for x in index.get("unbound") or []:
        k = x.get("kind")
        counts[k] = counts.get(k, 0) + 1

    return jsonify({
        "ok": True,
        "counts": counts,
        "total": len(items),
        "items": items,
        "vanilla_recipes": index.get("vanilla_recipes") or [],
    })


@bp.route("/api/project/<project_id>/tree")
def api_tree(project_id):
    """按 namespace 分组的轻量对象树，供前端侧栏使用。"""
    index = _load(project_id)
    objects = index.get("objects") or {}
    tree = {}
    for ident, obj in objects.items():
        ns = obj.get("namespace") or ""
        kind = obj.get("kind") or ""
        tree.setdefault(ns, {}).setdefault(kind, []).append({
            "identifier": ident,
            "name": obj.get("name"),
            "warnings": len(obj.get("warnings") or []),
        })
    for ns in tree:
        for kind in tree[ns]:
            tree[ns][kind].sort(key=lambda x: x["name"] or "")
    return jsonify({"ok": True, "tree": tree})