# -*- coding: utf-8 -*-
"""验证：manifest 读写 + 新建对象。"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws
from services import pipeline
from services import store

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"
OUT = os.path.join(ROOT, "_r4c.txt")

FAILS = []
LINES = []


def check(name, cond, detail=""):
    LINES.append("[%s] %s  %s" % ("OK " if cond else "ERR", name, detail))
    if not cond:
        FAILS.append(name)


def main():
    pid = ws.create_project("verify_r4c", BP, RP, copy=True)
    pipeline.run_probe(pid)
    c = create_app().test_client()
    base = "/api/project/%s" % pid

    # ---- manifest ----
    r = c.get(base + "/manifest").get_json()
    check("读取双包 manifest", r.get("ok"), str(list((r.get("packs") or {}).keys())))
    beh = (r.get("packs") or {}).get("behavior") or {}
    res = (r.get("packs") or {}).get("resource") or {}
    check("行为包 manifest 存在", beh.get("exists"), str(beh.get("errors")))
    check("资源包 manifest 存在", res.get("exists"), str(res.get("errors")))
    check("行为包校验通过", not beh.get("errors"), str(beh.get("errors")))
    check("资源包校验通过", not res.get("errors"), str(res.get("errors")))

    # 改 description 保存
    data = beh.get("data") or {}
    data.setdefault("header", {})["description"] = "verify_r4c"
    r = c.post(base + "/manifest", json={"pack": "behavior", "data": data}).get_json()
    check("保存 manifest", r.get("ok"), str(r))
    saved = store.read_json(pid, "behavior", "manifest.json")
    check("manifest 落盘", saved["header"]["description"] == "verify_r4c",
          saved["header"].get("description"))

    # 非法 manifest 被拒
    bad = {"header": {"name": "x", "uuid": "not-a-uuid", "version": [1, 0]},
           "modules": []}
    r = c.post(base + "/manifest", json={"pack": "behavior", "data": bad})
    check("非法 manifest 被拒", r.status_code == 400, str(r.status_code))

    # 模板
    r = c.post(base + "/manifest/template", json={"pack": "resource"}).get_json()
    check("生成模板", r.get("ok") and r.get("data", {}).get("modules"),
          str(r.get("data", {}).get("modules")))

    # ---- 新建对象 ----
    r = c.get(base + "/objects/kinds").get_json()
    check("kinds 接口", r.get("ok") and "item" in (r.get("kinds") or []), str(r.get("kinds")))

    r = c.post(base + "/objects/create", json={
        "kind": "item", "namespace": "demo", "name": "new_sword",
        "options": {"with_resource": True, "with_lang": True},
    }).get_json()
    check("创建 item", r.get("ok"), str(r.get("error") or r.get("created")))
    ident = r.get("identifier")
    check("identifier 正确", ident == "demo:new_sword", str(ident))

    check("行为包文件已生成",
          store.exists(pid, "behavior", "items/new_sword.json"))
    bd = store.read_json(pid, "behavior", "items/new_sword.json")
    check("主文件 identifier 正确",
          bd["minecraft:item"]["description"]["identifier"] == "demo:new_sword")

    check("资源包文件已生成",
          store.exists(pid, "resource", "items/new_sword.json"))

    lang = store.read_text(pid, "resource", "texts/zh_CN.lang")
    check("语言键已写入", "item.demo:new_sword.name=" in lang,
          [l for l in lang.splitlines() if "demo:new_sword" in l])

    # 重复创建应报错
    r = c.post(base + "/objects/create", json={
        "kind": "item", "namespace": "demo", "name": "new_sword"})
    check("重复创建被拒", r.status_code == 400, str(r.status_code))

    # 新对象进入索引
    idx = ws.load_index(pid)
    check("新对象已在索引中", "demo:new_sword" in (idx.get("objects") or {}),
          str(len(idx.get("objects") or {})))

    # entity 创建（含 groups/events 骨架）
    r = c.post(base + "/objects/create", json={
        "kind": "entity", "namespace": "demo", "name": "new_mob",
        "options": {"with_resource": True, "with_lang": False},
    }).get_json()
    check("创建 entity", r.get("ok"), str(r.get("error")))
    ed = store.read_json(pid, "behavior", "entities/new_mob.json")
    ent = ed["minecraft:entity"]
    check("entity 含 component_groups", isinstance(ent.get("component_groups"), dict))
    check("entity 含 events", isinstance(ent.get("events"), dict))
    check("客户端实体已生成",
          store.exists(pid, "resource", "entity/new_mob.entity.json"))

    ws.delete_project(pid)

    LINES.append("")
    LINES.append("失败 %d 项" % len(FAILS))
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    print("fails:", len(FAILS))


if __name__ == "__main__":
    main()