# -*- coding: utf-8 -*-
"""组件编辑路由(对应 plan.md 3.1-3.3)。

页面:
    GET /project/<pid>/edit/<path:ident>    对象编辑页

API:
    GET  /api/project/<pid>/edit/<ident>        编辑数据(文件分组/组件/语言/贴图)
    GET  /api/project/<pid>/components          组件库(按 kind+fv)
    POST /api/project/<pid>/edit/<ident>/file   保存整个文件 JSON
    POST /api/project/<pid>/edit/<ident>/component  增删改单个组件
    POST /api/project/<pid>/edit/<ident>/lang       更新语言键
"""

import os

from flask import Blueprint, jsonify, render_template, request

from services import workspace as ws
from services import store
from services import database as db
from services import pipeline

bp = Blueprint("editor", __name__)

EDITABLE_JSON_ROLES = {
    "primary", "resource_item", "block_ref", "client_entity",
    "attachable", "animation_controller", "spawn_rules",
    "loot_table", "recipe", "feature", "feature_rule", "trading",
}


def _locale_of(path):
    """从语言文件路径取 locale 名（texts/zh_CN.lang -> zh_CN）。"""
    base = os.path.basename(path or "").replace("\\", "/")
    if base.lower().endswith(".lang"):
        return base[:-5]
    return base


def _index(project_id):
    return pipeline.ensure_index(project_id)


def _object(project_id, ident):
    index = _index(project_id)
    obj = pipeline.find_object(index, ident)
    if not obj:
        raise KeyError("对象不存在: %s" % ident)
    return index, obj


def _file_payload(project_id, pack, rel, fv, role):
    """读取文件并给出基础信息。"""
    try:
        info = store.file_info(project_id, pack, rel)
        data = store.read_json(project_id, pack, rel)
        error = None
    except Exception as exc:
        info = {"pack": pack, "path": rel}
        data = None
        error = str(exc)
    scopes = {"components": {}, "component_groups": {}, "events": {}}
    if isinstance(data, dict):
        for key, val in data.items():
            if not (key.startswith("minecraft:") and isinstance(val, dict)):
                continue
            if isinstance(val.get("components"), dict):
                scopes["components"] = val.get("components") or {}
            if isinstance(val.get("component_groups"), dict):
                scopes["component_groups"] = val.get("component_groups") or {}
            if isinstance(val.get("events"), dict):
                scopes["events"] = val.get("events") or {}
            break
    return {
        "role": role,
        "pack": pack,
        "path": rel,
        "format_version": fv,
        "info": info,
        "data": data,
        "scopes": scopes,
        "error": error,
    }


# ---------------------------------------------------------------- 页面


@bp.route("/project/<project_id>/edit/<path:ident>")
def edit_page(project_id, ident):
    index = _index(project_id)
    obj = pipeline.find_object(index, ident)
    return render_template("editor.html", project_id=project_id,
                           ident=ident, obj=obj,
                           meta=ws.load_meta(project_id))


# ---------------------------------------------------------------- API: 编辑数据


@bp.route("/api/project/<project_id>/edit/<path:ident>")
def api_edit_data(project_id, ident):
    try:
        index, obj = _object(project_id, ident)
    except KeyError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    files = []
    lang_map = {}      # key -> [ {locale, pack, path} ]
    textures = []
    geometries = []

    prim = obj.get("primary")
    if prim:
        files.append(_file_payload(project_id, prim.get("pack"),
                                   prim.get("path"),
                                   prim.get("format_version"), "primary"))

    for ref in obj.get("references") or []:
        role = ref.get("role")
        if role == "lang":
            rpath = ref.get("path")
            loc = _locale_of(rpath)
            for key in ref.get("keys") or []:
                bucket = lang_map.setdefault(key, [])
                if not any(x.get("path") == rpath for x in bucket):
                    bucket.append({"locale": loc, "pack": ref.get("pack"),
                                   "path": rpath})
            continue
        if role in ("texture", "entity_texture"):
            textures.append(dict(ref))
            continue
        if role == "geometry":
            geometries.append(dict(ref))
            continue
        if role == "texture_index":
            continue
        if role in EDITABLE_JSON_ROLES and ref.get("path"):
            files.append(_file_payload(project_id, ref.get("pack"),
                                       ref.get("path"),
                                       ref.get("format_version"), role))

    # 语言键当前值：逐个 (key, pack, path) 读取，保留全部 locale
    lang_keys = []
    for key, entries in lang_map.items():
        enriched = []
        for ent in entries:
            value = ""
            try:
                ftext = store.read_text(project_id, ent["pack"], ent["path"])
                for row in store.parse_lang(ftext):
                    if row.get("key") == key:
                        value = row.get("value") or ""
                        break
            except Exception:
                pass
            enriched.append({
                "locale": ent["locale"],
                "pack": ent["pack"],
                "path": ent["path"],
                "value": value,
            })
        # 中文优先排序，便于阅读
        enriched.sort(key=lambda x: (0 if str(x["locale"]).lower().startswith("zh") else 1,
                                     x["locale"]))
        lang_keys.append({"key": key, "entries": enriched})
    lang_keys.sort(key=lambda x: x["key"])

    # 组件库(按 primary 的 kind + fv)
    components = None
    if prim:
        kind = prim.get("kind") or obj.get("kind")
        components = db.query_components(project_id, kind,
                                         prim.get("format_version"))

    return jsonify({
        "ok": True,
        "identifier": ident,
        "object": obj,
        "files": files,
        "lang_keys": lang_keys,
        "textures": textures,
        "geometries": geometries,
        "components": components,
    })


