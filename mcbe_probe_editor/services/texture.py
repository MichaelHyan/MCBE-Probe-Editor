# -*- coding: utf-8 -*-
"""贴图处理（像素画 / alpha 规则）。

对应 plan.md 4.1:
  * 读取支持 PNG，保留 alpha 通道
  * 不允许新增半透明像素；原本存在的半透明像素可原样写回
  * 颜色格式 RGB，保存为 PNG(RGBA)

alpha 规则:
    new_alpha in 1..254 且 old_alpha not in 1..254  ->  强制 255（禁止新增半透明）
    其余保持原样（原半透明像素允许继续写回）
"""

import base64
import io
import os

from . import store

try:
    from PIL import Image
except ImportError:      # pragma: no cover
    Image = None

STANDARD_TEXTURE_DIRS = {
    "item": "textures/items",
    "block": "textures/blocks",
    "entity": "textures/entity",
    "attachable": "textures/attachable",
}


def pillow_ok():
    return Image is not None


def _open(data):
    return Image.open(io.BytesIO(data))


def data_url(raw, mime="image/png"):
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def count_semi(rgba):
    alpha = rgba.getchannel("A")
    hist = alpha.histogram()
    return sum(hist[1:255])


# ---------------------------------------------------------------- 读取


def load_info(project_id, pack, rel):
    """读取贴图信息: 尺寸 / alpha 概况 / data_url。"""
    raw = store.read_bytes(project_id, pack, rel)
    info = {
        "pack": pack,
        "path": rel.replace("\\", "/"),
        "size": len(raw),
        "data_url": data_url(raw),
        "width": None,
        "height": None,
        "mode": None,
        "semi_transparent": 0,
        "error": None,
    }
    if Image is None:
        info["error"] = "Pillow 未安装，无法解析像素"
        return info
    try:
        im = _open(raw)
        rgba = im.convert("RGBA")
        info["width"] = rgba.width
        info["height"] = rgba.height
        info["mode"] = im.mode
        info["semi_transparent"] = count_semi(rgba)
    except Exception as exc:
        info["error"] = str(exc)
    return info


def suggest_path(kind, name):
    directory = STANDARD_TEXTURE_DIRS.get(kind, "textures/items")
    return "%s/%s.png" % (directory, name)


# ---------------------------------------------------------------- 保存


def save(project_id, pack, rel, png_b64, enforce=True):
    """保存贴图。png_b64 可为 dataURL 或纯 base64。

    返回 {'ok':True, 'fixed_pixels':n, 'width':w, 'height':h}
    """
    if Image is None:
        raise RuntimeError("Pillow 未安装")

    if not png_b64:
        raise ValueError("缺少图像数据")
    if "," in png_b64:
        png_b64 = png_b64.split(",", 1)[1]
    raw = base64.b64decode(png_b64)

    new_im = _open(raw).convert("RGBA")
    fixed = 0

    old_im = None
    if enforce and store.exists(project_id, pack, rel):
        try:
            old_im = _open(store.read_bytes(project_id, pack, rel)).convert("RGBA")
        except Exception:
            old_im = None

    px_new = new_im.load()
    w, h = new_im.size
    same_size = old_im is not None and old_im.size == (w, h)
    px_old = old_im.load() if same_size else None

    for y in range(h):
        for x in range(w):
            r, g, b, a = px_new[x, y]
            if 0 < a < 255:
                if px_old is not None and 0 < px_old[x, y][3] < 255:
                    continue          # 原本就是半透明，允许原样写回
                px_new[x, y] = (r, g, b, 255)
                fixed += 1

    existed = store.exists(project_id, pack, rel)

    buf = io.BytesIO()
    new_im.save(buf, format="PNG")
    store.write_bytes(project_id, pack, rel, buf.getvalue())

    return {"ok": True, "width": w, "height": h,
            "fixed_pixels": fixed, "created": not existed}


def create_blank(project_id, pack, rel, width=16, height=16):
    """创建空白(全透明)贴图。"""
    if Image is None:
        raise RuntimeError("Pillow 未安装")
    im = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    store.write_bytes(project_id, pack, rel, buf.getvalue())
    return {"ok": True, "width": im.width, "height": im.height, "path": rel}


# ---------------------------------------------------------------- 模型命名空间


def match_pack_for(project_id, rel, prefer="resource"):
    """判断某相对路径属于哪个包。"""
    for pack in (prefer, "resource", "behavior"):
        if pack not in ("behavior", "resource"):
            continue
        try:
            if store.exists(project_id, pack, rel):
                return pack
        except Exception:
            continue
    return None


def rewrite_geometry_ns(data, ns, name):
    """把 .geo.json 里的几何标识改写为 geometry.<ns>.<name>。

    兼容两种格式:
        1.16+  minecraft:geometry = [ {description:{identifier:...}} ]
        1.12   { "geometry.xxx": {...} }
    返回 (new_data, changed_count)
    """
    target = "geometry.%s.%s" % (ns, name)
    changed = 0

    if not isinstance(data, dict):
        return data, 0

    geos = data.get("minecraft:geometry")
    if isinstance(geos, list):
        for item in geos:
            if not isinstance(item, dict):
                continue
            desc = item.get("description")
            if isinstance(desc, dict):
                old = desc.get("identifier")
                if old != target:
                    desc["identifier"] = target
                    changed += 1
        return data, changed

    # 1.12 形态: 键名即几何标识
    for key in list(data.keys()):
        if not key.startswith("geometry."):
            continue
        if key != target:
            data[target] = data.pop(key)
            changed += 1
    return data, changed


def associate_model(project_id, pack, rel, ident):
    """把模型文件与对象关联，并改写命名空间。"""
    if not ident or ":" not in ident:
        raise ValueError("对象标识需为 namespace:name")
    ns, name = ident.split(":", 1)

    low = rel.lower()
    if not low.endswith(".json"):
        return {"ok": False, "reason": "仅支持 .geo.json 改写（bbmodel 请在 Blockbench 内处理）",
                "identifier": ident}

    data = store.read_json(project_id, pack, rel)
    data, changed = rewrite_geometry_ns(data, ns, name)
    if changed:
        store.write_json(project_id, pack, rel, data)
        store.record_change(project_id, pack, rel, "modify")
    return {"ok": True, "changed": changed, "target": "geometry.%s.%s" % (ns, name)}