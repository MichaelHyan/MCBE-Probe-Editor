# -*- coding: utf-8 -*-
"""验证：output 目录 + 示例库 API。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws
from services import pipeline
from services import database as db
from routes import export as export_mod

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"
OUT = os.path.join(ROOT, "_r4a.txt")

FAILS = []
LINES = []


def check(name, cond, detail=""):
    LINES.append("[%s] %s  %s" % ("OK " if cond else "ERR", name, detail))
    if not cond:
        FAILS.append(name)


def main():
    pid = ws.create_project("verify_r4a", BP, RP, copy=False)
    pipeline.run_probe(pid)
    c = create_app().test_client()
    base = "/api/project/%s" % pid

    # 1. output 目录
    LINES.append("output root = %s" % export_mod.OUTPUT_ROOT)
    check("output 在工程根下",
          os.path.dirname(export_mod.OUTPUT_ROOT) == ROOT,
          export_mod.OUTPUT_ROOT)

    r = c.post(base + "/export", json={"mode": "mcaddon"}).get_json()
    check("导出成功", r.get("ok"), str(r.get("output")))
    out = r.get("output") or ""
    check("导出落在 output/", "output" + os.sep in out or "/output/" in out, out)
    check("导出文件存在", os.path.isfile(out), out)

    # 2. 示例库
    exs = db.list_examples(pid, "item", "1.21.50", "minecraft:max_stack_size")
    check("有可用示例", len(exs) > 0, "n=%d" % len(exs))
    check("含 project 来源",
          any(x["source"] == "project" for x in exs),
          str([x["source"] for x in exs]))

    add = db.record_example("item", "1.21.50", "minecraft:max_stack_size",
                            16, label="manual16", source="local",
                            origin=pid)
    check("写入本地库示例", add.get("ok"), str(add))

    exs2 = db.list_examples(pid, "item", "1.21.50", "minecraft:max_stack_size")
    check("本地库示例可见",
          any(x["source"] == "local" and x["value"] == 16 for x in exs2),
          str([(x["source"], x["value"]) for x in exs2]))

    r = c.get(base + "/db/examples?kind=item&fv=1.21.50&component=minecraft:max_stack_size").get_json()
    check("示例 API 可用", r.get("ok") and len(r.get("examples") or []) > 0,
          "n=%d" % len(r.get("examples") or []))

    # 清理
    ws.delete_project(pid)
    p = db.official_path("item", "1.21.50")
    if os.path.isfile(p):
        os.remove(p)
        d = os.path.dirname(p)
        while d and os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            d = os.path.dirname(d)
    if os.path.isfile(out):
        os.remove(out)
    od = os.path.dirname(out)
    if os.path.isdir(od) and not os.listdir(od):
        os.rmdir(od)

    LINES.append("")
    LINES.append("失败 %d 项" % len(FAILS))
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    print("fails:", len(FAILS))


if __name__ == "__main__":
    main()