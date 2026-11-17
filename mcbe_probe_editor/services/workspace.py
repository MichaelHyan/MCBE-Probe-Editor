# -*- coding: utf-8 -*-
"""工作区管理。

工作区结构(对应 plan.md 1.1):
    workspaces/<project_id>/
        meta.json           项目元信息
        source/
            behavior_pack/  行为包原始文件
            resource_pack/  资源包原始文件
        index.json          对象索引表
        db/                 临时/正式组件数据库
        edits/changes.json  改动记录

职责:
  * 创建工作区(可选复制源包)
  * 读写 meta.json / index.json
  * 解析包目录、列举项目
"""

import json
import os
import shutil
import time
import uuid

# 工作区根目录放在工程根(包目录的上一级)
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_PKG_DIR)
WORKSPACE_ROOT = os.path.join(_PROJECT_ROOT, "workspaces")

BEHAVIOR_DIR = "behavior_pack"
RESOURCE_DIR = "resource_pack"


# ---------------------------------------------------------------- 基础


def norm(p):
    return p.replace("\\", "/")


def ensure_root():
    os.makedirs(WORKSPACE_ROOT, exist_ok=True)


def project_dir(project_id):
    return os.path.join(WORKSPACE_ROOT, project_id)


def source_dir(project_id, pack):
    sub = BEHAVIOR_DIR if pack == "behavior" else RESOURCE_DIR
    return os.path.join(project_dir(project_id), "source", sub)


def db_dir(project_id):
    return os.path.join(project_dir(project_id), "db")


def edits_dir(project_id):
    return os.path.join(project_dir(project_id), "edits")


def valid_project_id(pid):
    if not pid or not isinstance(pid, str):
        return False
    ok = all(c.isalnum() or c in "-_." for c in pid)
    return ok and pid not in (".", "..")


def new_project_id(name):
    """由名字生成一个安全且唯一的 project_id。"""
    ensure_root()
    base = "".join(c for c in (name or "project")
                   if c.isalnum() or c in "-_") or "project"
    base = base[:40]
    pid = base
    n = 1
    while os.path.exists(project_dir(pid)):
        n += 1
        pid = "%s_%d" % (base, n)
    return pid


# ---------------------------------------------------------------- 读写 JSON


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


def meta_path(project_id):
    return os.path.join(project_dir(project_id), "meta.json")


def index_path(project_id):
    return os.path.join(project_dir(project_id), "index.json")


def load_meta(project_id):
    return _read_json(meta_path(project_id), {})


def save_meta(project_id, meta):
    _write_json(meta_path(project_id), meta)


def load_index(project_id):
    return _read_json(index_path(project_id), {})


def save_index(project_id, index):
    _write_json(index_path(project_id), index)


# ---------------------------------------------------------------- 创建 / 导入


def _copy_tree(src, dst):
    """复制目录内容(合并)。返回复制的文件数。"""
    if not src or not os.path.isdir(src):
        return 0
    count = 0
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "__pycache__", ".idea", ".vscode")]
        rel = os.path.relpath(dirpath, src)
        target_dir = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target_dir, exist_ok=True)
        for fn in filenames:
            shutil.copy2(os.path.join(dirpath, fn),
                         os.path.join(target_dir, fn))
            count += 1
    return count


def create_project(name, behavior_src=None, resource_src=None, copy=True):
    """创建工作区。

    behavior_src / resource_src: 源包目录(或 None)
    copy: True 则把源包内容复制进 source/，否则只记录路径
    """
    ensure_root()
    pid = new_project_id(name)

    pdir = project_dir(pid)
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(os.path.join(pdir, "source"), exist_ok=True)
    os.makedirs(os.path.join(pdir, "edits"), exist_ok=True)
    os.makedirs(db_dir(pid), exist_ok=True)

    copied = {}
    if copy:
        if behavior_src:
            n = _copy_tree(behavior_src, source_dir(pid, "behavior"))
            copied["behavior"] = n
        if resource_src:
            n = _copy_tree(resource_src, source_dir(pid, "resource"))
            copied["resource"] = n

    meta = {
        "project_id": pid,
        "name": name or pid,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "copy_mode": bool(copy),
        "sources": {
            "behavior": norm(behavior_src) if behavior_src else None,
            "resource": norm(resource_src) if resource_src else None,
        },
        "copied_files": copied,
        "has_behavior": bool(behavior_src),
        "has_resource": bool(resource_src),
    }
    save_meta(pid, meta)
    return pid


