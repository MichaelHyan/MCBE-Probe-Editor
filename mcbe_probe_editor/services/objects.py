# -*- coding: utf-8 -*-
"""新建对象（按模组规则自动生成文件）。

设计原则（与 plan.md 0.3 及最新决定一致）：
  * identifier 一律由 namespace:name 自动推导，用户不手写 identifier
  * 文件路径、贴图键、geometry 标识、terrain 键等全部自动按模组规则生成
  * 主文件用「空模板」(仅 description，无组件)，模板来自 services/templates.py
  * 所有附加产物（资源注册 / attachable / 模型 / 材质 / 语言 / 贴图索引）均为可选
  * 唯一允许用户指定多个不同名文件的是 animation_controllers

贴图位置规则（新建时采用，已有贴图不迁移）：
    item        textures/items/<namespace>/<name>.png
    entity      textures/entity/<namespace>/<name>.png
    attachable  textures/attachable/<namespace>/<name>.png
    block       textures/blocks/<name>.png      （材质链，保持不带动 namespace）
"""

import os

from . import store
from . import templates as tpl_mod
from . import texture as tex

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

ITEM_TEXTURE_INDEX = "textures/item_texture.json"
TERRAIN_TEXTURE_INDEX = "textures/terrain_texture.json"
BLOCKS_JSON = "blocks.json"

# 贴图根目录（kind -> 目录）
TEXTURE_DIRS = {
    "item": "textures/items",
    "entity": "textures/entity",
    "attachable": "textures/attachable",
    "block": "textures/blocks",
}

# 按 kind 决定默认空白贴图尺寸（与各自模板的声明一致）
BLANK_TEXTURE_SIZE = {
    "item": (16, 16),
    "entity": (64, 64),
    "attachable": (16, 16),
    "block": (16, 16),
}


# ---------------------------------------------------------------- 路径规则


def behavior_path(kind, name):
    return "%s/%s.json" % (BEHAVIOR_DIRS[kind], name)


def resource_item_path(namespace, name):
    """资源包物品注册(1.10)：items/<ns>_<name>.json。"""
    return "items/%s_%s.json" % (namespace, name)


def attachable_path(name):
    return "attachables/%s.entity.json" % name


def client_entity_path(name):
    return "entity/%s.entity.json" % name


def model_path(name, subdir="entity"):
    return "models/%s/%s.geo.json" % (subdir, name)


def animation_controller_path(pack, name):
    return "animation_controllers/%s.json" % name


def texture_path(kind, namespace, name):
    """新贴图统一落位：textures/<类别>/<namespace>/<name>.png。"""
    base = TEXTURE_DIRS.get(kind, "textures/items")
    ns = (namespace or "").strip()
    if ns:
        base = "%s/%s" % (base, ns)
    return "%s/%s.png" % (base, name)


def item_texture_path(namespace, name):
    return texture_path("item", namespace, name)


def entity_texture_path(namespace, name):
    return texture_path("entity", namespace, name)


def attachable_texture_path(namespace, name):
    return texture_path("attachable", namespace, name)


def block_texture_path(name):
    return texture_path("block", None, name)


def lang_key(kind, ident):
    """语言键规则（对齐模组实测）：
      * item   -> item.<ident>            （不带 .name）
      * entity -> entity.<ident>.name
      * block  -> tile.<ident>.name
    """
    if kind == "item":
        return "item." + ident
    prefix = {"entity": "entity.", "block": "tile."}[kind]
    return prefix + ident + ".name"


def geometry_id(name):
    """模型几何标识（与测试项目一致：geometry.<name>）。"""
    return "geometry.%s" % name


# ---------------------------------------------------------------- 模板体


def resource_item_template(ident, name):
    return {
        "format_version": "1.10",
        "minecraft:item": {
            "description": {"identifier": ident, "category": "Nature"},
            "components": {"minecraft:icon": name},
        },
    }


def attachable_template(ident, namespace, name):
    return {
        "format_version": "1.10.0",
        "minecraft:attachable": {
            "description": {
                "identifier": ident,
                "materials": {
                    "default": "entity",
                    "enchanted": "entity_alphatest_glint",
                },
                "textures": {
                    "default": attachable_texture_path(namespace, name)[:-4],
                    "enchanted": "textures/misc/enchanted_item_glint",
                },
                "geometry": {"default": geometry_id(name)},
                "animations": {},
                "scripts": {"animate": []},
                "render_controllers": ["controller.render.item_default"],
            },
        },
    }


