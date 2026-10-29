# -*- coding: utf-8 -*-
"""GUI 离屏冒烟测试（不依赖人工点击，可直接在 CI / 沙箱里跑）。

用法：
    python tools/smoke_gui.py            # 功能自检，输出 PASS/FAIL
    python tools/smoke_gui.py --shot 0   # 输出指定 tab 的窗口截图（base64 到 stdout）

截图走 base64 到 stdout，是为了在"Python 进程禁止写文件"的受控环境里也能
用 ``python ... --shot 0 | base64 -d > shot.png`` 落盘。

自检覆盖：
  1. 主窗口、四个页签、菜单、状态栏齐备；
  2. 波长 → Si(111) 标准 2θ 自动联动；
  3. 文档算例（Si 28.4541 / C(002) 26.5584）能算出 d002 0.33551、g≈98.7%；
  4. La (110) 路径能给出 La；缺 La 时给 0 且不崩；
  5. 合成谱导入 + 自动寻峰（内存 Pattern 路径）；
  6. 三语热切换后界面上不残留 ⟪key⟫；
  7. 内部评估版状态栏文案正确。
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("POLYXRD_REG_NO_PROMPT", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from PySide6.QtCore import QBuffer, QIODevice, Qt  # noqa: E402
from PySide6.QtWidgets import (QApplication, QLabel, QMessageBox,  # noqa: E402
                               QPushButton, QSizeGrip, QTextBrowser, QWidget)

import graphite_app as A  # noqa: E402
import graphite_engine as E  # noqa: E402
import i18n as T  # noqa: E402
import registration as R  # noqa: E402

# 离屏无人值守：把所有模态框改成"记录不阻塞"，否则任何提示都会挂住进程
_dialogs: list[str] = []


def _no_modal(kind):
    def _fn(parent=None, title="", text="", *a, **k):
        _dialogs.append(f"{kind}:{text}")
        print(f"  [dlg/{kind}] {text}")
        return QMessageBox.Ok
    return staticmethod(_fn)


QMessageBox.information = _no_modal("info")
QMessageBox.warning = _no_modal("warn")
QMessageBox.critical = _no_modal("error")
QMessageBox.aboutQt = _no_modal("qt")

fails: list[str] = []


def check(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok   {msg}")
    else:
        fails.append(msg)
        print(f"  FAIL {msg}")


def _pv(x, amp, cen, fwhm, eta=0.5):
    u = (x - cen) / fwhm
    return amp * (eta / (1 + 4 * u * u) + (1 - eta) * np.exp(-4 * np.log(2) * u * u))


def synth_pattern() -> E.Pattern:
    """合成一条石墨 + Si 内标谱：C(002)、Si(111)、C(100)、C(110)、Si(331)。"""
    x = np.arange(20.0, 120.0, 0.02)
    y = np.full_like(x, 60.0) + 0.02 * (x - 20)
    y += _pv(x, 4200, 26.555, 0.22)          # C(002)
    y += _pv(x, 2600, 28.442, 0.16)          # Si(111)
    y += _pv(x, 120, 42.372, 0.26)           # C(100)
    y += _pv(x, 70, 77.504, 0.34)            # C(110) —— 弱峰，仅约 1.7% 主峰
    y += _pv(x, 130, 76.380, 0.22)           # Si(331)
    rng = np.random.default_rng(11)
    return E.Pattern(x, y + rng.normal(0, 2.0, x.size), name="synthetic")


def synth_si_standard(lam: float = E.WAVELENGTHS["Cu Kα1"]) -> E.Pattern:
    """合成全角度 Si 标样谱（20–120°，含 111/220/311/400/331/422/511）。"""
    x = np.arange(20.0, 120.0, 0.02)
    y = np.full_like(x, 40.0)
    for row in E.si_reference_table(lam, two_theta_max=119.0):
        fw = E.caglioti_fwhm(row["two_theta"], 0.015, -0.002, 0.006)
        y = y + _pv(x, row["rel_intensity"] * 20.0, row["two_theta"], fw, 0.5)
    rng = np.random.default_rng(5)
    return E.Pattern(x, y + rng.normal(0, 0.8, x.size), name="Si-standard")


def walk_texts(root: QWidget) -> list[str]:
    out = []
    for w in root.findChildren(QWidget):
        if isinstance(w, (QLabel, QPushButton)):
            out.append(w.text())
    for act in root.findChildren(object):
        pass
    return out


def main() -> int:
    app = QApplication(sys.argv[:1])
    win = A.MainWindow()
    win.show()
    app.processEvents()

    print("[1] 窗口结构")
    check(win.tabs.count() == 4, "四个页签齐备")
    check(win.windowTitle().startswith("PolyXRD Graphite"), "窗口标题正确")
    check(win.menuBar().actions() != [], "菜单栏非空")
    check(win.statusBar() is not None, "状态栏存在")
    if A.BUILD_VARIANT == "internal":
        check(win._reg_label is not None and win._reg_label.text() == T.tr("status.internal_eval"),
              "内部评估版状态栏文案")

    print("[2] 波长联动")
    lam = win.sp_lambda.value()
    check(abs(lam - 0.15405929) < 1e-8, f"默认 Cu Kα1 = {lam:.8f} nm")
    check(abs(win.sp_si_ref.value() - 28.4419) < 0.01,
          f"Si(111) 标准 2θ 自动计算 = {win.sp_si_ref.value():.5f}°")

    print("[3] 文档算例（AP_XRD-001）")
    win.sp_tt002.setValue(26.5584)
    win.sp_fw002.setValue(0.24)
    win.sp_si.setValue(28.4541)
    win.chk_si.setChecked(True)
    win._si_ref_auto = False
    win.sp_si_ref.setValue(28.44135)      # 文档采用的标准值
    win.cb_la.setCurrentIndex(0)          # (110)
    win.sp_la.setValue(77.6200)
    win.sp_fw_la.setValue(0.34)
    win.cb_br_mode.setCurrentIndex(1)     # 直接给仪器 FWHM
    win.sp_inst_002.setValue(0.10)
    win.sp_inst_la.setValue(0.16)
    win._recalc()
    r = win.result
    check(r is not None, "计算返回结果")
    if r:
        check(abs(r.delta_two_theta + 0.01275) < 1e-6,
              f"Δ2θ = {r.delta_two_theta:+.5f}°")
        check(abs(r.two_theta_002_corr - 26.54565) < 1e-4,
              f"C(002) 校正 2θ = {r.two_theta_002_corr:.5f}°")
        check(abs(r.d002_nm - 0.33551) < 3e-5, f"d002 = {r.d002_nm:.5f} nm")
        check(98.4 < r.g_percent < 99.0, f"g = {r.g_percent:.2f}%")
        check(r.lc_nm > 20, f"Lc = {r.lc_nm:.2f} nm")
        check(r.la_nm > 20, f"La = {r.la_nm:.2f} nm")
        check(win.card_g.value.text().endswith("%"), "结果卡已刷新")

    print("[4] 缺 La 的降级")
    win.cb_la.setCurrentIndex(2)          # 不计算 La
    win._recalc()
    check(win.result is not None and win.result.la_nm == 0.0, "未选 La 时 la=0 不报错")
    check("—" in win.card_la.value.text(), "La 结果卡显示占位符")

    print("[5] 谱图导入 + 寻峰")
    pat = synth_pattern()
    win.pattern = pat
    win.canvas.set_pattern(pat)
    win._do_find_peaks()
    check(len(win.peaks) >= 4, f"识别到 {len(win.peaks)} 个峰")
    check(win.tbl_peaks.rowCount() == len(win.peaks), "峰表行数与峰数一致")
    centers = sorted(p.two_theta for p in win.peaks)
    for want in (26.555, 28.442, 42.372, 77.504):
        check(any(abs(c - want) < 0.06 for c in centers), f"找到 {want:.3f}° 附近的峰")

    print("[5b] 弱峰定向拟合")
    win.sp_direct.setValue(77.504)
    n_before = len(win.peaks)
    win._fit_at_direct()
    check(len(win.peaks) == n_before, "重复拟合不产生重复峰")
    la_fit = min(win.peaks, key=lambda p: abs(p.two_theta - 77.504))
    check(abs(la_fit.two_theta - 77.504) < 0.05, f"定点拟合峰位 = {la_fit.two_theta:.4f}°")
    check(abs(la_fit.fwhm - 0.34) < 0.03, f"定点拟合 FWHM = {la_fit.fwhm:.4f}°")

    print("[5c] 峰角度标注与删除峰")
    check(win.chk_labels.isChecked() and win.canvas.show_labels, "默认在图上标注峰角度")
    win.chk_labels.setChecked(False)
    win.canvas.repaint()
    flips = [p.two_theta for p in win.peaks]
    check(win.canvas.show_labels is False and len(flips) > 0, "关标注后画布仍正常绘制")
    win.chk_labels.setChecked(True)
    win.canvas.repaint()
    check(win.canvas.show_labels is True, "重新开启标注")
    n_before = len(win.peaks)
    win.tbl_peaks.selectRow(0)
    win._delete_peak()
    check(len(win.peaks) == n_before - 1, f"删除选中峰（{n_before} → {len(win.peaks)}）")
    check(win.tbl_peaks.rowCount() == len(win.peaks), "峰表与峰列表同步")
    win._do_find_peaks()          # 恢复一份完整峰表供后续步骤使用
    check(len(win.peaks) == n_before, "重新寻峰后可恢复峰表")

    print("[5d] 质心（centroid）")
    check(win.tbl_peaks.columnCount() == 8, "峰表含 Centroid 列")
    cen_txt = win.tbl_peaks.item(0, 7).text() if win.tbl_peaks.item(0, 7) else ""
    check(cen_txt not in ("", "—"), f"Centroid 数值已给出（{cen_txt}）")
    check(len(win.centroids) == len(win.peaks), "质心列表与峰表同长")
    strong_i = max(range(len(win.peaks)), key=lambda i: win.peaks[i].height)
    c_strong = win.centroids[strong_i]
    check(c_strong is not None and abs(c_strong.two_theta - win.peaks[strong_i].two_theta) < 0.05,
          f"最强峰 质心 {c_strong.two_theta:.4f}° ≈ 拟合 {win.peaks[strong_i].two_theta:.4f}°")
    win.chk_centroid.setChecked(False)
    check(win.tbl_peaks.isColumnHidden(7), "取消勾选后隐藏 Centroid 列")
    check(win.canvas.show_centroid is False, "取消勾选后图上不画质心标记")
    win.chk_centroid.setChecked(True)
    check(not win.tbl_peaks.isColumnHidden(7) and win.canvas.show_centroid, "重新勾选后恢复")
    # 质心 → C(002)
    win.tbl_peaks.selectRow(strong_i)
    win.sp_tt002.setValue(0.0)
    win.btn_cen002.click()
    check(abs(win.sp_tt002.value() - c_strong.two_theta) < 1e-3,
          f"质心→C(002) 填入 {win.sp_tt002.value():.4f}°")
    check(win.sp_fw002.value() > 0, "C(002) 的 FWHM 仍取该峰拟合值")
    # 质心 → Si(111)
    si_i = min(range(len(win.peaks)), key=lambda i: abs(win.peaks[i].two_theta - 28.442))
    win.tbl_peaks.selectRow(si_i)
    win.btn_censi.click()
    check(abs(win.sp_si.value() - win.centroids[si_i].two_theta) < 1e-3,
          f"质心→Si(111) 填入 {win.sp_si.value():.4f}°")
    check(win.chk_si.isChecked(), "Si 内标自动启用")
    # 恢复拟合峰位，避免影响后续算例校验
    win.sp_tt002.setValue(26.5584)
    win.sp_fw002.setValue(0.24)
    win.sp_si.setValue(28.4541)

    print("[6] Si 标样 → Caglioti")
    win.si_pattern = synth_si_standard()
    win._detect_si_peaks()
    check(len(win.si_peaks) >= 5, f"Si 标样识别 {len(win.si_peaks)} 个峰")
    win._fit_caglioti()
    check(win.caglioti is not None, "Caglioti 拟合成功")
    if win.caglioti:
        check(win.caglioti.W > 0, f"W = {win.caglioti.W:.6f}")
        check(win.caglioti.rms < 0.02, f"RMS = {win.caglioti.rms:.5f}°")
        win._apply_caglioti()
        check(win.cb_br_mode.currentIndex() == 0, "已切回 Caglioti 模式")

    print("[7] 三语热切换")
    for code in ("en", "ja", "zh"):
        win._switch_language(code)
        app.processEvents()
        leftover = [t for t in walk_texts(win) if "⟪" in t]
        check(not leftover, f"{code}: 无未翻译文案 {leftover[:3]}")
    check(win.tabs.tabText(0) == T.tr("tab.calc"), "页签标题随语言刷新")
    # 横幅是动态文案，必须随语言切换（不能硬编码中文）
    win._switch_language("en")
    banner_en = win.banner.text()
    check(not any("\u4e00" <= ch <= "\u9fff" for ch in banner_en),
          f"en: 横幅无中文残留（{banner_en[:28]}…）")
    win._switch_language("zh")

    print("[8] 报表生成")
    win._recalc()
    inp = win._build_input()
    if win.result:
        text = E.build_report_text(inp, win.result, app_name=A.APP_NAME, version=A.APP_VERSION)
        check("石墨化度 g" in text and "堆叠厚度 Lc" in text, "报告含关键指标")
        check("c0/2" not in text, "报告未出现 c0/2 晶胞参数写法")
        check("PolyXRD Graphite" in text, "报告带软件标识")

    print("[8b] 示例数据菜单")
    win._load_example()
    check(win.result is not None and abs(win.result.g_percent - 98.8) < 0.2,
          f"示例 g = {win.result.g_percent:.2f}%")
    check(abs(win.result.two_theta_002_corr - 26.54565) < 1e-4,
          f"示例校正 2θ = {win.result.two_theta_002_corr:.5f}°")
    check(win.sp_tt002.value() > 0 and win.card_g.value.text().endswith("%"),
          "示例数据已回填并刷新结果卡")

    print("[9] 小提示图标（测试与计算要点）")
    check(win.btn_hint.text() == "?", "页签栏右上角提示按钮存在")
    check(win.tabs.cornerWidget(Qt.TopRightCorner) is not None, "提示图标挂在页签栏角落")
    check(bool(win.btn_hint.toolTip()) and "⟪" not in win.btn_hint.toolTip(),
          f"提示按钮 tooltip 已翻译（{win.btn_hint.toolTip()[:16]}…）")
    for code in ("zh", "en", "ja"):
        win._switch_language(code)
        app.processEvents()
        dlg = win._build_brief_dialog()
        tb = dlg.findChild(QTextBrowser, "briefText")
        plain = tb.toPlainText() if tb is not None else ""
        check(len(plain) > 400, f"{code}: 提示内容非空（{len(plain)} 字）")
        check("⟪" not in plain and "⟪" not in dlg.windowTitle(), f"{code}: 提示无漏译")
        check("c0/2" not in plain, f"{code}: 提示不含 c0/2 晶胞参数写法")
        for token in ("0.3440", "0.3354", "0.89", "1.84"):
            check(token in plain, f"{code}: 提示含常数 {token}")
        dlg.deleteLater()
    win._switch_language("zh")
    zh_text = win._build_brief_dialog().findChild(QTextBrowser, "briefText").toPlainText()
    for token in ("25–29.5", "72–82", "20–90", "Caglioti", "洛伦兹"):
        check(token in zh_text, f"中文提示含「{token}」")

    print("[10] 构建变体与注册机制")
    print(f"  --  variant = {A.BUILD_VARIANT}, 名称 = {A.variant_name()}")
    if A.BUILD_VARIANT == "setup":
        check(A.variant_name() == T.tr("variant.setup"), "setup 变体名称已翻译")
        check(win._reg is not None, "注册管理器已挂载")
        state_path = ROOT / "build" / "tmp" / "smoke_reg_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        unit = "江西威托新材料有限公司"
        code = R.generate_code(unit)
        st = R.save_state(state_path, code)
        check(st.registered and st.unit == unit, "注册码校验并落盘")
        R.refresh_status_label(win._reg_label, st)
        check(unit in win._reg_label.text(), f"状态栏显示注册单位（{win._reg_label.text()}）")
        check(R.load_state(state_path).registered, "重新读取注册状态仍有效")
        state_path.write_text('{"code": "PXRD1-AAAA-BBBB", "unit": "伪造单位"}',
                              encoding="utf-8")
        bad = R.load_state(state_path)
        check(not bad.registered, "手改的注册状态被拒（按未注册处理）")
        R.refresh_status_label(win._reg_label, bad)
        check("未注册" in win._reg_label.text(), "未注册时状态栏提示")
        state_path.unlink()
    else:
        check(A.variant_name() == T.tr("status.internal_eval"), "internal 变体名称已翻译")
        check(win._reg is None, "内部评估版无注册管理器")

    print("[10b] 内部评估版状态栏排布（居中 / 加粗 / 红色）")
    origin = A.BUILD_VARIANT
    A.BUILD_VARIANT = "internal"       # 临时切变体，源码环境下也能构造内部评估版窗口
    w2 = A.MainWindow()
    w2.show()
    app.processEvents()
    lbl = w2._reg_label
    sb2 = w2.statusBar()
    check(lbl.objectName() == "statusEval", "评估提示使用独立样式类 statusEval")
    check(bool(lbl.alignment() & Qt.AlignHCenter), "评估提示水平居中")
    cx = lbl.mapTo(sb2, lbl.rect().center()).x()
    # 状态栏右下角有 17 px 的尺寸手柄，居中的参照系是「可用区」而非整条宽度
    grip = sb2.findChild(QSizeGrip)
    avail = sb2.width() - (grip.width() if grip is not None else 0)
    check(abs(cx - avail // 2) <= 4,
          f"提示位于状态栏中线（{cx} vs {avail // 2}）")
    css = w2.styleSheet()
    rule = css.split("QLabel#statusEval")[1].split("}")[0] if "QLabel#statusEval" in css else ""
    check("#c62828" in rule, f"评估提示为红色（{rule.strip()[:24]}…）")
    check("font-weight: 700" in rule, "评估提示加粗")
    check("font-size" not in rule, "评估提示未单独改字号（沿用全局）")
    check("内部评估版本" in lbl.text(), f"评估提示文案：{lbl.text()}")
    w2.close()
    A.BUILD_VARIANT = origin

    print("[11] 截图输出")
    if "--shot" in sys.argv:
        idx = int(sys.argv[sys.argv.index("--shot") + 1])
        # 截图前恢复一份典型工作状态（示例数据 + 谱图 + Caglioti），便于人工审阅界面
        win._load_example()
        win.ed_client.setText("江西威托新材料有限公司")
        win.ed_operator.setText("赵同新")
        win.pattern = pat
        win.canvas.set_pattern(pat)
        win._do_find_peaks()
        win._recalc()
        win.tabs.setCurrentIndex(idx)
        app.processEvents()
        app.processEvents()
        pix = win.grab()
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        pix.save(buf, "PNG")
        sys.stdout.flush()
        sys.stdout.write("\n<<<B64>>>" + base64.b64encode(bytes(buf.data())).decode("ascii"))
        sys.stdout.write("<<<END>>>\n")
        return 0

    win.close()
    print()
    if fails:
        print(f"FAILED {len(fails)} 项：")
        for f in fails:
            print("  -", f)
        return 1
    print("ALL PASS —— GUI 冒烟通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
