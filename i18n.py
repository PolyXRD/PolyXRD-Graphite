# -*- coding: utf-8 -*-
"""PolyXRD Graphite 轻量 i18n：简体中文 / English / 日本語，运行时可热切换。

与 PolyXRD 家族其余成员保持一致：缺失键返回 ``⟪key⟫`` 标记（不做语言
回退），这样漏译会在界面上直接暴露，测试脚本也能据此断言三语齐全。
新增界面文案时必须三语同时补齐。
"""
from __future__ import annotations

LANGS = ("zh", "en", "ja")
LANG_NAMES = {"zh": "简体中文", "en": "English", "ja": "日本語"}

_current = "zh"

TABLE: dict[str, dict[str, str]] = {
    # ================================================================ 简体中文
    "zh": {
        "app.title": "PolyXRD Graphite · 石墨化度 / Lc / La 测定",
        "app.short": "PolyXRD Graphite",

        # ---- 菜单 ----
        "menu.file": "文件(&F)",
        "menu.open_pattern": "打开谱图(&O)…",
        "menu.export_txt": "导出报告 TXT(&T)…",
        "menu.export_csv": "导出报告 CSV(&C)…",
        "menu.exit": "退出(&X)",
        "menu.language": "语言(&L)",
        "menu.help": "帮助(&H)",
        "menu.brief": "测试与计算要点(&Q)…",
        "menu.method": "测定方法与判据(&M)…",
        "menu.example": "载入示例数据（AP_XRD-001）(&E)",
        "menu.example_done": "已载入示例数据：g = {g}%",
        "menu.about": "关于 {app}…",
        "menu.copyright": "版权与许可…",
        "menu.about_qt": "关于 Qt…",
        "menu.reg": "输入注册码 (&R)…",
        "btn.close": "关闭",

        # ---- 状态栏 ----
        "status.ready": "就绪",
        "status.internal_eval": "内部评估版本",
        "variant.setup": "安装版",
        "status.calc_done": "计算完成：g = {g}%，Lc = {lc} nm",
        "status.pattern_loaded": "已载入谱图：{name}（{n} 点，{lo:.2f}–{hi:.2f}°）",

        # ---- 通用 ----
        "common.yes": "是",
        "common.no": "否",
        "common.auto": "自动",
        "common.none": "不计算",
        "common.name": "项目",
        "common.value": "数值",
        "common.unit": "单位",
        "common.required": "必填",

        # ---- 计算页 ----
        "tab.calc": "① 计算",
        "tab.pattern": "② 谱图与寻峰",
        "tab.inst": "③ Si 标样 / 仪器宽化",
        "tab.method": "④ 方法与判据",

        "group.sample": "样品信息（写入报告）",
        "sample.name": "样品名称 / 编号",
        "sample.client": "委托单位",
        "sample.operator": "测试人",
        "sample.note": "备注",

        "group.instrument": "仪器与计算参数",
        "inst.target": "靶材 / 波长",
        "inst.lambda": "波长 λ (nm)",
        "inst.k_lc": "K(Lc)",
        "inst.k_la": "K(La)",
        "inst.k_hint": "默认 K(Lc)=0.89、K(La)=1.84（碳材料 XRD 规程）",

        "group.peaks": "峰位与半高宽（实测值）",
        "peak.item": "峰",
        "peak.two_theta": "2θ (°)",
        "peak.fwhm": "FWHM (°)",
        "peak.c002": "C(002)",
        "peak.si111": "Si(111) 内标",
        "peak.la": "La 峰",
        "peak.enable_si": "使用 Si 内标校正 2θ",
        "peak.si_ref": "Si(111) 标准 2θ (°)",
        "peak.la_mode": "La 用峰",
        "la.peak.110": "(110) 优先 · 2θ ≈ 77.5°",
        "la.peak.100": "(100) 备用 · 2θ ≈ 42.3–42.4°",
        "la.peak.none": "不计算 La",
        "peak.hint_002": "C(002)：24–30° 慢扫、步长 ≤0.02°；其峰位精度直接决定 g。",
        "peak.hint_la": "La 优先用 (110)：需扫到 72–82°，该区间无相邻石墨峰干扰；(100) 峰（2θ≈42.3–42.4°，d≈0.213 nm）仅作备用。",
        "peak.hint_si": "Si(111) 实测与标准之差即 2θ 零点漂移，用于校正峰位。",
        "banner.ok_110": "✔ La 采用 (110) 峰（2θ = {tt:.4f}°，落在 72–82° 优先区间），且已用 Si 标样扣除仪器宽化。",
        "banner.ok_110_nobr": "✔ La 采用 (110) 峰（2θ = {tt:.4f}°，落在 72–82° 优先区间）；仪器宽化尚未由 Si 标样拟合，Lc / La 会偏小。",
        "banner.warn_110_out": "⚠ La 峰 2θ = {tt:.4f}° 不在 72–82°：请确认已扫到 (110) 峰（Cu Kα1 理论 77.50°）。",
        "banner.warn_100": "⚠ 当前用 (100) 峰（2θ ≈ 42.3–42.4°，d ≈ 0.213 nm）估算 La。建议补测 72–82° 的 (110) 峰——强度低但无相邻峰干扰、角分辨率更高。",
        "banner.scan_short": "　（当前谱图扫描上限 {hi:.1f}°，未覆盖 82°）",

        "group.broadening": "仪器宽化扣除",
        "br.mode": "仪器宽化来源",
        "br.mode.caglioti": "由 Si 标样谱拟合 Caglioti",
        "br.mode.direct": "直接给定仪器 FWHM",
        "br.mode.none": "不扣除",
        "br.inst002": "仪器 FWHM @ C(002) (°)",
        "br.instla": "仪器 FWHM @ La 峰 (°)",
        "br.sub_mode": "扣除模型",
        "br.sub.gauss": "平方差（高斯）√(βobs²−βinst²)",
        "br.sub.lorentz": "直接相减（洛伦兹）βobs−βinst",
        "br.sub.none": "不扣除",
        "br.caglioti_state": "Caglioti：{text}",
        "br.caglioti_empty": "Caglioti：未拟合（请到「③ Si 标样」页自动识别并拟合）",

        "result.title": "计算结果",
        "result.g": "石墨化度 g",
        "result.lc": "堆叠厚度 Lc",
        "result.la": "微晶尺寸 La",
        "result.d002": "层间距 d002",
        "result.detail": "计算明细",
        "result.warnings": "提示与判据",
        "result.empty": "填入 C(002) 的 2θ 与 FWHM 后点「计算」。",
        "result.no_warning": "判据检查通过，无特别提示。",
        "result.formula": "g = (0.3440 − d002) / (0.3440 − 0.3354) × 100%　·　L = Kλ / (β cosθ)",

        "btn.calculate": "计算 (&C)",
        "btn.copy": "复制报告",
        "btn.export_txt": "导出 TXT",
        "btn.export_csv": "导出 CSV",
        "btn.reset": "重置输入",

        # ---- 谱图页 ----
        "pat.open": "打开谱图…",
        "pat.info": "未载入谱图。支持 .txt / .xy / .dat / .csv（两列：2θ、强度）。",
        "pat.info_loaded": "{name}　{n} 点　{lo:.2f}–{hi:.2f}°　步长 {step:.4f}°",
        "pat.find": "自动寻峰",
        "pat.min_height": "最小相对强度",
        "pat.min_dist": "最小峰间距 (°)",
        "pat.peaks": "识别到的峰",
        "pat.col.two_theta": "2θ (°)",
        "pat.col.d": "d (nm)",
        "pat.col.fwhm": "FWHM (°)",
        "pat.col.height": "峰高",
        "pat.col.rel": "相对强度 (%)",
        "pat.col.eta": "η",
        "pat.col.r2": "R²",
        "pat.use_002": "设为 C(002)",
        "pat.use_la": "设为 La 峰",
        "pat.use_si": "设为 Si(111)",
        "pat.direct": "定点拟合 2θ (°)",
        "pat.direct_btn": "拟合该位置",
        "pat.direct_ok": "定点拟合：2θ = {tt:.4f}°，FWHM = {fw:.4f}°（已插入峰表）",
        "pat.direct_missing": "未在 {tt:.2f}° 附近识别到峰（弱峰易被阈值滤掉）：可用「定点拟合 2θ」直接拟合。",
        "pat.no_peak": "请先在峰表中选中一行。",
        "pat.empty": "载入谱图后点「自动寻峰」；峰位与 FWHM 由 pseudo-Voigt 拟合给出。",
        "pat.filled": "已把 2θ = {tt:.4f}°、FWHM = {fw:.4f}° 填入计算页。",
        "pat.overview": "全谱",
        "pat.hint_marker": "标签 = 识别峰 2θ；虚线 = 理论峰位",
        "pat.show_labels": "图上标注 2θ",
        "pat.del_peak": "删除选中峰",
        "pat.del_ok": "已删除 2θ = {tt:.4f}° 的峰（原始谱数据不变）",

        # ---- Si 标样页 ----
        "inststd.open": "打开 Si 标样谱…",
        "inststd.auto": "自动识别 Si 峰",
        "inststd.fit": "拟合 Caglioti 并采用",
        "inststd.apply": "应用到计算页",
        "inststd.col.hkl": "hkl",
        "inststd.col.theory": "理论 2θ (°)",
        "inststd.col.obs": "实测 2θ (°)",
        "inststd.col.delta": "Δ2θ (°)",
        "inststd.col.fwhm": "FWHM (°)",
        "inststd.result": "Caglioti：{text}",
        "inststd.result_empty": "尚未拟合。识别 ≥3 个 Si 峰后即可拟合 U/V/W。",
        "inststd.empty": "Si 标样需全角度扫描（如 20–120°），覆盖低角 (111) 与高角 (331)/(422)，"
                        "才能在 C(002) 与 (110) 两处都给出可靠仪器宽化。",
        "inststd.applied": "已采用该 Caglioti 参数，计算页将按峰位自动取仪器 FWHM。",
        "inststd.nofit": "有效 Si 峰不足 3 个，无法拟合 Caglioti。",
        "inststd.loaded": "已载入 Si 标样：{name}；识别到 {n} 个峰。",
        "inststd.need_fit": "请先拟合 Caglioti。",

        # ---- 方法页 ----
        "method.html": "",   # 见 _METHOD_HTML

        # ---- 小提示图标（测试与计算要点）----
        "hint.title": "测试与计算要点",
        "hint.tooltip": "测试与计算要点：两段扫描（25–29.5° / 72–82°）、Si 内标校正、"
                        "Caglioti 仪器宽化、Scherer 计算 Lc 与 La",
        "hint.html": "",     # 见 _HINT_HTML

        # ---- 对话框 ----
        "dlg.open_pattern": "打开 XRD 谱图",
        "dlg.save_report": "导出报告",
        "filter.pattern": "谱图 (*.txt *.xy *.dat *.csv *.asc *.prn);;所有文件 (*.*)",
        "filter.txt": "文本报告 (*.txt);;所有文件 (*.*)",
        "filter.csv": "CSV 表格 (*.csv);;所有文件 (*.*)",
        "msg.error": "出错了",
        "msg.calc_fail": "计算失败：{err}",
        "msg.saved": "已保存：{path}",
        "msg.save_fail": "保存失败：{err}",
        "msg.copied": "报告已复制到剪贴板。",
        "msg.lang_switch": "界面语言已切换为 {lang}。",

        # ---- 关于 / 版权 ----
        "about.version": "版本 v{version} · {variant}",
        "about.desc": "石墨材料 XRD 分析工具：石墨化度（以 d002 表达）、Lc 堆叠厚度、La 微晶尺寸",
        "about.features": "Si 内标 2θ 校正 · Si 标样 Caglioti 仪器宽化扣除 · pseudo-Voigt 寻峰拟合 · 报告导出",
        "about.contact": "联系方式：",
        "about.copyright": "© 2026 PolyXRD Family · 保留所有权利",
        "copyright.title": "版权与许可 · {app}",
        "copyright.heading": "版权与许可要点（与仓库中的 LICENSE / LICENSE-CN 一致，以其为准）",
        "copyright.contact": "联系方式 / Contact：",
        "copyright.license_zh": (
            "<p style='margin:2px 0 6px 0;'><b>中文（简体）</b></p>"
            "<p style='margin:2px 0 6px 0;'>© 2026 PolyXRD Team。"
            "本软件采用<b>双许可</b>发布：使用者可选择<b>学术许可</b>"
            "（仅限非商业学术研究与教学，免费），或向版权持有人另行申请<b>商业许可</b>。</p>"
            "<ul style='margin:2px 0 8px 16px;'>"
            "<li>学术许可下可自由使用、复制、修改、合并、发布、分发与再许可，"
            "<b>仅限学术研究、教学及非商业目的</b>；</li>"
            "<li>软件副本或其主要部分中，必须保留上述版权声明与本许可声明；</li>"
            "<li>本软件按“原样”提供，不作任何明示或默示担保；版权持有人不对任何索赔、"
            "损害赔偿或其他责任负责；</li>"
            "<li><b>本学术许可不允许任何商业用途</b>：营利性组织内部业务、集成至商业产品／"
            "商业服务／SaaS／付费咨询、转售或以商业收益为目的再分发，均须在商用前联系"
            "版权持有人取得独立书面商业授权；</li>"
            "<li>使用本软件产出结果的论文、报告与公开演示，建议注明所用软件与版本；</li>"
            "<li>违反任一条款，本许可自动终止；终止后须停止使用并销毁所持有的全部副本。</li>"
            "</ul>"),
        "copyright.license_en": (
            "<p style='margin:2px 0 6px 0;'><b>English</b></p>"
            "<p style='margin:2px 0 6px 0;'>Copyright © 2026 PolyXRD Team. "
            "This software is distributed under a <b>dual license</b>: either the "
            "<b>Academic License</b> (free, for non-commercial academic research and "
            "education), or a separately obtained <b>Commercial License</b>.</p>"
            "<ul style='margin:2px 0 8px 16px;'>"
            "<li>You may use, copy, modify, merge, publish, distribute and sublicense the "
            "Software <b>solely for academic research, educational and non-commercial "
            "purposes</b>;</li>"
            "<li>The above copyright notice and this permission notice must be retained in "
            "all copies or substantial portions of the Software;</li>"
            "<li>The Software is provided “AS IS”, without warranty of any kind, and the "
            "copyright holder accepts no liability for any claim, damages or other "
            "liability;</li>"
            "<li><b>No commercial use is permitted under the Academic License</b>: use within "
            "a for-profit organization, integration into commercial products, services, SaaS "
            "or paid consulting, resale or redistribution for commercial gain all require a "
            "separate written commercial license;</li>"
            "<li>Publications and public presentations using results from this Software should "
            "cite the software and its version;</li>"
            "<li>Any violation terminates this license automatically; you must then stop using "
            "the Software and destroy all copies.</li>"
            "</ul>"),
    },

    # ================================================================== English
    "en": {
        "app.title": "PolyXRD Graphite · Graphitization / Lc / La",
        "app.short": "PolyXRD Graphite",

        "menu.file": "&File",
        "menu.open_pattern": "&Open Pattern…",
        "menu.export_txt": "Export Report (&T)…",
        "menu.export_csv": "Export Report (&C)…",
        "menu.exit": "E&xit",
        "menu.language": "&Language",
        "menu.help": "&Help",
        "menu.brief": "Test && Calculation Summary (&Q)…",
        "menu.method": "Method && Criteria (&M)…",
        "menu.example": "Load example data (AP_XRD-001) (&E)",
        "menu.example_done": "Example data loaded: g = {g}%",
        "menu.about": "&About {app}…",
        "menu.copyright": "Copyright && License…",
        "menu.about_qt": "About Qt…",
        "menu.reg": "Enter Registration &Code…",
        "btn.close": "Close",

        "status.ready": "Ready",
        "status.internal_eval": "Internal evaluation build",
        "variant.setup": "Installed build",
        "status.calc_done": "Done: g = {g}%, Lc = {lc} nm",
        "status.pattern_loaded": "Pattern loaded: {name} ({n} pts, {lo:.2f}–{hi:.2f}°)",

        "common.yes": "Yes",
        "common.no": "No",
        "common.auto": "Auto",
        "common.none": "None",
        "common.name": "Item",
        "common.value": "Value",
        "common.unit": "Unit",
        "common.required": "required",

        "tab.calc": "1 · Calculate",
        "tab.pattern": "2 · Pattern && Peaks",
        "tab.inst": "3 · Si Standard / Broadening",
        "tab.method": "4 · Method",

        "group.sample": "Sample information (written to report)",
        "sample.name": "Sample name / ID",
        "sample.client": "Client",
        "sample.operator": "Operator",
        "sample.note": "Remarks",

        "group.instrument": "Instrument && calculation parameters",
        "inst.target": "Target / wavelength",
        "inst.lambda": "Wavelength λ (nm)",
        "inst.k_lc": "K(Lc)",
        "inst.k_la": "K(La)",
        "inst.k_hint": "Defaults K(Lc)=0.89, K(La)=1.84 (carbon XRD standard practice)",

        "group.peaks": "Peak positions && FWHM (measured)",
        "peak.item": "Peak",
        "peak.two_theta": "2θ (°)",
        "peak.fwhm": "FWHM (°)",
        "peak.c002": "C(002)",
        "peak.si111": "Si(111) internal standard",
        "peak.la": "La peak",
        "peak.enable_si": "Apply Si internal-standard 2θ correction",
        "peak.si_ref": "Si(111) reference 2θ (°)",
        "peak.la_mode": "Peak for La",
        "la.peak.110": "(110) preferred · 2θ ≈ 77.5°",
        "la.peak.100": "(100) fallback · 2θ ≈ 42.3–42.4°",
        "la.peak.none": "Do not compute La",
        "peak.hint_002": "C(002): scan 24–30° slowly, step ≤ 0.02°; its position drives g.",
        "peak.hint_la": "Prefer (110) for La: scan 72–82°, free of neighbouring graphite peaks; "
                        "(100) at 2θ ≈ 42.3–42.4° (d ≈ 0.213 nm) is only a fallback.",
        "peak.hint_si": "Measured minus reference Si(111) gives the 2θ zero shift used to correct peak positions.",
        "banner.ok_110": "✔ La from the (110) peak (2θ = {tt:.4f}°, inside the preferred 72–82° window), with instrumental broadening removed using the Si standard.",
        "banner.ok_110_nobr": "✔ La from the (110) peak (2θ = {tt:.4f}°, inside 72–82°); instrumental broadening not yet fitted from a Si standard, so Lc / La are underestimated.",
        "banner.warn_110_out": "⚠ La peak at 2θ = {tt:.4f}° is outside 72–82°: confirm the (110) peak was actually scanned (Cu Kα1 theory 77.50°).",
        "banner.warn_100": "⚠ La is currently estimated from the (100) peak (2θ ≈ 42.3–42.4°, d ≈ 0.213 nm). Measuring (110) between 72–82° is preferred — weaker but free of overlapping peaks and with better angular resolution.",
        "banner.scan_short": "　(current pattern stops at {hi:.1f}°, below 82°)",

        "group.broadening": "Instrumental broadening removal",
        "br.mode": "Source of instrumental broadening",
        "br.mode.caglioti": "Caglioti fit from Si standard",
        "br.mode.direct": "Specify instrumental FWHM directly",
        "br.mode.none": "No removal",
        "br.inst002": "Instrumental FWHM @ C(002) (°)",
        "br.instla": "Instrumental FWHM @ La peak (°)",
        "br.sub_mode": "Removal model",
        "br.sub.gauss": "Quadrature (Gaussian) √(βobs²−βinst²)",
        "br.sub.lorentz": "Direct subtraction (Lorentzian) βobs−βinst",
        "br.sub.none": "No removal",
        "br.caglioti_state": "Caglioti: {text}",
        "br.caglioti_empty": "Caglioti: not fitted (go to tab 3 to detect Si peaks and fit)",

        "result.title": "Results",
        "result.g": "Graphitization degree g",
        "result.lc": "Stacking height Lc",
        "result.la": "Crystallite size La",
        "result.d002": "Interlayer spacing d002",
        "result.detail": "Details",
        "result.warnings": "Notes && checks",
        "result.empty": "Enter 2θ and FWHM of C(002), then press Calculate.",
        "result.no_warning": "All checks passed — no special notes.",
        "result.formula": "g = (0.3440 − d002) / (0.3440 − 0.3354) × 100%　·　L = Kλ / (β cosθ)",

        "btn.calculate": "&Calculate",
        "btn.copy": "Copy report",
        "btn.export_txt": "Export TXT",
        "btn.export_csv": "Export CSV",
        "btn.reset": "Reset inputs",

        "pat.open": "Open pattern…",
        "pat.info": "No pattern loaded. Supports .txt / .xy / .dat / .csv (two columns: 2θ, intensity).",
        "pat.info_loaded": "{name}　{n} pts　{lo:.2f}–{hi:.2f}°　step {step:.4f}°",
        "pat.find": "Find peaks",
        "pat.min_height": "Min. relative height",
        "pat.min_dist": "Min. peak distance (°)",
        "pat.peaks": "Detected peaks",
        "pat.col.two_theta": "2θ (°)",
        "pat.col.d": "d (nm)",
        "pat.col.fwhm": "FWHM (°)",
        "pat.col.height": "Height",
        "pat.col.rel": "Rel. int. (%)",
        "pat.col.eta": "η",
        "pat.col.r2": "R²",
        "pat.use_002": "Use as C(002)",
        "pat.use_la": "Use as La peak",
        "pat.use_si": "Use as Si(111)",
        "pat.direct": "Fit at 2θ (°)",
        "pat.direct_btn": "Fit this position",
        "pat.direct_ok": "Local fit: 2θ = {tt:.4f}°, FWHM = {fw:.4f}° (added to peak table)",
        "pat.direct_missing": "No peak found near {tt:.2f}° (weak peaks fall below the threshold) — use “Fit at 2θ” instead.",
        "pat.no_peak": "Select a row in the peak table first.",
        "pat.empty": "Load a pattern and press Find peaks; positions and FWHM come from pseudo-Voigt fits.",
        "pat.filled": "Filled 2θ = {tt:.4f}°, FWHM = {fw:.4f}° into the calculation tab.",
        "pat.overview": "Full pattern",
        "pat.hint_marker": "Labels = fitted 2θ; dashed lines = theoretical positions",
        "pat.show_labels": "Label 2θ on plot",
        "pat.del_peak": "Delete peak",
        "pat.del_ok": "Removed the peak at 2θ = {tt:.4f}° (raw data untouched)",

        "inststd.open": "Open Si standard pattern…",
        "inststd.auto": "Detect Si peaks",
        "inststd.fit": "Fit Caglioti && adopt",
        "inststd.apply": "Apply to calculation tab",
        "inststd.col.hkl": "hkl",
        "inststd.col.theory": "2θ theory (°)",
        "inststd.col.obs": "2θ observed (°)",
        "inststd.col.delta": "Δ2θ (°)",
        "inststd.col.fwhm": "FWHM (°)",
        "inststd.result": "Caglioti: {text}",
        "inststd.result_empty": "Not fitted yet. Three or more Si peaks are needed to fit U/V/W.",
        "inststd.empty": "Scan the Si standard over a wide range (e.g. 20–120°) so that both low-angle (111) "
                        "and high-angle (331)/(422) peaks are covered — needed for reliable broadening "
                        "at C(002) and at (110).",
        "inststd.applied": "Caglioti parameters adopted; instrumental FWHM is now taken at each peak position.",
        "inststd.nofit": "Fewer than 3 usable Si peaks — cannot fit Caglioti.",
        "inststd.loaded": "Si standard loaded: {name}; {n} peaks detected.",
        "inststd.need_fit": "Fit Caglioti first.",

        "method.html": "",

        "hint.title": "Test and calculation summary",
        "hint.tooltip": "Test and calculation summary: two scan ranges (25–29.5° / 72–82°), "
                        "Si internal standard, Caglioti instrumental broadening, Scherer Lc and La",
        "hint.html": "",

        "dlg.open_pattern": "Open XRD pattern",
        "dlg.save_report": "Export report",
        "filter.pattern": "Patterns (*.txt *.xy *.dat *.csv *.asc *.prn);;All files (*.*)",
        "filter.txt": "Text report (*.txt);;All files (*.*)",
        "filter.csv": "CSV table (*.csv);;All files (*.*)",
        "msg.error": "Error",
        "msg.calc_fail": "Calculation failed: {err}",
        "msg.saved": "Saved: {path}",
        "msg.save_fail": "Save failed: {err}",
        "msg.copied": "Report copied to clipboard.",
        "msg.lang_switch": "UI language switched to {lang}.",

        "about.version": "Version v{version} · {variant}",
        "about.desc": "XRD analysis for carbon materials: graphitization degree (in d002), Lc stacking height, La crystallite size",
        "about.features": "Si internal-standard 2θ correction · Caglioti broadening removal · pseudo-Voigt peak fitting · report export",
        "about.contact": "Contact: ",
        "about.copyright": "© 2026 PolyXRD Family · All rights reserved",
        "copyright.title": "Copyright && License · {app}",
        "copyright.heading": "Key points (the LICENSE / LICENSE-CN files in the repository prevail)",
        "copyright.contact": "Contact: ",
        "copyright.license_zh": (
            "<p style='margin:2px 0 6px 0;'><b>中文（简体）</b></p>"
            "<p style='margin:2px 0 6px 0;'>© 2026 PolyXRD Team。"
            "本软件采用<b>双许可</b>发布：使用者可选择<b>学术许可</b>"
            "（仅限非商业学术研究与教学，免费），或向版权持有人另行申请<b>商业许可</b>。</p>"
            "<p style='margin:2px 0 6px 0;'>学术许可仅限学术研究、教学及非商业目的，"
            "须保留版权与许可声明；软件按“原样”提供，不提供任何担保；"
            "<b>不允许任何商业用途</b>。详见 LICENSE-CN。</p>"),
        "copyright.license_en": (
            "<p style='margin:2px 0 6px 0;'><b>English</b></p>"
            "<p style='margin:2px 0 6px 0;'>Copyright © 2026 PolyXRD Team. "
            "This software is distributed under a <b>dual license</b>: either the "
            "<b>Academic License</b> (free, for non-commercial academic research and "
            "education), or a separately obtained <b>Commercial License</b>.</p>"
            "<ul style='margin:2px 0 8px 16px;'>"
            "<li>You may use, copy, modify, merge, publish, distribute and sublicense the "
            "Software <b>solely for academic research, educational and non-commercial "
            "purposes</b>;</li>"
            "<li>The above copyright notice and this permission notice must be retained in "
            "all copies or substantial portions of the Software;</li>"
            "<li>The Software is provided “AS IS”, without warranty of any kind, and the "
            "copyright holder accepts no liability for any claim, damages or other "
            "liability;</li>"
            "<li><b>No commercial use is permitted under the Academic License</b>: use within "
            "a for-profit organization, integration into commercial products, services, SaaS "
            "or paid consulting, resale or redistribution for commercial gain all require a "
            "separate written commercial license;</li>"
            "<li>Publications and public presentations using results from this Software should "
            "cite the software and its version;</li>"
            "<li>Any violation terminates this license automatically; you must then stop using "
            "the Software and destroy all copies.</li>"
            "</ul>"),
    },

    # ================================================================== 日本語
    "ja": {
        "app.title": "PolyXRD Graphite · 黒鉛化度 / Lc / La 測定",
        "app.short": "PolyXRD Graphite",

        "menu.file": "ファイル(&F)",
        "menu.open_pattern": "パターンを開く(&O)…",
        "menu.export_txt": "レポートを TXT 出力(&T)…",
        "menu.export_csv": "レポートを CSV 出力(&C)…",
        "menu.exit": "終了(&X)",
        "menu.language": "言語(&L)",
        "menu.help": "ヘルプ(&H)",
        "menu.brief": "測定・計算の要点(&Q)…",
        "menu.method": "測定方法と判定基準(&M)…",
        "menu.example": "サンプルデータを読み込む（AP_XRD-001）(&E)",
        "menu.example_done": "サンプルデータを読み込みました：g = {g}%",
        "menu.about": "{app} について…",
        "menu.copyright": "著作権とライセンス…",
        "menu.about_qt": "Qt について…",
        "menu.reg": "登録コードを入力 (&R)…",
        "btn.close": "閉じる",

        "status.ready": "準備完了",
        "status.internal_eval": "内部評価版",
        "variant.setup": "インストール版",
        "status.calc_done": "計算完了：g = {g}%、Lc = {lc} nm",
        "status.pattern_loaded": "パターン読込：{name}（{n} 点、{lo:.2f}–{hi:.2f}°）",

        "common.yes": "はい",
        "common.no": "いいえ",
        "common.auto": "自動",
        "common.none": "計算しない",
        "common.name": "項目",
        "common.value": "値",
        "common.unit": "単位",
        "common.required": "必須",

        "tab.calc": "① 計算",
        "tab.pattern": "② パターンとピーク",
        "tab.inst": "③ Si 標準試料 / 装置幅",
        "tab.method": "④ 方法と判定基準",

        "group.sample": "試料情報（レポートに記載）",
        "sample.name": "試料名 / 番号",
        "sample.client": "依頼元",
        "sample.operator": "測定者",
        "sample.note": "備考",

        "group.instrument": "装置と計算パラメータ",
        "inst.target": "ターゲット / 波長",
        "inst.lambda": "波長 λ (nm)",
        "inst.k_lc": "K(Lc)",
        "inst.k_la": "K(La)",
        "inst.k_hint": "既定値 K(Lc)=0.89、K(La)=1.84（炭素材料 XRD 標準手順）",

        "group.peaks": "ピーク位置と半値幅（実測）",
        "peak.item": "ピーク",
        "peak.two_theta": "2θ (°)",
        "peak.fwhm": "FWHM (°)",
        "peak.c002": "C(002)",
        "peak.si111": "Si(111) 内部標準",
        "peak.la": "La ピーク",
        "peak.enable_si": "Si 内部標準で 2θ を補正する",
        "peak.si_ref": "Si(111) 標準 2θ (°)",
        "peak.la_mode": "La に用いるピーク",
        "la.peak.110": "(110) 優先 · 2θ ≈ 77.5°",
        "la.peak.100": "(100) 代替 · 2θ ≈ 42.3–42.4°",
        "la.peak.none": "La を計算しない",
        "peak.hint_002": "C(002)：24–30° を低速・ステップ ≤0.02° で走査。ピーク位置が g を決めます。",
        "peak.hint_la": "La は (110) を優先：72–82° まで走査すると隣接ピークの干渉がない。"
                        "(100)（2θ≈42.3–42.4°、d≈0.213 nm）は代替のみ。",
        "peak.hint_si": "Si(111) の実測値と標準値の差が 2θ の零点ずれで、ピーク位置の補正に使う。",
        "banner.ok_110": "✔ La は (110) ピーク（2θ = {tt:.4f}°、優先区間 72–82° 内）を使用し、Si 標準で装置幅を除去済み。",
        "banner.ok_110_nobr": "✔ La は (110) ピーク（2θ = {tt:.4f}°、72–82° 内）を使用。装置幅が未フィットのため Lc / La は小さめになります。",
        "banner.warn_110_out": "⚠ La ピーク 2θ = {tt:.4f}° は 72–82° の外です：(110) ピーク（Cu Kα1 理論 77.50°）まで走査したか確認してください。",
        "banner.warn_100": "⚠ 現在 (100) ピーク（2θ ≈ 42.3–42.4°、d ≈ 0.213 nm）で La を推定しています。72–82° の (110) の測定を推奨します（弱いが重なりがなく角度分解能が高い）。",
        "banner.scan_short": "　（現在のパターン上限 {hi:.1f}°、82° 未満）",

        "group.broadening": "装置幅の除去",
        "br.mode": "装置幅の取得方法",
        "br.mode.caglioti": "Si 標準試料から Caglioti フィット",
        "br.mode.direct": "装置 FWHM を直接入力",
        "br.mode.none": "除去しない",
        "br.inst002": "装置 FWHM @ C(002) (°)",
        "br.instla": "装置 FWHM @ La ピーク (°)",
        "br.sub_mode": "除去モデル",
        "br.sub.gauss": "二乗差（ガウス）√(βobs²−βinst²)",
        "br.sub.lorentz": "単純差（ローレンツ）βobs−βinst",
        "br.sub.none": "除去しない",
        "br.caglioti_state": "Caglioti：{text}",
        "br.caglioti_empty": "Caglioti：未フィット（タブ③で Si ピークを認識してフィット）",

        "result.title": "計算結果",
        "result.g": "黒鉛化度 g",
        "result.lc": "積層厚み Lc",
        "result.la": "微結晶子径 La",
        "result.d002": "面間隔 d002",
        "result.detail": "計算内訳",
        "result.warnings": "注意と判定",
        "result.empty": "C(002) の 2θ と FWHM を入力し「計算」を押してください。",
        "result.no_warning": "判定基準を満たしています（特記事項なし）。",
        "result.formula": "g = (0.3440 − d002) / (0.3440 − 0.3354) × 100%　·　L = Kλ / (β cosθ)",

        "btn.calculate": "計算 (&C)",
        "btn.copy": "レポートをコピー",
        "btn.export_txt": "TXT 出力",
        "btn.export_csv": "CSV 出力",
        "btn.reset": "入力をリセット",

        "pat.open": "パターンを開く…",
        "pat.info": "パターン未読込。.txt / .xy / .dat / .csv（2 列：2θ、強度）に対応。",
        "pat.info_loaded": "{name}　{n} 点　{lo:.2f}–{hi:.2f}°　ステップ {step:.4f}°",
        "pat.find": "ピーク探索",
        "pat.min_height": "最小相対強度",
        "pat.min_dist": "最小ピーク間隔 (°)",
        "pat.peaks": "検出ピーク",
        "pat.col.two_theta": "2θ (°)",
        "pat.col.d": "d (nm)",
        "pat.col.fwhm": "FWHM (°)",
        "pat.col.height": "高さ",
        "pat.col.rel": "相対強度 (%)",
        "pat.col.eta": "η",
        "pat.col.r2": "R²",
        "pat.use_002": "C(002) に設定",
        "pat.use_la": "La ピークに設定",
        "pat.use_si": "Si(111) に設定",
        "pat.direct": "指定位置フィット 2θ (°)",
        "pat.direct_btn": "この位置をフィット",
        "pat.direct_ok": "指定位置フィット：2θ = {tt:.4f}°、FWHM = {fw:.4f}°（ピーク表に追加）",
        "pat.direct_missing": "{tt:.2f}° 付近にピークが検出されません（弱いピークは閾値以下）：「指定位置フィット」を使用してください。",
        "pat.no_peak": "先にピーク表の行を選択してください。",
        "pat.empty": "パターンを読み込み「ピーク探索」を押してください。位置と FWHM は pseudo-Voigt で算出します。",
        "pat.filled": "2θ = {tt:.4f}°、FWHM = {fw:.4f}° を計算タブに反映しました。",
        "pat.overview": "全範囲",
        "pat.hint_marker": "ラベル = 検出ピークの 2θ、破線 = 理論ピーク位置",
        "pat.show_labels": "2θ をグラフに表示",
        "pat.del_peak": "選択ピークを削除",
        "pat.del_ok": "2θ = {tt:.4f}° のピークを削除しました（生データは不変）",

        "inststd.open": "Si 標準パターンを開く…",
        "inststd.auto": "Si ピークを認識",
        "inststd.fit": "Caglioti をフィットして採用",
        "inststd.apply": "計算タブに適用",
        "inststd.col.hkl": "hkl",
        "inststd.col.theory": "理論 2θ (°)",
        "inststd.col.obs": "実測 2θ (°)",
        "inststd.col.delta": "Δ2θ (°)",
        "inststd.col.fwhm": "FWHM (°)",
        "inststd.result": "Caglioti：{text}",
        "inststd.result_empty": "未フィット。Si ピークが 3 本以上あれば U/V/W をフィットできます。",
        "inststd.empty": "Si 標準試料は広角走査（例 20–120°）を行い、低角 (111) と高角 (331)/(422) を"
                        "含めてください。C(002) と (110) の両方で信頼できる装置幅が得られます。",
        "inststd.applied": "Caglioti パラメータを採用しました。各ピーク位置の装置 FWHM を自動で使います。",
        "inststd.nofit": "有効な Si ピークが 3 本未満のため Caglioti をフィットできません。",
        "inststd.loaded": "Si 標準を読み込み：{name}、{n} 本のピークを認識。",
        "inststd.need_fit": "先に Caglioti をフィットしてください。",

        "method.html": "",

        "hint.title": "測定・計算の要点",
        "hint.tooltip": "測定・計算の要点：2 段スキャン（25–29.5° / 72–82°）、Si 内部標準、"
                        "Caglioti 装置幅、Scherer 式による Lc・La",
        "hint.html": "",

        "dlg.open_pattern": "XRD パターンを開く",
        "dlg.save_report": "レポート出力",
        "filter.pattern": "パターン (*.txt *.xy *.dat *.csv *.asc *.prn);;すべてのファイル (*.*)",
        "filter.txt": "テキスト (*.txt);;すべてのファイル (*.*)",
        "filter.csv": "CSV (*.csv);;すべてのファイル (*.*)",
        "msg.error": "エラー",
        "msg.calc_fail": "計算に失敗しました：{err}",
        "msg.saved": "保存しました：{path}",
        "msg.save_fail": "保存に失敗しました：{err}",
        "msg.copied": "レポートをクリップボードにコピーしました。",
        "msg.lang_switch": "表示言語を {lang} に切り替えました。",

        "about.version": "バージョン v{version} · {variant}",
        "about.desc": "炭素材料の XRD 解析：黒鉛化度（d002 表現）、積層厚み Lc、微結晶子径 La",
        "about.features": "Si 内部標準 2θ 補正 · Si 標準試料による Caglioti 装置幅除去 · pseudo-Voigt ピークフィット · レポート出力",
        "about.contact": "連絡先：",
        "about.copyright": "© 2026 PolyXRD Family · All rights reserved",
        "copyright.title": "著作権とライセンス · {app}",
        "copyright.heading": "要点（リポジトリの LICENSE / LICENSE-CN が優先します）",
        "copyright.contact": "連絡先 / Contact：",
        "copyright.license_zh": (
            "<p style='margin:2px 0 6px 0;'><b>中文（简体）</b></p>"
            "<p style='margin:2px 0 6px 0;'>© 2026 PolyXRD Team。本ソフトウェアは<b>デュアルライセンス</b>"
            "（非営利の学術研究・教育向け<b>学術ライセンス</b>、または別途取得する<b>商用ライセンス</b>）"
            "で提供されます。学術ライセンスは非営利目的に限定され、著作権表示の保持が必要です。"
            "ソフトウェアは現状のまま提供され、いかなる保証もありません。詳細は LICENSE-CN を参照。</p>"),
        "copyright.license_en": (
            "<p style='margin:2px 0 6px 0;'><b>English</b></p>"
            "<p style='margin:2px 0 6px 0;'>Copyright © 2026 PolyXRD Team. "
            "This software is distributed under a <b>dual license</b>: either the "
            "<b>Academic License</b> (free, for non-commercial academic research and "
            "education), or a separately obtained <b>Commercial License</b>.</p>"
            "<ul style='margin:2px 0 8px 16px;'>"
            "<li>You may use, copy, modify, merge, publish, distribute and sublicense the "
            "Software <b>solely for academic research, educational and non-commercial "
            "purposes</b>;</li>"
            "<li>The above copyright notice and this permission notice must be retained in "
            "all copies or substantial portions of the Software;</li>"
            "<li>The Software is provided “AS IS”, without warranty of any kind;</li>"
            "<li><b>No commercial use is permitted under the Academic License</b>;</li>"
            "<li>Any violation terminates this license automatically.</li>"
            "</ul>"),
    },
}