def resolve_pack_dir(project_id, pack):
    """返回当前项目该包的实际目录(优先 source/,其次原始路径)。"""
    src = source_dir(project_id, pack)
    if os.path.isdir(src):
        return src
    meta = load_meta(project_id)
    raw = (meta.get("sources") or {}).get(pack)
    if raw and os.path.isdir(raw):
        return raw
    return None


def ensure_pack_dir(project_id, pack):
    """确保某包的 source 目录存在（新建对象时按需创建）。"""
    d = source_dir(project_id, pack)
    os.makedirs(d, exist_ok=True)
    return d


def list_projects():
    ensure_root()
    out = []
    for name in sorted(os.listdir(WORKSPACE_ROOT)):
        pdir = os.path.join(WORKSPACE_ROOT, name)
        if not os.path.isdir(pdir):
            continue
        meta = _read_json(os.path.join(pdir, "meta.json"), {})
        if not meta:
            continue
        idx = _read_json(os.path.join(pdir, "index.json"), {})
        stats = idx.get("stats") or {}
        meta["_objects"] = stats.get("objects", 0)
        meta["_indexed"] = bool(idx)
        out.append(meta)
    return out


def delete_project(project_id):
    if not valid_project_id(project_id):
        return False
    pdir = project_dir(project_id)
    if not os.path.isdir(pdir):
        return False
    shutil.rmtree(pdir, ignore_errors=True)
    return True


# ---------------------------------------------------------------- mcaddon 导入


def inspect_mcaddon(zip_path):
    """检视 mcaddon/zip: 找出其中的 behavior / resource 包根目录。

    返回 {'behavior': 子目录名, 'resource': 子目录名, 'members': [...]}
    以 manifest.json 中的 modules[].type 判定包类型。
    """
    import zipfile

    info = {"behavior": None, "resource": None, "packs": []}
    if not os.path.isfile(zip_path):
        return info
    try:
        zf = zipfile.ZipFile(zip_path, "r")
    except Exception:
        return info

    with zf:
        for member in zf.namelist():
            if not member.lower().endswith("manifest.json"):
                continue
            try:
                raw = zf.read(member).decode("utf-8-sig")
                data = json.loads(raw)
            except Exception:
                continue
            root = member.rsplit("/", 1)[0] if "/" in member else ""
            module_type = None
            for m in (data.get("modules") or []):
                if isinstance(m, dict) and m.get("type"):
                    module_type = m["type"]
                    break
            kind = None
            if module_type == "data":
                kind = "behavior"
            elif module_type == "resources":
                kind = "resource"
            if kind and not info[kind]:
                info[kind] = root
            header = data.get("header") or {}
            info["packs"].append({
                "root": root, "type": module_type,
                "name": header.get("name"),
                "uuid": header.get("uuid"),
                "version": header.get("version")})
    return info


def extract_mcaddon(zip_path, project_id, pack_roots):
    """把 mcaddon 内容解压到工作区 source/ 下。"""
    import zipfile

    ensure_root()
    if not os.path.isfile(zip_path):
        return False
    with zipfile.ZipFile(zip_path, "r") as zf:
        for kind in ("behavior", "resource"):
            root = pack_roots.get(kind)
            dst = source_dir(project_id, kind)
            os.makedirs(dst, exist_ok=True)
            for member in zf.namelist():
                if root:
                    if not member.startswith(root + "/"):
                        continue
                    rel = member[len(root) + 1:]
                else:
                    rel = member
                if not rel or rel.endswith("/"):
                    continue
                target = os.path.join(dst, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as out:
                    out.write(src.read())
        if not pack_roots.get("resource"):
            # 无明确资源包: 全部按行为包落盘
            pass
    return True