def client_entity_template(ident, namespace, name):
    return {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": ident,
                "materials": {"default": "entity_alphatest"},
                "textures": {
                    "default": entity_texture_path(namespace, name)[:-4]},
                "geometry": {"default": geometry_id(name)},
                "render_controllers": ["controller.render.default"],
            },
        },
    }


def model_template(name):
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": geometry_id(name),
                    "texture_width": 64,
                    "texture_height": 64,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2.5,
                    "visible_bounds_offset": [0, 0.75, 0],
                },
                "bones": [{"name": "body", "pivot": [0, 0, 0]}],
            }
        ],
    }


def animation_controller_template(name, fv="1.8.0"):
    return {
        "format_version": fv,
        "animation_controllers": {
            "controller.animation.%s" % name: {"states": {}},
        },
    }


def blocks_json_entry(name):
    keys = ("up", "down", "south", "north", "west", "east")
    return {
        "textures": {k: "%s_%s" % (name, k) for k in keys},
        "sound": "stone",
    }


def terrain_texture_entries(name, png_path=None):
    """六个贴图键 -> png 路径（去扩展名）。默认指向约定路径。

    png_path 用于把六面地址统一改指向某张图（六地址共用一张是常态）。
    """
    keys = ("up", "down", "south", "north", "west", "east")
    path = png_path or block_texture_path(name)
    if path.lower().endswith(".png"):
        path = path[:-4]
    return {"%s_%s" % (name, k): {"textures": [path]} for k in keys}


# ---------------------------------------------------------------- 贴图落盘


def ensure_blank_texture(project_id, kind, namespace, name):
    """按统一规则在 textures/<类别>/<ns>/<name>.png 生成空白贴图。

    已存在则跳过。返回写入的路径或 None。
    目录由 store 的原子写入自动创建。
    """
    if kind not in BLANK_TEXTURE_SIZE:
        return None
    rel = texture_path(kind, namespace, name)
    if store.exists(project_id, "resource", rel):
        return None
    w, h = BLANK_TEXTURE_SIZE[kind]
    try:
        tex.create_blank(project_id, "resource", rel, w, h)
    except Exception:
        return None
    store.record_change(project_id, "resource", rel, "add")
    return rel


def register_item_texture(project_id, key, png_rel):
    """把指定贴图登记进 textures/item_texture.json（键名 key）。

    png_rel 为资源包相对路径，如 textures/items/ns/name.png
    返回 True 表示新增/更新，False 表示无变化。
    """
    rel = (png_rel or "").replace("\\", "/")
    if rel.lower().endswith(".png"):
        rel = rel[:-4]
    try:
        idx = store.read_json(project_id, "resource", ITEM_TEXTURE_INDEX)
        if not isinstance(idx, dict):
            idx = {}
    except Exception:
        idx = {}
    idx.setdefault("resource_pack_name", "vanilla")
    idx.setdefault("texture_name", "atlas.items")
    data = idx.get("texture_data")
    if not isinstance(data, dict):
        data = {}
        idx["texture_data"] = data
    if data.get(key) == {"textures": rel}:
        return False
    data[key] = {"textures": rel}
    store.write_json(project_id, "resource", ITEM_TEXTURE_INDEX, idx)
    store.record_change(project_id, "resource", ITEM_TEXTURE_INDEX, "modify")
    return True


# ---------------------------------------------------------------- 索引写入


def _ensure_item_texture_index(project_id, namespace, name):
    try:
        idx = store.read_json(project_id, "resource", ITEM_TEXTURE_INDEX)
    except Exception:
        idx = {"resource_pack_name": "vanilla", "texture_name": "atlas.items",
               "texture_data": {}}
    if not isinstance(idx, dict):
        idx = {}
    idx.setdefault("resource_pack_name", "vanilla")
    idx.setdefault("texture_name", "atlas.items")
    data = idx.get("texture_data")
    if not isinstance(data, dict):
        data = {}
        idx["texture_data"] = data
    if name in data:
        return False
    data[name] = {"textures": item_texture_path(namespace, name)[:-4]}
    store.write_json(project_id, "resource", ITEM_TEXTURE_INDEX, idx)
    store.record_change(project_id, "resource", ITEM_TEXTURE_INDEX, "modify")
    return True


