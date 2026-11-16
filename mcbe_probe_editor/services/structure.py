# -*- coding: utf-8 -*-
"""结构(.mcstructure)版本检查 / 降版本工具。

对应 plan.md 4.3：
  * 不解析结构内容(方块语义)，仅处理容器编码与版本
  * fv2 -> fv1: block_indices 由 List<IntArray> 转两层 List<List<Int>>
  * -1 是「结构空位」，放置时跳过、保留目标原方块；绝不能替换为 air 索引
  * 缺液体层补全 -1；已有液体层不丢弃
  * 幂等、备份、转后自检

算法移植自已验证的 Taoism_B/structures/downgrade_mcstructure.py。
"""

import os
import shutil
import struct
import time

from . import workspace as ws
from . import store

BACKUP_DIRNAME = "_fv2_backup"


# ---------------------------------------------------------------- NBT 读取


class _Reader(object):
    __slots__ = ("data", "pos")

    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, n):
        v = self.data[self.pos:self.pos + n]
        if len(v) != n:
            raise ValueError("unexpected EOF at offset %d" % self.pos)
        self.pos += n
        return v

    def u8(self):
        return self.take(1)[0]

    def i16(self):
        return struct.unpack("<h", self.take(2))[0]

    def i32(self):
        return struct.unpack("<i", self.take(4))[0]

    def i64(self):
        return struct.unpack("<q", self.take(8))[0]

    def f32(self):
        return struct.unpack("<f", self.take(4))[0]

    def f64(self):
        return struct.unpack("<d", self.take(8))[0]

    def string(self):
        n = self.i16()
        return self.take(n).decode("utf-8", "replace")


def _read_payload(r, t):
    if t == 1:
        return r.u8()
    if t == 2:
        return r.i16()
    if t == 3:
        return r.i32()
    if t == 4:
        return r.i64()
    if t == 5:
        return r.f32()
    if t == 6:
        return r.f64()
    if t == 7:
        return r.take(r.i32())
    if t == 8:
        return r.string()
    if t == 9:
        et = r.u8()
        n = r.i32()
        return ("list", et, [_read_payload(r, et) for _ in range(n)])
    if t == 10:
        items = []
        while True:
            tt = r.u8()
            if tt == 0:
                break
            name = r.string()
            items.append((name, tt, _read_payload(r, tt)))
        return ("compound", items)
    if t == 11:
        n = r.i32()
        return ("int_array", [r.i32() for _ in range(n)])
    if t == 12:
        n = r.i32()
        return ("long_array", [r.i64() for _ in range(n)])
    raise ValueError("unknown tag type %d" % t)


def parse_nbt(raw):
    r = _Reader(raw)
    t = r.u8()
    if t != 10:
        raise ValueError("root tag is not TAG_Compound (got %d)" % t)
    r.string()
    return _read_payload(r, 10)


# ---------------------------------------------------------------- NBT 写出


