#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCBE Probe Editor - 探测原型
============================
扫描行为包 / 资源包，按 plan.md 的索引表结构生成 index.json。

用法:
    python probe.py <behavior_pack> [resource_pack] [-o index.json]

对应 plan.md 要点:
  * namespace 从文件内容探测(description.identifier)，不依赖目录名
  * 一个文件只有一种 format_version，记录在引用项上
  * 语言 / 贴图索引等多对象共享文件用 keys 区分归属，不复制文件
  * tick.json / lines/ / pack_icon / 备份文件 归入 special_files
  * .mcstructure 不解析内容，只记录路径与大小
  * 资源侧物品(1.10)是引用文件，行为侧物品才是 primary

修正记录:
  v3: 原版动画/控制器前缀白名单；同 identifier 跨 kind 合并；texture_key 降级 notes；
      配方回退按 result.item 关联
  v4: 修复 controller.animation.* 误入 anim_bind（按前缀分离 anim/ctrl）；
      收集 description.scripts.animate；配方 result 支持数组；
      原版结果(minecraft:)归入 vanilla_recipes，不再报 unbound
"""

import argparse
import json
import os
import sys
from collections import OrderedDict

SKIP_DIRS = {".git", "_fv2_backup", "__pycache__", ".idea", ".vscode"}
SKIP_SUFFIX = (".bak", ".bk", ".tmp")

TOP_KINDS = OrderedDict([
    ("minecraft:item", "item"),
    ("minecraft:block", "block"),
    ("minecraft:entity", "entity"),
    ("minecraft:client_entity", "entity"),
    ("minecraft:attachable", "item"),
])

SPECIAL_ICONS = {"pack_icon.png", "pack_icon1.png"}
CONFIG_FILES = {"blocks.json", "sounds.json", "sound_definitions.json"}
TEX_INDEX_FILES = {"item_texture.json", "terrain_texture.json"}

LANG_PREFIXES = [
    ("action.hint.exit.", "entity"),
    ("item.", "item"),
    ("tile.", "block"),
    ("entity.", "entity"),
]

VANILLA_ANIM_PREFIXES = (
    "animation.humanoid.",
    "animation.zombie.",
    "animation.armor_stand.",
    "animation.quadruped.",
    "animation.animation.",
    "animation.creeper.",
    "animation.enderman.",
    "animation.spider.",
    "animation.blaze.",
    "animation.ghast.",
    "animation.slime.",
    "animation.villager.",
    "animation.witch.",
    "animation.wither.",
    "animation.dragon.",
    "animation.arrow.",
    "animation.parrot.",
    "animation.irongolem.",
    "animation.llama.",
    "animation.panda.",
    "animation.fox.",
    "animation.bee.",
    "animation.cat.",
    "animation.horse.",
    "animation.ocelot.",
    "animation.wolf.",
    "animation.phantom.",
    "animation.ravager.",
    "animation.pillager.",
    "animation.skeleton.",
    "animation.warden.",
    "animation.allay.",
    "animation.axolotl.",
    "animation.goat.",
    "animation.frog.",
    "animation.camel.",
    "animation.sniffer.",
    "animation.tadpole.",
    "animation.armadillo.",
    "animation.breeze.",
    "animation.bat.",
    "animation.chicken.",
    "animation.cow.",
    "animation.pig.",
    "animation.sheep.",
    "animation.turtle.",
    "animation.squid.",
    "animation.cod.",
    "animation.salmon.",
    "animation.tropicalfish.",
    "animation.pufferfish.",
    "animation.dolphin.",
    "animation.guardian.",
    "animation.elderguardian.",
    "animation.shulker.",
    "animation.strider.",
    "animation.hoglin.",
    "animation.piglin.",
    "animation.zoglin.",
    "animation.zombie_villager.",
    "animation.husk.",
    "animation.drowned.",
    "animation.stray.",
    "animation.wither_skeleton.",
    "animation.magma_cube.",
    "animation.silverfish.",
    "animation.endermite.",
    "animation.vex.",
    "animation.evoker.",
    "animation.vindicator.",
    "animation.illusioner.",
    "animation.agent.",
    "animation.npc.",
    "animation.player.",
    "animation.spear.",
)

VANILLA_CTRL_PREFIXES = tuple(
    "controller." + p for p in VANILLA_ANIM_PREFIXES) + (
    "controller.animation.player.",
    "controller.animation.thirdperson.",
    "controller.animation.firstperson.",
    "controller.animation.elytra",
    "controller.animation.spear.",
)

VANILLA_TEXTURE_KEYS = {
    "crossbow_standby", "crossbow_pulling_0", "crossbow_pulling_1",
    "crossbow_pulling_2", "crossbow_arrow", "bow_standby",
    "bow_pulling_0", "bow_pulling_1", "bow_pulling_2", "arrow",
    "shield", "trident", "spyglass", "clock", "compass", "recovery_compass",
}


# ---------------------------------------------------------------- 基础工具


def norm(p):
    return p.replace("\\", "/")


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as exc:
        return {"__error__": str(exc)}


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def fv_of(data):
    if not isinstance(data, dict):
        return None
    v = data.get("format_version")
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return ".".join(str(x) for x in v)
    return str(v)


def walk_files(root):
    out = []
    if not root or not os.path.isdir(root):
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.lower().endswith(SKIP_SUFFIX):
                continue
            ap = os.path.join(dirpath, fn)
            out.append((norm(os.path.relpath(ap, root)), ap))
    return out


def classify(data):
    """返回 (kind, identifier, top_key)。"""
    if not isinstance(data, dict):
        return None, None, None
    for top, kind in TOP_KINDS.items():
        body = data.get(top)
        if isinstance(body, dict):
            desc = body.get("description") or {}
            ident = desc.get("identifier")
            if isinstance(ident, str):
                return kind, ident, top
    return None, None, None


def role_for(top, pack):
    if top == "minecraft:item":
        return "primary" if pack == "behavior" else "resource_item"
    if top == "minecraft:block":
        return "primary" if pack == "behavior" else "block_ref"
    if top == "minecraft:entity":
        return "primary"
    if top == "minecraft:client_entity":
        return "client_entity"
    if top == "minecraft:attachable":
        return "attachable"
    return "unknown"


def icon_keys(components):
    keys = []
    if not isinstance(components, dict):
        return keys
    icon = components.get("minecraft:icon")
    if isinstance(icon, str):
        keys.append(icon)
    elif isinstance(icon, dict):
        if isinstance(icon.get("texture"), str):
            keys.append(icon["texture"])
        t = icon.get("textures")
        if isinstance(t, str):
            keys.append(t)
        elif isinstance(t, list):
            keys.extend([x for x in t if isinstance(x, str)])
        elif isinstance(t, dict):
            keys.extend([x for x in t.values() if isinstance(x, str)])
    out = []
    for k in keys:
        if isinstance(k, str) and k not in out:
            out.append(k)
    return out


def find_loot(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "minecraft:loot" and isinstance(v, str) and v.endswith(".json"):
                if v not in acc:
                    acc.append(v)
            else:
                find_loot(v, acc)
    elif isinstance(node, list):
        for item in node:
            find_loot(item, acc)


def is_vanilla_anim(name):
    return any(name.startswith(p) for p in VANILLA_ANIM_PREFIXES)


def is_vanilla_ctrl(name):
    return any(name.startswith(p) for p in VANILLA_CTRL_PREFIXES)


def push(extra, bucket, name):
    arr = extra.setdefault(bucket, [])
    if isinstance(name, str) and name not in arr:
        arr.append(name)


def collect_anim_refs(desc, extra):
    """从 description 收集 animation / animation_controller 引用，按前缀分离。"""
    anims = desc.get("animations")
    if isinstance(anims, dict):
        for k2, v2 in anims.items():
            if isinstance(v2, str):
                if v2.startswith("controller.animation."):
                    push(extra, "ctrl_bind", v2)
                elif v2.startswith("animation."):
                    push(extra, "anim_bind", v2)
            # key 本身若是完整动画名（少见），也收集
            if isinstance(k2, str) and k2.startswith("animation."):
                push(extra, "anim_bind", k2)

    scripts = desc.get("scripts")
    if isinstance(scripts, dict):
        animate = scripts.get("animate")
        if isinstance(animate, list):
            for a in animate:
                if isinstance(a, str):
                    if a.startswith("controller.animation."):
                        push(extra, "ctrl_bind", a)
                    elif a.startswith("animation."):
                        push(extra, "anim_bind", a)
                    # 短名指向 description.animations 的 key，已由上面覆盖
                elif isinstance(a, dict):
                    for kk in a:
                        if not isinstance(kk, str):
                            continue
                        if kk.startswith("controller.animation."):
                            push(extra, "ctrl_bind", kk)
                        elif kk.startswith("animation."):
                            push(extra, "anim_bind", kk)
        elif isinstance(animate, dict):
            for kk in animate:
                if not isinstance(kk, str):
                    continue
                if kk.startswith("controller.animation."):
                    push(extra, "ctrl_bind", kk)
                elif kk.startswith("animation."):
                    push(extra, "anim_bind", kk)


# ---------------------------------------------------------------- 探测器


class Probe(object):
    def __init__(self):
        self.packs = {}
        self.objects = OrderedDict()
        self.special_files = []
        self.structures = []
        self.unbound = []
        self.vanilla_recipes = []
        self.file_errors = []
        self.assets = 0
        self.stats = {}

        self._files = {}
        self._cand = []
        self._other = []
        self._lang = []
        self._texidx = []
        self._tex = {}
        self._anim = {}
        self._ctrl = {}
        self._extras = {}
        self._notes = {}
        self._recipe_fallback = []

    # ------------------------------------------------------------ 入口
    def run(self, bp_dir, rp_dir):
        for pack, root in (("behavior", bp_dir), ("resource", rp_dir)):
            if not root or not os.path.isdir(root):
                continue
            self.packs[pack] = self.read_manifest(root, pack)
            files = walk_files(root)
            self._files[pack] = set(rel for rel, _ in files)
            for rel, ap in files:
                self.ingest(pack, rel, ap)

        self.build_objects()
        self.resolve_other()
        self.parse_texture_index()
        self.resolve_lang()
        self.resolve_recipe_fallback()
        self.link_assets()
        self.link_animations()
        self.finalize()

    # ------------------------------------------------------------ 摄取
    def ingest(self, pack, rel, ap):
        low = rel.lower()
        base = os.path.basename(low)

        if base in SPECIAL_ICONS:
            self.special(pack, rel, "pack_icon")
            return
        if base == "tick.json" and low.startswith("functions/"):
            self.special(pack, rel, "package_config")
            return
        if low.startswith("lines/"):
            self.special(pack, rel, "assets")
            return
        if low.endswith(".mcstructure"):
            self.structures.append({
                "pack": pack, "path": rel, "size": os.path.getsize(ap)})
            return
        if low.endswith(".lang"):
            self._lang.append((pack, rel, ap))
            return
        if base in TEX_INDEX_FILES:
            self._texidx.append((pack, rel, ap))
            return
        if base in CONFIG_FILES:
            self._other.append((pack, rel, ap, None))
            return
        if not low.endswith(".json"):
            self.assets += 1
            return

        data = read_json(ap)
        if isinstance(data, dict) and "__error__" in data:
            self.file_errors.append(
                {"pack": pack, "path": rel, "error": data["__error__"]})
            return
        if not isinstance(data, dict):
            self.file_errors.append(
                {"pack": pack, "path": rel, "error": "root is not object"})
            return

        kind, ident, top = classify(data)
        if ident:
            self._cand.append({
                "pack": pack, "path": rel, "fv": fv_of(data),
                "kind": kind, "ident": ident, "top": top,
                "role": role_for(top, pack), "data": data})
            return

        self.index_definitions(pack, rel, data)
        self._other.append((pack, rel, ap, data))

    def index_definitions(self, pack, rel, data):
        fv = fv_of(data)
        ctrls = data.get("animation_controllers")
        if isinstance(ctrls, dict):
            for name in ctrls:
                self._ctrl.setdefault(
                    name, {"pack": pack, "path": rel, "format_version": fv})
        anims = data.get("animations")
        if isinstance(anims, dict):
            for name in anims:
                self._anim.setdefault(
                    name, {"pack": pack, "path": rel, "format_version": fv})

    def special(self, pack, rel, reason):
        self.special_files.append({"pack": pack, "path": rel, "reason": reason})

    def note(self, ident, msg):
        bucket = self._notes.setdefault(ident, [])
        if msg not in bucket:
            bucket.append(msg)

    # ------------------------------------------------------------ 对象构建
    def build_objects(self):
        grouped = OrderedDict()
        for c in self._cand:
            grouped.setdefault(c["ident"], []).append(c)

        for ident, cands in grouped.items():
            ns, sep, name = ident.partition(":")
            if not sep:
                ns, name = "", ident

            primaries = [c for c in cands if c["role"] == "primary"]
            primaries.sort(key=lambda c: 0 if c["pack"] == "behavior" else 1)

            if primaries:
                kind = primaries[0]["kind"]
            else:
                kind = cands[0]["kind"]

            kinds = []
            for c in cands:
                if c["kind"] not in kinds:
                    kinds.append(c["kind"])

            obj = {
                "kind": kind,
                "kinds": kinds,
                "namespace": ns,
                "name": name,
                "primary": None,
                "references": [],
                "warnings": [],
                "notes": [],
            }
            self.objects[ident] = obj

            if primaries:
                p = primaries[0]
                obj["primary"] = {
                    "pack": p["pack"], "path": p["path"],
                    "format_version": p["fv"], "kind": p["kind"]}
                if p["fv"] is None:
                    obj["warnings"].append("missing_format_version")
                self.collect_primary(ident, p)

                for extra in primaries[1:]:
                    if extra["kind"] == p["kind"]:
                        obj["warnings"].append(
                            "duplicate_primary: %s" % extra["path"])
                        self.note(ident, "duplicate_primary_file: %s" % extra["path"])
                    else:
                        self.add_ref(ident, {
                            "role": "primary_%s" % extra["kind"],
                            "pack": extra["pack"], "path": extra["path"],
                            "format_version": extra["fv"]})
                        self.collect_primary(ident, extra)
            else:
                obj["warnings"].append("missing_primary")

            for c in cands:
                if primaries and c is primaries[0]:
                    continue
                if c["role"] == "primary":
                    continue
                self.add_ref(ident, {
                    "role": c["role"], "pack": c["pack"], "path": c["path"],
                    "format_version": c["fv"]})
                if c["fv"] is None:
                    self.add_warning(ident, "missing_format_version")
                self.collect_ref(ident, c)

            if len(kinds) > 1:
                self.note(ident, "multi_kind: %s" % ",".join(kinds))

    def collect_primary(self, ident, cand):
        data = cand["data"]
        top = cand["top"]
        body = data.get(top) or {}
        comps = body.get("components") or {}
        desc = body.get("description") or {}
        extra = self._extras.setdefault(ident, {})

        for k in icon_keys(comps):
            push(extra, "icon_keys", k)

        loot = []
        find_loot(comps, loot)
        for lp in loot:
            path = norm(lp)
            self.add_ref(ident, {
                "role": "loot_table", "pack": cand["pack"], "path": path,
                "exists": path in self._files.get(cand["pack"], set())})

        collect_anim_refs(desc, extra)

    def collect_ref(self, ident, cand):
        data = cand["data"]
        top = cand["top"]
        body = data.get(top) or {}
        desc = body.get("description") or {}
        comps = body.get("components") or {}
        extra = self._extras.setdefault(ident, {})

        if cand["role"] == "resource_item":
            for k in icon_keys(comps):
                push(extra, "icon_keys", k)

        if cand["role"] in ("client_entity", "attachable"):
            textures = desc.get("textures")
            if isinstance(textures, dict):
                for v in textures.values():
                    if isinstance(v, str):
                        push(extra, "entity_textures", v)
            geo = desc.get("geometry")
            if isinstance(geo, dict):
                for v in geo.values():
                    if isinstance(v, str):
                        push(extra, "geometries", v)
            collect_anim_refs(desc, extra)

    def add_ref(self, ident, ref):
        obj = self.objects.get(ident)
        if obj is None:
            return
        for r in obj["references"]:
            if r.get("role") == ref.get("role") and \
                    r.get("pack") == ref.get("pack") and \
                    r.get("path") == ref.get("path"):
                if "keys" in ref:
                    r.setdefault("keys", [])
                    for k in ref["keys"]:
                        if k not in r["keys"]:
                            r["keys"].append(k)
                return
        obj["references"].append(ref)

    def add_warning(self, ident, msg):
        obj = self.objects.get(ident)
        if obj is not None and msg not in obj["warnings"]:
            obj["warnings"].append(msg)

    # ------------------------------------------------------------ 其他 JSON
    def resolve_other(self):
        for pack, rel, ap, data in self._other:
            low = rel.lower()
            if data is None:
                data = read_json(ap)
            if not isinstance(data, dict):
                continue

            if self.handle_recipe(pack, rel, data):
                continue
            if self.handle_spawn(pack, rel, data):
                continue
            if self.handle_feature(pack, rel, data):
                continue
            if os.path.basename(low) in CONFIG_FILES:
                self.special(pack, rel, "pack_config")
                continue
            if self.handle_sounds(pack, rel, data):
                continue

            role = None
            for name, prefix in (
                ("loot_table", "loot_tables/"),
                ("trading", "trading/"),
                ("animation_controller", "animation_controllers/"),
                ("animation", "animations/"),
                ("render_controller", "render_controllers/"),
                ("particle", "particles/"),
                ("model", "models/"),
                ("material", "materials/"),
                ("function", "functions/"),
            ):
                if low.startswith(prefix):
                    role = name
                    break
            if role:
                self.unbound.append({
                    "kind": role, "pack": pack, "path": rel,
                    "format_version": fv_of(data)})
                continue

            if "animation_controllers" in data or "animations" in data:
                continue

            self.unbound.append({"kind": "unknown", "pack": pack,
                                 "path": rel, "format_version": fv_of(data)})

    @staticmethod
    def recipe_result_item(result):
        if isinstance(result, dict):
            return result.get("item")
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                return first.get("item")
            if isinstance(first, str):
                return first
        if isinstance(result, str):
            return result
        return None

    def handle_recipe(self, pack, rel, data):
        for key in ("minecraft:recipe_shaped", "minecraft:recipe_shapeless",
                    "minecraft:recipe_furnace", "minecraft:recipe_brewing_mix",
                    "minecraft:recipe_brewing_container"):
            if key in data and isinstance(data[key], dict):
                body = data[key]
                desc = body.get("description") or {}
                ident = desc.get("identifier")
                result_item = self.recipe_result_item(body.get("result") or body.get("output"))

                if isinstance(ident, str) and ident in self.objects:
                    self.add_ref(ident, {
                        "role": "recipe", "pack": pack, "path": rel,
                        "format_version": fv_of(data),
                        "recipe_id": ident})
                elif isinstance(result_item, str) and result_item in self.objects:
                    self.add_ref(result_item, {
                        "role": "recipe", "pack": pack, "path": rel,
                        "format_version": fv_of(data),
                        "recipe_id": ident,
                        "matched_by": "result_item"})
                    if ident != result_item:
                        self.note(result_item,
                                  "recipe_id_mismatch: %s" % ident)
                elif isinstance(result_item, str) and \
                        result_item.startswith("minecraft:"):
                    self.vanilla_recipes.append({
                        "pack": pack, "path": rel, "recipe_id": ident,
                        "result_item": result_item})
                else:
                    self.unbound.append({
                        "kind": "recipe", "pack": pack, "path": rel,
                        "identifier": ident, "result_item": result_item,
                        "format_version": fv_of(data)})
                return True
        return False

    def resolve_recipe_fallback(self):
        self._recipe_fallback = []

    def handle_spawn(self, pack, rel, data):
        if "minecraft:spawn_rules" not in data:
            return False
        body = data["minecraft:spawn_rules"]
        ident = None
        if isinstance(body, dict):
            ident = (body.get("description") or {}).get("identifier")
        if isinstance(ident, str) and ident in self.objects:
            self.add_ref(ident, {
                "role": "spawn_rules", "pack": pack, "path": rel,
                "format_version": fv_of(data)})
        else:
            self.unbound.append({"kind": "spawn_rules", "pack": pack,
                                 "path": rel, "identifier": ident,
                                 "format_version": fv_of(data)})
        return True

    def handle_feature(self, pack, rel, data):
        if "minecraft:feature_rules" in data:
            body = data["minecraft:feature_rules"]
            desc = body.get("description") or {} if isinstance(body, dict) else {}
            places = desc.get("places_feature")
            target = places if isinstance(places, str) else None
            if target and target in self.objects:
                self.add_ref(target, {"role": "feature_rule", "pack": pack,
                                      "path": rel, "format_version": fv_of(data)})
            else:
                self.unbound.append({"kind": "feature_rule", "pack": pack,
                                     "path": rel, "target": target,
                                     "format_version": fv_of(data)})
            return True

        feat_keys = [k for k in data if k.startswith("minecraft:")
                     and k.endswith("_feature")]
        if feat_keys:
            body = data[feat_keys[0]]
            desc = body.get("description") or {} if isinstance(body, dict) else {}
            ident = desc.get("identifier")
            target = None
            if isinstance(body, dict):
                rb = body.get("replace_rules")
                if isinstance(rb, list) and rb and isinstance(rb[0], dict):
                    target = rb[0].get("places_block")
            if isinstance(target, str) and target in self.objects:
                self.add_ref(target, {"role": "feature", "pack": pack,
                                      "path": rel, "format_version": fv_of(data)})
            else:
                self.unbound.append({"kind": "feature", "pack": pack,
                                     "path": rel, "identifier": ident,
                                     "format_version": fv_of(data)})
            return True
        return False

    def handle_sounds(self, pack, rel, data):
        es = data.get("entity_sounds")
        if not isinstance(es, dict):
            return False
        ents = es.get("entities")
        if not isinstance(ents, dict):
            return True
        for ident in ents:
            if ident in self.objects:
                self.add_ref(ident, {"role": "sounds", "pack": pack,
                                     "path": rel})
        return True

    # ------------------------------------------------------------ 贴图索引
    def parse_texture_index(self):
        for pack, rel, ap in self._texidx:
            data = read_json(ap)
            if not isinstance(data, dict):
                continue
            tdata = data.get("texture_data")
            if not isinstance(tdata, dict):
                continue
            for key, val in tdata.items():
                paths = []
                if isinstance(val, str):
                    paths.append(val)
                elif isinstance(val, dict):
                    t = val.get("textures")
                    if isinstance(t, str):
                        paths.append(t)
                    elif isinstance(t, list):
                        paths.extend([x for x in t if isinstance(x, str)])
                    elif isinstance(t, dict):
                        paths.extend([x for x in t.values() if isinstance(x, str)])
                for p in paths:
                    self._tex.setdefault(key, []).append(
                        {"pack": pack, "index": rel, "path": norm(p)})
            self.special(pack, rel, "texture_index")

    # ------------------------------------------------------------ 语言
    def resolve_lang(self):
        lookup = {}
        for ident in self.objects:
            lookup[ident] = ident
            ns, _, name = ident.partition(":")
            if ns and name:
                lookup[ns + "." + name] = ident

        bound = 0
        for pack, rel, ap in self._lang:
            text = read_text(ap)
            for lineno, line in enumerate(text.splitlines(), 1):
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                key = s.split("=", 1)[0].strip()
                pk, ident = self.match_lang_key(key, lookup)
                if ident:
                    bound += 1
                    self.add_ref(ident, {"role": "lang", "pack": pack,
                                         "path": rel, "keys": [key]})
                else:
                    self.unbound.append({"kind": "lang_key", "pack": pack,
                                         "path": rel, "key": key,
                                         "line": lineno, "prefix_kind": pk})
        self.stats["lang_keys_bound"] = bound

    def match_lang_key(self, key, lookup):
        stripped = key
        prefix_kind = None
        for prefix, kind in LANG_PREFIXES:
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix):]
                prefix_kind = kind
                break
        if stripped.endswith(".name"):
            stripped = stripped[:-5]
        if stripped in lookup:
            return prefix_kind, lookup[stripped]
        if "." in stripped:
            cand = stripped.replace(".", ":", 1)
            if cand in lookup:
                return prefix_kind, lookup[cand]
        return prefix_kind, None

    # ------------------------------------------------------------ 资产关联
    def resolve_asset(self, pack, raw):
        files = self._files.get(pack, set())
        cands = [raw]
        if not raw.lower().endswith((".png", ".tga", ".jpg", ".jpeg")):
            cands = [raw + ".png", raw + ".tga", raw]
        for c in cands:
            c2 = norm(c)
            if c2 in files:
                return c2
        return None

    def link_assets(self):
        for ident, extra in self._extras.items():
            obj = self.objects.get(ident)
            if obj is None:
                continue
            for key in extra.get("icon_keys", []):
                idxfiles = set()
                for ent in self._tex.get(key, []):
                    idxfiles.add(ent["index"])
                for idx in idxfiles:
                    self.add_ref(ident, {
                        "role": "texture_index", "pack": "resource",
                        "path": idx, "keys": [key]})
                if key not in self._tex:
                    if key in VANILLA_TEXTURE_KEYS:
                        self.note(ident, "vanilla_texture_key: %s" % key)
                    else:
                        self.note(ident, "texture_key_missing: %s" % key)
                for ent in self._tex.get(key, []):
                    p = self.resolve_asset(ent["pack"], ent["path"])
                    self.add_ref(ident, {
                        "role": "texture", "pack": ent["pack"],
                        "path": p or ent["path"],
                        "resolved": p is not None})

            for raw in extra.get("entity_textures", []):
                p = self.resolve_asset("resource", raw)
                self.add_ref(ident, {
                    "role": "entity_texture", "pack": "resource",
                    "path": p or norm(raw), "resolved": p is not None})

            for geo in extra.get("geometries", []):
                self.add_ref(ident, {"role": "geometry", "name": geo})

    def link_animations(self):
        for ident, extra in self._extras.items():
            if ident not in self.objects:
                continue
            for name in extra.get("ctrl_bind", []):
                info = self._ctrl.get(name)
                if info:
                    self.add_ref(ident, {
                        "role": "animation_controller", "pack": info["pack"],
                        "path": info["path"],
                        "format_version": info["format_version"],
                        "name": name})
                elif is_vanilla_ctrl(name):
                    self.note(ident, "vanilla_ctrl_ref: %s" % name)
                else:
                    self.add_warning(ident, "anim_ctrl_missing: %s" % name)
            for name in extra.get("anim_bind", []):
                if name.startswith("controller."):
                    continue
                info = self._anim.get(name)
                if info:
                    self.add_ref(ident, {
                        "role": "animation", "pack": info["pack"],
                        "path": info["path"],
                        "format_version": info["format_version"],
                        "name": name})
                elif is_vanilla_anim(name):
                    self.note(ident, "vanilla_anim_ref: %s" % name)
                else:
                    self.add_warning(ident, "anim_missing: %s" % name)

    # ------------------------------------------------------------ 收尾
    def finalize(self):
        for ident, obj in self.objects.items():
            obj["references"].sort(key=lambda r: (r.get("role", ""),
                                                  r.get("pack", ""),
                                                  r.get("path", "")))
            notes = self._notes.get(ident)
            if notes:
                obj["notes"] = notes
        kinds = {}
        for o in self.objects.values():
            kinds[o["kind"]] = kinds.get(o["kind"], 0) + 1
        self.stats["objects"] = len(self.objects)
        self.stats["kinds"] = kinds
        self.stats["references"] = sum(len(o["references"])
                                       for o in self.objects.values())
        self.stats["warnings"] = sum(len(o["warnings"])
                                     for o in self.objects.values())
        self.stats["notes"] = sum(len(o["notes"])
                                  for o in self.objects.values())
        self.stats["non_json_assets"] = self.assets
        self.stats["vanilla_recipes"] = len(self.vanilla_recipes)

    def read_manifest(self, root, pack):
        mf = os.path.join(root, "manifest.json")
        if not os.path.isfile(mf):
            return {}
        data = read_json(mf)
        if not isinstance(data, dict):
            return {}
        header = data.get("header") or {}
        modules = data.get("modules") or []
        mtype = None
        for m in modules:
            if isinstance(m, dict) and m.get("type"):
                mtype = m["type"]
                break
        return {
            "uuid": header.get("uuid"),
            "name": header.get("name"),
            "version": header.get("version"),
            "min_engine_version": header.get("min_engine_version"),
            "module_type": mtype,
            "dependencies": data.get("dependencies") or [],
            "pack_type": pack,
        }

    def dump(self):
        return {
            "packs": self.packs,
            "stats": self.stats,
            "objects": self.objects,
            "special_files": self.special_files,
            "structures": self.structures,
            "unbound": self.unbound,
            "vanilla_recipes": self.vanilla_recipes,
            "file_errors": self.file_errors,
        }


def main():
    ap = argparse.ArgumentParser(description="MCBE pack probe -> index.json")
    ap.add_argument("behavior_pack", nargs="?", default=None)
    ap.add_argument("resource_pack", nargs="?", default=None)
    ap.add_argument("-o", "--output", default="index.json")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.behavior_pack and not args.resource_pack:
        print("usage: probe.py <behavior_pack> [resource_pack] [-o index.json]")
        return 2

    p = Probe()
    p.run(args.behavior_pack, args.resource_pack)
    index = p.dump()

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    if not args.quiet:
        st = p.stats
        print("objects      : %d" % st.get("objects", 0))
        for k, v in sorted(st.get("kinds", {}).items()):
            print("  %-14s %d" % (k, v))
        print("references   : %d" % st.get("references", 0))
        print("warnings     : %d" % st.get("warnings", 0))
        print("notes        : %d" % st.get("notes", 0))
        print("lang bound   : %d" % st.get("lang_keys_bound", 0))
        print("vanilla rec. : %d" % st.get("vanilla_recipes", 0))
        print("special files: %d" % len(p.special_files))
        print("structures   : %d" % len(p.structures))
        print("unbound      : %d" % len(p.unbound))
        print("file errors  : %d" % len(p.file_errors))
        print("output       : %s" % os.path.abspath(args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
