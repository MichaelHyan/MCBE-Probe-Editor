# -*- coding: utf-8 -*-
"""空模板库（按 kind + format_version）。

对本地库中现存的每个 format_version，生成一份「仅基本信息、无组件」的模板，
供新建对象时直接复制代码，或作为手动加代码的起点。

位置：
    db/official/templates/<kind>/<format_version>.json

模板内容只有 description(identifier 占位) 与空 components，没有任何组件。
"""

import os

from . import database as db

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PKG_DIR)
TEMPLATE_ROOT = os.path.join(_PROJECT_ROOT, "db", "official", "templates")

KINDS = ("item", "entity", "block")


def template_path(kind, fv):
    return os.path.join(TEMPLATE_ROOT, kind, db.safe_fv(fv) + ".json")


def _blank(kind, fv):
    if kind == "item":
        return {
            "format_version": fv,
            "minecraft:item": {
                "description": {
                    "identifier": "__IDENT__",
                    "menu_category": {"category": "equipment"},
                },
                "components": {},
            },
        }
    if kind == "block":
        return {
            "format_version": fv,
            "minecraft:block": {
                "description": {
                    "identifier": "__IDENT__",
                    "register_to_creative_menu": True,
                },
                "components": {},
            },
        }
    return {
        "format_version": fv,
        "minecraft:entity": {
            "description": {
                "identifier": "__IDENT__",
                "is_spawnable": True,
                "is_summonable": True,
            },
            "components": {},
            "component_groups": {},
            "events": {},
        },
    }


def ensure_templates(extra_versions=None):
    """扫描正式库所有 kind+fv 补全空模板。

    extra_versions: {kind: [fv, ...]} 额外补充（如项目临时库现存的版本）
    返回新建的 [{kind, format_version}]
    """
    created = []
    versions = {kind: set() for kind in KINDS}
    for bucket in db.list_official_buckets():
        kind = bucket.get("kind")
        fv = bucket.get("format_version")
        if kind in versions and fv and fv != "unknown":
            versions[kind].add(str(fv))
    for kind, fvs in (extra_versions or {}).items():
        if kind in versions:
            for fv in fvs:
                if fv and fv != "unknown":
                    versions[kind].add(str(fv))

    for kind, fvs in versions.items():
        for fv in sorted(fvs):
            path = template_path(kind, fv)
            if os.path.isfile(path):
                continue
            db._write_json(path, _blank(kind, fv))
            created.append({"kind": kind, "format_version": fv})
    return created


def load_template(kind, fv):
    path = template_path(kind, fv)
    if not os.path.isfile(path):
        return None
    return db._read_json(path, None)


def list_templates(kind=None):
    out = []
    kinds = [kind] if kind else list(KINDS)
    for k in kinds:
        kdir = os.path.join(TEMPLATE_ROOT, k)
        if not os.path.isdir(kdir):
            continue
        for fn in sorted(os.listdir(kdir)):
            if not fn.endswith(".json"):
                continue
            data = db._read_json(os.path.join(kdir, fn), {}) or {}
            out.append({
                "kind": k,
                "format_version": data.get("format_version", fn[:-5]),
                "path": "templates/%s/%s" % (k, fn),
            })
    out.sort(key=lambda x: (x["kind"], x["format_version"]))
    return out


def _fill(node, ident):
    if isinstance(node, dict):
        return {k: _fill(v, ident) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill(v, ident) for v in node]
    if node == "__IDENT__":
        return ident
    return node


def materialize(kind, fv, identifier):
    """取模板并填入 identifier，返回可写入主文件的 dict。"""
    tpl = load_template(kind, fv)
    if tpl is None:
        tpl = _blank(kind, fv)
    return _fill(tpl, identifier)