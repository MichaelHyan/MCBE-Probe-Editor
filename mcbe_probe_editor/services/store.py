# -*- coding: utf-8 -*-
"""工作区文件读写 + 改动记录。

对应 plan.md:
  * 一切改动都落在工作区 source/ 下
  * 改动记录 edits/changes.json (add / modify / delete)
"""

import json
import os
import time

from . import workspace as ws


def norm(p):
    return p.replace("\\", "/")


# ---------------------------------------------------------------- 路径解析


def pack_root(project_id, pack):
    """返回该包的工作区根目录。"""
    return ws.resolve_pack_dir(project_id, pack)


def resolve_file(project_id, pack, rel):
    """把 (pack, 相对路径) 解析成绝对路径。

    只允许落在该包目录内，防止路径穿越。
    """
    if pack not in ("behavior", "resource"):
        raise ValueError("invalid pack: %r" % (pack,))
    if not rel or not isinstance(rel, str):
        raise ValueError("invalid path")
    rel = norm(rel).lstrip("/")
    if ".." in rel.split("/"):
        raise ValueError("path traversal denied: %r" % rel)

    root = pack_root(project_id, pack)
    if not root:
        raise FileNotFoundError("pack not found: %s" % pack)

    full = os.path.normpath(os.path.join(root, rel.replace("/", os.sep)))
    root_norm = os.path.normpath(root)
    if not (full == root_norm or full.startswith(root_norm + os.sep)):
        raise ValueError("path escapes pack root")
    return full


def exists(project_id, pack, rel):
    try:
        return os.path.isfile(resolve_file(project_id, pack, rel))
    except Exception:
        return False


# ---------------------------------------------------------------- 读写


def read_text(project_id, pack, rel):
    full = resolve_file(project_id, pack, rel)
    with open(full, "r", encoding="utf-8-sig") as f:
        return f.read()


def read_json(project_id, pack, rel):
    txt = read_text(project_id, pack, rel)
    return json.loads(txt)


def read_bytes(project_id, pack, rel):
    full = resolve_file(project_id, pack, rel)
    with open(full, "rb") as f:
        return f.read()


def _atomic_write(full, data_bytes):
    os.makedirs(os.path.dirname(full), exist_ok=True)
    tmp = full + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data_bytes)
    os.replace(tmp, full)


def write_json(project_id, pack, rel, obj, indent=2):
    """写 JSON 文件(覆盖)。"""
    full = resolve_file(project_id, pack, rel)
    text = json.dumps(obj, ensure_ascii=False, indent=indent)
    _atomic_write(full, text.encode("utf-8"))


def write_text(project_id, pack, rel, text):
    full = resolve_file(project_id, pack, rel)
    _atomic_write(full, text.encode("utf-8"))


def write_bytes(project_id, pack, rel, data):
    full = resolve_file(project_id, pack, rel)
    _atomic_write(full, data)


def file_info(project_id, pack, rel):
    full = resolve_file(project_id, pack, rel)
    st = os.stat(full)
    return {
        "pack": pack,
        "path": norm(rel),
        "size": st.st_size,
        "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
    }


# ---------------------------------------------------------------- 改动记录


def changes_path(project_id):
    return os.path.join(ws.project_dir(project_id), "edits", "changes.json")


def load_changes(project_id):
    p = changes_path(project_id)
    if not os.path.isfile(p):
        return {
            "project_id": project_id,
            "changes": [],
        }
    try:
        with open(p, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "changes" not in data:
            return {"project_id": project_id, "changes": []}
        return data
    except Exception:
        return {"project_id": project_id, "changes": []}


def _save_changes(project_id, data):
    p = changes_path(project_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def record_change(project_id, pack, rel, op):
    """记录一次改动。同一文件多次改动只保留最早记录 + 更新次数。"""
    data = load_changes(project_id)
    key = (pack, norm(rel))
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    for c in data["changes"]:
        if (c.get("pack"), c.get("path")) == key:
            c["op"] = op
            c["time"] = now
            c["times"] = int(c.get("times", 1)) + 1
            _save_changes(project_id, data)
            return c

    entry = {
        "pack": pack,
        "path": norm(rel),
        "op": op,
        "time": now,
        "times": 1,
    }
    data["changes"].append(entry)
    _save_changes(project_id, data)
    return entry


def clear_changes(project_id):
    data = {"project_id": project_id, "changes": []}
    _save_changes(project_id, data)
    return data


def changed_files(project_id):
    """返回 packed 的改动集合 {(pack, path)}。"""
    data = load_changes(project_id)
    return set((c.get("pack"), c.get("path")) for c in data["changes"])


# ---------------------------------------------------------------- 语言文件


def parse_lang(text):
    """解析 .lang 为 [(key, value, raw_line, lineno)]。

    raw_line 保留原始行(含注释、空行)，便于原样回写。
    """
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            out.append({
                "key": None, "value": None,
                "raw": line, "lineno": lineno})
            continue
        key, _, value = stripped.partition("=")
        out.append({
            "key": key.strip(),
            "value": value,
            "raw": line,
            "lineno": lineno,
        })
    return out


def update_lang_keys(text, updates):
    """按键更新 .lang 内容，保留其余行与顺序。

    updates: {key: new_value}
    返回 (new_text, applied_keys, missing_keys)
    """
    lines = text.splitlines()
    applied = []
    missing = list(updates.keys())

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            lines[i] = "%s=%s" % (key, updates[key])
            applied.append(key)
            if key in missing:
                missing.remove(key)

    new_text = "\n".join(lines)
    if text.endswith("\n"):
        new_text += "\n"
    return new_text, applied, missing