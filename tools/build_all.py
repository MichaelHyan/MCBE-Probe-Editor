# -*- coding: utf-8 -*-
"""正式库构建总入口：文档解析 + 缺口补全 + 自检。

流程：
  1. 解析 bedrock.dev 缓存文档（标题通道 + 表格通道 + 侧栏补名）
  2. 修正 description（截断到第一个 <table>/<hN>，避免混入 "Parameters"）
  3. 写入 db/official/components/<kind>/<fv>.json 与 docs
  4. 补全：临时库有、文档无的组件，从临时库复制（source=probe，
     examples[].source=project，origin 保留对象 identifier），并在 note 标注
  5. 自检：读回桶、统计 verified/with_value、抽查字段、扫描 description 残留
"""
import os
import re
import json
import glob
import html as htmlmod
import time
from urllib.parse import unquote

TOOLS = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(TOOLS, "_cache")
PROJECT = os.path.dirname(TOOLS)
OFFICIAL = os.path.join(PROJECT, "mcbe_probe_editor", "db", "official")
TEMP_DIR = os.path.join(PROJECT, "mcbe_probe_editor", "workspaces",
                        "TaoismV5", "db", "temp", "components")
REPORT = os.path.join(CACHE, "_build_all_report.txt")
NOW = time.strftime("%Y-%m-%d %H:%M:%S")

VERSION_SRC = {
    "1.12.0": "1.12.0.0/1.12.0.28",
    "1.16.0": "1.16.0.0/1.16.100.60",
    "1.21.0": "1.21.0.0/1.21.130.28",
    "1.26.0": "1.26.0.0/1.26.60.5",
}

HEAD_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.S | re.I)
ANCHOR_ID_RE = re.compile(r'id="([^"]*)"')
TABLE_RE = re.compile(r"<table\b.*?</table>", re.S | re.I)
TR_SPLIT_RE = re.compile(r"<tr\b", re.I)
CELL_OPEN_RE = re.compile(r"<t([dh])\b[^>]*>", re.I)
SIDEBAR_RE = re.compile(r'href="#(minecraft%3A[^"]+)"[^>]*>([^<]+)<', re.I)
NAME_CLEAN_RE = re.compile(r"^(minecraft:[^\s(]+)")
DESC_CUT_RE = re.compile(r"<h[1-6]\b|<table\b", re.I)

SECTION_EXCLUDE = {
    "client entity documentation", "spawn egg", "data-driven spawning",
    "spawn rules", "built-in events", "filters", "id lists",
    "entity definition properties", "entity description properties",
    "item definition properties", "item description properties",
    "block definition properties", "block description properties",
    "block event responses", "block trigger components",
    "animation_controllers", "animations", "enable_attachables",
    "held_item_ignores_lighting", "held_item_scale", "hide_armor",
    "identifier", "locators", "materials, textures, animations",
    "min_engine_version", "particle", "render_controllers", "scripts",
    "index",
}

NAME_BLOCKLIST = {
    "minecraft:biome_filter", "minecraft:brightness_filter", "minecraft:density_limit",
    "minecraft:difficulty_filter", "minecraft:herd", "minecraft:permute_type",
    "minecraft:spawns_on_surface", "minecraft:spawns_underwater", "minecraft:weight",
    "minecraft:entity_born", "minecraft:entity_spawned",
    "minecraft:entity_transformed", "minecraft:on_prime",
}


# ---------------------------------------------------------------- 工具


def text_of(fragment):
    s = re.sub(r"<[^>]+>", "", fragment)
    s = htmlmod.unescape(s).replace("\u200b", "")
    return re.sub(r"\s+", " ", s).strip().strip("# ").strip()


def clean_name(raw):
    s = (raw or "").strip()
    m = NAME_CLEAN_RE.match(s)
    return (m.group(1) if m else s) if s else ""


def literal(raw):
    if raw is None:
        return None
    s = raw.strip()
    if not s or s.lower() in ("na", "n/a", "-", "n\\a"):
        return None
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if s[0] in "[{":
        try:
            return json.loads(s)
        except Exception:
            return None
    t = re.sub(r"[fFdD]$", "", s)
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if (re.fullmatch(r"-?\d*\.\d+([eE][+-]?\d+)?", t)
            or re.fullmatch(r"-?\d+[eE][+-]?\d+", t)):
        return float(t)
    return s


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


def split_rows(html):
    out = []
    for seg in TR_SPLIT_RE.split(html)[1:]:
        opens = list(CELL_OPEN_RE.finditer(seg))
        if not opens:
            continue
        cells = []
        for i, m in enumerate(opens[:4]):
            s = m.end()
            e = opens[i + 1].start() if i + 1 < len(opens) else len(seg)
            cells.append(text_of(seg[s:e]))
        if any(cells):
            out.append((opens[0].group(1).lower(), cells))
    return out


def build_default(params):
    obj = {}
    for p in params:
        v = literal(p["default_raw"])
        if v is not None:
            obj[p["name"]] = v
    return obj


