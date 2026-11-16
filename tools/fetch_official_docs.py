# -*- coding: utf-8 -*-
"""从 bedrock.dev 抓取指定版本 × kind 的官方文档 HTML 到本地缓存。

已实测可用的版本路径：
    1.12.0 -> 1.12.0.0/1.12.0.28
    1.16.0 -> 1.16.0.0/1.16.100.60
    1.21.0 -> 1.21.0.0/1.21.130.28
    1.26.0 -> 1.26.0.0/1.26.60.5
1.12.0 站点未提供 Item 文档页，故 item 仅 1.16+。
"""
import os
import json
import time
import urllib.request
import urllib.error

TOOLS = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(TOOLS, "_cache")
LOG = os.path.join(CACHE, "_log.txt")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

# format_version -> bedrock.dev 版本路径
VERSION_PATHS = {
    "1.12.0": "1.12.0.0/1.12.0.28",
    "1.16.0": "1.16.0.0/1.16.100.60",
    "1.21.0": "1.21.0.0/1.21.130.28",
    "1.26.0": "1.26.0.0/1.26.60.5",
}

# kind -> (页面名, 支持的版本)
KIND_PAGES = {
    "entity": ("Entities", ["1.12.0", "1.16.0", "1.21.0", "1.26.0"]),
    "item": ("Item", ["1.16.0", "1.21.0", "1.26.0"]),
    "block": ("Blocks", ["1.12.0", "1.16.0", "1.21.0", "1.26.0"]),
}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main():
    os.makedirs(CACHE, exist_ok=True)
    open(LOG, "w", encoding="utf-8").close()
    report = []
    for kind, (page, versions) in KIND_PAGES.items():
        for fv in versions:
            out = os.path.join(CACHE, "%s_%s.html" % (kind, fv))
            if os.path.isfile(out) and os.path.getsize(out) > 1024:
                log("cached %s %s %d" % (kind, fv, os.path.getsize(out)))
                report.append({"kind": kind, "fv": fv, "status": "cached", "size": os.path.getsize(out)})
                continue
            url = "https://bedrock.dev/docs/%s/%s" % (VERSION_PATHS[fv], page)
            try:
                data = fetch(url)
                with open(out, "wb") as f:
                    f.write(data)
                log("ok %s %s %d" % (kind, fv, len(data)))
                report.append({"kind": kind, "fv": fv, "status": "ok", "size": len(data)})
            except urllib.error.HTTPError as exc:
                log("ERR %s %s HTTP %s" % (kind, fv, exc.code))
                report.append({"kind": kind, "fv": fv, "status": "HTTP %s" % exc.code, "size": 0})
            except Exception as exc:
                log("ERR %s %s %s" % (kind, fv, exc))
                report.append({"kind": kind, "fv": fv, "status": "ERR", "size": 0})
            time.sleep(0.5)

    with open(os.path.join(CACHE, "_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    log("done")


if __name__ == "__main__":
    main()