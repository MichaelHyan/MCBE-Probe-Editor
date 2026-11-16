# -*- coding: utf-8 -*-
"""组件数据库。

对应 plan.md 2.1/2.2:

临时库(载入时生成，退出释放):
    db/temp/<project_id>/
        inventory.json
        components/<kind>/<format_version>.json

正式库(长久保存):
    db/official/
        components/<kind>/<format_version>.json
        docs/<kind>/<component>.md
        meta.json

关键规则: 各版本互相独立，查询按 format_version 精确命中，不回落低版本。
"""

import json
import os
import re
import time

from . import workspace as ws

# 正式库位置(工程根下，跨项目共享)
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PKG_DIR)
OFFICIAL_ROOT = os.path.join(_PROJECT_ROOT, "db", "official")

KNOWN_KINDS = ("item", "entity", "block", "structure")

# 由实际数据推断出的 value_type 名称
VALUE_TYPES = (
    "integer", "float", "boolean", "string", "enum",
    "object", "array", "any",
)


# ---------------------------------------------------------------- 基础 IO


def _read_json(path, default=None):
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def safe_fv(fv):
    """format_version -> 可用作文件名的字符串。"""
    if fv is None:
        return "unknown"
    s = str(fv).strip()
    if not s:
        return "unknown"
    return re.sub(r"[^0-9A-Za-z._-]", "_", s)


def fv_label(fv):
    return "unknown" if fv is None else str(fv)


# ---------------------------------------------------------------- 类型推断


def infer_value_type(value):
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "any"


def clip_value(value, limit=8000):
    """返回可直接回填的真实取值；过大时退化为摘要，避免库文件膨胀。"""
    try:
        size = len(json.dumps(value, ensure_ascii=False))
    except Exception:
        return summarize_value(value)
    return value if size <= limit else summarize_value(value)


def summarize_value(value):
    """给组件条目生成一个可读的取值摘要。"""
    t = infer_value_type(value)
    if t in ("integer", "float", "boolean", "string"):
        return value
    if t == "array":
        return {"length": len(value),
                "sample": value[:3] if value else []}
    if t == "object":
        return {"keys": list(value.keys())[:20],
                "key_count": len(value)}
    return value


# ---------------------------------------------------------------- 组件提取


def extract_components(data, kind):
    """从主文件 JSON 中提取 components 字典。

    返回 (components: dict, container: str|None)
    container 说明组件所在位置(item/entity/block 的顶层键)。
    """
    if not isinstance(data, dict):
        return {}, None

    top_map = {
        "item": "minecraft:item",
        "entity": "minecraft:entity",
        "block": "minecraft:block",
        "structure": None,
    }
    top = top_map.get(kind)
    if top and isinstance(data.get(top), dict):
        body = data[top]
        comps = body.get("components")
        if isinstance(comps, dict):
            return comps, top
        return {}, top

    # 兜底: 任意 minecraft:* 顶层键
    for key, val in data.items():
        if key.startswith("minecraft:") and isinstance(val, dict):
            comps = val.get("components")
            if isinstance(comps, dict):
                return comps, key
    return {}, None


def extract_group_components(data, kind):
    """提取 component_groups 内出现的组件（组体直接是组件集合）。

    Bedrock 实体的标准写法:
        "component_groups": { "bow": { "minecraft:x": {...} } }
    少数文件可能保留 "components" 包装层，两种都兼容。

    返回 {组件名: 首个实际值}，用于把组内独有组件补进组件库。
    """
    if not isinstance(data, dict):
        return {}

    top_map = {
        "item": "minecraft:item",
        "entity": "minecraft:entity",
        "block": "minecraft:block",
    }
    body = data.get(top_map.get(kind))
    if not isinstance(body, dict):
        for key, val in data.items():
            if key.startswith("minecraft:") and isinstance(val, dict):
                body = val
                break
    if not isinstance(body, dict):
        return {}

    groups = body.get("component_groups")
    if not isinstance(groups, dict):
        return {}

    out = {}
    for grp in groups.values():
        if not isinstance(grp, dict):
            continue
        keys = list(grp.keys())
        has_mc = any(str(k).startswith("minecraft:") for k in keys)
        items = grp
        if not has_mc and isinstance(grp.get("components"), dict):
            items = grp["components"]
        for cname, cval in items.items():
            if not str(cname).startswith("minecraft:"):
                continue
            if cname not in out:
                out[cname] = cval
    return out