# ------------------------------------------------------------------------------
# 方法说明页（富文本，按语言提供）
# ------------------------------------------------------------------------------
_METHOD_HTML: dict[str, str] = {
    "zh": """
<h2>测定方法与判据</h2>
<p>本工具按炭素/石墨材料 XRD 的通行做法组织计算，全部输入均为<b>实测峰位与半高宽</b>，
结果可追溯到 λ、K 值与宽化扣除模型。参数依据见文末参考文献。</p>

<h3>一、石墨化度 g（层间距表达）</h3>
<p style="font-size:15px;"><b>g = (0.3440 − d<sub>002</sub>) / (0.3440 − 0.3354) × 100%</b></p>
<p>0.3440 nm 为完全未石墨化（乱层）碳的层间距，0.3354 nm 为理想石墨；两者之差 0.0086 nm 即分母。
本工具统一以 <b>d<sub>002</sub></b> 表达，不使用晶胞参数 c<sub>0</sub>/2 写法（二者数值等价，
d<sub>002</sub> = c<sub>0</sub>/2）。</p>
<p><b>关键：d<sub>002</sub> 因此必须由精确峰位算出。</b>C(002) 峰位对 2θ 误差极敏感——
0.01° 的峰位偏差约带来 0.15 个百分点石墨化度偏差，故需用内标校正（见第二节）。</p>

<h3>二、Si 内标 2θ 校正</h3>
<ol>
<li>石墨中掺入适量 Si 粉（约 10–20 wt%），混匀、填池、刮平、轻压，与待测样同条件扫描；</li>
<li>读出 Si(111) 实测峰位 2θ<sub>obs</sub>，与标准值 2θ<sub>ref</sub> 比较，得零点漂移
Δ2θ = 2θ<sub>ref</sub> − 2θ<sub>obs</sub>；</li>
<li>把同一 Δ2θ 施加到 C(002)（以及 La 峰）实测峰位上：2θ<sub>corr</sub> = 2θ<sub>obs</sub> + Δ2θ。</li>
</ol>
<p>Si(111) 的标准 2θ 由晶格常数 a = 0.54310205 nm 与所选波长按 Bragg 式算出（Cu Kα1 约 28.442°），
界面可手动覆盖为仪器/ICDD 标定值。</p>
<p><b>为什么必须掺内标：</b>C(002) 位于 26.5° 附近，样品装填高度、表面离焦、透明效应都会整体
推移峰位；这类几何误差对同一谱图上的所有峰近似相同，用内标点对点扣除最有效。</p>

<h3>三、Lc（堆叠厚度）与 La（微晶尺寸）</h3>
<p style="font-size:15px;"><b>L = K λ / (β cosθ)</b>（Scherrer 式，β 为<b>扣除仪器宽化后</b>的样品半高宽，弧度）</p>
<ul>
<li><b>Lc</b>：由 C(002) 求得，K = 0.89；</li>
<li><b>La</b>：优先用 <b>(110)</b> 峰（Cu Kα 时 2θ ≈ 77.5°，需扫到 <b>72–82°</b>），K = 1.84；
条件不具备时退用 <b>(100)</b> 峰（2θ ≈ 42.4°，d ≈ 0.213 nm），K 同样取 1.84，
但该峰与相邻 (10<span style="text-decoration:overline">1</span>) 等反射靠近、且角度低分辨率差，
结果应标注为估算值。</li>
</ul>
<p><b>为什么 (110) 优先：</b>La 反映石墨层内的晶畴尺寸，必须用 hk0 型反射。(110) 角度高、
同一 Δd 对应的 Δ2θ 更大（分辨率更高），且 72–82° 区间没有其他强石墨峰叠加；
(100) 虽然强度更高，但与三维反射邻近，分峰误差更大。</p>

<h3>四、仪器宽化的扣除（Si 标样，全角度）</h3>
<ol>
<li>另测一份纯 Si 标样（或 LaB₆）谱，<b>全角度扫描</b>（建议 20–120°，与样品同狭缝、同步长）；</li>
<li>工具自动按 Si 理论峰位识别 111 / 220 / 311 / 400 / 331 / 422… 并逐个做 pseudo-Voigt 拟合，
得到各角度的仪器半高宽；</li>
<li>用 <b>Caglioti 式</b> FWHM² = U·tan²θ + V·tanθ + W 拟合 U/V/W，即可外推到任意峰位
（C(002) 与 (110) 处的仪器宽化由同一组参数给出，无需重复测标样）；</li>
<li>扣除模型二选一：<b>平方差</b> β = √(β<sub>obs</sub>² − β<sub>inst</sub>²)（两者近似高斯）或
<b>直接相减</b> β = β<sub>obs</sub> − β<sub>inst</sub>（两者近似洛伦兹）。同一批样品必须用同一模型，
报告需注明。</li>
</ol>
<p>若未扣除仪器宽化，Lc/La 会系统性偏小；当晶粒较大（β<sub>obs</sub> 接近 β<sub>inst</sub>）时，
这种偏小可达数十个百分点。</p>

<h3>五、操作流程（推荐）</h3>
<ol>
<li>装样：石墨 + Si 粉混匀（内标），另备纯 Si 标样；</li>
<li>扫 C(002)：24–30°，步长 ≤0.02°，停留 ≥1 s；</li>
<li>扫 La 峰：72–82°（(110)），步长 ≤0.02°，停留 ≥2 s（该峰强度低）；</li>
<li>扫 Si 标样：20–120°，与样品同条件；</li>
<li>在「② 谱图」页自动寻峰并拟合 FWHM；在「③」页拟合 Caglioti 并采用；回到「①」页计算并导出报告。</li>
</ol>

<h3>六、常见问题</h3>
<ul>
<li><b>g 为负或 &gt;100%</b>：峰位识别错误、内标方向反了，或 d<sub>002</sub> 超出 0.3354–0.3440 nm 适用范围
（高石墨化样品可能略超 100%，应核对峰位与波长）。</li>
<li><b>La 空值</b>：未输入 La 峰，或该峰实测半高宽不大于仪器宽化（晶粒过大，需换用更高分辨率条件或改由 (110) 计算）。</li>
<li><b>La 与 Lc 数量级不符</b>：确认 La 用的是 (110)/(100) 而不是 (002)；并确认 K 值与宽化模型一致。</li>
<li><b>波长选择</b>：精确峰位请用 Kα1 单色（或 Kα1 剥离后）数据；用 Kα 平均会使峰位与 d 值略偏，
本工具提供 1.5405929（CODATA）与 1.54056（传统）两个 Cu Kα1 值以复现既有报告。</li>
</ul>

<h3>参考文献</h3>
<ol style="font-size:12px;">
<li>Franklin R. E. <i>Acta Crystallographica</i>, 1951, 4: 253–261.（石墨化度与层间距关系）</li>
<li>Iwashita N., Park C. R., Fujimoto H., Shiraishi M., Inagaki M. <i>Carbon</i>, 2004, 42: 701–714.
（碳材料 XRD 标准测定规程：Lc 用 K=0.89，(110) 求 La 用 K=1.84）</li>
<li>Warren B. E. <i>Physical Review</i>, 1941, 59: 693.（hk 带展宽与面内尺寸）</li>
<li>章斌. 石墨化度的测定. 岛津应用数据集 AP_XRD-001（Si 内标法示例：Si(111) 28.4541° → 校正 C(002) 26.54565°，d=0.33551 nm，g=98.8%）</li>
</ol>
""",
    "en": """
<h2>Method and criteria</h2>
<p>All inputs are <b>measured peak positions and FWHM</b>; every result is traceable to the wavelength,
the Scherrer constant and the broadening model.</p>

<h3>1. Graphitization degree g (interlayer-spacing form)</h3>
<p style="font-size:15px;"><b>g = (0.3440 − d<sub>002</sub>) / (0.3440 − 0.3354) × 100%</b></p>
<p>0.3440 nm is fully turbostratic carbon, 0.3354 nm is ideal graphite; their difference (0.0086 nm) is the
denominator. This tool always uses <b>d<sub>002</sub></b> and never the cell-parameter form c<sub>0</sub>/2
(numerically identical, d<sub>002</sub> = c<sub>0</sub>/2).</p>
<p>A 0.01° error in C(002) shifts g by roughly 0.15 percentage points — hence the internal standard.</p>

<h3>2. Si internal-standard 2θ correction</h3>
<ol>
<li>Mix Si powder (≈10–20 wt%) into the graphite, fill the holder, level and press gently; scan under the
same conditions as the sample.</li>
<li>Δ2θ = 2θ<sub>ref</sub> − 2θ<sub>obs</sub> from Si(111).</li>
<li>Apply the same Δ2θ to C(002) (and the La peak): 2θ<sub>corr</sub> = 2θ<sub>obs</sub> + Δ2θ.</li>
</ol>
<p>The Si(111) reference is computed from a = 0.54310205 nm and the chosen wavelength
(≈28.442° for Cu Kα1) and can be overridden with an instrument/ICDD value.</p>

<h3>3. Lc and La</h3>
<p style="font-size:15px;"><b>L = K λ / (β cosθ)</b> — β is the specimen FWHM <b>after</b> removing
instrumental broadening (radians).</p>
<ul>
<li><b>Lc</b> from C(002), K = 0.89;</li>
<li><b>La</b> preferably from <b>(110)</b> (2θ ≈ 77.5° for Cu Kα; scan <b>72–82°</b>), K = 1.84.
The <b>(100)</b> peak (2θ ≈ 42.4°, d ≈ 0.213 nm) is a fallback only and should be reported as an estimate.</li>
</ul>
<p>La requires hk0 reflections. (110) sits at high angle (better angular resolution) and is free of
overlapping graphite peaks in 72–82°; (100) is stronger but overlaps neighbouring 3-D reflections.</p>

<h3>4. Instrumental broadening (Si standard, wide-range scan)</h3>
<ol>
<li>Scan a pure Si (or LaB₆) standard over a wide range (e.g. 20–120°) with the same slits and step.</li>
<li>The tool matches the theoretical Si positions, fits each peak with pseudo-Voigt and returns the
instrumental FWHM vs 2θ.</li>
<li>Caglioti FWHM² = U·tan²θ + V·tanθ + W is fitted, giving the instrumental width at any angle.</li>
<li>Removal: quadrature √(β<sub>obs</sub>² − β<sub>inst</sub>²) (Gaussian-like) or direct subtraction
β<sub>obs</sub> − β<sub>inst</sub> (Lorentzian-like). Use one model consistently and state it in the report.</li>
</ol>

<h3>5. Recommended workflow</h3>
<ol>
<li>Prepare graphite + Si (internal standard) and a pure Si standard.</li>
<li>C(002): 24–30°, step ≤ 0.02°, dwell ≥ 1 s.</li>
<li>La peak: 72–82°, step ≤ 0.02°, dwell ≥ 2 s (weak peak).</li>
<li>Si standard: 20–120°, same conditions.</li>
<li>Tab 2: find peaks and fit FWHM. Tab 3: fit Caglioti. Tab 1: calculate and export.</li>
</ol>

<h3>6. Troubleshooting</h3>
<ul>
<li><b>g &lt; 0 or &gt; 100%</b>: wrong peak, reversed correction sign, or d<sub>002</sub> outside
0.3354–0.3440 nm.</li>
<li><b>Empty La</b>: La peak not entered, or its FWHM is not larger than the instrumental width.</li>
<li><b>La vs Lc inconsistent</b>: check that La used (110)/(100) and not (002).</li>
<li><b>Wavelength</b>: use Kα1 data for precise positions. Two Cu Kα1 values are provided
(1.5405929 CODATA, 1.54056 traditional) to reproduce legacy reports.</li>
</ul>

<h3>References</h3>
<ol style="font-size:12px;">
<li>Franklin R. E. <i>Acta Cryst.</i> 1951, 4, 253–261.</li>
<li>Iwashita N. et al. <i>Carbon</i> 2004, 42, 701–714 (standard procedure: K=0.89 for Lc, K=1.84 for La from (110)).</li>
<li>Warren B. E. <i>Phys. Rev.</i> 1941, 59, 693.</li>
<li>Zhang B. Determination of graphitization degree, Shimadzu Application Data Sheet AP_XRD-001 (Si internal standard example).</li>
</ol>
""",
    "ja": """
<h2>測定方法と判定基準</h2>
<p>入力はすべて<b>実測のピーク位置と半値幅</b>で、結果は波長・Scherrer 定数・幅補正モデルまで追跡できます。</p>

<h3>1. 黒鉛化度 g（面間隔表現）</h3>
<p style="font-size:15px;"><b>g = (0.3440 − d<sub>002</sub>) / (0.3440 − 0.3354) × 100%</b></p>
<p>0.3440 nm は完全な乱層構造、0.3354 nm は理想黒鉛。本ツールは <b>d<sub>002</sub></b> 表現に統一し、
格子定数 c<sub>0</sub>/2 の表記は用いません（数値は等価）。</p>
<p>C(002) の 0.01° の誤差は g の約 0.15 ポイントに相当するため、内部標準が必須です。</p>

<h3>2. Si 内部標準による 2θ 補正</h3>
<ol>
<li>黒鉛に Si 粉末（10–20 wt% 程度）を混合し、同条件で走査。</li>
<li>Δ2θ = 2θ<sub>ref</sub> − 2θ<sub>obs</sub>（Si(111)）。</li>
<li>C(002)（および La ピーク）に同じ Δ2θ を適用。</li>
</ol>
<p>Si(111) の標準値は a = 0.54310205 nm と波長から Bragg 式で算出（Cu Kα1 で約 28.442°）。
装置・ICDD の値で上書き可能です。</p>

<h3>3. Lc と La</h3>
<p style="font-size:15px;"><b>L = K λ / (β cosθ)</b>（β は<b>装置幅を除いた後</b>の半値幅、ラジアン）</p>
<ul>
<li><b>Lc</b>：C(002)、K = 0.89；</li>
<li><b>La</b>：<b>(110)</b> を優先（Cu Kα で 2θ ≈ 77.5°、<b>72–82°</b> まで走査）、K = 1.84。
<b>(100)</b>（2θ ≈ 42.4°、d ≈ 0.213 nm）は代替で、推定値として報告してください。</li>
</ul>
<p>La は hk0 反射が必要です。(110) は高角で角度分解能が高く、72–82° に重なりがありません。</p>

<h3>4. 装置幅の除去（Si 標準・広角走査）</h3>
<ol>
<li>純 Si（または LaB₆）標準を広角（例 20–120°）で、同一スリット・同一ステップで走査。</li>
<li>理論位置に合わせて各ピークを pseudo-Voigt でフィットし、装置 FWHM を得る。</li>
<li>Caglioti 式 FWHM² = U·tan²θ + V·tanθ + W をフィットし任意角へ外挿。</li>
<li>除去：二乗差 √(β<sub>obs</sub>² − β<sub>inst</sub>²) または単純差 β<sub>obs</sub> − β<sub>inst</sub>。
同一試料群では同一モデルを用い、レポートに明記。</li>
</ol>

<h3>5. 推奨手順</h3>
<ol>
<li>黒鉛 + Si（内部標準）、および純 Si 標準を準備。</li>
<li>C(002)：24–30°、ステップ ≤0.02°、滞留 ≥1 s。</li>
<li>La ピーク：72–82°、ステップ ≤0.02°、滞留 ≥2 s。</li>
<li>Si 標準：20–120°、同条件。</li>
<li>タブ②でピーク探索、タブ③で Caglioti、タブ①で計算・出力。</li>
</ol>

<h3>6. よくある問題</h3>
<ul>
<li><b>g &lt; 0 または &gt; 100%</b>：ピーク誤認、補正符号の逆転、d<sub>002</sub> が範囲外。</li>
<li><b>La が空</b>：La ピーク未入力、または実測 FWHM が装置幅以下。</li>
<li><b>La と Lc が不整合</b>：La に (002) を使っていないか確認。</li>
<li><b>波長</b>：精密な位置には Kα1 を使用。Cu Kα1 は 1.5405929（CODATA）と 1.54056（従来値）を用意。</li>
</ul>

<h3>参考文献</h3>
<ol style="font-size:12px;">
<li>Franklin R. E. <i>Acta Cryst.</i> 1951, 4, 253–261.</li>
<li>Iwashita N. et al. <i>Carbon</i> 2004, 42, 701–714.</li>
<li>Warren B. E. <i>Phys. Rev.</i> 1941, 59, 693.</li>
<li>章斌「黒鉛化度の測定」島津アプリケーションデータ AP_XRD-001.</li>
</ol>
""",
}


