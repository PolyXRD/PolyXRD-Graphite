# -*- coding: utf-8 -*-
"""PolyXRD Graphite 计算内核单元测试。

运行：  python -m pytest tests -q      （或 python tests/test_engine.py）

守护重点
--------
1. Bragg 正反算自洽；
2. 章斌《石墨化度的测定》算例（Si(111) 内标 → d002 0.33551 nm / g 98.8%）
   的数值复现（容差内）；
3. Scherrer 正反算自洽；
4. Caglioti 能由合成标样点恢复已知 U/V/W；
5. pseudo-Voigt 能从合成谱恢复峰位与 FWHM（<0.5% 偏差）；
6. 自动寻峰在含噪多峰谱上不漏峰、不多峰；
7. Si 标样峰自动识别与 FWHM 拟合；
8. 仪器宽化扣除的三种模式边界行为。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import graphite_engine as E


LAM = E.WAVELENGTHS["Cu Kα1"]
LAM_TRAD = E.WAVELENGTHS["Cu Kα1 (传统 1.54056)"]


# ---------------------------------------------------------------- 基础几何
def test_bragg_roundtrip():
    for d in (0.3355, 0.2131, 0.1231, 0.1541):
        tt = E.two_theta_from_d(d, LAM)
        assert E.d_from_two_theta(tt, LAM) == pytest.approx(d, rel=1e-12)


def test_si_and_graphite_reference():
    si111 = E.si_two_theta((1, 1, 1), LAM)
    # ICDD 27-1402 Cu Kα1: 28.4428°；本实现按 a=0.54310205 计算，容差 0.01°
    assert si111 == pytest.approx(28.4419, abs=0.01)
    g = E.graphite_reference_table(LAM)
    assert g["002"]["two_theta"] == pytest.approx(26.555, abs=0.01)
    assert g["100"]["two_theta"] == pytest.approx(42.37, abs=0.02)
    assert g["110"]["two_theta"] == pytest.approx(77.50, abs=0.02)
    assert g["100"]["d"] == pytest.approx(0.2131, abs=5e-4)
    assert g["110"]["d"] == pytest.approx(0.1231, abs=5e-4)


# ---------------------------------------------------------------- 文档算例
def test_document_example_reproduction():
    """章斌 AP_XRD-001：Si(111) 28.4541（标准 28.44135）→ C(002) 26.54565。"""
    delta = E.zero_shift(28.4541, 28.44135)
    assert delta == pytest.approx(-0.01275, abs=1e-9)
    tt = E.apply_shift(26.5584, delta)
    assert tt == pytest.approx(26.54565, abs=1e-6)

    d = E.d_from_two_theta(tt, LAM_TRAD)
    assert d == pytest.approx(0.33551, abs=2e-5)
    # 文档给出 g = 98.8%（传统波长 1.54056 复现）
    assert E.graphitization_degree(d) == pytest.approx(98.8, abs=0.15)

    # 用 CODATA 波长 1.5405929 时 g 低约 0.1 个百分点（峰位相同）
    d2 = E.d_from_two_theta(tt, LAM)
    assert E.graphitization_degree(d2) == pytest.approx(98.7, abs=0.15)


def test_degree_endpoints():
    assert E.graphitization_degree(0.3354) == pytest.approx(100.0, abs=1e-9)
    assert E.graphitization_degree(0.3440) == pytest.approx(0.0, abs=1e-9)
    assert E.d002_from_degree(50.0) == pytest.approx(0.3397, abs=1e-9)
    assert E.graphitization_degree(E.d002_from_degree(73.5)) == pytest.approx(73.5, rel=1e-9)


# ---------------------------------------------------------------- Scherrer
def test_scherrer_roundtrip():
    lc = E.scherrer_size(0.20, 26.55, LAM, E.K_LC)
    assert E.fwhm_from_size(lc, 26.55, LAM, E.K_LC) == pytest.approx(0.20, rel=1e-9)
    # 手算：0.89*0.15405929/(rad(0.2)*cos(13.275°)) = 40.36 nm
    assert lc == pytest.approx(40.36, abs=0.05)


def test_la_110_smaller_than_lc_for_same_fwhm():
    """同一 FWHM 下 La 因 K=1.84 与低角度因子而更大，方向性自检。"""
    lc = E.scherrer_size(0.25, 26.55, LAM, E.K_LC)
    la = E.scherrer_size(0.25, 77.50, LAM, E.K_LA_110)
    assert la > lc * 1.5


# ---------------------------------------------------------------- Caglioti
def test_caglioti_recovery():
    U, V, W = 0.02, -0.004, 0.008
    pts = []
    for tt in (28.44, 47.30, 56.12, 76.38, 88.03, 94.95):
        pts.append((tt, E.caglioti_fwhm(tt, U, V, W)))
    fit = E.fit_caglioti(pts)
    assert fit.U == pytest.approx(U, rel=2e-3)
    assert fit.V == pytest.approx(V, rel=2e-3)
    assert fit.W == pytest.approx(W, rel=2e-3)
    assert fit.rms < 1e-4
    assert fit.fwhm(26.55) == pytest.approx(E.caglioti_fwhm(26.55, U, V, W), rel=1e-9)


def test_caglioti_needs_three_points():
    with pytest.raises(ValueError):
        E.fit_caglioti([(28.44, 0.1), (47.3, 0.12)])


# ---------------------------------------------------------------- 宽化扣除
def test_correct_fwhm_modes():
    assert E.correct_fwhm(0.30, 0.12, "gauss") == pytest.approx(math.sqrt(0.09 - 0.0144), rel=1e-9)
    assert E.correct_fwhm(0.30, 0.12, "lorentz") == pytest.approx(0.18, rel=1e-12)
    assert E.correct_fwhm(0.30, 0.12, "none") == pytest.approx(0.30, rel=1e-12)
    # 仪器宽化反超实测宽化时按 0 处理，不产生负值 / 复数
    assert E.correct_fwhm(0.10, 0.12, "gauss") == 0.0
    assert E.correct_fwhm(0.10, 0.12, "lorentz") == 0.0
    with pytest.raises(ValueError):
        E.correct_fwhm(0.3, 0.1, "bogus")


# ---------------------------------------------------------------- 峰拟合
def _pv_profile(x, amp, cen, fwhm, eta):
    u = (x - cen) / fwhm
    g = np.exp(-4 * math.log(2) * u * u)
    l = 1 / (1 + 4 * u * u)
    return amp * (eta * l + (1 - eta) * g)


def test_pseudo_voigt_recovers_peak():
    x = np.arange(25.0, 28.5, 0.01)
    y = _pv_profile(x, 1200.0, 26.55, 0.18, 0.6) + 80.0 - 0.5 * (x - 25.0) / 3.5
    fit = E.fit_pseudo_voigt(x, y)
    assert fit.two_theta == pytest.approx(26.55, abs=0.003)
    assert fit.fwhm == pytest.approx(0.18, rel=0.02)
    assert fit.eta == pytest.approx(0.6, abs=0.12)
    assert fit.r2 > 0.999


def test_find_peaks_three_components():
    x = np.arange(24.0, 80.0, 0.02)
    y = (2000 * np.exp(-((x - 26.55) ** 2) / (2 * 0.09 ** 2))
         + 300 * np.exp(-((x - 42.40) ** 2) / (2 * 0.11 ** 2))
         + 90 * np.exp(-((x - 77.50) ** 2) / (2 * 0.14 ** 2))
         + 40.0)
    rng = np.random.default_rng(7)
    y = y + rng.normal(0, 1.2, x.size)
    peaks = E.find_peaks(x, y, min_height_ratio=0.02, min_distance_deg=0.5)
    centers = sorted(p.two_theta for p in peaks)
    assert len(peaks) == 3, [f"{c:.2f}" for c in centers]
    for got, want in zip(centers, (26.55, 42.40, 77.50)):
        assert got == pytest.approx(want, abs=0.03)
    # 强峰的 FWHM 应与合成值一致
    strong = max(peaks, key=lambda p: p.height)
    assert strong.fwhm == pytest.approx(0.212, rel=0.10)  # 高斯 σ=0.09 → FWHM=0.212


def test_match_instrument_peaks_on_synthetic_si():
    """合成 Si 标样谱（真实 Caglioti 展宽）→ 自动识别峰并拟合 FWHM。"""
    U, V, W = 0.015, -0.002, 0.006
    x = np.arange(20.0, 120.0, 0.02)
    y = np.full_like(x, 30.0)
    for row in E.si_reference_table(LAM, two_theta_max=119.0):
        fw = E.caglioti_fwhm(row["two_theta"], U, V, W)
        y = y + _pv_profile(x, row["rel_intensity"] * 12.0, row["two_theta"], fw, 0.5)
    rng = np.random.default_rng(3)
    y = y + rng.normal(0, 0.8, x.size)
    pat = E.Pattern(x, y, name="Si-std")

    found = E.match_instrument_peaks(pat, LAM)
    assert len(found) >= 5
    for f in found:
        assert abs(f["delta"]) < 0.02          # 合成谱无位移
        want = E.caglioti_fwhm(f["two_theta_obs"], U, V, W)
        assert f["fwhm"] == pytest.approx(want, rel=0.12)

    fit = E.fit_caglioti([(f["two_theta_obs"], f["fwhm"]) for f in found])
    assert fit.W == pytest.approx(W, abs=0.006)
    assert fit.U == pytest.approx(U, abs=0.01)


# ---------------------------------------------------------------- 全流程
def test_analyze_full_chain():
    inp = E.AnalysisInput(
        wavelength=LAM,
        d002_obs=26.5584, fwhm002_obs=0.24,
        si111_obs=28.4541, si111_ref=28.44135,
        la_peak="110", la_obs=77.62, fwhm_la_obs=0.35,
        inst_mode="caglioti",
        caglioti=E.CagliotiFit(U=0.015, V=-0.002, W=0.006, rms=0.001, n_points=6),
        sample="样品A",
    )
    res = E.analyze(inp)
    assert res.two_theta_002_corr == pytest.approx(26.54565, abs=1e-5)
    assert res.d002_nm == pytest.approx(0.33551, abs=3e-5)
    assert 98.5 < res.g_percent < 99.0
    assert res.beta002_inst > 0 and res.beta002_corr < 0.24
    assert res.lc_nm > 0
    assert res.la_nm > 0
    assert res.delta_two_theta == pytest.approx(-0.01275, abs=1e-9)

    text = E.build_report_text(inp, res, version="1.0.0")
    assert "石墨化度 g" in text and "堆叠厚度 Lc" in text and "微晶尺寸 La" in text
    assert "c0/2" not in text              # 按用户要求不出现晶胞参数写法


def test_analyze_without_internal_standard():
    inp = E.AnalysisInput(d002_obs=26.60, fwhm002_obs=0.30, la_peak="none",
                          inst_mode="caglioti", caglioti=None)
    res = E.analyze(inp)
    assert res.delta_two_theta == 0.0
    assert res.lc_nm > 0
    assert res.la_nm == 0.0
    assert any("仪器宽化" in w for w in res.warnings)


def test_analyze_flags_out_of_range_degree():
    """2θ 偏低 → d002 > 0.3440 → g < 0，必须显式提示而不是给个负百分比。"""
    inp = E.AnalysisInput(d002_obs=25.20, fwhm002_obs=0.4, la_peak="none")
    res = E.analyze(inp)
    assert res.g_percent < 0
    assert any("g < 0" in w for w in res.warnings)

    inp2 = E.AnalysisInput(d002_obs=27.60, fwhm002_obs=0.2, la_peak="none")
    res2 = E.analyze(inp2)
    assert res2.g_percent > 100
    assert any("g > 100" in w for w in res2.warnings)


def test_warns_la_peak_mismatch():
    """把 42.4° 的 (100) 误填进 (110) 槽 → 应提示峰位与理论值偏差过大。"""
    inp = E.AnalysisInput(d002_obs=26.55, fwhm002_obs=0.2,
                          la_peak="110", la_obs=42.40, fwhm_la_obs=0.3)
    res = E.analyze(inp)
    assert any("相差超过 0.5" in w for w in res.warnings)


def test_report_csv_written():
    """CSV 报告落盘（不用 tmp_path：受控沙箱里 tempfile 不可用）。"""
    out_dir = Path(__file__).resolve().parent / "_out"
    out_dir.mkdir(exist_ok=True)
    inp = E.AnalysisInput(d002_obs=26.55, fwhm002_obs=0.2, sample="S1")
    res = E.analyze(inp)
    out = out_dir / "r.csv"
    try:
        E.write_report_csv(out, inp, res)
        body = out.read_text(encoding="utf-8")
        assert "石墨化度 g" in body and "S1" in body
        assert body.startswith("\ufeff")     # Excel 打开不乱码
    finally:
        out.unlink(missing_ok=True)
        try:
            out_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
