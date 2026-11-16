#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端自检：创建工作区 -> 探测 -> 临时组件库 -> 查询。"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from services import workspace as ws
from services import pipeline
from services import database as db
from services import store

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"


def main():
    print("[1] 创建工作区 (copy=False)")
    pid = ws.create_project("e2e_test", BP, RP, copy=False)
    print("    project_id =", pid)
    print("    dir        =", ws.project_dir(pid))

    print("[2] 探测 + 建临时库")
    index, inventory = pipeline.run_probe(pid)
    stats = index.get("stats", {})
    print("    objects    =", stats.get("objects"))
    print("    kinds      =", stats.get("kinds"))
    print("    references =", stats.get("references"))
    print("    warnings   =", stats.get("warnings"))

    print("[3] 临时库桶")
    for b in db.list_temp_buckets(pid):
        print("    %-8s v%-10s %d 个组件" %
              (b["kind"], b["format_version"], b["count"]))

    print("[4] 查询 items:sword_b 的 item/1.21.50 组件")
    res = db.query_components(pid, "item", "1.21.50")
    merged = res.get("merged") or {}
    print("    组件数 =", len(merged))
    for name in list(merged)[:6]:
        e = merged[name]
        print("      %-38s %-10s origin=%s" %
              (name, e.get("value_type"), e.get("origin")))

    print("[5] 读对象主文件")
    ident = "items:sword_b"
    obj = pipeline.find_object(index, ident)
    prim = obj["primary"]
    data = store.read_json(pid, prim["pack"], prim["path"])
    comps = data["minecraft:item"]["components"]
    print("    %s -> %d 个组件, icon=%s" %
          (ident, len(comps), comps.get("minecraft:icon")))

    print("[6] 语言键 / 贴图引用")
    roles = {}
    for r in obj["references"]:
        roles[r["role"]] = roles.get(r["role"], 0) + 1
    print("    roles =", roles)

    print("\n清理测试工作区 …")
    ws.delete_project(pid)
    print("完成。")


if __name__ == "__main__":
    main()