# -*- coding: utf-8 -*-
"""探测流水线：跑 probe -> 写 index.json -> 建临时组件库。

把「导入项目后的第一步」收拢到一处，供路由与 CLI 复用。
"""

import time

from . import workspace as ws
from . import store
from . import database as db
from .probe import Probe


def _reader(project_id):
    def read(pack, rel):
        return store.read_json(project_id, pack, rel)
    return read


def run_probe(project_id, rebuild_db=True):
    """对项目执行探测，返回 (index, inventory|None)。"""
    bp_dir = ws.resolve_pack_dir(project_id, "behavior")
    rp_dir = ws.resolve_pack_dir(project_id, "resource")
    if not bp_dir and not rp_dir:
        raise ValueError("项目未包含任何可探测的包目录")

    probe = Probe()
    probe.run(bp_dir, rp_dir)
    index = probe.dump()
    index["project_id"] = project_id
    index["generated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    index["generated_ts"] = time.time()
    ws.save_index(project_id, index)

    inventory = None
    if rebuild_db:
        # 临时库只反映当前探测结果：重建前先释放旧库，避免陈旧桶堆积
        db.clear_temp(project_id)
        inventory = db.build_temp(project_id, index, _reader(project_id))

    meta = ws.load_meta(project_id)
    meta["last_probe"] = index["generated"]
    meta["stats"] = index.get("stats", {})
    ws.save_meta(project_id, meta)
    return index, inventory


def ensure_index(project_id):
    """取索引；不存在则自动探测。"""
    index = ws.load_index(project_id)
    if index and index.get("objects") is not None:
        return index
    index, _ = run_probe(project_id)
    return index


def find_object(index, ident):
    return ((index or {}).get("objects") or {}).get(ident)