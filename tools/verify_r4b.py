# -*- coding: utf-8 -*-
"""验证：component_groups / events scope 编辑 + 示例下拉 API。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws
from services import pipeline
from services import database as db
from services import store

BP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_B"
RP = r"D:/git/MCBE-add-on-Taoism-Craft/Taoism_R"
OUT = os.path.join(ROOT, "_r4b.txt")

FAILS = []
LINES = []


def check(name, cond, detail=""):
    LINES.append("[%s] %s  %s" % ("OK " if cond else "ERR", name, detail))
    if not cond:
        FAILS.append(name)


def main():
    pid = ws.create_project("verify_r4b", BP, RP, copy=True)
    pipeline.run_probe(pid)
    c = create_app().test_client()
    base = "/api/project/%s" % pid

    # 找一个含 component_groups 的实体
    idx = ws.load_index(pid)
    target = None
    for ident, o in (idx.get("objects") or {}).items():
        if o.get("kind") != "entity":
            continue
        prim = o.get("primary") or {}
        if prim.get("pack") != "behavior" or not prim.get("path"):
            continue
        try:
            d = store.read_json(pid, prim["pack"], prim["path"])
        except Exception:
            continue
        body = d.get("minecraft:entity") or {}
        if body.get("component_groups") and body.get("events"):
            target = (ident, prim, body)
            break

    check("找到含 groups+events 的实体", target is not None,
          target[0] if target else "none")

    if target:
        ident, prim, body = target
        groups = list((body.get("component_groups") or {}).keys())
        events = list((body.get("events") or {}).keys())
        LINES.append("  groups=%d events=%d" % (len(groups), len(events)))

        # 1. 编辑数据含 scopes
        r = c.get(base + "/edit/" + ident).get_json()
        f0 = (r.get("files") or [{}])[0]
        sc = f0.get("scopes") or {}
        check("载荷含 scopes.components", isinstance(sc.get("components"), dict))
        check("载荷含 scopes.component_groups",
              isinstance(sc.get("component_groups"), dict),
              "n=%d" % len(sc.get("component_groups") or {}))
        check("载荷含 scopes.events",
              isinstance(sc.get("events"), dict),
              "n=%d" % len(sc.get("events") or {}))

        pack, rel = prim["pack"], prim["path"]

        # 2. 往组件组加一条
        g0 = groups[0]
        r = c.post(base + "/edit/%s/entry" % ident, json={
            "pack": pack, "path": rel,
            "scope": "component_groups." + g0,
            "name": "minecraft:test_probe", "value": {"v": 1},
        }).get_json()
        check("组内新增条目", r.get("ok"), str(r))

        d = store.read_json(pid, pack, rel)
        got = ((d.get("minecraft:entity") or {}).get("component_groups") or {}) \
            .get(g0, {}).get("components", {}).get("minecraft:test_probe")
        check("组内条目落盘", got == {"v": 1}, str(got))

        # 3. 往 events 加一条
        r = c.post(base + "/edit/%s/entry" % ident, json={
            "pack": pack, "path": rel, "scope": "events",
            "name": "test_event", "value": {"add": {"component_groups": []}},
        }).get_json()
        check("事件新增", r.get("ok"), str(r))
        d = store.read_json(pid, pack, rel)
        ev = ((d.get("minecraft:entity") or {}).get("events") or {}).get("test_event")
        check("事件落盘", isinstance(ev, dict), str(ev))

        # 4. 删除刚加的
        r = c.post(base + "/edit/%s/entry" % ident, json={
            "pack": pack, "path": rel, "scope": "events",
            "name": "test_event", "op": "delete",
        }).get_json()
        check("事件删除", r.get("ok"), str(r))
        d = store.read_json(pid, pack, rel)
        ev2 = ((d.get("minecraft:entity") or {}).get("events") or {}).get("test_event")
        check("事件已删除", ev2 is None, str(ev2))

        # 5. 整组替换
        r = c.post(base + "/edit/%s/entry" % ident, json={
            "pack": pack, "path": rel, "scope": "component_groups",
            "name": "test_group", "value": {"components": {"minecraft:health": {"value": 1}}},
            "op": "set_group",
        }).get_json()
        check("新增整组", r.get("ok"), str(r))
        d = store.read_json(pid, pack, rel)
        tg = ((d.get("minecraft:entity") or {}).get("component_groups") or {}).get("test_group")
        check("整组落盘", isinstance(tg, dict), str(tg))

    # 6. 示例 API
    ex = c.get(base + "/db/examples?kind=item&fv=1.21.50&component=minecraft:max_stack_size").get_json()
    check("示例 API", ex.get("ok"), "n=%d" % len(ex.get("examples") or []))

    ws.delete_project(pid)
    # 清本地库测试残留
    for fv in ("1.21.50",):
        p = db.official_path("item", fv)
        if os.path.isfile(p):
            os.remove(p)

    LINES.append("")
    LINES.append("失败 %d 项" % len(FAILS))
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    print("fails:", len(FAILS))


if __name__ == "__main__":
    main()