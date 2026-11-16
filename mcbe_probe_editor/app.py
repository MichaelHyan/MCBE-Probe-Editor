#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCBE Probe Editor - Flask 入口。

启动:
    python app.py [--host 127.0.0.1] [--port 5000] [--debug]

路由划分(对应 plan.md 工程结构):
    project  导入 / 工作区
    index    索引 / 对象浏览
    editor   组件编辑
    browser  文件浏览
    asset    资产(贴图/模型)
    export   导出
"""

import argparse
import os
import sys

from flask import Flask, jsonify, redirect, url_for

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from routes import project as bp_project
from routes import index as bp_index
from routes import editor as bp_editor
from routes import browser as bp_browser
from routes import asset as bp_asset
from routes import export as bp_export
from routes import structure as bp_structure
from routes import db as bp_db
from routes import unbound as bp_unbound
from routes import i18n as bp_i18n
from routes import manifest as bp_manifest
from routes import objects as bp_objects
from services import i18n as i18n


def create_app(debug=False):
    app = Flask(
        __name__,
        template_folder=os.path.join(_HERE, "templates"),
        static_folder=os.path.join(_HERE, "static"),
    )
    app.config["JSON_AS_ASCII"] = False
    app.config["DEBUG"] = bool(debug)
    # 禁用静态文件长缓存，避免浏览器用旧 JS（本地工具无带宽顾虑）
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.secret_key = "mcbe-probe-editor-local-dev"
    app.json.ensure_ascii = False

    app.register_blueprint(bp_project.bp)
    app.register_blueprint(bp_index.bp)
    app.register_blueprint(bp_editor.bp)
    app.register_blueprint(bp_browser.bp)
    app.register_blueprint(bp_asset.bp)
    app.register_blueprint(bp_export.bp)
    app.register_blueprint(bp_structure.bp)
    app.register_blueprint(bp_db.bp)
    app.register_blueprint(bp_unbound.bp)
    app.register_blueprint(bp_i18n.bp)
    app.register_blueprint(bp_manifest.bp)
    app.register_blueprint(bp_objects.bp)

    @app.errorhandler(Exception)
    def on_error(exc):
        from werkzeug.exceptions import HTTPException
        if isinstance(exc, HTTPException):
            return exc
        app.logger.exception("unhandled error: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500

    @app.context_processor
    def inject_static_ver():
        """给模板一个静态资源版本号（取 static 下最大 mtime）。"""
        base = os.path.join(_HERE, "static")
        newest = 0
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                try:
                    newest = max(newest, int(os.path.getmtime(
                        os.path.join(dirpath, fn))))
                except OSError:
                    pass
        from flask import session
        lang = i18n.normalize(session.get("ui_lang"))
        return {
            "static_ver": newest,
            "ui_lang": lang,
            "ui_langs": i18n.langs_meta(),
            "i18n_dict": i18n.get(lang),
        }

    @app.route("/")
    def root():
        return redirect(url_for("project.projects_page"))

    return app


def main():
    ap = argparse.ArgumentParser(description="MCBE Probe Editor")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    app = create_app(debug=args.debug)
    print("MCBE Probe Editor  ->  http://%s:%d/" % (args.host, args.port))
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

