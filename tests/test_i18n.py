# -*- coding: utf-8 -*-
"""i18n 与注册模块的一致性测试。

守护点
------
1. 三语键集合完全一致（漏译会在界面显示 ⟪key⟫，这里提前拦住）；
2. 所有文案的占位符在三种语言下一致（避免 .format 时 KeyError）；
3. 方法说明页三语都非空且含核心公式；
4. 家族注册码机制可生成 / 校验 / 拒绝伪造。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import i18n as T
import registration as R


def test_three_languages_have_same_keys():
    zh = set(T.TABLE["zh"])
    for lang in ("en", "ja"):
        other = set(T.TABLE[lang])
        assert other == zh, f"{lang} 缺少 {sorted(zh - other)}，多余 {sorted(other - zh)}"


def test_placeholders_match_across_languages():
    pat = re.compile(r"\{(\w+)\}")
    for key, zh_text in T.TABLE["zh"].items():
        want = set(pat.findall(zh_text))
        if not want:
            continue
        for lang in ("en", "ja"):
            got = set(pat.findall(T.TABLE[lang][key]))
            assert got == want, f"{lang}/{key} 占位符不一致：{got} != {want}"


def test_no_untranslated_marker():
    for lang in T.LANGS:
        T.set_language(lang)
        for key in T.TABLE["zh"]:
            if key == "method.html":
                continue
            assert "⟪" not in T.tr(key), f"{lang}/{key} 未被翻译"
    T.set_language("zh")


def test_method_pages_present():
    for lang in T.LANGS:
        T.set_language(lang)
        html = T.method_html()
        assert len(html) > 1500, f"{lang} 方法页过短"
        for token in ("0.3440", "0.3354", "0.89", "1.84", "72"):
            assert token in html, f"{lang} 方法页缺少 {token}"
    T.set_language("zh")


def test_hint_pages_present():
    """小提示图标里的一页说明：三语齐备，含关键常数，且不出现晶胞参数写法。"""
    for lang in T.LANGS:
        T.set_language(lang)
        html = T.hint_html()
        assert len(html) > 800, f"{lang} 提示页过短"
        for token in ("0.3440", "0.3354", "0.89", "1.84", "72–82", "Caglioti"):
            assert token in html, f"{lang} 提示页缺少 {token}"
        assert "c0/2" not in html
    T.set_language("zh")


def test_format_works():
    T.set_language("zh")
    assert "v1.0.0" in T.tr("about.version", version="1.0.0", variant="内部评估版本")
    assert "3.14" in T.tr("status.calc_done", g="98.7", lc="3.14")


def test_registration_roundtrip():
    unit = "江西威托新材料有限公司"
    code = R.generate_code(unit)
    assert code.startswith("PXRD1-")
    assert R.verify_code(code) == unit
    # 容错：小写、去连字符、带空格
    assert R.verify_code(code.replace("-", "").lower()) == unit
    assert R.verify_code("  " + code + "  ") == unit
    # 伪造：改动 body 中部一个字符即失效（尾部可能落在 Base32 填充位，不敏感）
    idx = len("PXRD1-") + 6
    tampered = code[:idx] + ("A" if code[idx] != "A" else "B") + code[idx + 1:]
    assert R.verify_code(tampered) is None
    assert R.verify_code("PXRD1-XXXX-XXXX") is None