def _write_string(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _write_payload(t, v):
    if t == 1:
        return struct.pack("<b", v - 256 if v > 127 else v)
    if t == 2:
        return struct.pack("<h", v)
    if t == 3:
        return struct.pack("<i", v)
    if t == 4:
        return struct.pack("<q", v)
    if t == 5:
        return struct.pack("<f", v)
    if t == 6:
        return struct.pack("<d", v)
    if t == 7:
        return struct.pack("<i", len(v)) + v
    if t == 8:
        return _write_string(v)
    if t == 9:
        et, items = v[1], v[2]
        out = [bytes([et]), struct.pack("<i", len(items))]
        for item in items:
            out.append(_write_payload(et, item))
        return b"".join(out)
    if t == 10:
        out = []
        for name, tt, vv in v[1]:
            out.append(bytes([tt]))
            out.append(_write_string(name))
            out.append(_write_payload(tt, vv))
        out.append(b"\x00")
        return b"".join(out)
    if t == 11:
        out = [struct.pack("<i", len(v[1]))]
        for x in v[1]:
            out.append(struct.pack("<i", x))
        return b"".join(out)
    if t == 12:
        out = [struct.pack("<i", len(v[1]))]
        for x in v[1]:
            out.append(struct.pack("<q", x))
        return b"".join(out)
    raise ValueError("cannot write tag type %d" % t)


def serialize_nbt(root):
    return b"\x0a" + _write_string("") + _write_payload(10, root)


# ---------------------------------------------------------------- 字段工具


def _get(compound, key):
    for name, t, v in compound[1]:
        if name == key:
            return t, v
    return None


def _set(compound, key, t, v):
    for i, (name, _, _) in enumerate(compound[1]):
        if name == key:
            compound[1][i] = (name, t, v)
            return True
    compound[1].append((key, t, v))
    return False


def _layers(structure):
    t, bi = _get(structure, "block_indices")
    layers = []
    for item in bi[2]:
        kind = item[0]
        if kind == "int_array":
            layers.append(list(item[1]))
        elif kind == "list":
            layers.append(list(item[2]))
        else:
            raise ValueError("unexpected block_indices element: %r" % (kind,))
    return layers


def _palette_names(structure):
    _, pal = _get(structure, "palette")
    _, default = _get(pal, "default")
    _, bp = _get(default, "block_palette")
    names = []
    for entry in bp[2]:
        _, nm = _get(entry, "name")
        names.append(nm)
    return names


# ---------------------------------------------------------------- 检查


def inspect_raw(raw):
    """只读取元信息，不做转换。"""
    info = {"format_version": None, "size": None, "cells": None,
            "layers": None, "palette": None, "void_cells": None,
            "error": None}
    try:
        root = parse_nbt(raw)
    except Exception as exc:
        info["error"] = str(exc)
        return info

    f = _get(root, "format_version")
    info["format_version"] = f[1] if f else None

    size = _get(root, "size")
    if size:
        sx, sy, sz = size[1][2]
        info["size"] = [sx, sy, sz]
        info["cells"] = sx * sy * sz

    if info["format_version"] in (1, 2):
        st = _get(root, "structure")
        if st:
            try:
                layers = _layers(st[1])
                info["layers"] = len(layers)
                info["palette"] = len(_palette_names(st[1]))
                if layers:
                    info["void_cells"] = sum(1 for x in layers[0] if x == -1)
            except Exception as exc:
                info["error"] = str(exc)
    return info


def check_v1(root):
    """校验 fv1 结构是否合法。返回 (ok, msg)。"""
    f = _get(root, "format_version")
    if f is None or f[1] != 1:
        return False, "format_version != 1"

    size = _get(root, "size")
    sx, sy, sz = size[1][2]
    cells = sx * sy * sz

    st = _get(root, "structure")
    t, bi = _get(st[1], "block_indices")
    if bi[1] != 9:
        return False, "block_indices elem_type=%d (expect 9)" % bi[1]
    if len(bi[2]) != 2:
        return False, "layers=%d (expect 2)" % len(bi[2])

    l0 = list(bi[2][0][2])
    l1 = list(bi[2][1][2])
    if len(l0) != cells or len(l1) != cells:
        return False, "layer length %d/%d != cells %d" % (len(l0), len(l1), cells)

    names = _palette_names(st[1])
    n = len(names)
    for x in l0:
        if x != -1 and not (0 <= x < n):
            return False, "layer0 index %d out of palette range %d" % (x, n)
    for x in l1:
        if x != -1 and not (0 <= x < n):
            return False, "layer1 index %d out of palette range %d" % (x, n)
    return True, "ok"


def downgrade_root(root):
    """把 fv2 的 root 就地改为 fv1。返回描述 dict。"""
    size = _get(root, "size")
    sx, sy, sz = size[1][2]
    cells = sx * sy * sz

    st = _get(root, "structure")
    layers = _layers(st[1])
    if not layers:
        raise ValueError("block_indices is empty")
    for l in layers:
        if len(l) != cells:
            raise ValueError("layer length %d != cells %d" % (len(l), cells))

    names = _palette_names(st[1])

    layer0 = list(layers[0])
    if len(layers) >= 2:
        layer1 = list(layers[1])
        liquid_kept = sum(1 for x in layer1 if x != -1)
    else:
        layer1 = [-1] * cells
        liquid_kept = 0

    _set(st[1], "block_indices", 9,
         ("list", 9, [("list", 3, layer0), ("list", 3, layer1)]))
    _set(root, "format_version", 3, 1)

    return {
        "cells": cells,
        "palette": len(names),
        "kept_void": sum(1 for x in layer0 if x == -1),
        "liquid_kept": liquid_kept,
        "layers_before": len(layers),
    }


# ---------------------------------------------------------------- 工作区集成


def _backup_dir(project_id, pack, rel):
    """备份目录放在结构文件所在目录下的 _fv2_backup/。"""
    full = store.resolve_file(project_id, pack, rel)
    return os.path.join(os.path.dirname(full), BACKUP_DIRNAME)


def inspect(project_id, pack, rel):
    raw = store.read_bytes(project_id, pack, rel)
    info = inspect_raw(raw)
    info["pack"] = pack
    info["path"] = rel.replace("\\", "/")
    info["bytes"] = len(raw)
    return info


def downgrade(project_id, pack, rel, backup=True):
    """执行降版本。已是 fv1 则跳过(幂等)。"""
    raw = store.read_bytes(project_id, pack, rel)
    root = parse_nbt(raw)

    f = _get(root, "format_version")
    fv = f[1] if f else None
    if fv != 2:
        return {"ok": True, "skipped": True, "reason": "format_version=%s" % fv,
                "format_version": fv}

    if backup:
        bdir = _backup_dir(project_id, pack, rel)
        os.makedirs(bdir, exist_ok=True)
        bak = os.path.join(bdir, os.path.basename(rel) +
                           "." + time.strftime("%Y%m%d_%H%M%S"))
        with open(bak, "wb") as fh:
            fh.write(raw)

    info = downgrade_root(root)
    out = serialize_nbt(root)

    # 转后自检
    again = parse_nbt(out)
    ok, msg = check_v1(again)
    if not ok:
        raise ValueError("转换后自检失败: %s" % msg)

    store.write_bytes(project_id, pack, rel, out)
    store.record_change(project_id, pack, rel, "modify")
    info.update({"ok": True, "skipped": False, "check": msg})
    return info


def list_structures(index):
    """从索引中列出结构文件及其版本。"""
    out = []
    for item in (index or {}).get("structures") or []:
        out.append({
            "pack": item.get("pack"),
            "path": item.get("path"),
            "size": item.get("size"),
        })
    return out