def _write_block_material(project_id, ident, name, dirs):
    """blocks.json 条目 + terrain_texture 条目 + 空白 png。"""
    # blocks.json
    try:
        bj = store.read_json(project_id, "resource", BLOCKS_JSON)
        if not isinstance(bj, dict):
            bj = {}
    except Exception:
        bj = {"format_version": "1.16.100"}
    bj.setdefault("format_version", "1.16.100")
    if ident not in bj:
        bj[ident] = blocks_json_entry(name)
        store.write_json(project_id, "resource", BLOCKS_JSON, bj)
        store.record_change(project_id, "resource", BLOCKS_JSON, "modify")
        dirs.append({"pack": "resource", "path": BLOCKS_JSON})

    # terrain_texture
    try:
        tt = store.read_json(project_id, "resource", TERRAIN_TEXTURE_INDEX)
        if not isinstance(tt, dict):
            tt = {}
    except Exception:
        tt = {"resource_pack_name": "vanilla",
              "texture_name": "atlas.terrain",
              "padding": 8, "num_mip_levels": 0, "texture_data": {}}
    tt.setdefault("resource_pack_name", "vanilla")
    tt.setdefault("texture_name", "atlas.terrain")
    tdata = tt.get("texture_data")
    if not isinstance(tdata, dict):
        tdata = {}
        tt["texture_data"] = tdata
    entries = terrain_texture_entries(name)
    changed = False
    for k, v in entries.items():
        if k not in tdata:
            tdata[k] = v
            changed = True
    if changed:
        store.write_json(project_id, "resource", TERRAIN_TEXTURE_INDEX, tt)
        store.record_change(project_id, "resource", TERRAIN_TEXTURE_INDEX, "modify")
        dirs.append({"pack": "resource", "path": TERRAIN_TEXTURE_INDEX})

    # 空白贴图
    png = block_texture_path(name)
    if not store.exists(project_id, "resource", png):
        try:
            tex.create_blank(project_id, "resource", png, 16, 16)
            store.record_change(project_id, "resource", png, "add")
            dirs.append({"pack": "resource", "path": png})
        except Exception:
            pass


# ---------------------------------------------------------------- 创建


def create(project_id, kind, namespace, name, options=None):
    """创建一个对象。返回 {ok, identifier, created, warnings}。"""
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
    fv = str(options.get("format_version") or DEFAULT_FV[kind])
    created, warnings = [], []

    # 按需创建包目录（项目可能只有单侧包）
    from . import workspace as ws_mod
    for _p in ("behavior", "resource"):
        try:
            ws_mod.ensure_pack_dir(project_id, _p)
        except Exception:
            pass

    # 0. 补全空模板库（本地库现存版本）
    try:
        tpl_mod.ensure_templates()
    except Exception as exc:
        warnings.append("模板库补全失败: %s" % exc)

    # 1. 行为包主文件（空模板）
    bpath = behavior_path(kind, nm)
    if store.exists(project_id, "behavior", bpath):
        raise ValueError("行为包文件已存在: %s" % bpath)
    store.write_json(project_id, "behavior", bpath,
                     tpl_mod.materialize(kind, fv, ident))
    store.record_change(project_id, "behavior", bpath, "add")
    created.append({"pack": "behavior", "path": bpath})

    # 2. 资源包侧注册（按 kind 分派，全部自动命名）
    if kind == "item":
        if options.get("with_resource", False):
            rpath = resource_item_path(ns, nm)
            if store.exists(project_id, "resource", rpath):
                warnings.append("资源包注册已存在，跳过: %s" % rpath)
            else:
                store.write_json(project_id, "resource", rpath,
                                 resource_item_template(ident, nm))
                store.record_change(project_id, "resource", rpath, "add")
                created.append({"pack": "resource", "path": rpath})
        if options.get("with_attachable", False):
            apath = attachable_path(nm)
            if store.exists(project_id, "resource", apath):
                warnings.append("attachable 已存在，跳过: %s" % apath)
            else:
                store.write_json(project_id, "resource", apath,
                                 attachable_template(ident, ns, nm))
                store.record_change(project_id, "resource", apath, "add")
                created.append({"pack": "resource", "path": apath})
            # attachable 模板必然引用贴图，缺则补空白
            png = ensure_blank_texture(project_id, "attachable", ns, nm)
            if png:
                created.append({"pack": "resource", "path": png})

    elif kind == "entity":
        if options.get("with_resource", False):
            rpath = client_entity_path(nm)
            if store.exists(project_id, "resource", rpath):
                warnings.append("实体资源注册已存在，跳过: %s" % rpath)
            else:
                store.write_json(project_id, "resource", rpath,
                                 client_entity_template(ident, ns, nm))
                store.record_change(project_id, "resource", rpath, "add")
                created.append({"pack": "resource", "path": rpath})
            # client_entity 模板必然引用贴图，缺则补空白
            png = ensure_blank_texture(project_id, "entity", ns, nm)
            if png:
                created.append({"pack": "resource", "path": png})
        if options.get("with_model", False):
            mpath = model_path(nm)
            if store.exists(project_id, "resource", mpath):
                warnings.append("模型已存在，跳过: %s" % mpath)
            else:
                store.write_json(project_id, "resource", mpath,
                                 model_template(nm))
                store.record_change(project_id, "resource", mpath, "add")
                created.append({"pack": "resource", "path": mpath})

    elif kind == "block":
        if options.get("with_material", False):
            _write_block_material(project_id, ident, nm, created)

    # 3. 物品贴图索引 + 空白贴图
    if kind == "item" and options.get("with_texture", False):
        if _ensure_item_texture_index(project_id, ns, nm):
            created.append({"pack": "resource", "path": ITEM_TEXTURE_INDEX})
        png = ensure_blank_texture(project_id, "item", ns, nm)
        if png:
            created.append({"pack": "resource", "path": png})

    # 4. 动画控制器（唯一允许用户指定多个不同名文件）
    ac_list = options.get("animation_controllers") or []
    if isinstance(ac_list, list):
        for ac in ac_list:
            ac_name = (ac.get("name") or "").strip() if isinstance(ac, dict) else ""
            if not ac_name:
                continue
            ac_pack = (ac.get("pack") or "behavior").strip()
            if ac_pack not in ("behavior", "resource"):
                ac_pack = "behavior"
            ac_fv = str(ac.get("format_version") or "1.8.0")
            ac_path = animation_controller_path(ac_pack, ac_name)
            if store.exists(project_id, ac_pack, ac_path):
                warnings.append("动画控制器已存在，跳过: %s" % ac_path)
                continue
            store.write_json(project_id, ac_pack, ac_path,
                             animation_controller_template(ac_name, ac_fv))
            store.record_change(project_id, ac_pack, ac_path, "add")
            created.append({"pack": ac_pack, "path": ac_path})

    # 5. 语言键
    if options.get("with_lang", False):
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

    return {"ok": True, "identifier": ident, "format_version": fv,
            "created": created, "warnings": warnings}


