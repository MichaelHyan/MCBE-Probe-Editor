# -*- coding: utf-8 -*-
"""manifest.json 处理（项目级，不属于对象索引）。

职责:
  * 读 / 写行为包 / 资源包 manifest
  * 校验（uuid / modules.type / 版本数组）
  * 生成新 manifest 模板
"""

import json
import os
import re
import uuid as _uuid

from . import store
from . import workspace as ws

MANIFEST = "manifest.json"

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                     r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

MODULE_TYPES = ("data", "resources", "script", "javascript", "skin_pack",
                "world_template")


def new_uuid():
    return str(_uuid.uuid4())


def load(project_id, pack):
    """读取某包 manifest。返回 dict 或 None。"""
    try:
        return store.read_json(project_id, pack, MANIFEST)
    except Exception:
        return None


def save(project_id, pack, data):
    store.write_json(project_id, pack, MANIFEST, data)
    store.record_change(project_id, pack, MANIFEST, "modify")
    return data


def validate(data):
    """校验 manifest 结构，返回 (errors, warnings)。"""
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["根节点必须是对象"], []

    header = data.get("header")
    if not isinstance(header, dict):
        errors.append("缺少 header 对象")
        header = {}

    for key in ("name", "uuid", "version"):
        if header.get(key) in (None, ""):
            errors.append("header.%s 缺失" % key)

    uid = header.get("uuid")
    if uid and not UUID_RE.match(str(uid)):
        errors.append("header.uuid 格式不合法")

    ver = header.get("version")
    if ver is not None and not (isinstance(ver, list)
                                and len(ver) == 3
                                and all(isinstance(x, int) for x in ver)):
        errors.append("header.version 需为 [int,int,int]")

    modules = data.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append("modules 必须是非空数组")
    else:
        for i, m in enumerate(modules):
            if not isinstance(m, dict):
                errors.append("modules[%d] 不是对象" % i)
                continue
            mt = m.get("type")
            if mt not in MODULE_TYPES:
                warnings.append("modules[%d].type=%r 不在常见类型中" % (i, mt))
            mu = m.get("uuid")
            if not mu:
                errors.append("modules[%d].uuid 缺失" % i)
            elif not UUID_RE.match(str(mu)):
                errors.append("modules[%d].uuid 格式不合法" % i)
            mv = m.get("version")
            if mv is not None and not (isinstance(mv, list) and len(mv) == 3):
                errors.append("modules[%d].version 需为 [int,int,int]" % i)

    deps = data.get("dependencies")
    if deps is not None and not isinstance(deps, list):
        errors.append("dependencies 需为数组")

    return errors, warnings


def describe(project_id, pack):
    """返回给 UI 的描述。"""
    data = load(project_id, pack)
    root = ws.resolve_pack_dir(project_id, pack)
    errors, warnings = ([], [])
    if data is not None:
        errors, warnings = validate(data)
    return {
        "pack": pack,
        "exists": data is not None,
        "path": (root or "").replace("\\", "/"),
        "data": data,
        "errors": errors,
        "warnings": warnings,
    }


def template(pack, name):
    """生成新 manifest 模板。"""
    module_type = "data" if pack == "behavior" else "resources"
    return {
        "format_version": 2 if pack == "behavior" else 2,
        "header": {
            "name": name or ("%s Pack" % pack.title()),
            "description": "",
            "uuid": new_uuid(),
            "version": [1, 0, 0],
            "min_engine_version": [1, 20, 0],
        },
        "modules": [{
            "type": module_type,
            "uuid": new_uuid(),
            "version": [1, 0, 0],
        }],
    }
