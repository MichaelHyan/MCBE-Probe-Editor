# -*- coding: utf-8 -*-
"""未绑定视图 + 组件数据库链路自检（copy=True 独立工作区）。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws
from services import pipeline
from services import database as db

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"

FAILS = []


def show(name, resp, expect=200):
    ok = resp.status_code == expect
    if not ok:
        FAILS.append(name)
    print("  [%s] %-44s %s" % ("OK " if ok else "ERR", name, resp.status_code))
    return resp


def check(name, cond, detail=""):
    print("  [%s] %-44s %s" % ("OK " if cond else "ERR", name, detail))
    if not cond:
        FAILS.append(name)


def main():
    pid = ws.create_project("db_test", BP, RP, copy=False)
    pipeline.run_probe(pid)
    app = create_app()
    c = app.test_client()
    base = "/api/project/%s" % pid

    print("\n== 页面 ==")
    show("GET unbound page", c.get("/project/%s/unbound" % pid))
    show("GET database page", c.get("/project/%s/database" % pid))

    print("\n== 未绑定项 ==")
    r = show("GET unbound/detail", c.get(base + "/unbound/detail?limit=5")).get_json()
    check("counts 非空", bool(r.get("counts")), str(r.get("counts")))
    check("分页正确", len(r.get("items", [])) <= 5, "items=%d" % len(r.get("items", [])))

    r2 = c.get(base + "/unbound/detail?kind=lang_key&limit=3").get_json()
    check("按 kind 过滤生效",
          all(x.get("kind") == "lang_key" for x in r2.get("items", [])),
          "total=%s" % r2.get("total"))

    print("\n== 组件数据库 ==")
    r = show("GET db/buckets", c.get(base + "/db/buckets")).get_json()
    temp = r.get("temp") or []
    check("临时桶非空", len(temp) > 0, "%d 个桶" % len(temp))

    if temp:
        b = temp[0]
        kind, fv = b["kind"], b["format_version"]
        r = c.get(base + "/db/bucket?kind=%s&fv=%s" % (kind, fv)).get_json()
        bucket = r.get("bucket") or {}
        check("桶查询返回 merged",
              bool(bucket.get("merged")),
              "kind=%s fv=%s 组件=%d" % (kind, fv, len(bucket.get("merged") or {})))

        r = c.post(base + "/db/promote", json={"kind": kind, "fv": fv}).get_json()
        check("提升到正式库", r.get("ok") and r.get("total", 0) > 0,
              "added=%s total=%s" % (r.get("added"), r.get("total")))

        name = list(bucket["merged"].keys())[0]
        r = c.post(base + "/db/verify",
                   json={"kind": kind, "fv": fv, "name": name,
                         "doc": "# %s\n\n测试文档。" % name}).get_json()
        check("标记核实", r.get("ok"), "doc_ref=%s" % r.get("doc_ref"))

        r = c.get(base + "/db/doc?kind=%s&name=%s" % (kind, name)).get_json()
        check("文档已写入", bool(r.get("content")), (r.get("content") or "")[:20])

        r = c.get(base + "/db/buckets").get_json()
        off = [x for x in (r.get("official") or [])
               if x["kind"] == kind and x["format_version"] == fv]
        check("正式库桶已存在", bool(off),
              "verified=%s" % (off[0].get("verified") if off else None))

    ws.delete_project(pid)
    print("\n" + "=" * 52)
    if FAILS:
        print("失败 %d 项:" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())