def build_entry(name, value, source="probe", origin=None):
    """把实际组件值转成数据库条目结构。

    条目分「短期(临时库)」与「长期(正式库)」两种存在形态：
      * 临时库：example 为本模组实际取值，note 为空（快速参考）
      * 正式库：example 可替换为官方示例，note 为用法说明，verified 表示已核实
    """
    sample = clip_value(value)
    return {
        "value_type": infer_value_type(value),
        "default": sample,
        "example": sample,
        "examples": [{
            "label": "probe",
            "source": "project",
            "value": sample,
            "origin": origin,
            "added": time.strftime("%Y-%m-%d %H:%M:%S"),
        }],
        "note": "",
        "description": "",
        "doc_ref": None,
        "verified": False,
        "source": source,
        "added_in": None,
        "deprecated": False,
    }


# 单组件示例上限（跨对象合并后仍保留足够参考量）
MAX_EXAMPLES = 60


def add_project_value(bucket, name, value, origin=None):
    """把某对象的实际取值并入桶条目。

    同名组件不覆盖首个条目，仅按值去重追加示例；
    这样同桶（同 kind + 同 format_version）内其他对象的取值也能作为示例出现。
    """
    entry = bucket.get(name)
    if entry is None:
        bucket[name] = build_entry(name, value, source="probe", origin=origin)
        return True
    return add_project_example(entry, value, origin)