def description_of(body):
    """组件说明：优先第一个 <p>，否则截断到下一个标题/表格。"""
    pm = re.search(r"<p>(.*?)</p>", body, re.S | re.I)
    if pm:
        return text_of(pm.group(1))
    head = DESC_CUT_RE.split(body, 1)[0]
    return text_of(head)


# ---------------------------------------------------------------- 文档解析


def parse_headings(html):
    out = []
    for m in HEAD_RE.finditer(html):
        inner = m.group(2)
        idm = ANCHOR_ID_RE.search(inner)
        out.append({
            "level": int(m.group(1)),
            "id": unquote(idm.group(1)) if idm else "",
            "title": text_of(inner),
            "start": m.start(),
            "end": m.end(),
        })
    return out


def parse_by_heading(html):
    heads = parse_headings(html)
    comps, section = {}, ""
    for i, h in enumerate(heads):
        if not h["id"].startswith("minecraft:"):
            section = h["title"].lower().strip("# ").strip()
            continue
        if section in SECTION_EXCLUDE:
            continue
        name = clean_name(h["id"])
        if not name or name in comps or name in NAME_BLOCKLIST:
            continue
        end = len(html)
        for nxt in heads[i + 1:]:
            if nxt["level"] <= h["level"]:
                end = nxt["start"]
                break
        body = html[h["end"]:end]
        tm = TABLE_RE.search(body)
        params = []
        if tm:
            for ck, cells in split_rows(tm.group(0)):
                if ck == "h" or len(cells) < 4 or not cells[0]:
                    continue
                params.append({"name": cells[0], "type": cells[1],
                               "default_raw": cells[2], "description": cells[3]})
        comps[name] = {
            "description": description_of(body),
            "params": params,
            "default": build_default(params),
            "has_params": bool(params),
        }
    return comps


def parse_by_rows(html):
    comps = {}
    for ck, cells in split_rows(html):
        if ck == "h" or not cells or not cells[0]:
            continue
        name = clean_name(cells[0])
        if not name.startswith("minecraft:") or name in NAME_BLOCKLIST:
            continue
        if name in comps:
            continue
        dflt = literal(cells[2]) if len(cells) >= 3 else None
        comps[name] = {
            "description": cells[3] if len(cells) >= 4 else "",
            "params": [], "default": {} if dflt is None else dflt,
            "has_params": False,
        }
    return comps


def parse_sidebar(html):
    return {clean_name(unquote(m.group(1))) for m in SIDEBAR_RE.finditer(html)}


def parse_doc(path, kind):
    html = open(path, encoding="utf-8", errors="replace").read()
    comps = parse_by_heading(html)
    if kind in ("block", "item"):
        for name, entry in parse_by_rows(html).items():
            comps.setdefault(name, entry)
    for name in parse_sidebar(html):
        if not name or name in comps or name in NAME_BLOCKLIST:
            continue
        comps[name] = {"description": "", "params": [], "default": {},
                       "has_params": False}
    return comps


# ---------------------------------------------------------------- 条目构造


def doc_safe(name):
    return re.sub(r"[^0-9A-Za-z._-]", "_", name)


def docs_value_of(entry):
    d = entry.get("default")
    if isinstance(d, dict):
        return d
    if d is not None and not isinstance(d, (list, str, int, float, bool)):
        return d
    return d if d is not None else {}


def make_official_entry(kind, name, entry, fv, source_path):
    value = entry.get("default")
    if value is None:
        value = {}
    return {
        "value_type": infer_type(value),
        "default": value,
        "example": value,
        "examples": [{
            "label": fv,
            "source": "official",
            "value": value,
            "origin": "bedrock.dev %s" % source_path,
            "added": NOW,
        }],
        "note": "来源：bedrock.dev 官方文档（%s）；未人工核实" % fv,
        "description": entry.get("description") or "",
        "doc_ref": "docs/%s/%s.md" % (kind, doc_safe(name)),
        "verified": False,
        "source": "manual",
        "added_in": None,
        "deprecated": False,
    }


