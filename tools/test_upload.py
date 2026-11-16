# -*- coding: utf-8 -*-
"""上传接口端到端自检：构造最小 mcaddon -> POST /api/projects/upload。"""
import io
import json
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcbe_probe_editor"))

from app import create_app
from services import workspace as ws

TMP = os.path.join(ROOT, "_tmp_upload")
ADDON = os.path.join(TMP, "test.mcaddon")

BP_MANIFEST = {
    "format_version": 1,
    "header": {"name": "Test BP", "uuid": "11111111-1111-1111-1111-111111111111",
               "version": [1, 0, 0], "min_engine_version": [1, 20, 0]},
    "modules": [{"type": "data", "uuid": "11111111-1111-1111-1111-111111111112",
                 "version": [1, 0, 0]}],
}
RP_MANIFEST = {
    "format_version": 1,
    "header": {"name": "Test RP", "uuid": "22222222-2222-2222-2222-222222222222",
               "version": [1, 0, 0]},
    "modules": [{"type": "resources", "uuid": "22222222-2222-2222-2222-222222222223",
                 "version": [1, 0, 0]}],
}
ITEM = {
    "format_version": "1.21.50",
    "minecraft:item": {
        "description": {"identifier": "demo:test_item",
                        "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:max_stack_size": 64,
            "minecraft:icon": {"textures": {"default": "test_item"}},
        },
    },
}
ITEM_TEXTURE = {
    "resource_pack_name": "test",
    "texture_name": "atlas.items",
    "texture_data": {"test_item": {"textures": "textures/items/test_item"}},
}
LANG = "item.demo:test_item.name=测试物品\n"


def build():
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)

    png = _tiny_png()
    with zipfile.ZipFile(ADDON, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("BP/manifest.json", json.dumps(BP_MANIFEST, ensure_ascii=False))
        zf.writestr("BP/items/test_item.json", json.dumps(ITEM, ensure_ascii=False))
        zf.writestr("RP/manifest.json", json.dumps(RP_MANIFEST, ensure_ascii=False))
        zf.writestr("RP/textures/item_texture.json",
                    json.dumps(ITEM_TEXTURE, ensure_ascii=False))
        zf.writestr("RP/texts/zh_CN.lang", LANG)
        zf.writestr("RP/textures/items/test_item.png", png)
    print("built:", ADDON, os.path.getsize(ADDON), "bytes")


def _tiny_png():
    """生成 2x2 红色 PNG（不依赖 Pillow）。"""
    import struct
    import zlib

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)

    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    raw = b""
    for _ in range(2):
        raw += b"\x00" + b"\xff\x00\x00" * 2
    idat = zlib.compress(raw)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def main():
    build()
    app = create_app()
    c = app.test_client()

    with open(ADDON, "rb") as f:
        data = {"file": (io.BytesIO(f.read()), "test.mcaddon"),
                "name": "upload_test"}
        r = c.post("/api/projects/upload", data=data,
                   content_type="multipart/form-data")

    print("status:", r.status_code)
    j = r.get_json() or {}
    print("ok    :", j.get("ok"))
    print("error :", j.get("error"))
    print("packs :", j.get("packs"))
    pid = j.get("project_id")
    if pid:
        idx = c.get("/api/project/%s/index" % pid).get_json()
        print("stats :", (idx.get("stats") or {}).get("objects"),
              (idx.get("stats") or {}).get("kinds"))
        objs = c.get("/api/project/%s/objects" % pid).get_json()
        for o in objs.get("objects", []):
            print("  object:", o["identifier"], o["kind"],
                  "refs=" + str(o["ref_count"]))
        detail = c.get("/api/project/%s/object/demo%%3Atest_item" % pid)
        print("detail status:", detail.status_code)
        # 清理
        ws.delete_project(pid)

    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if j.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())