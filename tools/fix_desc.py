# -*- coding: utf-8 -*-
"""修正正式库 description 污染（嵌套表感知版）。

根本原因：
  * block 的组件表在 Description 单元格内嵌了参数表（<table>）
  * 早期解析用「全文档 <tr 切分」，把嵌套表的行也切开，导致组件行被截断，
    整格文本（含子字段标题）被当作 description
  * 子字段标题在 HTML 中渲染为 `xxx#`，形成 `...surviveconditions#` 类污染

修复方法：
  用标签嵌套栈解析出「顶层表格 → 顶层行 → 顶层单元格」，
  Description 单元格截断到第一个 <h3> 或 <table> 之前，只保留组件级说明。

依赖 tools/_cache 的 HTML，必须在删除缓存前执行。
"""
import os
import re
import json
import html as htmlmod

TOOLS = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(TOOLS, "_cache")
PROJECT = os.path.dirname(TOOLS)
OFFICIAL = os.path.join(PROJECT, "mcbe_probe_editor", "db", "official")
OUT = os.path.join(CACHE, "_fix_desc.txt")

STRUCT_TAG = re.compile(r"<(/?)(table|tr|td|th)\b[^>]*>", re.I)
TAG_ANY = re.compile(r"<[^>]+>")
DESC_CUT = re.compile(r"<h3\b|<table\b", re.I)

DESC_FILES = {
    ("item", "1.16.0"): "item_1.16.0.html",
    ("block", "1.12.0"): "block_1.12.0.html",
    ("block", "1.16.0"): "block_1.16.0.html",
    ("block", "1.21.0"): "block_1.21.0.html",
    ("block", "1.26.0"): "block_1.26.0.html",
}


def text_of(s):
    s = TAG_ANY.sub("", s)
    s = htmlmod.unescape(s).replace("\u200b", "")
    return re.sub(r"\s+", " ", s).strip().strip("# ").strip()


def structure_events(html):
    """扫描结构性标签，返回 [{tag,start,end,path}]，path 为祖先标签链。"""
    stack, events = [], []
    for m in STRUCT_TAG.finditer(html):
        closing = m.group(1) == "/"
        tag = m.group(2).lower()
        if not closing:
            stack.append({"tag": tag, "start": m.end()})
            continue
        for i in range(len(stack) - 1, -1, -1):
            if stack[i]["tag"] != tag:
                continue
            el = stack[i]
            path = tuple(x["tag"] for x in stack[:i])
            events.append({"tag": tag, "start": el["start"],
                           "end": m.start(), "path": path})
            del stack[i:]
            break
    return events


def clean_desc(cell_html):
    cut = DESC_CUT.search(cell_html)
    return text_of(cell_html[:cut.start()] if cut else cell_html)


def parse_clean_descriptions(html_path):
    """返回 {组件名: 干净 description}"""
    if not os.path.isfile(html_path):
        return {}
    html = open(html_path, encoding="utf-8", errors="replace").read()
    events = structure_events(html)

    tables = [e for e in events if e["tag"] == "table" and not e["path"]]
    out = {}
    for tbl in tables:
        rows = [e for e in events
                if e["tag"] == "tr" and e["path"] == ("table",)
                and e["start"] >= tbl["start"] and e["end"] <= tbl["end"]]
        for row in rows:
            cells = [e for e in events
                     if e["tag"] in ("td", "th") and e["path"] == ("table", "tr")
                     and e["start"] >= row["start"] and e["end"] <= row["end"]]
            if len(cells) < 4:
                continue
            name = text_of(html[cells[0]["start"]:cells[0]["end"]])
            name = name.split("(")[0].strip().rstrip(":").strip()
            if not name.startswith("minecraft:") or name in out:
                continue
            out[name] = clean_desc(html[cells[3]["start"]:cells[3]["end"]])
    return out


def scan_suspicious(desc):
    """description 中残留子字段标题的特征：小写标识符紧跟 #。"""
    return bool(re.search(r"[a-z0-9_]#(?!\s*[0-9A-Fa-f]{3,6}\b)", desc))


def main():
    lines = []
    for (kind, fv), html_name in DESC_FILES.items():
        clean = parse_clean_descriptions(os.path.join(CACHE, html_name))
        path = os.path.join(OFFICIAL, "components", kind, fv + ".json")
        if not os.path.isfile(path):
            lines.append("SKIP %-6s %-8s 桶不存在" % (kind, fv))
            continue
        data = json.load(open(path, encoding="utf-8"))
        comps = data.get("components") or {}
        fixed, missed = 0, []
        for name, entry in comps.items():
            new = clean.get(name)
            if new is None:
                missed.append(name)
                continue
            if entry.get("description") != new:
                entry["description"] = new
                fixed += 1
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(path + ".tmp", path)
        lines.append("FIX  %-6s %-8s 解析=%-3d 修正=%-3d 未匹配=%d"
                     % (kind, fv, len(clean), fixed, len(missed)))

    lines += ["", "=== 残留扫描 ==="]
    total_bad = 0
    for kind in ("entity", "item", "block"):
        d = os.path.join(OFFICIAL, "components", kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            comps = json.load(open(os.path.join(d, fn), encoding="utf-8")).get("components") or {}
            bad = [n for n, e in comps.items()
                   if scan_suspicious(e.get("description") or "")]
            total_bad += len(bad)
            if bad:
                lines.append("  %-6s %-8s 可疑 %d：%s"
                             % (kind, fn[:-5], len(bad), ", ".join(sorted(bad)[:6])))
    if not total_bad:
        lines.append("  无残留")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()