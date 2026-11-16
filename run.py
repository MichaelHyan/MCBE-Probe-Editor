#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动入口（工程根目录）。

    python run.py                  # 默认 127.0.0.1:5000
    python run.py --port 8080
    python run.py --debug
"""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "mcbe_probe_editor"))

from app import main

if __name__ == "__main__":
    main()