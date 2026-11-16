# -*- coding: utf-8 -*-
"""正式库收尾：核实状态标记 + 人工剔除 + 组件文档生成（按组件跨版本聚合）。

构建流程最后一步，幂等（可重复执行）。

规则：
  * 官方来源（bedrock.dev 文档 / Mojang JSON Schema，source="manual"）免复核，
    verified = True
  * 文档未收录、取自项目实际值的条目（source="probe"）经人工确认后
    verified = True，note 标注「人工确认」
  * REMOVE 中的条目从桶中删除并移除对应 docs
  * docs 按 (kind, component) 聚合所有版本，单文件多版本分节，
    避免同名组件跨版本互相覆盖
  * item 1.16.0：子字段结构写入对应版本小节
    （文档该列默认值整列为空，default 保持 {}，不臆造）

字段结构来源：tools/official_item116_fields.json（已固化，不依赖缓存）；
若缺失则回退解析 tools/_cache/item_1.16.0.html。
"""
import os
import re
import json
import time
import html as htmlmod

TOOLS = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(TOOLS, "_cache")
PROJECT = os.path.dirname(TOOLS)
OFFICIAL = os.path.join(PROJECT, "mcbe_probe_editor", "db", "official")
FIELDS_JSON = os.path.join(TOOLS, "official_item116_fields.json")
REMOVED = os.path.join(CACHE, "_removed.json")

NOW = time.strftime("%Y-%m-%d %H:%M:%S")

REMOVE = {
    ("entity", "1.21.0"): [
        "minecraft:player.exhaustion",
        "minecraft:player.experience",
        "minecraft:player.level",
        "minecraft:player.saturation",
    ],
}

TR_SPLIT = re.compile(r"<tr\b", re.I)
CELL_OPEN = re.compile(r"<t([dh])\b[^>]*>", re.I)
H3_ID_RE = re.compile(r'<h3[^>]*>\s*<a[^>]*id="([^"]+)"', re.S | re.I)
TAG = re.compile(r"<[^>]+>")


def text_of(s):
    s = TAG.sub("", s)
    s = htmlmod.unescape(s).replace("\u200b", "")
    return re.sub(r"\s+", " ", s).strip().strip("# ").strip()


def doc_safe(name):
    return re.sub(r"[^0-9A-Za-z._-]", "_", name)


def doc_path(kind, name):
    return os.path.join(OFFICIAL, "docs", kind, doc_safe(name) + ".md")


def cells_raw(seg):
    opens = list(CELL_OPEN.finditer(seg))
    out = []
    for i, m in enumerate(opens):
        s = m.end()
        e = opens[i + 1].start() if i + 1 < len(opens) else len(seg)
        out.append(seg[s:e])
    return out


def fields_from_html():
    p = os.path.join(CACHE, "item_1.16.0.html")
    if not os.path.isfile(p):
        return {}
    html = open(p, encoding="utf-8", errors="replace").read()
    out = {}
    for tm in re.finditer(r"<table\b.*?</table>", html, re.S | re.I):
        seg = tm.group(0)
        if "minecraft:" not in seg:
            continue
        for r in TR_SPLIT.split(seg)[1:]:
            cs = cells_raw(r)
            if len(cs) < 4:
                continue
            name = text_of(cs[0]).split("(")[0].strip().rstrip(":").strip()
            if not name.startswith("minecraft:"):
                continue
            fields = [f for f in H3_ID_RE.findall(cs[3]) if not f.startswith("minecraft:")]
            if not fields:
                continue
            out.setdefault(name, [])
            for f in fields:
                if f not in out[name]:
                    out[name].append(f)
    return out


def item116_fields():
    if os.path.isfile(FIELDS_JSON):
        try:
            return json.load(open(FIELDS_JSON, encoding="utf-8"))
        except Exception:
            pass
    return fields_from_html()