@bp.route("/api/project/<project_id>/components")
def api_components(project_id):
    kind = request.args.get("kind", "")
    fv = request.args.get("fv", "")
    if not kind or not fv:
        return jsonify({"ok": False, "error": "需要 kind 与 fv"}), 400
    data = db.query_components(project_id, kind, fv)
    return jsonify({"ok": True, "components": data})


@bp.route("/api/project/<project_id>/buckets")
def api_buckets(project_id):
    return jsonify({
        "ok": True,
        "temp": db.list_temp_buckets(project_id),
        "official": db.list_official_buckets(),
    })


# ---------------------------------------------------------------- API: 保存文件


@bp.route("/api/project/<project_id>/edit/<path:ident>/file", methods=["POST"])
def api_save_file(project_id, ident):
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    rel = body.get("path")
    data = body.get("data")
    if not pack or not rel:
        return jsonify({"ok": False, "error": "缺少 pack/path"}), 400
    if data is None:
        return jsonify({"ok": False, "error": "缺少 data"}), 400

    try:
        store.write_json(project_id, pack, rel, data)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    store.record_change(project_id, pack, rel, "modify")
    return jsonify({"ok": True})


@bp.route("/api/project/<project_id>/edit/<path:ident>/component",
           methods=["POST"])
def api_edit_component(project_id, ident):
    """在对象主文件里增 / 改 / 删一个组件。

    body: {
      "pack","path",          目标文件
      "container",            顶层键(如 minecraft:item)，可选自动推断
      "name",                 组件名
      "value"|null,           新值(删除时省略/为 null 且 op=delete)
      "op": "set" | "delete"
    }
    """
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    rel = body.get("path")
    name = body.get("name")
    op = body.get("op") or "set"
    container = body.get("container")

    if not pack or not rel or not name:
        return jsonify({"ok": False, "error": "缺少 pack/path/name"}), 400

    try:
        data = store.read_json(project_id, pack, rel)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "文件根不是对象"}), 400

    if not container:
        for key, val in data.items():
            if key.startswith("minecraft:") and isinstance(val, dict):
                container = key
                break
    if not container or not isinstance(data.get(container), dict):
        return jsonify({"ok": False, "error": "找不到组件容器"}), 400

    body_obj = data[container]
    comps = body_obj.get("components")
    if not isinstance(comps, dict):
        comps = {}
        body_obj["components"] = comps

    if op == "delete":
        if name not in comps:
            return jsonify({"ok": False, "error": "组件不存在"}), 404
        del comps[name]
    else:
        if "value" not in body:
            return jsonify({"ok": False, "error": "缺少 value"}), 400
        comps[name] = body["value"]

    try:
        store.write_json(project_id, pack, rel, data)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    store.record_change(project_id, pack, rel, "modify")
    return jsonify({"ok": True, "container": container,
                    "components": comps})


def _resolve_scope(root, scope):
    """把 scope 字符串解析到 (容器 dict, 错误信息)。

    scope: "components" | "component_groups" | "component_groups.<组名>" | "events"
    """
    if not isinstance(root, dict):
        return None, "文件根不是对象"

    container = None
    for key, val in root.items():
        if key.startswith("minecraft:") and isinstance(val, dict):
            container = key
            break
    if container is None:
        return None, "找不到 minecraft:* 容器"

    body = root[container]

    if scope in (None, "", "components"):
        if not isinstance(body.get("components"), dict):
            body["components"] = {}
        return body["components"], None

    if scope == "component_groups":
        if not isinstance(body.get("component_groups"), dict):
            body["component_groups"] = {}
        return body["component_groups"], None

    if scope.startswith("component_groups."):
        gname = scope[len("component_groups."):]
        groups = body.get("component_groups")
        if not isinstance(groups, dict):
            return None, "该文件没有 component_groups"
        grp = groups.get(gname)
        if not isinstance(grp, dict):
            return None, "组件组不存在: %s" % gname
        # 标准写法：组体本身就是组件集合，不再套 components 层
        return grp, None

    if scope == "events":
        if not isinstance(body.get("events"), dict):
            body["events"] = {}
        return body["events"], None

    return None, "未知 scope: %s" % scope