# ---------------------------------------------------------------- 骨架模板
# 供「无自动产物」的槽位生成空骨架，便于在代码区继续编辑。

def animation_template(name):
    return {
        "format_version": "1.10.0",
        "animations": {
            "animation.%s" % name: {
                "loop": True,
                "animation_length": 1.0,
                "bones": {},
            },
        },
    }


def loot_table_template(ident):
    return {
        "pools": [{
            "rolls": 1,
            "entries": [{"type": "item", "name": ident, "weight": 1}],
        }],
    }


def trading_template(ident):
    return {
        "tiers": [{
            "groups": [{
                "num_to_select": 1,
                "trades": [{
                    "wants": [{"item": "minecraft:emerald", "quantity": 1}],
                    "gives": [{"item": ident, "quantity": 1}],
                    "max_uses": 7,
                    "trader_exp": 1,
                }],
            }],
        }],
    }


def feature_template(namespace, name, ident):
    return {
        "format_version": "1.13.0",
        "minecraft:ore_feature": {
            "description": {"identifier": "%s:%s_feature" % (namespace, name)},
            "count": 8,
            "replace_rules": [{
                "places_block": ident,
                "may_replace": ["minecraft:stone"],
            }],
        },
    }


def feature_rule_template(namespace, name):
    return {
        "format_version": "1.13.0",
        "minecraft:feature_rules": {
            "description": {
                "identifier": "%s_feature_rule" % name,
                "places_feature": "%s:%s_feature" % (namespace, name),
            },
            "conditions": {
                "placement_pass": "underground_pass",
                "minecraft:biome_filter": [{
                    "test": "has_biome_tag",
                    "operator": "==",
                    "value": "overworld",
                }],
            },
            "distribution": {
                "iterations": 1,
                "coordinate_eval_order": "zyx",
                "x": {"distribution": "uniform", "extent": [0, 16]},
                "y": {"distribution": "uniform", "extent": [-60, 50]},
                "z": {"distribution": "uniform", "extent": [0, 16]},
            },
        },
    }


def recipe_template(ident):
    return {
        "format_version": "1.20.10",
        "minecraft:recipe_shapeless": {
            "description": {"identifier": ident},
            "tags": ["crafting_table"],
            "ingredients": [{"item": "minecraft:stone"}],
            "result": {"item": ident, "count": 1},
        },
    }


def render_controller_template(name):
    return {
        "format_version": "1.10.0",
        "render_controllers": {
            "controller.render.%s" % name: {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
            },
        },
    }
