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
from services import objects as objs
from services import texture as tex
from services import templates as tpl_mod

bp = Blueprint("editor", __name__)

EDITABLE_JSON_ROLES = {
    "primary", "resource_item", "block_ref", "client_entity",
    "attachable", "animation_controller", "spawn_rules",
    "loot_table", "recipe", "feature", "feature_rule", "trading",
    "blocks_json", "terrain_texture", "animation",
    "attachable_animation", "attachable_animation_controller",
    "animation_controller_behavior", "animation_controller_resource",
    "render_controller", "geometry",
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
            if ref.get("path") and ref.get("resolved", True):
                files.append(_file_payload(project_id, ref.get("pack"),
                                           ref.get("path"),
                                           ref.get("format_version"),
                                           "geometry"))
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


# ---------------------------------------------------------------- 关联槽位

REGISTRATION_TOP = {
    "resource_item": "minecraft:item",
    "attachable": "minecraft:attachable",
    "client_entity": "minecraft:client_entity",
    "spawn_rules": "minecraft:spawn_rules",
}

ANIM_TOP = {
    "animation": ("animations", "animation."),
    "attachable_animation": ("animations", "animation."),
    "animation_controller_behavior": ("animation_controllers",
                                      "controller.animation."),
    "animation_controller_resource": ("animation_controllers",
                                      "controller.animation."),
    "attachable_animation_controller": ("animation_controllers",
                                        "controller.animation."),
}

HOST_ANIM_SLOTS = ("attachable_animation", "attachable_animation_controller")

CANDIDATE_PREFIX = {
    "resource_item": ("resource", "items/"),
    "attachable": ("resource", "attachables/"),
    "client_entity": ("resource", "entity/"),
    "geometry": ("resource", "models/"),
    "texture": ("resource", "textures/"),
    "animation": ("resource", "animations/"),
    "attachable_animation": ("resource", "animations/"),
    "animation_controller_behavior": ("behavior", "animation_controllers/"),
    "animation_controller_resource": ("resource", "animation_controllers/"),
    "attachable_animation_controller": ("resource", "animation_controllers/"),
    "spawn_rules": ("behavior", "spawn_rules/"),
    "loot_table": ("behavior", "loot_tables/"),
    "trading": ("behavior", "trading/"),
    "feature": ("behavior", "features/"),
    "feature_rule": ("behavior", "feature_rules/"),
    "blocks_json": ("resource", "blocks.json"),
    "terrain_texture": ("resource", "textures/terrain_texture.json"),
}

# 候选不是目录扫描、而是「固定共享文件」的槽
EXACT_FILE_SLOTS = {"blocks_json", "terrain_texture"}


def _short_anim(long_name):
    if long_name.startswith("controller.animation."):
        return long_name[len("controller.animation."):]
    if long_name.startswith("animation."):
        return long_name[len("animation."):]
    return long_name


def _ref_host(obj, want):
    for ref in obj.get("references") or []:
        if ref.get("role") == want and ref.get("path"):
            return ref.get("pack"), ref.get("path")
    return None, None


def _host_file(obj, slot):
    if slot == "animation_controller_behavior":
        prim = obj.get("primary") or {}
        return prim.get("pack"), prim.get("path")
    if slot in HOST_ANIM_SLOTS:
        return _ref_host(obj, "attachable")
    if slot == "geometry":
        p, r = _ref_host(obj, "client_entity")
        if r:
            return p, r
        return _ref_host(obj, "attachable")
    return _ref_host(obj, "client_entity")


def _link_registration(project_id, ident, pack, rel, slot):
    top = REGISTRATION_TOP[slot]
    data = store.read_json(project_id, pack, rel)
    body = data.get(top)
    if not isinstance(body, dict):
        return False, "该文件不是 %s，无法关联" % top
    desc = body.get("description")
    if not isinstance(desc, dict):
        desc = {}
        body["description"] = desc
    if desc.get("identifier") != ident:
        desc["identifier"] = ident
        store.write_json(project_id, pack, rel, data)
        store.record_change(project_id, pack, rel, "modify")
    return True, None


def _link_geometry(project_id, ident, pack, rel, obj, namespace, name):
    # 模组规则：geometry 标识为单段 geometry.<name>（与新建模板一致）
    gid = "geometry.%s" % name
    res = {"ok": True, "changed": 0, "target": gid}
    try:
        data = store.read_json(project_id, pack, rel)
        changed = 0
        geos = data.get("minecraft:geometry")
        if isinstance(geos, list):
            for item in geos:
                if not isinstance(item, dict):
                    continue
                desc = item.get("description")
                if isinstance(desc, dict) and desc.get("identifier") != gid:
                    desc["identifier"] = gid
                    changed += 1
        else:
            for key in list(data.keys()):
                if isinstance(key, str) and key.startswith("geometry.") \
                        and key != gid:
                    data[gid] = data.pop(key)
                    changed += 1
        if changed:
            store.write_json(project_id, pack, rel, data)
            store.record_change(project_id, pack, rel, "modify")
        res["changed"] = changed
    except Exception as exc:
        res = {"ok": False, "reason": str(exc), "target": gid}

    hpack, hrel = _host_file(obj, "geometry")
    if hpack and hrel and store.exists(project_id, hpack, hrel):
        data = store.read_json(project_id, hpack, hrel)
        body = None
        for key, val in (data or {}).items():
            if key.startswith("minecraft:") and isinstance(val, dict):
                body = val
                break
        if body is not None:
            desc = body.get("description")
            if isinstance(desc, dict):
                geo = desc.get("geometry")
                if isinstance(geo, dict):
                    if gid not in geo.values():
                        geo["default"] = gid
                        store.write_json(project_id, hpack, hrel, data)
                        store.record_change(project_id, hpack, hrel, "modify")
    return res


def _link_animation(project_id, ident, pack, rel, slot, obj):
    key, prefix = ANIM_TOP[slot]
    data = store.read_json(project_id, pack, rel)
    defs = data.get(key)
    if not isinstance(defs, dict) or not defs:
        return False, "该文件不含 %s 定义" % key

    hpack, hrel = _host_file(obj, slot)
    if not hpack or not hrel:
        return False, "该对象缺少宿主注册文件（client_entity / attachable）"

    host = store.read_json(project_id, hpack, hrel)
    body = None
    for k, v in (host or {}).items():
        if k.startswith("minecraft:") and isinstance(v, dict):
            body = v
            break
    if body is None:
        return False, "宿主文件结构异常"
    desc = body.get("description")
    if not isinstance(desc, dict):
        desc = {}
        body["description"] = desc
    anims = desc.get("animations")
    if not isinstance(anims, dict):
        anims = {}
        desc["animations"] = anims

    added = 0
    for full in defs:
        if not isinstance(full, str) or not full.startswith(prefix):
            continue
        short = _short_anim(full)
        if anims.get(short) == full:
            continue
        anims[short] = full
        added += 1
    if added:
        store.write_json(project_id, hpack, hrel, host)
        store.record_change(project_id, hpack, hrel, "modify")
    return {"ok": True, "added": added, "host": "%s/%s" % (hpack, hrel)}


BLOCK_FACES = ("up", "down", "south", "north", "west", "east")


def _read_blocks_json(project_id):
    try:
        bj = store.read_json(project_id, "resource", objs.BLOCKS_JSON)
        if isinstance(bj, dict):
            return bj
    except Exception:
        pass
    return {"format_version": "1.16.100"}


def _ensure_blocks_json(project_id, ident, name):
    """确保 blocks.json 有该方块条目。返回 (face->texkey 映射, 写入文件列表)。

    已有条目**保留其既有键名**（可能是自定义的，如 sixface_top），只补缺失面。
    """
    created = []
    bj = _read_blocks_json(project_id)
    bj.setdefault("format_version", "1.16.100")

    entry = bj.get(ident)
    if not isinstance(entry, dict):
        entry = {}
    tex = entry.get("textures")
    if not isinstance(tex, dict):
        tex = {}

    changed = False
    for face in BLOCK_FACES:
        if face not in tex:
            tex[face] = "%s_%s" % (name, face)
            changed = True

    entry["textures"] = tex
    if not entry.get("sound"):
        entry["sound"] = "stone"
        changed = True

    if bj.get(ident) != entry:
        bj[ident] = entry
        changed = True

    if changed:
        store.write_json(project_id, "resource", objs.BLOCKS_JSON, bj)
        store.record_change(project_id, "resource", objs.BLOCKS_JSON,
                            "modify")
        created.append(objs.BLOCKS_JSON)

    return dict(tex), created


def _block_texture_keys(ident, texmap, name):
    """从 face->texkey 映射取出实际使用到的贴图键（去重，含非标准面键）。"""
    keys = []
    for face in BLOCK_FACES:
        v = texmap.get(face)
        if isinstance(v, str) and v and v not in keys:
            keys.append(v)
    for k, v in texmap.items():
        if isinstance(v, str) and v and v not in keys:
            keys.append(v)
    if not keys:
        keys = ["%s_%s" % (name, f) for f in BLOCK_FACES]
    return keys


def _existing_block_keys(project_id, ident, name):
    """只读：该方块在 blocks.json 中实际引用的贴图键（不写盘）。"""
    bj = _read_blocks_json(project_id)
    entry = bj.get(ident)
    tex = entry.get("textures") if isinstance(entry, dict) else None
    return _block_texture_keys(ident, tex if isinstance(tex, dict) else {}, name)


def _ensure_terrain(project_id, name, texkeys, png=None, overwrite=False):
    """按给定贴图键写 terrain_texture.json。

    png 为空时用约定路径 textures/blocks/<name>.png。
    overwrite=False：只补缺失键，已存在的键保持原值。
    overwrite=True ：全部改写为 png。
    """
    created = []
    try:
        tt = store.read_json(project_id, "resource",
                             objs.TERRAIN_TEXTURE_INDEX)
        if not isinstance(tt, dict):
            tt = {}
    except Exception:
        tt = {}
    tt.setdefault("resource_pack_name", "vanilla")
    tt.setdefault("texture_name", "atlas.terrain")
    tdata = tt.get("texture_data")
    if not isinstance(tdata, dict):
        tdata = {}
        tt["texture_data"] = tdata

    path = png or objs.block_texture_path(name)
    if path.lower().endswith(".png"):
        path = path[:-4]

    changed = False
    for key in texkeys:
        if not key:
            continue
        val = {"textures": [path]}
        if overwrite:
            if tdata.get(key) != val:
                tdata[key] = val
                changed = True
        elif key not in tdata:
            tdata[key] = val
            changed = True

    if changed:
        store.write_json(project_id, "resource",
                         objs.TERRAIN_TEXTURE_INDEX, tt)
        store.record_change(project_id, "resource",
                            objs.TERRAIN_TEXTURE_INDEX, "modify")
        created.append(objs.TERRAIN_TEXTURE_INDEX)
    return created


def _link_block_texture(project_id, ident, name, png, overwrite=True):
    """绑定方块贴图。

    overwrite=True （关联）：该方块引用的全部贴图键统一切换到该 png。
    overwrite=False（新建）：只补缺失索引，保留已有六面独立贴图。
    """
    created = []
    texmap, c1 = _ensure_blocks_json(project_id, ident, name)
    created.extend(c1)
    keys = _block_texture_keys(ident, texmap, name)
    created.extend(_ensure_terrain(project_id, name, keys, png,
                                   overwrite=overwrite))
    return {"ok": True, "created": created, "png": png,
            "overwrite": overwrite, "texture_keys": keys}


def _link_material(project_id, ident, name):
    png = objs.block_texture_path(name)
    return _link_block_texture(project_id, ident, name, png, overwrite=False)


@bp.route("/api/project/<project_id>/edit/<path:ident>/slots")
def api_slots(project_id, ident):
    try:
        index, obj = _object(project_id, ident)
    except KeyError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    kind = obj.get("kind")
    slots = obj.get("slots") or {}
    out = []
    for key, s in slots.items():
        pack, prefix = CANDIDATE_PREFIX.get(key, (s.get("pack"), None))
        cands = []
        # 精确共享文件槽：候选就是该文件本身，不递归目录
        if key in EXACT_FILE_SLOTS and prefix:
            root = ws.resolve_pack_dir(project_id, pack)
            if root and os.path.isfile(
                    os.path.join(root, prefix.replace("/", os.sep))):
                cands.append({"pack": pack, "path": prefix})
            item = dict(s)
            item["candidates"] = cands
            out.append(item)
            continue
        if prefix:
            root = ws.resolve_pack_dir(project_id, pack)
            if root:
                base = os.path.join(root, prefix.replace("/", os.sep))
                exts = (".png", ".tga") if s.get("file_kind") == "image" \
                    else (".json",)
                if os.path.isdir(base):
                    for dirpath, _d, fns in os.walk(base):
                        for fn in sorted(fns):
                            if not fn.lower().endswith(exts):
                                continue
                            ap = os.path.join(dirpath, fn)
                            rel = os.path.relpath(ap, root).replace("\\", "/")
                            cands.append({"pack": pack, "path": rel})
        item = dict(s)
        item["candidates"] = cands
        out.append(item)
    return jsonify({"ok": True, "identifier": ident, "kind": kind,
                    "slots": out})


@bp.route("/api/project/<project_id>/edit/<path:ident>/slots/link",
          methods=["POST"])
def api_slot_link(project_id, ident):
    body = request.get_json(silent=True) or {}
    slot = body.get("slot")
    pack = body.get("pack")
    rel = body.get("path")
    if not slot or not pack or not rel:
        return jsonify({"ok": False, "error": "缺少 slot/pack/path"}), 400

    try:
        _index_, obj = _object(project_id, ident)
    except KeyError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    if not store.exists(project_id, pack, rel):
        return jsonify({"ok": False, "error": "文件不存在"}), 404

    ns = ident.partition(":")[0]
    name = ident.partition(":")[2]
    try:
        if slot in REGISTRATION_TOP:
            ok, err = _link_registration(project_id, ident, pack, rel, slot)
            if not ok:
                return jsonify({"ok": False, "error": err}), 400
            result = {"ok": True}
        elif slot == "geometry":
            result = _link_geometry(project_id, ident, pack, rel, obj, ns, name)
        elif slot in ANIM_TOP:
            result = _link_animation(project_id, ident, pack, rel, slot, obj)
        elif slot == "texture" and obj.get("kind") == "item":
            low = (rel or "").lower()
            if not low.endswith((".png", ".tga")):
                return jsonify({"ok": False,
                                "error": "物品贴图槽需要图片文件（png/tga）"}), 400
            ok = objs.register_item_texture(project_id, name, rel)
            result = {"ok": True, "registered": ok,
                      "path": rel, "key": name}
        elif slot == "texture" and obj.get("kind") == "block":
            low = (rel or "").lower()
            if not low.endswith((".png", ".tga")):
                return jsonify({"ok": False,
                                "error": "方块贴图槽需要图片文件（png/tga）"}), 400
            result = _link_block_texture(project_id, ident, name, rel,
                                         overwrite=True)
        elif slot == "blocks_json":
            texmap, bl = _ensure_blocks_json(project_id, ident, name)
            tl = _ensure_terrain(project_id, name,
                                 _block_texture_keys(ident, texmap, name))
            result = {"ok": True, "created": bl + tl,
                      "texture_keys": _block_texture_keys(ident, texmap, name)}
        elif slot == "terrain_texture":
            keys = _existing_block_keys(project_id, ident, name)
            result = {"ok": True,
                      "created": _ensure_terrain(project_id, name, keys),
                      "texture_keys": keys}
        elif slot == "material":
            result = _link_material(project_id, ident, name)
        else:
            return jsonify({"ok": False,
                            "error": "该槽位不支持手动关联"}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    try:
        pipeline.run_probe(project_id)
    except Exception:
        pass
    return jsonify({"ok": True, "slot": slot, "result": result})


@bp.route("/api/project/<project_id>/edit/<path:ident>/slots/create",
          methods=["POST"])
def api_slot_create(project_id, ident):
    body = request.get_json(silent=True) or {}
    slot = body.get("slot")
    ac_names = body.get("animation_controller_names") or []
    if not slot:
        return jsonify({"ok": False, "error": "缺少 slot"}), 400

    try:
        _index_, obj = _object(project_id, ident)
    except KeyError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    kind = obj.get("kind")
    ns = ident.partition(":")[0]
    name = ident.partition(":")[2]
    created, warnings = [], []

    for p in ("behavior", "resource"):
        try:
            ws.ensure_pack_dir(project_id, p)
        except Exception:
            pass

    def _write(pack, rel, data):
        if store.exists(project_id, pack, rel):
            warnings.append("已存在，跳过: %s/%s" % (pack, rel))
            return False
        store.write_json(project_id, pack, rel, data)
        store.record_change(project_id, pack, rel, "add")
        created.append({"pack": pack, "path": rel})
        return True

    try:
        if slot == "resource_item" and kind == "item":
            _write("resource", objs.resource_item_path(ns, name),
                   objs.resource_item_template(ident, name))
            if objs._ensure_item_texture_index(project_id, ns, name):
                created.append({"pack": "resource",
                                "path": objs.ITEM_TEXTURE_INDEX})
            png = objs.ensure_blank_texture(project_id, "item", ns, name)
            if png:
                created.append({"pack": "resource", "path": png})
        elif slot == "texture_index" and kind == "item":
            if objs._ensure_item_texture_index(project_id, ns, name):
                created.append({"pack": "resource",
                                "path": objs.ITEM_TEXTURE_INDEX})
            png = objs.ensure_blank_texture(project_id, "item", ns, name)
            if png:
                created.append({"pack": "resource", "path": png})
        elif slot == "attachable" and kind == "item":
            _write("resource", objs.attachable_path(name),
                   objs.attachable_template(ident, ns, name))
            png = objs.ensure_blank_texture(project_id, "attachable", ns, name)
            if png:
                created.append({"pack": "resource", "path": png})
        elif slot == "client_entity" and kind == "entity":
            _write("resource", objs.client_entity_path(name),
                   objs.client_entity_template(ident, ns, name))
            png = objs.ensure_blank_texture(project_id, "entity", ns, name)
            if png:
                created.append({"pack": "resource", "path": png})
        elif slot == "geometry" and kind in ("entity", "item"):
            _write("resource", objs.model_path(name), objs.model_template(name))
        elif slot == "texture" and kind == "item":
            png = objs.texture_path("item", ns, name)
            if not store.exists(project_id, "resource", png):
                try:
                    tex.create_blank(project_id, "resource", png, 16, 16)
                    store.record_change(project_id, "resource", png, "add")
                    created.append({"pack": "resource", "path": png})
                except Exception as exc:
                    return jsonify({"ok": False,
                                    "error": str(exc)}), 400
            if objs.register_item_texture(project_id, name, png):
                created.append({"pack": "resource",
                                "path": objs.ITEM_TEXTURE_INDEX})
        elif slot == "texture" and kind == "entity":
            png = objs.ensure_blank_texture(project_id, "entity", ns, name)
            if png:
                created.append({"pack": "resource", "path": png})
                # 回填 client_entity 的贴图引用
                hpack, hrel = _host_file(obj, "texture")
                if hpack and hrel and store.exists(project_id, hpack, hrel):
                    data = store.read_json(project_id, hpack, hrel)
                    body = None
                    for k, v in (data or {}).items():
                        if k.startswith("minecraft:") and isinstance(v, dict):
                            body = v
                            break
                    desc = (body or {}).get("description")
                    if isinstance(desc, dict):
                        texs = desc.get("textures")
                        if not isinstance(texs, dict):
                            texs = {}
                            desc["textures"] = texs
                        if "default" not in texs:
                            texs["default"] = png[:-4]
                            store.write_json(project_id, hpack, hrel, data)
                            store.record_change(project_id, hpack, hrel,
                                                "modify")
        elif slot == "texture" and kind == "block":
            png = objs.block_texture_path(name)
            if not store.exists(project_id, "resource", png):
                try:
                    tex.create_blank(project_id, "resource", png, 16, 16)
                    store.record_change(project_id, "resource", png, "add")
                    created.append({"pack": "resource", "path": png})
                except Exception as exc:
                    return jsonify({"ok": False, "error": str(exc)}), 400
            # 新建贴图 = 创建空白 png 并接管该方块全部贴图键
            # （键名沿用 blocks.json 已有命名，不破坏既有结构）
            res = _link_block_texture(project_id, ident, name, png,
                                      overwrite=True)
            for p in res.get("created") or []:
                created.append({"pack": "resource", "path": p})
        elif slot == "blocks_json" and kind == "block":
            texmap, bl = _ensure_blocks_json(project_id, ident, name)
            keys = _block_texture_keys(ident, texmap, name)
            tl = _ensure_terrain(project_id, name, keys)
            for p in bl + tl:
                created.append({"pack": "resource", "path": p})
        elif slot == "terrain_texture" and kind == "block":
            keys = _existing_block_keys(project_id, ident, name)
            for p in _ensure_terrain(project_id, name, keys):
                created.append({"pack": "resource", "path": p})
        elif slot == "material" and kind == "block":
            res = _link_material(project_id, ident, name)
            for p in res.get("created") or []:
                created.append({"pack": "resource", "path": p})
        elif slot in ("animation_controller_behavior",
                      "animation_controller_resource",
                      "attachable_animation_controller"):
            pack = ("behavior" if slot == "animation_controller_behavior"
                    else "resource")
            names = [x for x in ac_names if isinstance(x, str) and x.strip()]
            if not names:
                names = ["%s_ac" % name]
            for ac in names:
                ac = ac.strip()
                _write(pack, objs.animation_controller_path(pack, ac),
                       objs.animation_controller_template(ac))
        elif slot in ("animation", "attachable_animation"):
            _write("resource", "animations/%s.animation.json" % name,
                   objs.animation_template(name))
        elif slot == "loot_table":
            _write("behavior", "loot_tables/%s/%s.json" % (
                "entities" if kind == "entity" else "blocks", name),
                objs.loot_table_template(ident))
        elif slot == "trading" and kind == "entity":
            _write("behavior", "trading/%s.json" % name,
                   objs.trading_template(ident))
        elif slot == "feature" and kind == "block":
            _write("behavior", "features/%s_feature.json" % name,
                   objs.feature_template(ns, name, ident))
        elif slot == "feature_rule" and kind == "block":
            _write("behavior", "feature_rules/%s_feature_rule.json" % name,
                   objs.feature_rule_template(ns, name))
        elif slot == "recipe" and kind in ("item", "block"):
            _write("behavior", "recipes/%s.json" % name,
                   objs.recipe_template(ident))
        elif slot == "render_controller" and kind == "entity":
            _write("resource", "render_controllers/%s.render_controllers.json"
                   % name, objs.render_controller_template(name))
        elif slot == "spawn_rules" and kind == "entity":
            _write("behavior", "spawn_rules/%s.json" % name, {
                "format_version": "1.8.0",
                "minecraft:spawn_rules": {
                    "description": {"identifier": ident,
                                    "population_control": "animal"},
                    "conditions": [{"minecraft:spawns_on_surface": {},
                                    "minecraft:brightness_filter": {
                                        "min": 0, "max": 15,
                                        "adjust_for_weather": False},
                                    "minecraft:weight": {"default": 10},
                                    "minecraft:herd": {"min_size": 1,
                                                       "max_size": 2}}],
                },
            })
        else:
            return jsonify({"ok": False,
                            "error": "该槽位不支持自动创建"}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    try:
        pipeline.run_probe(project_id)
    except Exception:
        pass
    return jsonify({"ok": True, "slot": slot, "created": created,
                    "warnings": warnings})
