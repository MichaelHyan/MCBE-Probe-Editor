#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""结构降版本链路自检（copy=True 独立工作区，不污染源目录）。"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws
from services import pipeline
from services import structure as st
from services import store

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"


def main():
    pid = ws.create_project("struct_test", BP, RP, copy=True)
    print("project:", pid)
    pipeline.run_probe(pid)

    app = create_app()
    c = app.test_client()
    base = "/api/project/%s" % pid

    print("\n== [1] 结构列表（真实文件）==")
    r = c.get(base + "/structures").get_json()
    rows = r.get("structures") or []
    print("  结构数 =", len(rows))
    fv_hist = {}
    for row in rows:
        fv = row.get("format_version")
        fv_hist[fv] = fv_hist.get(fv, 0) + 1
    print("  format_version 分布 =", fv_hist)
    for row in rows[:4]:
        print("    %-42s fv=%-4s layers=%-3s pal=%-4s void=%s" % (
            row.get("path"), row.get("format_version"),
            row.get("layers"), row.get("palette"), row.get("void_cells")))

    need = [x for x in rows if x.get("format_version") == 2]
    print("  需要降版本 =", len(need))

    if need:
        print("\n== [2] 单个降版本 ==")
        t = need[0]
        r = c.post(base + "/structure/downgrade",
                   json={"pack": t["pack"], "path": t["path"]}).get_json()
        res = (r.get("results") or [{}])[0]
        print("  目标:", t["path"])
        print("  ok=%s skipped=%s cells=%s void=%s liquid=%s check=%s" % (
            res.get("ok"), res.get("skipped"), res.get("cells"),
            res.get("kept_void"), res.get("liquid_kept"), res.get("check")))

        print("\n== [3] 幂等复跑 ==")
        r2 = c.post(base + "/structure/downgrade",
                    json={"pack": t["pack"], "path": t["path"]}).get_json()
        res2 = (r2.get("results") or [{}])[0]
        print("  skipped=%s reason=%s" % (res2.get("skipped"),
                                          res2.get("reason")))

        print("\n== [4] 备份目录 ==")
        full = store.resolve_file(pid, t["pack"], t["path"])
        bdir = os.path.join(os.path.dirname(full), st.BACKUP_DIRNAME)
        if os.path.isdir(bdir):
            for fn in os.listdir(bdir):
                print("   ", fn, os.path.getsize(os.path.join(bdir, fn)), "字节")
        else:
            print("    (无备份)")

    print("\n清理…")
    ws.delete_project(pid)
    print("完成")


if __name__ == "__main__":
    main()