_HINT_HTML: dict[str, str] = {
    "zh": """
<h2>测试与计算要点</h2>
<p>XRD 测试分两段扫描完成：低角段测石墨化度，高角段测 L<sub>a</sub>；仪器宽化另用
NIST 硅标样单独标定。以下为本工具的默认计算链与适用边界。</p>

<h3>一、扫描方案</h3>
<table width="100%" border="0" cellspacing="0" cellpadding="6">
<tr>
<td style="background-color:#eef4fb; border-bottom:1px solid #c9d8e8;"><b>段次</b></td>
<td style="background-color:#eef4fb; border-bottom:1px solid #c9d8e8;"><b>2θ 范围</b></td>
<td style="background-color:#eef4fb; border-bottom:1px solid #c9d8e8;"><b>采集内容</b></td>
<td style="background-color:#eef4fb; border-bottom:1px solid #c9d8e8;"><b>用途</b></td></tr>
<tr>
<td>① 低角段</td><td>25–29.5°</td><td>C(002) 与 Si(111)<br>（样品混入硅粉内标）</td>
<td>硅内标校正 C(002) 峰位 → 层间距 d<sub>002</sub>、石墨化度 g</td></tr>
<tr>
<td style="background-color:#f7fafd;">② 高角段</td><td style="background-color:#f7fafd;">72–82°</td>
<td style="background-color:#f7fafd;">C(110)</td>
<td style="background-color:#f7fafd;">Scherer 式计算碳网平面微晶尺寸 L<sub>a</sub></td></tr>
<tr>
<td>③ 标样</td><td>20–90°</td><td>NIST 硅标样<br>（单独测试，不混样）</td>
<td>拟合 Caglioti 函数，得仪器宽化随 2θ 的变化关系</td></tr>
</table>

<h3>二、计算链</h3>
<ul>
<li><b>布拉格</b>：d<sub>002</sub> = λ / (2 sin θ<sub>002</sub>)，θ 取校正后 2θ 的一半；</li>
<li><b>Franklin</b>：g = (0.3440 − d<sub>002</sub>) / (0.3440 − 0.3354) × 100%；</li>
<li><b>Scherer</b>：L<sub>c</sub> = 0.89 λ / (β<sub>002</sub> cos θ<sub>002</sub>)、
L<sub>a</sub> = 1.84 λ / (β<sub>110</sub> cos θ<sub>110</sub>)；
β 为衍射峰半高宽，计算时换算为弧度。</li>
</ul>

<h3>三、仪器宽化扣除</h3>
<p>假设衍射峰为洛伦兹型，按 β = β<sub>obs</sub> − β<sub>inst</sub> 直接相减；工具另提供
高斯平方差 √(β<sub>obs</sub>² − β<sub>inst</sub>²) 备选，同一批样品须固定同一模型。
Si 标样 20–90° 覆盖 Si(331)（≈76.37°），与石墨 (110)（≈77.5°）几乎同位，
该处仪器宽化可直接近邻取值，不必外推。</p>

<h3>四、适用边界</h3>
<p>本计算<b>未分离微观应变宽化</b>，L<sub>c</sub>、L<sub>a</sub> 用于<b>样品间对比</b>，
不作为绝对晶粒尺寸报出。同一批样品须固定辐射、K 值、宽化扣除模型与扫描条件。</p>

<h3>五、辐射与波长</h3>
<p>Cu Kα，λ = 0.15406 nm。工具内置 1.5405929 nm（CODATA）与 1.54056 nm（传统仪器软件值），
亦可自定义；波长取值影响 g 的末位，跨批次对比时须统一。</p>
""",
    "en": """
<h2>Test and calculation summary</h2>
<p>The measurement is split into two scan ranges — low angle for the graphitization degree, high angle
for L<sub>a</sub>. Instrumental broadening is calibrated separately on a NIST Si standard.
Below is the default calculation chain and where it stops being valid.</p>

<h3>1. Scan plan</h3>
<table width="100%" border="0" cellspacing="0" cellpadding="6">
<tr style="background-color:#eef4fb;">
<td><b>Step</b></td><td><b>2θ range</b></td><td><b>Collected</b></td><td><b>Purpose</b></td></tr>
<tr>
<td>① Low angle</td><td>25–29.5°</td><td>C(002) and Si(111)<br>(Si powder mixed into the sample)</td>
<td>Internal-standard correction of C(002) → d<sub>002</sub>, graphitization degree g</td></tr>
<tr style="background-color:#f7fafd;">
<td>② High angle</td><td>72–82°</td><td>C(110)</td>
<td>In-plane crystallite size L<sub>a</sub> by the Scherer equation</td></tr>
<tr>
<td>③ Standard</td><td>20–90°</td><td>NIST Si standard<br>(scanned separately, not mixed)</td>
<td>Caglioti fit → instrumental broadening versus 2θ</td></tr>
</table>

<h3>2. Calculation chain</h3>
<ul>
<li><b>Bragg</b>: d<sub>002</sub> = λ / (2 sin θ<sub>002</sub>), θ taken from the corrected 2θ;</li>
<li><b>Franklin</b>: g = (0.3440 − d<sub>002</sub>) / (0.3440 − 0.3354) × 100%;</li>
<li><b>Scherer</b>: L<sub>c</sub> = 0.89 λ / (β<sub>002</sub> cos θ<sub>002</sub>),
L<sub>a</sub> = 1.84 λ / (β<sub>110</sub> cos θ<sub>110</sub>);
β is the FWHM, converted to radians.</li>
</ul>

<h3>3. Removing instrumental broadening</h3>
<p>The profile is assumed Lorentzian, so β = β<sub>obs</sub> − β<sub>inst</sub> is subtracted directly;
Gaussian quadrature √(β<sub>obs</sub>² − β<sub>inst</sub>²) is offered as an alternative — use one model
for a whole sample set. A 20–90° Si standard includes Si(331) (≈76.37°), almost coincident with
graphite (110) (≈77.5°), so the instrumental width there needs no extrapolation.</p>

<h3>4. Validity limits</h3>
<p><b>Micro-strain broadening is not separated.</b> L<sub>c</sub> and L<sub>a</sub> are intended for
<b>comparison between samples</b>, not as absolute crystallite sizes. Keep radiation, K values,
broadening model and scan conditions identical within a sample set.</p>

<h3>5. Radiation and wavelength</h3>
<p>Cu Kα, λ = 0.15406 nm. 1.5405929 nm (CODATA) and 1.54056 nm (traditional instrument value) are
built in, and a custom value may be entered; the choice shifts the last digit of g, so keep it fixed
across batches.</p>
""",
    "ja": """
<h2>測定・計算の要点</h2>
<p>XRD 測定は 2 段のスキャンで行います。低角側で黒鉛化度、高角側で L<sub>a</sub> を求め、
装置幅は NIST ケイ素標準試料で別途校正します。以下は本ツールの既定の計算手順と適用範囲です。</p>

<h3>1. スキャン計画</h3>
<table width="100%" border="0" cellspacing="0" cellpadding="6">
<tr style="background-color:#eef4fb;">
<td><b>段</b></td><td><b>2θ 範囲</b></td><td><b>取得する反射</b></td><td><b>用途</b></td></tr>
<tr>
<td>① 低角</td><td>25–29.5°</td><td>C(002) と Si(111)<br>（試料に Si 粉末を内標として混合）</td>
<td>Si 内部標準で C(002) を補正 → 面間隔 d<sub>002</sub>、黒鉛化度 g</td></tr>
<tr style="background-color:#f7fafd;">
<td>② 高角</td><td>72–82°</td><td>C(110)</td>
<td>Scherer 式により網面方向の微結晶子径 L<sub>a</sub></td></tr>
<tr>
<td>③ 標準</td><td>20–90°</td><td>NIST ケイ素標準<br>（単独測定、混合しない）</td>
<td>Caglioti 関数のフィット → 装置幅の 2θ 依存性</td></tr>
</table>

<h3>2. 計算の流れ</h3>
<ul>
<li><b>Bragg</b>：d<sub>002</sub> = λ / (2 sin θ<sub>002</sub>)。θ は補正後の 2θ の半分；</li>
<li><b>Franklin</b>：g = (0.3440 − d<sub>002</sub>) / (0.3440 − 0.3354) × 100%；</li>
<li><b>Scherer</b>：L<sub>c</sub> = 0.89 λ / (β<sub>002</sub> cos θ<sub>002</sub>)、
L<sub>a</sub> = 1.84 λ / (β<sub>110</sub> cos θ<sub>110</sub>)。
β は半値幅で、計算時にラジアンへ換算。</li>
</ul>

<h3>3. 装置幅の除去</h3>
<p>回折ピークをローレンツ型と仮定し、β = β<sub>obs</sub> − β<sub>inst</sub> の差し引きで除去します
（ガウス二乗差 √(β<sub>obs</sub>² − β<sub>inst</sub>²) も選択可）。同一試料群では同じモデルに統一して
ください。20–90° の Si 標準には Si(331)（≈76.37°）が含まれ、黒鉛 (110)（≈77.5°）とほぼ同一位置
のため、この角度の装置幅は外挿せずに近傍値を使えます。</p>

<h3>4. 適用範囲</h3>
<p>本計算は<b>微小ひずみによる広がりを分離していません</b>。L<sub>c</sub>、L<sub>a</sub> は
<b>試料間の比較</b>に用いるもので、絶対的な結晶子径として報告しないでください。同一試料群では
線源、K 値、幅補正モデル、測定条件を固定してください。</p>

<h3>5. 線源と波長</h3>
<p>Cu Kα、λ = 0.15406 nm。1.5405929 nm（CODATA）と 1.54056 nm（従来の装置ソフト値）を内蔵し、
任意値も入力できます。波長は g の末尾桁に効くため、バッチ間で統一してください。</p>
""",
}


def hint_html() -> str:
    """当前语言的「测试与计算要点」提示 HTML。"""
    return _HINT_HTML.get(_current) or _HINT_HTML["zh"]


def method_html() -> str:
    """当前语言的「方法与判据」页 HTML。"""
    return _METHOD_HTML.get(_current) or _METHOD_HTML["zh"]


def set_language(lang: str) -> None:
    """切换当前语言（未知代码忽略）。"""
    global _current
    if lang in TABLE:
        _current = lang


def current_language() -> str:
    return _current


def tr(key: str, **kw) -> str:
    """取当前语言的字符串；缺失时返回 ⟪key⟫ 标记（不回退，便于暴露漏译）。"""
    if key == "method.html":
        return method_html()
    if key == "hint.html":
        return hint_html()
    s = TABLE.get(_current, {}).get(key)
    if s is None:
        return f"⟪{key}⟫"
    return s.format(**kw) if kw else s