def normalize_note(entry, fv):
    if entry.get("source") == "probe":
        return "人工确认；取自项目实际值（%s）" % fv
    note = (entry.get("note") or "")
    note = note.replace("；未人工核实", "").replace("，未人工核实", "")
    while note.startswith("来源："):
        note = note[len("来源："):]
    return note


def write_aggregated_doc(kind, name, versions, fields_map):
    """versions: [(fv, entry)]，按 fv 升序输出多版本分节。"""
    path = doc_path(kind, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fvs = sorted({fv for fv, _ in versions})
    all_verified = all(e.get("verified") for _, e in versions)
    lines = ["# `%s`" % name, "",
             "- 出现版本：%s" % "、".join("`%s`" % v for v in fvs),
             "- 核实状态：**%s**" % ("已核实" if all_verified else "部分待复核"), ""]

    # 说明：取第一个非空的 description
    desc = next((e.get("description") for _, e in versions if e.get("description")), "")
    if desc:
        lines += ["## 说明", "", desc, ""]

    for fv, entry in sorted(versions, key=lambda x: x[0]):
        lines += ["## `%s`" % fv, "",
                  "- 来源：%s" % (entry.get("note") or "未知"),
                  "- 核实状态：%s" % ("已核实" if entry.get("verified") else "待复核")]
        fields = (fields_map if (kind == "item" and fv == "1.16.0") else {}).get(name)
        if fields:
            lines += ["", "字段结构（官方文档未提供默认值）："]
            lines += ["- `%s`" % f for f in fields]
        lines += ["", "取值：", "", "```json",
                  json.dumps(entry.get("default"), ensure_ascii=False, indent=2),
                  "```", ""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    fields_map = item116_fields()
    removed_log = []
    # (kind, name) -> [(fv, entry)]
    collected = {}
    stale_docs = set()

    for kind in ("entity", "item", "block", "structure"):
        d = os.path.join(OFFICIAL, "components", kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            fv = fn[:-5]
            p = os.path.join(d, fn)
            data = json.load(open(p, encoding="utf-8"))
            comps = data.get("components") or {}

            for name in REMOVE.get((kind, fv), []):
                entry = comps.pop(name, None)
                if entry is None:
                    continue
                removed_log.append({"kind": kind, "fv": fv, "name": name, "entry": entry})

            for name, entry in comps.items():
                entry["verified"] = True
                entry["note"] = normalize_note(entry, fv)
                entry.pop("_fv", None)
                collected.setdefault((kind, name), []).append((fv, entry))

            data["components"] = comps
            data["updated"] = NOW
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, p)

    # 聚合写 docs
    for (kind, name), versions in collected.items():
        write_aggregated_doc(kind, name, versions, fields_map)
        stale_docs.add(doc_path(kind, name))

    # 清理不再对应任何组件的 md（例如被剔除的 player.*）
    for kind in ("entity", "item", "block", "structure"):
        d = os.path.join(OFFICIAL, "docs", kind)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(d, fn)
            if p not in stale_docs:
                os.remove(p)

    if removed_log:
        os.makedirs(CACHE, exist_ok=True)
        with open(REMOVED, "w", encoding="utf-8") as f:
            json.dump(removed_log, f, ensure_ascii=False, indent=2)

    for kind in ("entity", "item", "block"):
        d = os.path.join(OFFICIAL, "components", kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            comps = json.load(open(os.path.join(d, fn), encoding="utf-8")).get("components") or {}
            nv = sum(1 for v in comps.values() if v.get("verified"))
            print("%-6s %-8s n=%-4d verified=%d" % (kind, fn[:-5], len(comps), nv))
    print("docs 聚合后文件数：")
    for kind in ("entity", "item", "block"):
        d = os.path.join(OFFICIAL, "docs", kind)
        n = len([x for x in os.listdir(d) if x.endswith(".md")]) if os.path.isdir(d) else 0
        print("  %-6s %d" % (kind, n))
    print("剔除 %d 条" % len(removed_log))


if __name__ == "__main__":
    main()