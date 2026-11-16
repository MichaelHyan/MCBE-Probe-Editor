# -*- coding: utf-8 -*-
"""界面语言路由。

API:
    GET  /api/i18n              当前语言字典（含可选 ?lang=）
    POST /api/ui-lang           切换界面语言（写入 session）
"""

from flask import Blueprint, jsonify, request, session

from services import i18n as I

bp = Blueprint("i18n", __name__)


@bp.route("/api/i18n")
def api_i18n():
    lang = I.normalize(request.args.get("lang") or session.get("ui_lang"))
    return jsonify({
        "ok": True,
        "lang": lang,
        "langs": I.langs_meta(),
        "dict": I.get(lang),
    })


@bp.route("/api/ui-lang", methods=["POST"])
def api_set_lang():
    body = request.get_json(silent=True) or {}
    lang = I.normalize(body.get("lang"))
    session["ui_lang"] = lang
    return jsonify({"ok": True, "lang": lang})