def write_official_doc(kind, name, entry, fv, source_path):
    path = os.path.join(OFFICIAL, "docs", kind, doc_safe(name) + ".md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    value = entry.get("default")
    if value is None:
        value = {}
    lines = ["# `%s`" % name, "", "- 版本：`%s`" % fv,
             "- 来源：bedrock.dev `%s`" % source_path,
             "- 核实状态：**未人工核实**", ""]
    if entry.get("description"):
        lines += ["## 说明", "", entry["description"], ""]
    if entry.get("has_params"):
        lines += ["## 参数", "", "| 名称 | 类型 | 文档默认值 | 说明 |", "|---|---|---|---|"]
        for p in entry["params"]:
            d = (p["default_raw"] or "").replace("|", "\\|")
            desc = (p["description"] or "").replace("|", "\\|")
            lines.append("| `%s` | %s | %s | %s |" % (p["name"], p["type"], d, desc))
        lines.append("")
    lines += ["## 合成取值", "", "```json",
              json.dumps(value, ensure_ascii=False, indent=2), "```", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_bucket(kind, fv, comps):
    path = os.path.join(OFFICIAL, "components", kind, fv + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"kind": kind, "format_version": fv,
               "updated": NOW, "components": comps}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def load_temp(kind, fv):
    p = os.path.join(TEMP_DIR, kind, fv + ".json")
    if not os.path.isfile(p):
        return {}
    try:
        return json.load(open(p, encoding="utf-8-sig")).get("components") or {}
    except Exception:
        return {}


def fill_from_temp(kind, fv, comps, temp_comps):
    """把文档缺失、临时库有的组件补进来（source=probe，示例 source=project）。"""
    added = []
    for name, t in temp_comps.items():
        if name in comps:
            continue
        exs = t.get("examples") or []
        if not exs and t.get("example") is not None:
            exs = [{"label": "probe", "source": "project",
                    "value": t.get("example"), "origin": None, "added": NOW}]
        fixed = []
        for ex in exs[:20]:
            fixed.append({
                "label": "probe",
                "source": "project",
                "value": ex.get("value"),
                "origin": ex.get("origin"),
                "added": ex.get("added") or NOW,
            })
        value = t.get("example")
        if value is None:
            value = t.get("default")
        if value is None:
            value = {}
        comps[name] = {
            "value_type": t.get("value_type") or infer_type(value),
            "default": value,
            "example": value,
            "examples": fixed,
            "note": "文档缺失，取自项目实际值（%s），未人工核实" % fv,
            "description": "",
            "doc_ref": None,
            "verified": False,
            "source": "probe",
            "added_in": None,
            "deprecated": False,
        }
        # 生成说明文档
        path = os.path.join(OFFICIAL, "docs", kind, doc_safe(name) + ".md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# `%s`\n\n- 版本：`%s`\n- 来源：项目临时库（bedrock.dev 文档未收录）\n"
                    "- 核实状态：**未人工核实**\n\n## 项目实际取值\n\n```json\n%s\n```\n"
                    % (name, fv, json.dumps(value, ensure_ascii=False, indent=2)))
        added.append(name)
    return added


# ---------------------------------------------------------------- 自检


def selfcheck(lines):
    lines.append("=== 自检 ===")
    for kind in ("entity", "item", "block"):
        d = os.path.join(OFFICIAL, "components", kind)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            p = os.path.join(d, fn)
            data = json.load(open(p, encoding="utf-8"))
            comps = data.get("components") or {}
            if not comps:
                lines.append("  ! %s/%s 空桶" % (kind, fn))
                continue
            bad_desc, bad_field, n_verified, n_value = [], [], 0, 0
            for name, e in comps.items():
                if e.get("description", "").endswith("Parameters"):
                    bad_desc.append(name)
                if not {"value_type", "default", "example", "examples", "note",
                        "description", "doc_ref", "verified", "source"} <= set(e):
                    bad_field.append(name)
                if e.get("verified"):
                    n_verified += 1
                if e.get("default") not in (None, {}, []):
                    n_value += 1
            lines.append("  %-6s %-8s n=%-4d with_value=%-4d verified=%-3d desc_bad=%-3d field_bad=%d"
                          % (kind, fn, len(comps), n_value, n_verified,
                             len(bad_desc), len(bad_field)))
            for nm in bad_desc[:3]:
                lines.append("      desc_bad: %s" % nm)
            for nm in bad_field[:3]:
                lines.append("      field_bad: %s" % nm)


def main():
    lines = []
    for path in sorted(glob.glob(os.path.join(CACHE, "*.html"))):
        base = os.path.basename(path)[:-5]
        kind, _, fv = base.rpartition("_")
        if kind not in ("entity", "item", "block") or fv not in VERSION_SRC:
            continue

        parsed = parse_doc(path, kind)
        if len(parsed) <= 3:
            lines.append("SKIP  %-6s %-7s 文档无组件清单（%d 条）" % (kind, fv, len(parsed)))
            continue

        source_path = VERSION_SRC[fv]
        comps = {}
        for name in sorted(parsed):
            comps[name] = make_official_entry(kind, name, parsed[name], fv, source_path)
            write_official_doc(kind, name, parsed[name], fv, source_path)

        temp_comps = load_temp(kind, fv)
        added = fill_from_temp(kind, fv, comps, temp_comps)

        write_bucket(kind, fv, comps)
        nv = sum(1 for v in comps.values() if v["default"] not in (None, {}, []))
        lines.append("WRITE %-6s %-7s docs=%-4d from_temp=%-3d total=%-4d with_value=%d"
                     % (kind, fv, len(parsed), len(added), len(comps), nv))
        if added:
            lines.append("      from_temp: " + ", ".join(sorted(added)))

    lines.append("")
    selfcheck(lines)

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()