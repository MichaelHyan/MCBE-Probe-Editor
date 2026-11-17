# -*- coding: utf-8 -*-
"""对象关联槽位（slots）。

把 references 中分散的 role 聚合成「具名固定关联位置」，供编辑页渲染可操作列表。
所有槽位一律可选，不做必填约束，只标注 linked / optional 状态。

对应关系约定（与模组实测一致）：
  * 语言键：资源包 texts/*.lang 固定位置写入，所有对象共享文件，不作为关联槽位
  * 掉落表：仅 entity / block
  * 配方：item / block 可有多个
  * 贴图：物品直接挂在贴图索引（item_texture.json）上，索引链接到 png
  * 实体动画控制器：行为包与资源包是两个独立物，分两个槽
"""

SLOT_DEFS = {
    "item": [
        {"key": "resource_item", "label": "资源包注册", "roles": ["resource_item"],
         "create": True, "suggest": "items/{ns}_{name}.json", "pack": "resource"},
        {"key": "attachable", "label": "attachable（含贴图）",
         "roles": ["attachable", "entity_texture"], "multiple": True,
         "create": True, "suggest": "attachables/{name}.entity.json", "pack": "resource"},
        {"key": "attachable_animation", "label": "attachable 动画",
         "roles": ["attachable_animation"], "multiple": True,
         "create": True, "pack": "resource"},
        {"key": "attachable_animation_controller", "label": "attachable 动画控制器",
         "roles": ["attachable_animation_controller"], "multiple": True,
         "create": True, "pack": "resource"},
        {"key": "geometry", "label": "attachable 模型", "roles": ["geometry"],
         "multiple": True, "create": True,
         "suggest": "models/entity/{name}.geo.json", "pack": "resource"},
        {"key": "texture", "label": "贴图", "roles": ["texture", "texture_index"],
         "create": True, "kind": "image",
         "suggest": "textures/items/{ns}/{name}.png", "pack": "resource",
         "ref_order": ["texture", "texture_index"]},
        {"key": "recipe", "label": "配方", "roles": ["recipe"], "multiple": True,
         "create": True, "suggest": "recipes/{name}.json", "pack": "behavior"},
    ],
    "entity": [
        {"key": "client_entity", "label": "实体资源注册", "roles": ["client_entity"],
         "create": True, "suggest": "entity/{name}.entity.json", "pack": "resource"},
        {"key": "geometry", "label": "模型", "roles": ["geometry"], "multiple": True,
         "create": True, "suggest": "models/entity/{name}.geo.json", "pack": "resource"},
        {"key": "animation", "label": "动画", "roles": ["animation"], "multiple": True,
         "create": True, "pack": "resource"},
        {"key": "animation_controller_behavior", "label": "动画控制器（行为包）",
         "roles": ["animation_controller_behavior"], "multiple": True,
         "create": True, "suggest": "animation_controllers/{name}.json",
         "pack": "behavior"},
        {"key": "animation_controller_resource", "label": "动画控制器（资源包）",
         "roles": ["animation_controller_resource"], "multiple": True,
         "create": True, "suggest": "animation_controllers/{name}.json",
         "pack": "resource"},
        {"key": "texture", "label": "贴图", "roles": ["texture", "entity_texture"],
         "create": True, "pack": "resource", "kind": "image"},
        {"key": "spawn_rules", "label": "生成规则", "roles": ["spawn_rules"],
         "create": True, "suggest": "spawn_rules/{name}.json", "pack": "behavior"},
        {"key": "loot_table", "label": "掉落表", "roles": ["loot_table"],
         "create": True, "pack": "behavior"},
        {"key": "trading", "label": "交易表", "roles": ["trading"],
         "create": True, "pack": "behavior"},
        {"key": "sounds", "label": "声音", "roles": ["sounds"]},
        {"key": "render_controller", "label": "渲染控制器", "roles": ["render_controller"],
         "multiple": True, "create": True, "pack": "resource"},
    ],
    "block": [
        # 主体：贴图文件（六面地址可指向同一张，也可能多张）
        {"key": "texture", "label": "贴图", "roles": ["block_texture"],
         "multiple": True, "create": True, "kind": "image",
         "suggest": "textures/blocks/{name}.png", "pack": "resource",
         "ref_order": ["block_texture"]},
        # 共享登记文件之一：blocks.json（identifier -> 六个贴图键）
        {"key": "blocks_json", "label": "blocks.json 登记",
         "roles": ["blocks_json"], "create": True,
         "suggest": "blocks.json", "pack": "resource"},
        # 共享登记文件之二：terrain_texture.json（贴图键 -> png）
        {"key": "terrain_texture", "label": "terrain_texture.json 登记",
         "roles": ["terrain_texture"], "create": True,
         "suggest": "textures/terrain_texture.json", "pack": "resource"},
        {"key": "feature", "label": "feature", "roles": ["feature"], "multiple": True,
         "create": True, "pack": "behavior"},
        {"key": "feature_rule", "label": "feature_rule", "roles": ["feature_rule"],
         "multiple": True, "create": True, "pack": "behavior"},
        {"key": "loot_table", "label": "掉落表", "roles": ["loot_table"],
         "create": True, "pack": "behavior"},
        {"key": "recipe", "label": "配方", "roles": ["recipe"], "multiple": True,
         "create": True, "pack": "behavior"},
    ],
}

SLOT_ORDER = {k: [s["key"] for s in v] for k, v in SLOT_DEFS.items()}


def suggest_path(slot, namespace, name):
    s = slot.get("suggest")
    if not s:
        return None
    return s.format(ns=namespace or "", name=name or "")


def build_slots(kind, references, namespace=None, name=None):
    """从 references 聚合出槽位字典（全部可选）。"""
    refs_by_role = {}
    for r in references or []:
        refs_by_role.setdefault(r.get("role"), []).append(r)

    defs = SLOT_DEFS.get(kind) or []
    out = {}
    for d in defs:
        roles = d.get("roles") or [d["key"]]
        refs = []
        for role in roles:
            refs.extend(refs_by_role.get(role, []))
        state = "linked" if refs else "optional"
        # geometry：引用了名字但未解析到实际文件 -> 待指定
        if d["key"] == "geometry" and refs:
            if not any(r.get("resolved") for r in refs):
                state = "pending"
        # texture：主体是贴图文件；只有索引登记而缺图 -> 待补图
        if d["key"] == "texture":
            def _is_img(r):
                p = str(r.get("path") or "").lower()
                return p.endswith((".png", ".tga", ".jpg", ".jpeg"))
            real = [r for r in refs
                    if _is_img(r) and r.get("resolved") is not False]
            if real:
                state = "linked"
            elif refs:
                state = "pending"
            order = d.get("ref_order") or ["texture", "texture_index"]
            refs.sort(key=lambda r: (0 if _is_img(r) else 1,
                                     order.index(r.get("role"))
                                     if r.get("role") in order
                                     else len(order)))
        out[d["key"]] = {
            "key": d["key"],
            "label": d.get("label") or d["key"],
            "roles": roles,
            "state": state,
            "refs": refs,
            "multiple": bool(d.get("multiple")),
            "can_create": bool(d.get("create")),
            "pack": d.get("pack"),
            "file_kind": d.get("kind") or "json",
            "suggest": suggest_path(d, namespace, name),
        }
    return out