def add_project_example(entry, value, origin=None):
    """按值指纹去重后追加一条 project 来源示例。"""
    if not isinstance(entry, dict):
        return False
    exs = _norm_examples(entry)
    sample = clip_value(value)
    sig = _value_sig(sample)
    for ex in exs:
        if _value_sig(ex.get("value")) == sig:
            return False
    if len(exs) >= MAX_EXAMPLES:
        return False
    exs.append({
        "label": "probe",
        "source": "project",
        "value": sample,
        "origin": origin,
        "added": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    entry["examples"] = exs
    return True


# ---------------------------------------------------------------- 示例库


def _value_sig(value):
    """示例值的指纹，用于去重。"""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except Exception:
        return repr(value)


def _norm_examples(entry):
    """兼容旧条目：把单条 example 升级成 examples 数组。"""
    if not isinstance(entry, dict):
        return []
    exs = entry.get("examples")
    if isinstance(exs, list) and exs:
        return exs
    single = entry.get("example")
    if single is None:
        single = entry.get("default")
    if single is None:
        return []
    return [{"label": "probe", "source": "project",
             "value": single, "origin": None, "added": None}]


def list_examples(project_id, kind, fv, component):
    """列出某组件所有可用示例（本地库 + 本项目实际值）。

    返回 [{source, label, value, origin}]，source:
      * local    本地库（正式库沉淀，跨项目共享）
      * project  本项目当前文件实际值
      * official 官方文档核实写入
    """
    label = fv_label(fv)
    out = []

    offi = load_official_bucket(kind, label) or {}
    off_entry = (offi.get("components") or {}).get(component) or {}
    for ex in _norm_examples(off_entry):
        src = ex.get("source") or "local"
        out.append({
            "source": "official" if src == "official" else "local",
            "label": ex.get("label") or "local",
            "value": ex.get("value"),
            "origin": ex.get("origin"),
            "added": ex.get("added"),
        })

    temp = load_temp_bucket(project_id, kind, label) or {}
    temp_entry = (temp.get("components") or {}).get(component) or {}
    for ex in _norm_examples(temp_entry):
        out.append({
            "source": "project",
            "label": ex.get("label") or "probe",
            "value": ex.get("value"),
            "origin": ex.get("origin"),
            "added": ex.get("added"),
        })

    # 去重（保留顺序：本地库优先）
    seen = set()
    uniq = []
    for ex in out:
        sig = (ex["source"], _value_sig(ex.get("value")))
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(ex)
    return uniq


def record_example(kind, fv, component, value, label=None,
                   source="local", origin=None):
    """把一条示例写入本地库（正式库，跨项目共享）。"""
    label_fv = fv_label(fv)
    offi = load_official_bucket(kind, label_fv) or {
        "kind": kind, "format_version": label_fv, "components": {}}
    comps = offi.get("components") or {}

    entry = comps.get(component)
    if entry is None:
        entry = build_entry(component, value, source="manual", origin=origin)
        comps[component] = entry

    exs = _norm_examples(entry)
    sig = _value_sig(value)
    for ex in exs:
        if _value_sig(ex.get("value")) == sig and ex.get("source") == source:
            entry["examples"] = exs
            offi["components"] = comps
            save_official_bucket(kind, label_fv, comps)
            return {"ok": True, "added": False, "count": len(exs)}

    exs.append({
        "label": label or "manual",
        "source": source,
        "value": value,
        "origin": origin,
        "added": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    entry["examples"] = exs[:60]
    entry["example"] = value
    comps[component] = entry
    offi["components"] = comps
    save_official_bucket(kind, label_fv, comps)
    return {"ok": True, "added": True, "count": len(entry["examples"])}


# ---------------------------------------------------------------- 临时库


def temp_root(project_id):
    return os.path.join(ws.db_dir(project_id), "temp")


def temp_components_path(project_id, kind, fv):
    return os.path.join(temp_root(project_id), "components",
                        kind, safe_fv(fv) + ".json")


def temp_inventory_path(project_id):
    return os.path.join(temp_root(project_id), "inventory.json")


def clear_temp(project_id):
    """释放临时库(退出项目时调用)。"""
    root = temp_root(project_id)
    if not os.path.isdir(root):
        return False
    import shutil
    shutil.rmtree(root, ignore_errors=True)
    return True


def load_temp_bucket(project_id, kind, fv):
    return _read_json(temp_components_path(project_id, kind, fv), None)


def list_temp_buckets(project_id):
    """返回 [{kind, format_version, count}]"""
    root = os.path.join(temp_root(project_id), "components")
    out = []
    if not os.path.isdir(root):
        return out
    for kind in sorted(os.listdir(root)):
        kdir = os.path.join(root, kind)
        if not os.path.isdir(kdir):
            continue
        for fn in sorted(os.listdir(kdir)):
            if not fn.endswith(".json"):
                continue
            data = _read_json(os.path.join(kdir, fn), {}) or {}
            out.append({
                "kind": kind,
                "format_version": data.get("format_version", fn[:-5]),
                "count": len(data.get("components") or {}),
            })
    return out


def build_temp(project_id, index, reader):
    """根据索引表读取实际文件，生成临时组件库。

    reader(pack, rel) -> dict|None  用于读 JSON(由调用方注入，避免循环依赖)
    返回统计信息。
    """
    objects = (index or {}).get("objects") or {}
    # bucket[(kind, fv)] -> {component_name: entry}
    buckets = {}
    inventory = {
        "project_id": project_id,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "objects": len(objects),
        "files": [],
        "buckets": [],
    }

    for ident, obj in objects.items():
        prim = obj.get("primary")
        if not prim:
            continue
        pack = prim.get("pack")
        path = prim.get("path")
        fv = prim.get("format_version")
        kind = prim.get("kind") or obj.get("kind")

        if not pack or not path or kind not in KNOWN_KINDS:
            continue
        try:
            data = reader(pack, path)
        except Exception as exc:
            inventory["files"].append({
                "object": ident, "pack": pack, "path": path,
                "error": str(exc)})
            continue

        comps, container = extract_components(data, kind)
        group_comps = extract_group_components(data, kind)
        if not comps and not group_comps:
            continue

        key = (kind, fv_label(fv))
        bucket = buckets.setdefault(key, {})
        # 同桶内所有同类对象的取值都并入示例，编辑任一对象时都能看到同版本示例
        for cname, cval in comps.items():
            add_project_value(bucket, cname, cval, ident)
        # 组内独有组件同样入库，保证组件组的「+ 添加」与顶层一致
        for cname, cval in group_comps.items():
            add_project_value(bucket, cname, cval, ident)

        inventory["files"].append({
            "object": ident, "pack": pack, "path": path,
            "kind": kind, "format_version": fv_label(fv),
            "components": len(comps), "group_components": len(group_comps),
            "container": container})

    # 落盘
    for (kind, fv), comps in buckets.items():
        payload = {
            "kind": kind,
            "format_version": fv,
            "generated": inventory["generated"],
            "components": comps,
        }
        _write_json(temp_components_path(project_id, kind, fv), payload)
        inventory["buckets"].append({
            "kind": kind, "format_version": fv, "count": len(comps)})

    inventory["buckets"].sort(
        key=lambda b: (b["kind"], b["format_version"]))
    _write_json(temp_inventory_path(project_id), inventory)
    return inventory


# ---------------------------------------------------------------- 正式库


def official_path(kind, fv):
    return os.path.join(OFFICIAL_ROOT, "components", kind,
                        safe_fv(fv) + ".json")


def docs_path(kind, component):
    name = re.sub(r"[^0-9A-Za-z._-]", "_", component)
    return os.path.join(OFFICIAL_ROOT, "docs", kind, name + ".md")


def load_official_bucket(kind, fv):
    return _read_json(official_path(kind, fv), None)


def list_official_buckets():
    root = os.path.join(OFFICIAL_ROOT, "components")
    out = []
    if not os.path.isdir(root):
        return out
    for kind in sorted(os.listdir(root)):
        kdir = os.path.join(root, kind)
        if not os.path.isdir(kdir):
            continue
        for fn in sorted(os.listdir(kdir)):
            if not fn.endswith(".json"):
                continue
            data = _read_json(os.path.join(kdir, fn), {}) or {}
            comps = data.get("components") or {}
            out.append({
                "kind": kind,
                "format_version": data.get("format_version", fn[:-5]),
                "count": len(comps),
                "verified": sum(1 for c in comps.values()
                                if isinstance(c, dict) and c.get("verified")),
            })
    return out


def save_official_bucket(kind, fv, components):
    payload = {
        "kind": kind,
        "format_version": fv_label(fv),
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "components": components,
    }
    _write_json(official_path(kind, fv), payload)
    return payload


# ---------------------------------------------------------------- 合并查询


def query_components(project_id, kind, fv):
    """按 kind + format_version 精确查询(不跨版本合并)。

    返回 {'temp': {...}, 'official': {...}, 'merged': {...}, 'format_version': fv}
    temp 优先展示实际值，official 提供默认值/文档/核实状态。
    """
    label = fv_label(fv)
    temp = load_temp_bucket(project_id, kind, label) or {}
    offi = load_official_bucket(kind, label) or {}

    temp_comps = (temp.get("components") or {})
    offi_comps = (offi.get("components") or {})

    merged = {}
    for name, entry in offi_comps.items():
        e = dict(entry)
        e["origin"] = "official"
        merged[name] = e
    for name, entry in temp_comps.items():
        if name in merged:
            e = dict(merged[name])
            e["actual"] = entry.get("default")
            e["actual_type"] = entry.get("value_type")
            e["in_use"] = True
            exs = _norm_examples(e)
            seen = set(_value_sig(x.get("value")) for x in exs)
            for ex in _norm_examples(entry):
                if _value_sig(ex.get("value")) not in seen:
                    ex = dict(ex)
                    ex["source"] = "project"
                    exs.append(ex)
                    seen.add(_value_sig(ex.get("value")))
            e["examples"] = exs
            # 正式库没有官方示例时，回退使用实际值作为示例
            if not e.get("example") and entry.get("example") is not None:
                e["example"] = entry.get("example")
            merged[name] = e
        else:
            e = dict(entry)
            e["origin"] = "temp"
            e["in_use"] = True
            merged[name] = e

    return {
        "kind": kind,
        "format_version": label,
        "temp": temp_comps,
        "official": offi_comps,
        "merged": merged,
    }


def promote_to_official(project_id, kind, fv, names=None):
    """把临时库条目提升到正式库(可指定组件名)。"""
    label = fv_label(fv)
    temp = load_temp_bucket(project_id, kind, label)
    if not temp:
        return {"ok": False, "reason": "temp bucket not found"}

    temp_comps = temp.get("components") or {}
    offi = load_official_bucket(kind, label) or {
        "kind": kind, "format_version": label, "components": {}}
    offi_comps = offi.get("components") or {}

    added, updated = 0, 0
    for name, entry in temp_comps.items():
        if names and name not in names:
            continue
        if name in offi_comps:
            target = offi_comps[name]
            # 只补缺失字段，不覆盖已核实的描述
            for k, v in entry.items():
                if k not in target:
                    target[k] = v
            # 合并示例（project 来源）
            tgt_exs = _norm_examples(target)
            seen = set(_value_sig(x.get("value")) for x in tgt_exs)
            for ex in _norm_examples(entry):
                if _value_sig(ex.get("value")) not in seen:
                    ex = dict(ex)
                    ex["source"] = "project"
                    if not ex.get("origin"):
                        ex["origin"] = project_id
                    tgt_exs.append(ex)
                    seen.add(_value_sig(ex.get("value")))
            target["examples"] = tgt_exs[:60]
            updated += 1
        else:
            offi_comps[name] = dict(entry)
            added += 1

    offi["components"] = offi_comps
    save_official_bucket(kind, label, offi_comps)
    return {"ok": True, "added": added, "updated": updated,
            "total": len(offi_comps)}


def write_doc(kind, component, content):
    path = docs_path(kind, component)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def read_doc(kind, component):
    path = docs_path(kind, component)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def mark_verified(kind, fv, component, doc_rel=None):
    """把正式库条目标记为已核实。"""
    label = fv_label(fv)
    offi = load_official_bucket(kind, label)
    if not offi:
        return False
    comps = offi.get("components") or {}
    if component not in comps:
        return False
    entry = comps[component]
    entry["verified"] = True
    if doc_rel:
        entry["doc_ref"] = doc_rel
    save_official_bucket(kind, label, comps)
    return True