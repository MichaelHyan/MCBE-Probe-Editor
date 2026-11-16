# -*- coding: utf-8 -*-
"""新建对象（按标准写法生成文件）。

对应 plan.md 0.3 的文件标准写法。所有生成均为"新建时采用"，不改动既有文件。
"""

import os

from . import store
from . import database as db

KINDS = ("item", "entity", "block")

BEHAVIOR_DIRS = {
    "item": "items",
    "entity": "entities",
    "block": "blocks",
}
RESOURCE_DIRS = {
    "item": "items",
    "entity": "entity",
    "block": "blocks",
}
DEFAULT_FV = {
    "item": "1.21.50",
    "entity": "1.20.10",
    "block": "1.17.3",
}


# ---------------------------------------------------------------- 路径


def behavior_path(kind, name):
    return "%s/%s.json" % (BEHAVIOR_DIRS[kind], name)


def resource_path(kind, name):
    d = RESOURCE_DIRS[kind]
    if kind == "entity":
        return "entity/%s.entity.json" % name
    return "%s/%s.json" % (d, name)


def lang_key(kind, ident):
    prefix = {"item": "item.", "entity": "entity.", "block": "tile."}[kind]
    return prefix + ident + ".name"


def texture_path(kind, name):
    d = {"item": "textures/items",
         "entity": "textures/entity",
         "block": "textures/blocks"}[kind]
    return "%s/%s.png" % (d, name)


# ---------------------------------------------------------------- 模板


def behavior_template(kind, ident, fv=None):
    fv = fv or DEFAULT_FV[kind]
    if kind == "item":
        return {
            "format_version": fv,
            "minecraft:item": {
                "description": {
                    "identifier": ident,
                    "menu_category": {"category": "equipment"},
                },
                "components": {
                    "minecraft:max_stack_size": 64,
                    "minecraft:icon": {"textures": {"default": ident.split(":")[-1]}},
                },
            },
        }
    if kind == "block":
        return {
            "format_version": fv,
            "minecraft:block": {
                "description": {"identifier": ident,
                                "register_to_creative_menu": True},
                "components": {},
            },
        }
    return {
        "format_version": fv,
        "minecraft:entity": {
            "description": {
                "identifier": ident,
                "is_spawnable": True,
                "is_summonable": True,
            },
            "components": {},
            "component_groups": {},
            "events": {},
        },
    }


def resource_template(kind, ident, fv=None):
    if kind == "item":
        return {
            "format_version": "1.10",
            "minecraft:item": {
                "description": {"identifier": ident, "category": "Nature"},
                "components": {
                    "minecraft:icon": ident.split(":")[-1],
                },
            },
        }
    if kind == "block":
        return {
            "format_version": "1.19.30",
            "minecraft:block": {
                "description": {"identifier": ident},
                "components": {},
            },
        }
    # entity -> client_entity
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": ident,
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": texture_path(kind, ident.split(":")[-1])},
                "geometry": {"default": "geometry.%s.%s"
                             % (ident.split(":")[0], ident.split(":")[1])},
                "render_controllers": ["controller.render.default"],
            },
        },
    }


# ---------------------------------------------------------------- 创建


def create(project_id, kind, namespace, name, options=None):
    """创建一个对象。返回 {ok, created:[...], warnings:[...]}。"""
    options = options or {}
    if kind not in KINDS:
        raise ValueError("不支持的 kind: %s" % kind)
    ns = (namespace or "").strip()
    nm = (name or "").strip()
    if not ns or not nm:
        raise ValueError("namespace 与 name 均不能为空")
    for bad in (" ", "/", "\\", ":"):
        if bad in ns or bad in nm:
            raise ValueError("namespace / name 不能包含 %r" % bad)

    ident = "%s:%s" % (ns, nm)
    fv = options.get("format_version") or DEFAULT_FV[kind]
    created, warnings = [], []

    # 1. 行为包主文件
    bpath = behavior_path(kind, nm)
    if store.exists(project_id, "behavior", bpath):
        raise ValueError("行为包文件已存在: %s" % bpath)
    store.write_json(project_id, "behavior", bpath,
                     behavior_template(kind, ident, fv))
    store.record_change(project_id, "behavior", bpath, "add")
    created.append({"pack": "behavior", "path": bpath})

    # 2. 资源包注册（可选）
    if options.get("with_resource", True):
        rpath = resource_path(kind, nm)
        if store.exists(project_id, "resource", rpath):
            warnings.append("资源包文件已存在，跳过: %s" % rpath)
        else:
            store.write_json(project_id, "resource", rpath,
                             resource_template(kind, ident))
            store.record_change(project_id, "resource", rpath, "add")
            created.append({"pack": "resource", "path": rpath})

    # 3. 语言键（写 zh_CN）
    if options.get("with_lang", True):
        loc = options.get("locale") or "zh_CN"
        lpath = "texts/%s.lang" % loc
        key = lang_key(kind, ident)
        try:
            text = store.read_text(project_id, "resource", lpath)
        except Exception:
            text = ""
        if key + "=" in text:
            warnings.append("语言键已存在: %s" % key)
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += "%s=%s\n" % (key, nm)
            store.write_text(project_id, "resource", lpath, text)
            store.record_change(project_id, "resource", lpath, "modify")
            created.append({"pack": "resource", "path": lpath})

    # 4. 贴图索引登记
    if options.get("with_texture", False):
        try:
            idx = store.read_json(project_id, "resource",
                                  "textures/item_texture.json")
        except Exception:
            idx = None
        if isinstance(idx, dict) and isinstance(idx.get("texture_data"), dict):
            key = nm
            if key not in idx["texture_data"]:
                idx["texture_data"][key] = {
                    "textures": texture_path(kind, nm)[:-4]}
                store.write_json(project_id, "resource",
                                 "textures/item_texture.json", idx)
                store.record_change(project_id, "resource",
                                    "textures/item_texture.json", "modify")
                created.append({"pack": "resource",
                                "path": "textures/item_texture.json"})
        else:
            warnings.append("未找到 / 无法解析 item_texture.json，已跳过贴图索引")

    return {"ok": True, "identifier": ident, "created": created,
            "warnings": warnings}
