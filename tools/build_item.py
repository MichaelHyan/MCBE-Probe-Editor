# -*- coding: utf-8 -*-
"""用 Mojang 官方 JSON Schema 构建 item 正式库（1.21.0 / 1.26.0）。

数据源（通过 GitHub Contents API 的 raw 通道，绕过 raw.githubusercontent 的 TLS 吊销问题）：
  1.26.0 <- metadata/json_schemas/server/item/1.26.30/Item Components.json
            （组件清单 + 描述；默认值按 $ref 解析具体 schema）
  1.21.0 <- metadata/json_schemas/server/item/1.20.50/ 目录下 minecraft_*.json
            （最近可得 schema；note 中注明）

所有下载文件缓存在 tools/_cache/raw_*.json，失败跳过不中断。
结果增量写入 tools/_cache/_item_report.txt。
"""
import os
import re
import json
import time
import urllib.request
import urllib.error

TOOLS = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(TOOLS, "_cache")
PROJECT = os.path.dirname(TOOLS)
OFFICIAL = os.path.join(PROJECT, "mcbe_probe_editor", "db", "official")
REPORT = os.path.join(CACHE, "_item_report.txt")
NOW = time.strftime("%Y-%m-%d %H:%M:%S")

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/vnd.github.raw",
}
API = "https://api.github.com/repos/Mojang/bedrock-samples/contents/"
ITEM_BASE = "metadata/json_schemas/server/item/"


def safe(name):
    return re.sub(r"[^0-9A-Za-z._-]", "_", name)


def cached_get(rel_path, timeout=20):
    """下载并缓存（rel_path 相对仓库根）。失败返回 None。"""
    out = os.path.join(CACHE, "raw_" + safe(rel_path))
    if os.path.isfile(out) and os.path.getsize(out) > 2:
        try:
            return json.load(open(out, encoding="utf-8"))
        except Exception:
            pass
    url = API + rel_path.replace(" ", "%20")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        obj = json.loads(data.decode("utf-8"))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return obj
    except Exception:
        return None


def api_list(rel_path):
    url = API + rel_path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
        with urllib.request.urlopen(req, timeout=25) as r:
            return [(x["name"], x["type"]) for x in json.load(r)]
    except Exception:
        return []


def infer_type(value):
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


def extract_default(schema, depth=0):
    """从 schema 递归提取默认值，返回 dict/list/标量或 None。"""
    if not isinstance(schema, dict) or depth > 6:
        return None
    if "default" in schema:
        return schema["default"]
    for key in ("oneOf", "anyOf", "allOf"):
        subs = schema.get(key)
        if isinstance(subs, list):
            for sub in subs:
                v = extract_default(sub, depth + 1)
                if v is not None:
                    return v
    props = schema.get("properties")
    if isinstance(props, dict):
        obj = {}
        for k, v in props.items():
            dv = extract_default(v, depth + 1)
            if dv is not None:
                obj[k] = dv
        if obj:
            return obj
    return None


def resolve_ref(base_rel, ref):
    """把 $ref 解析成仓库相对路径。base_rel 形如 .../item/1.26.30/"""
    if not ref or ref.startswith("http"):
        return None
    return os.path.normpath(os.path.join(base_rel, ref)).replace("\\", "/")


def write_doc(name, entry):
    path = os.path.join(OFFICIAL, "docs", "item", safe(name) + ".md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = ["# `%s`" % name, "", "- 版本：`%s`" % entry["_fv"],
             "- 来源：%s" % entry["note"], "- 核实状态：**未人工核实**", ""]
    if entry["description"]:
        lines += ["## 说明", "", entry["description"], ""]
    lines += ["## 默认值", "", "```json",
              json.dumps(entry["default"], ensure_ascii=False, indent=2), "```", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def make_entry(name, desc, value, fv, origin):
    v = value if value is not None else {}
    return {
        "value_type": infer_type(v),
        "default": v,
        "example": v,
        "examples": [{"label": fv, "source": "official",
                      "value": v, "origin": origin, "added": NOW}],
        "note": "来源：%s；未人工核实" % origin,
        "description": desc or "",
        "doc_ref": "docs/item/%s.md" % safe(name),
        "verified": False,
        "source": "manual",
        "added_in": None,
        "deprecated": False,
        "_fv": fv,
    }


def write_bucket(fv, comps):
    clean = {}
    for name, e in comps.items():
        e2 = dict(e)
        e2.pop("_fv", None)
        clean[name] = e2
    path = os.path.join(OFFICIAL, "components", "item", fv + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"kind": "item", "format_version": fv,
               "updated": NOW, "components": clean}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path, len(clean)


def build_1260(log):
    """1.26.0：Item Components.json 给清单+描述，$ref 解析默认值。"""
    base = ITEM_BASE + "1.26.30/"
    merged = cached_get(base + "Item Components.json")
    if not merged:
        log("FAIL 1.26.0 无法获取 Item Components.json")
        return
    props = merged.get("properties") or {}
    origin = "bedrock-samples json_schemas/server/item/1.26.30"
    comps = {}
    n_ref, n_ok, n_dflt = 0, 0, 0
    for name, node in props.items():
        if not name.startswith("minecraft:") or not isinstance(node, dict):
            continue
        desc = node.get("description") or ""
        value = extract_default(node)
        ref = node.get("$ref")
        if ref and value is None:
            n_ref += 1
            target = resolve_ref(base, ref)
            if target:
                sub = cached_get(target)
                if sub:
                    n_ok += 1
                    if not desc:
                        desc = sub.get("description") or ""
                    value = extract_default(sub)
        if value is not None:
            n_dflt += 1
        entry = make_entry(name, desc, value, "1.26.0", origin)
        comps[name] = entry
        write_doc(name, entry)
    path, cnt = write_bucket("1.26.0", comps)
    log("WRITE item 1.26.0 n=%d with_value=%d (ref=%d resolved=%d) -> %s"
        % (cnt, n_dflt, n_ref, n_ok, os.path.relpath(path, PROJECT)))


def build_1210(log):
    """1.21.0：1.20.50 目录下逐个 minecraft_*.json。"""
    base = ITEM_BASE + "1.20.50/"
    files = api_list(base)
    if not files:
        log("FAIL 1.21.0 无法列出 1.20.50 目录")
        return
    origin = "bedrock-samples json_schemas/server/item/1.20.50（最近可得）"
    comps = {}
    n_dflt, fails = 0, 0
    for fn, typ in files:
        if typ != "file" or not fn.startswith("minecraft_"):
            continue
        schema = cached_get(base + fn)
        if not schema:
            fails += 1
            continue
        title = schema.get("title")
        name = title if (title and title.startswith("minecraft:")) else ("minecraft:" + fn[len("minecraft_"):-5].split(" ")[0])
        desc = schema.get("description") or ""
        value = extract_default(schema)
        if value is not None:
            n_dflt += 1
        entry = make_entry(name, desc, value, "1.21.0", origin)
        comps[name] = entry
        write_doc(name, entry)
    path, cnt = write_bucket("1.21.0", comps)
    log("WRITE item 1.21.0 n=%d with_value=%d fails=%d -> %s"
        % (cnt, n_dflt, fails, os.path.relpath(path, PROJECT)))


def main():
    os.makedirs(CACHE, exist_ok=True)
    f = open(REPORT, "w", encoding="utf-8")

    def log(s):
        f.write(s + "\n")
        f.flush()
        os.fsync(f.fileno())

    log("start %s" % NOW)
    build_1260(log)
    build_1210(log)
    log("done")
    f.close()


if __name__ == "__main__":
    main()