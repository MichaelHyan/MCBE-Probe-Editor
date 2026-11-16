#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动入口（工程根目录）。

    python run.py                  # 默认 127.0.0.1:5000
    python run.py --port 8080
    python run.py --debug
    python run.py --no-browser     # 启动后不自动打开浏览器
"""

import os
import sys
import threading
import time
import webbrowser

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "mcbe_probe_editor"))

from app import main


def _guess_port(argv, default=5000):
    """从命令行参数里粗略解析端口（支持 --port 8080 / --port=8080）。"""
    for i, arg in enumerate(argv):
        if arg == "--port" and i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                pass
        elif arg.startswith("--port="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                pass
    return default


def _open_browser_later(url, delay=1.2):
    """后台线程延迟打开浏览器，失败静默忽略。"""
    def _worker():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_worker, name="open-browser", daemon=True).start()


if __name__ == "__main__":
    no_browser = "--no-browser" in sys.argv[1:]
    if no_browser:  # app.py 的 argparse 不认识它，先摘掉
        sys.argv.remove("--no-browser")

    # --debug 下 Werkzeug 重载器会再执行一遍本脚本，
    # 只在真正提供服务的子进程打开，避免冒出两个标签页。
    skip = ("--debug" in sys.argv[1:]
            and os.environ.get("WERKZEUG_RUN_MAIN") != "true")
    if not no_browser and not skip:
        _open_browser_later("http://127.0.0.1:%d/" % _guess_port(sys.argv[1:]))

    main()