@bp.route("/api/project/<project_id>/edit/<path:ident>/entry", methods=["POST"])
def api_edit_entry(project_id, ident):
    """通用条目增删改（components / component_groups[.<组>] / events）。

    body: {pack, path, scope, name, value?, op?}
      * scope="component_groups" 且 op="set_group" 时，value 为整组内容
    """
    body = request.get_json(silent=True) or {}
    pack = body.get("pack")
    rel = body.get("path")
    scope = body.get("scope") or "components"
    name = body.get("name")
    op = body.get("op") or "set"

    if not pack or not rel or not name:
        return jsonify({"ok": False, "error": "缺少 pack/path/name"}), 400

    try:
        data = store.read_json(project_id, pack, rel)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    # 整组新增/替换
    if op == "set_group" and scope == "component_groups":
        root_container = None
        for key, val in (data or {}).items():
            if key.startswith("minecraft:") and isinstance(val, dict):
                root_container = key
                break
        if root_container is None:
            return jsonify({"ok": False, "error": "找不到容器"}), 400
        body_obj = data[root_container]
        groups = body_obj.get("component_groups")
        if not isinstance(groups, dict):
            groups = {}
            body_obj["component_groups"] = groups
        if "value" not in body:
            return jsonify({"ok": False, "error": "缺少 value"}), 400
        groups[name] = body["value"]
        try:
            store.write_json(project_id, pack, rel, data)
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        store.record_change(project_id, pack, rel, "modify")
        return jsonify({"ok": True, "scope": scope, "name": name})

    target, err = _resolve_scope(data, scope)
    if target is None:
        return jsonify({"ok": False, "error": err}), 400

    if op == "delete":
        if name not in target:
            return jsonify({"ok": False, "error": "条目不存在"}), 404
        del target[name]
    else:
        if "value" not in body:
            return jsonify({"ok": False, "error": "缺少 value"}), 400
        target[name] = body["value"]

    try:
        store.write_json(project_id, pack, rel, data)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    store.record_change(project_id, pack, rel, "modify")
    return jsonify({"ok": True, "scope": scope, "name": name})


@bp.route("/api/project/<project_id>/edit/<path:ident>/lang", methods=["POST"])
def api_edit_lang(project_id, ident):
    """更新该对象的语言键。

    新格式: {"updates": [{"key":.., "pack":.., "path":.., "value":..}]}
    旧格式: {"updates": {key: value}, "pack":.., "path":..} 仍兼容
    """
    body = request.get_json(silent=True) or {}
    updates = body.get("updates")

    if not updates:
        return jsonify({"ok": False, "error": "没有需要更新的键"}), 400

    applied = []
    missing = []

    # ---------------- 新格式：逐 locale 精确写入 ----------------
    if isinstance(updates, list):
        # 按 (pack, path) 分组，减少文件读写
        grouped = {}
        for u in updates:
            if not isinstance(u, dict):
                continue
            key = u.get("key")
            pack = u.get("pack")
            rel = u.get("path")
            if not key or not pack or not rel:
                continue
            grouped.setdefault((pack, rel), {})[key] = u.get("value", "")

        for (pack, rel), kv in grouped.items():
            try:
                ftext = store.read_text(project_id, pack, rel)
            except Exception:
                continue
            new_text, done, miss = store.update_lang_keys(ftext, kv)
            if done:
                store.write_text(project_id, pack, rel, new_text)
                store.record_change(project_id, pack, rel, "modify")
                applied.extend(done)
            missing.extend(miss)

        return jsonify({"ok": True, "applied": sorted(set(applied)),
                        "missing": sorted(set(missing))})

    # ---------------- 旧格式：{key: value} ----------------
    if not isinstance(updates, dict):
        return jsonify({"ok": False, "error": "updates 格式不正确"}), 400

    pack = body.get("pack")
    rel = body.get("path")
    targets = []
    if pack and rel:
        targets.append((pack, rel))
    else:
        try:
            _, obj = _object(project_id, ident)
        except KeyError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 404
        for ref in obj.get("references") or []:
            if ref.get("role") == "lang":
                targets.append((ref.get("pack"), ref.get("path")))

    if not targets:
        return jsonify({"ok": False, "error": "该对象没有语言文件"}), 404

    applied_all, missing_all = [], list(updates.keys())
    for p, r in targets:
        try:
            ftext = store.read_text(project_id, p, r)
        except Exception:
            continue
        new_text, done, miss = store.update_lang_keys(ftext, updates)
        if done:
            store.write_text(project_id, p, r, new_text)
            store.record_change(project_id, p, r, "modify")
            applied_all.extend(done)
            missing_all = miss

    return jsonify({"ok": True, "applied": sorted(set(applied_all)),
                    "missing": missing_all})
