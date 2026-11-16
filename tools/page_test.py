#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""页面渲染 + 写回链路自检。

写回测试使用 copy=True 的独立工作区，不污染源模组目录。
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws
from services import pipeline
from services import store
from services import database as db

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"

FAILS = []


def show(name, resp, expect=200):
    body = resp.get_data(as_text=True)
    ok = resp.status_code == expect
    if not ok:
        FAILS.append(name)
    print("  [%s] %-48s %s%s" % (
        "OK " if ok else "ERR", name, resp.status_code,
        "" if ok else "  <- " + body[:160].replace("\n", " ")))
    return resp


def expect_true(name, cond, detail=""):
    print("  [%s] %-48s %s" % ("OK " if cond else "ERR", name, detail))
    if not cond:
        FAILS.append(name)


def main():
    pid = ws.create_project("page_test", BP, RP, copy=False)
    print("page_test project:", pid)
    pipeline.run_probe(pid)

    app = create_app()
    c = app.test_client()

    print("\n== 页面 ==")
    show("GET / (302 -> /projects)", c.get("/"), 302)
    show("GET /projects", c.get("/projects"))
    show("GET /project/<pid>/index", c.get("/project/%s/index" % pid))
    show("GET /project/<pid>/browser", c.get("/project/%s/browser" % pid))
    show("GET /project/<pid>/paint", c.get("/project/%s/paint" % pid))
    show("GET object page", c.get("/project/%s/object/items:sword_b" % pid))
    show("GET editor page", c.get("/project/%s/edit/items:sword_b" % pid))
    show("GET nonexistent object", c.get("/project/%s/object/xx:none" % pid))

    print("\n== 只读 API ==")
    for name, url in [
        ("projects", "/api/projects"),
        ("index", "/api/project/%s/index" % pid),
        ("objects", "/api/project/%s/objects" % pid),
        ("objects?kind=item", "/api/project/%s/objects?kind=item" % pid),
        ("object", "/api/project/%s/object/items:sword_b" % pid),
        ("unbound", "/api/project/%s/unbound" % pid),
        ("tree", "/api/project/%s/tree" % pid),
        ("files", "/api/project/%s/files" % pid),
        ("buckets", "/api/project/%s/buckets" % pid),
        ("components", "/api/project/%s/components?kind=item&fv=1.21.50" % pid),
        ("edit data", "/api/project/%s/edit/items:sword_b" % pid),
        ("texture", "/api/project/%s/texture?pack=resource&path=textures/items/sword_b.png" % pid),
        ("exports", "/api/project/%s/exports" % pid),
    ]:
        show("GET " + name, c.get(url))

    # 越权路径必须被拒
    show("GET raw path-traversal (400)",
         c.get("/api/project/%s/raw?pack=resource&path=../../manifest.json" % pid), 400)

    ws.delete_project(pid)

    # ---------------------------------------------------------------- 写回
    print("\n== 写回链路 (copy=True 独立工作区) ==")
    pid2 = ws.create_project("write_test", BP, RP, copy=True)
    print("write_test project:", pid2)
    pipeline.run_probe(pid2)

    ident = "items:sword_b"
    obj = pipeline.find_object(ws.load_index(pid2), ident)
    prim = obj["primary"]
    pack, rel = prim["pack"], prim["path"]

    before = store.read_json(pid2, pack, rel)
    orig_stack = before["minecraft:item"]["components"]["minecraft:max_stack_size"]

    print("\n [A] 修改组件 max_stack_size 1 -> 16")
    r = c.post("/api/project/%s/edit/%s/component" % (pid2, ident),
               json={"pack": pack, "path": rel,
                     "name": "minecraft:max_stack_size", "value": 16})
    show("POST component set", r)
    after = store.read_json(pid2, pack, rel)
    got = after["minecraft:item"]["components"]["minecraft:max_stack_size"]
    expect_true("值已写入磁盘", got == 16, "got=%r" % (got,))

    print("\n [B] 新增组件 minecraft:foobar")
    r = c.post("/api/project/%s/edit/%s/component" % (pid2, ident),
               json={"pack": pack, "path": rel,
                     "name": "minecraft:foobar", "value": {"a": 1}})
    show("POST component add", r)
    after = store.read_json(pid2, pack, rel)
    expect_true("新组件存在",
                "minecraft:foobar" in after["minecraft:item"]["components"])

    print("\n [C] 删除组件 minecraft:foobar")
    r = c.post("/api/project/%s/edit/%s/component" % (pid2, ident),
               json={"pack": pack, "path": rel,
                     "name": "minecraft:foobar", "op": "delete"})
    show("POST component delete", r)
    after = store.read_json(pid2, pack, rel)
    expect_true("新组件已删除",
                "minecraft:foobar" not in after["minecraft:item"]["components"])

    print("\n [D] 语言键写回")
    lang_refs = [x for x in obj["references"] if x["role"] == "lang"]
    zh = [x for x in lang_refs if "zh_CN" in x["path"]]
    if zh:
        lpack, lrel = zh[0]["pack"], zh[0]["path"]
        key = zh[0]["keys"][0]
        r = c.post("/api/project/%s/edit/%s/lang" % (pid2, ident),
                   json={"updates": {key: "宝剑X"}, "pack": lpack, "path": lrel})
        show("POST lang", r)
        text = store.read_text(pid2, lpack, lrel)
        expect_true("语言值已更新", ("%s=宝剑X" % key) in text)

    print("\n [E] 改动记录")
    changes = store.load_changes(pid2).get("changes") or []
    for ch in changes:
        print("      %-6s %s/%s (x%s)" %
              (ch["op"], ch["pack"], ch["path"], ch.get("times")))
    expect_true("改动记录非空", len(changes) > 0, "%d 条" % len(changes))

    print("\n [F] 导出 mcaddon")
    r = c.post("/api/project/%s/export" % pid2, json={"mode": "mcaddon"})
    show("POST export mcaddon", r)
    j = r.get_json() or {}
    exp_file = j.get("download")
    expect_true("导出文件已生成", bool(exp_file), exp_file or "")

    if exp_file:
        import zipfile
        full = j.get("output") or exp_file
        with zipfile.ZipFile(full) as zf:
            names = zf.namelist()
        has_b = any(n.endswith("items/items_sword_b.json") for n in names)
        expect_true("zip 内含行为包物品文件", has_b, "%d 个条目" % len(names))

    print("\n [G] 导出 changes")
    r = c.post("/api/project/%s/export" % pid2, json={"mode": "changes"})
    show("POST export changes", r)
    out = (r.get_json() or {}).get("output")
    expect_true("changes 目录已生成", bool(out) and os.path.isdir(out or ""),
                out or "")

    print("\n [H] 贴图写回 (alpha 规则)")
    tex_rel = "textures/items/sword_b.png"
    info = c.get("/api/project/%s/texture?pack=resource&path=%s"
                 % (pid2, tex_rel)).get_json()
    data_url = info["texture"]["data_url"]
    r = c.post("/api/project/%s/texture" % pid2,
               json={"pack": "resource", "path": tex_rel, "image": data_url})
    show("POST texture (原样写回)", r)
    j = r.get_json() or {}
    expect_true("写回成功且未修正像素",
                j.get("ok") and j.get("fixed_pixels") == 0,
                "fixed=%s" % j.get("fixed_pixels"))

    print("\n [I] 清理")
    ws.delete_project(pid2)

    print("\n" + "=" * 56)
    if FAILS:
        print("失败项 %d:" % len(FAILS))
        for f in FAILS:
            print("  -", f)
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())