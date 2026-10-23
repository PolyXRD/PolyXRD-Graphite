# -*- coding: utf-8 -*-
"""PolyXRD Graphite 计算内核（纯 numpy + stdlib，不依赖 Qt）。

覆盖石墨材料 XRD 的三项核心指标与配套校正：

1. **石墨化度 g**（Franklin 式，以层间距 d002 表达）::

       g = (0.3440 - d002) / (0.3440 - 0.3354) x 100%

   等价于文献中的晶胞参数写法 g = (0.3440 - c0/2) / 0.0086 x 100%，
   本工具按用户要求统一以 d002 表达，界面与报告不再出现 c0/2。

2. **Lc（堆叠厚度）**：Scherrer 式，K = 0.89，用 C(002) 半高宽。

3. **La（微晶尺寸，面内）**：Scherrer 式，K = 1.84，**优先用 (110)** 峰
   （Cu Kα 时 2θ ≈ 77.5°，需扫到 72–82°）；条件不足时退用 (100) 峰
   （2θ ≈ 42.4°，d ≈ 0.213 nm）。

配套校正：

* **Si 内标 2θ 校正**：Δ2θ = 2θ(Si, 标准) - 2θ(Si, 实测)，平移校正待测峰。
* **仪器宽化扣除**：由 Si 标样全角度谱反算 Caglioti 系数 U/V/W，再按
  高斯（平方差）或洛伦兹（直接相减）模型扣除仪器半高宽。
* **寻峰与 pseudo-Voigt 拟合**：从实测谱自动给出峰位 / FWHM / 峰高。

常数取值与依据
--------------
* d002 上下限 0.3440 nm（完全未石墨化）/ 0.3354 nm（理想石墨）：
  Franklin, *Acta Cryst.* 1951, 4, 253；Maire & Méring 的同一表达式。
* K(Lc)=0.89、K(La)=1.84：Iwashita N. et al., *Carbon* 2004, 42, 701–714
  （碳材料 XRD 标准测定规程）；Warren, *Phys. Rev.* 1941, 59, 693（hk 带）。
* Si 晶格常数 a = 0.54310205 nm、石墨 a = 0.24612 nm：
  ICDD/COD 常用值，用于生成理论 2θ 参照位（可由界面覆盖）。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

# ------------------------------------------------------------------------------
# 物理常数与材料参数
# ------------------------------------------------------------------------------
#: 常用靶材波长（nm）。Kα1 用于精确峰位；Kα 平均用于常规扫描的峰位近似。
#: 1.5405929 为 CODATA / Deslattes 推荐的 Cu Kα1 值；1.54056 为仪器软件
#: 长期沿用的传统值（岛津等厂商默认），两者使 g 相差约 0.1 个百分点，
#: 因此单独列出供复现既有报告。
WAVELENGTHS: dict[str, float] = {
    "Cu Kα1": 0.15405929,
    "Cu Kα1 (传统 1.54056)": 0.15405600,
    "Cu Kα2": 0.15444274,
    "Cu Kα (平均)": 0.15418380,
    "Co Kα1": 0.17889650,
    "Mo Kα1": 0.07093000,
    "Fe Kα1": 0.19360420,
    "Cr Kα1": 0.22897000,
}
DEFAULT_WAVELENGTH_KEY = "Cu Kα1"

#: Si 晶格常数（nm）
SI_A = 0.54310205
#: 石墨 a 轴（nm）
GRAPHITE_A = 0.246120

#: 层间距两端点（nm）：完全未石墨化 / 理想石墨
D002_DISORDERED = 0.3440
D002_IDEAL = 0.3354
#: Franklin 式分母（= D002_DISORDERED - D002_IDEAL）
D002_SPAN = 0.0086

#: Scherrer 常数
K_LC = 0.89
K_LA_110 = 1.84
K_LA_100 = 1.84

#: 推荐 (110) 扫描区间（2θ，Cu Kα）
TT_110_WINDOW = (72.0, 82.0)

#: Si 允许的反射（hkl）与粗略相对强度（仅用于标样峰识别排序）
_SI_HKL = (
    ((1, 1, 1), 100.0),
    ((2, 2, 0), 55.0),
    ((3, 1, 1), 30.0),
    ((4, 0, 0), 6.0),
    ((3, 3, 1), 11.0),
    ((4, 2, 2), 12.0),
    ((5, 1, 1), 6.0),
    ((4, 4, 0), 3.0),
    ((5, 3, 1), 7.0),
    ((6, 2, 0), 4.0),
    ((5, 3, 3), 2.0),
)


# ------------------------------------------------------------------------------
# 基础衍射几何
# ------------------------------------------------------------------------------
def d_from_two_theta(two_theta_deg: float, wavelength_nm: float) -> float:
    """Bragg：由 2θ(°) 与波长(nm) 求面间距 d(nm)。"""
    theta = math.radians(two_theta_deg / 2.0)
    s = math.sin(theta)
    if s <= 0:
        raise ValueError("2θ 必须为正")
    return wavelength_nm / (2.0 * s)


def two_theta_from_d(d_nm: float, wavelength_nm: float) -> float:
    """Bragg：由面间距 d(nm) 与波长(nm) 求 2θ(°)。"""
    if d_nm <= 0:
        raise ValueError("d 必须为正")
    s = wavelength_nm / (2.0 * d_nm)
    if s >= 1.0:
        raise ValueError("该 d 值超出此波长可观测范围")
    return 2.0 * math.degrees(math.asin(s))


def _cubic_d(hkl: Sequence[int], a: float) -> float:
    h, k, l = hkl
    s = h * h + k * k + l * l
    return a / math.sqrt(s)


def _hex_d(hkl: Sequence[int], a: float, c: float) -> float:
    """六方晶系面间距。"""
    h, k, l = hkl
    inv_d2 = (4.0 / 3.0) * (h * h + h * k + k * k) / (a * a) + (l * l) / (c * c)
    return 1.0 / math.sqrt(inv_d2)


def si_two_theta(hkl: Sequence[int], wavelength_nm: float, a: float = SI_A) -> float:
    """Si（金刚石立方，Fd-3m）某反射的理论 2θ(°)。"""
    return two_theta_from_d(_cubic_d(hkl, a), wavelength_nm)


def graphite_two_theta(hkl: Sequence[int], wavelength_nm: float,
                       a: float = GRAPHITE_A, c: float = 2 * D002_IDEAL) -> float:
    """石墨（六方，P6₃/mmc）某反射的理论 2θ(°)。"""
    return two_theta_from_d(_hex_d(hkl, a, c), wavelength_nm)


def si_reference_table(wavelength_nm: float, a: float = SI_A,
                       two_theta_max: float = 130.0) -> list[dict]:
    """Si 标样理论峰表（按 2θ 升序），供内标校正 / 仪器宽化峰识别。"""
    rows = []
    for hkl, rel in _SI_HKL:
        try:
            tt = si_two_theta(hkl, wavelength_nm, a)
        except ValueError:
            continue
        if tt > two_theta_max:
            continue
        rows.append({
            "hkl": "".join(str(v) for v in hkl),
            "d": _cubic_d(hkl, a),
            "two_theta": tt,
            "rel_intensity": rel,
        })
    rows.sort(key=lambda r: r["two_theta"])
    return rows


def graphite_reference_table(wavelength_nm: float,
                            a: float = GRAPHITE_A,
                            d002: float = D002_IDEAL) -> dict[str, dict]:
    """石墨关键反射的理论值（002 / 100 / 110）。"""
    c = 2.0 * d002
    out = {}
    for name, hkl in (("002", (0, 0, 2)), ("100", (1, 0, 0)), ("110", (1, 1, 0))):
        d = _hex_d(hkl, a, c)
        out[name] = {
            "hkl": name,
            "d": d,
            "two_theta": two_theta_from_d(d, wavelength_nm),
        }
    return out


# ------------------------------------------------------------------------------
# 内标（2θ）校正
# ------------------------------------------------------------------------------
def zero_shift(si_obs: float, si_ref: float) -> float:
    """单点内标：待测谱整体 2θ 平移量 Δ = 标准 - 实测（°）。"""
    return float(si_ref) - float(si_obs)


def apply_shift(two_theta_obs: float, delta: float) -> float:
    """对待测峰施加平移校正。"""
    return float(two_theta_obs) + float(delta)


def fit_linear_calibration(pairs: Iterable[tuple[float, float]]) -> tuple[float, float, float]:
    """多点内标线性校正：2θ_corr = a + b·2θ_obs。

    pairs 为 (实测 2θ, 标准 2θ) 序列；返回 (a, b, rms)。点数 < 2 时
    退化为纯平移（b=1）。用于 Si 全角度谱同时含多个峰、可分离
    零点位移与角度比例误差的场合。
    """
    arr = np.asarray(list(pairs), dtype=float)
    if arr.ndim != 2 or arr.shape[0] == 0:
        raise ValueError("至少需要一个内标点")
    if arr.shape[0] == 1:
        a = arr[0, 1] - arr[0, 0]
        return float(a), 1.0, 0.0
    x, y = arr[:, 0], arr[:, 1]
    b, a = np.polyfit(x, y, 1)
    rms = float(np.sqrt(np.mean((a + b * x - y) ** 2)))
    return float(a), float(b), rms


# ------------------------------------------------------------------------------
# 石墨化度 / 晶粒尺寸
# ------------------------------------------------------------------------------
def graphitization_degree(d002_nm: float) -> float:
    """Franklin 石墨化度 g（%），以 d002 表达。"""
    g = (D002_DISORDERED - float(d002_nm)) / D002_SPAN * 100.0
    return g


def d002_from_degree(g_percent: float) -> float:
    """由石墨化度反算 d002(nm)（用于校核与作图）。"""
    return D002_DISORDERED - float(g_percent) / 100.0 * D002_SPAN


def scherrer_size(fwhm_deg: float, two_theta_deg: float,
                  wavelength_nm: float, K: float) -> float:
    """Scherrer 晶粒尺寸 L = Kλ / (β cosθ)，返回 nm。

    fwhm_deg 为**已扣除仪器宽化**的样品半高宽（°），内部转为弧度。
    """
    beta = math.radians(float(fwhm_deg))
    if beta <= 0:
        raise ValueError("半高宽必须为正")
    theta = math.radians(float(two_theta_deg) / 2.0)
    return K * wavelength_nm / (beta * math.cos(theta))


def fwhm_from_size(size_nm: float, two_theta_deg: float,
                   wavelength_nm: float, K: float) -> float:
    """Scherrer 反算：由尺寸(nm)给出理论半高宽(°)。"""
    if size_nm <= 0:
        raise ValueError("尺寸必须为正")
    theta = math.radians(float(two_theta_deg) / 2.0)
    beta = K * wavelength_nm / (size_nm * math.cos(theta))
    return math.degrees(beta)


# ------------------------------------------------------------------------------
# 仪器宽化：Caglioti 拟合与扣除
# ------------------------------------------------------------------------------
def caglioti_fwhm(two_theta_deg: float, U: float, V: float, W: float) -> float:
    """Caglioti 式：FWHM² = U·tan²θ + V·tanθ + W，返回 FWHM(°)。"""
    t = math.tan(math.radians(two_theta_deg / 2.0))
    val = U * t * t + V * t + W
    return math.sqrt(val) if val > 0 else 0.0


@dataclass(frozen=True)
class CagliotiFit:
    U: float
    V: float
    W: float
    rms: float
    n_points: int

    def fwhm(self, two_theta_deg: float) -> float:
        return caglioti_fwhm(two_theta_deg, self.U, self.V, self.W)

    def as_text(self) -> str:
        return (f"U={self.U:.6f}  V={self.V:.6f}  W={self.W:.6f}  "
                f"(RMS={self.rms:.5f}°, n={self.n_points})")


def fit_caglioti(points: Iterable[tuple[float, float]]) -> CagliotiFit:
    """由 (2θ, FWHM) 点集最小二乘拟合 Caglioti U/V/W。

    自变量取 (tan²θ, tanθ, 1)，因变量取 FWHM²，线性最小二乘闭式解；
    已知 Si 各峰位与半高宽后即可外推到任意角度。
    """
    arr = np.asarray(list(points), dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 3:
        raise ValueError("Caglioti 拟合至少需要 3 个标样峰")
    tt, fw = arr[:, 0], arr[:, 1]
    t = np.tan(np.radians(tt / 2.0))
    A = np.column_stack([t * t, t, np.ones_like(t)])
    y = fw * fw
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    U, V, W = (float(c) for c in coef)
    pred = np.sqrt(np.maximum(A @ coef, 0.0))
    rms = float(np.sqrt(np.mean((pred - fw) ** 2)))
    return CagliotiFit(U=U, V=V, W=W, rms=rms, n_points=int(arr.shape[0]))


def correct_fwhm(beta_obs_deg: float, beta_inst_deg: float,
                 mode: str = "gauss") -> float:
    """扣除仪器宽化后的样品半高宽（°）。

    mode:
      * ``"gauss"``    —— 平方差：β = sqrt(β_obs² − β_inst²)（两者近似高斯）
      * ``"lorentz"``  —— 直接相减：β = β_obs − β_inst（两者近似洛伦兹）
      * ``"none"``     —— 不扣除
    结果恒 ≥ 0；β_obs ≤ β_inst 时返回 0（提示宽化被仪器完全占据）。
    """
    bo = float(beta_obs_deg)
    bi = max(float(beta_inst_deg), 0.0)
    if mode == "none":
        return bo
    if mode == "lorentz":
        return max(bo - bi, 0.0)
    if mode == "gauss":
        v = bo * bo - bi * bi
        return math.sqrt(v) if v > 0 else 0.0
    raise ValueError(f"未知的宽化扣除模式: {mode}")


# ------------------------------------------------------------------------------
# 实测谱读取
# ------------------------------------------------------------------------------
_PATTERN_SUFFIXES = {".txt", ".xy", ".dat", ".csv", ".asc", ".prn", ".xrdml", ".raw"}


@dataclass
class Pattern:
    """一条实测谱（两列 2θ / 强度）。"""
    two_theta: np.ndarray
    intensity: np.ndarray
    name: str = ""
    source: str = ""
    meta: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return int(self.two_theta.size)

    @property
    def span(self) -> tuple[float, float]:
        return float(self.two_theta.min()), float(self.two_theta.max())

    def clipped(self, lo: float, hi: float) -> "Pattern":
        m = (self.two_theta >= lo) & (self.two_theta <= hi)
        return Pattern(self.two_theta[m], self.intensity[m], self.name, self.source, dict(self.meta))


def _parse_numbers(line: str) -> list[float]:
    out = []
    for tok in line.replace(",", " ").replace(";", " ").split():
        try:
            out.append(float(tok))
        except ValueError:
            continue
    return out


def read_pattern(path: str | Path) -> Pattern:
    """读取两列文本谱（空白/逗号/分号分隔，自动跳过注释与表头）。

    支持岛津 ``.txt``（Profile Data Ascii Dump）、``.xy`` / ``.dat`` /
    ``.csv`` / ``.asc`` / ``.prn`` 等常见导出。单行取到 ≥2 个数时按
    第 1、2 列解释；若首列不是角度（例如从 0,1,2… 起）则按点序号
    与步长无法反推，直接原样保留并由界面校验。
    """
    p = Path(path)
    xs: list[float] = []
    ys: list[float] = []
    meta: dict[str, str] = {}
    with p.open("r", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            if line[0] in "#;!/*'":
                key = line.lstrip("#;!/*' ")
                if "=" in key or ":" in key:
                    k, _, v = key.replace("=", ":").partition(":")
                    k, v = k.strip(), v.strip()
                    if k and v and len(meta) < 80:
                        meta[k] = v
                continue
            nums = _parse_numbers(line)
            if len(nums) < 2:
                continue
            xs.append(nums[0])
            ys.append(nums[1])
    if len(xs) < 5:
        raise ValueError(f"谱图有效数据点过少（{len(xs)} 行）：{p.name}")
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    order = np.argsort(x)
    return Pattern(x[order], y[order], name=p.stem, source=str(p), meta=meta)


# ------------------------------------------------------------------------------
# 寻峰与 pseudo-Voigt 拟合
# ------------------------------------------------------------------------------
def moving_average(y: np.ndarray, window: int = 5) -> np.ndarray:
    """对称移动平均（奇窗；边界用镜像填充，保持长度一致）。"""
    w = max(1, int(window) | 1)
    if w == 1:
        return y.astype(float)
    pad = w // 2
    padded = np.pad(y.astype(float), pad, mode="reflect")
    kernel = np.ones(w) / w
    return np.convolve(padded, kernel, mode="valid")


def _linear_baseline(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """以窗口两端各 10% 点的均值连线作为线性背底（返回斜率、截距）。"""
    n = x.size
    k = max(1, n // 10)
    (x1, y1) = float(np.mean(x[:k])), float(np.mean(y[:k]))
    (x2, y2) = float(np.mean(x[-k:])), float(np.mean(y[-k:]))
    if x2 == x1:
        return 0.0, float(np.mean(y))
    slope = (y2 - y1) / (x2 - x1)
    return slope, y1 - slope * x1


def _pseudo_voigt(x: np.ndarray, amp: float, center: float,
                  fwhm: float, eta: float) -> np.ndarray:
    """归一化到峰高 1 的 pseudo-Voigt（Gaussian + Lorentzian 线性组合）。"""
    w = max(fwhm, 1e-6)
    u = (x - center) / w
    gauss = np.exp(-4.0 * math.log(2.0) * u * u)
    lorentz = 1.0 / (1.0 + 4.0 * u * u)
    return amp * (eta * lorentz + (1.0 - eta) * gauss)


@dataclass
class PeakFit:
    """单峰拟合结果。"""
    two_theta: float          # 峰位（°）
    fwhm: float               # 半高宽（°）
    height: float             # 峰高（扣背底）
    area: float               # 积分强度（峰面积）
    eta: float                # Lorentz 比例 0..1
    r2: float                 # 拟合优度
    two_theta_raw: float = 0.0  # 未细化时的原始峰位
    d: float = 0.0            # 面间距（nm，需外部按波长回填）


def fit_pseudo_voigt(x: np.ndarray, y: np.ndarray,
                     center: float | None = None,
                     fwhm: float | None = None,
                     max_iter: int = 120) -> PeakFit:
    """对一段局部谱做「线性背底 + 单峰 pseudo-Voigt」最小二乘拟合。

    Levenberg–Marquardt 迭代，参数 [amp, center, fwhm, eta, b0, b1]；
    失败时退回「半高宽直读 + 抛物线峰位」的稳健估计，永不抛异常
    （谱图交互场景下宁可给近似值也不能中断）。
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 7:
        raise ValueError("拟合窗口点数过少")

    b0, b1 = _linear_baseline(x, y)
    base = b0 * x + b1
    yd = np.clip(y - base, 0.0, None)
    i_max = int(np.argmax(yd))
    amp0 = float(yd[i_max]) or 1.0
    center0 = float(x[i_max]) if center is None else float(center)
    if fwhm is None:
        fwhm0 = _fwhm_direct(x, yd)
    else:
        fwhm0 = float(fwhm)
    fwhm0 = min(max(fwhm0, 2.5 * float(np.abs(np.diff(x)).mean()), 1e-3), (x[-1] - x[0]))

    p = np.array([amp0, center0, fwhm0, 0.5, b0, b1], dtype=float)
    lower = np.array([0.0, x[0], fwhm0 * 0.2, 0.0, -np.inf, -np.inf])
    upper = np.array([amp0 * 50.0, x[-1], (x[-1] - x[0]) * 2.0, 1.0, np.inf, np.inf])

    def model(pp: np.ndarray) -> np.ndarray:
        return _pseudo_voigt(x, pp[0], pp[1], pp[2], pp[3]) + pp[4] * x + pp[5]

    def sse(pp: np.ndarray) -> float:
        r = model(pp) - y
        return float(r @ r)

    cur = sse(p)
    lam = 1e-3
    for _ in range(max_iter):
        r = model(p) - y
        J = np.empty((x.size, p.size))
        for j in range(p.size):
            dp = np.zeros_like(p)
            step = max(abs(p[j]) * 1e-4, 1e-6)
            dp[j] = step
            J[:, j] = (model(p + dp) - model(p - dp)) / (2.0 * step)
        JtJ = J.T @ J
        g = J.T @ r
        try:
            step = np.linalg.solve(JtJ + lam * np.diag(np.diag(JtJ) + 1e-12), -g)
        except np.linalg.LinAlgError:
            break
        trial = np.clip(p + step, lower, upper)
        new = sse(trial)
        if new < cur:
            p, cur = trial, new
            lam = max(lam * 0.3, 1e-9)
            if float(np.max(np.abs(step))) < 1e-6:
                break
        else:
            lam *= 5.0
            if lam > 1e8:
                break

    amp, cen, fw, eta, bb0, bb1 = (float(v) for v in p)
    yhat = model(p)
    ss_tot = float(np.sum((y - y.mean()) ** 2)) or 1.0
    r2 = 1.0 - cur / ss_tot
    if not np.isfinite(r2) or amp <= 0 or fw <= 0:
        return _fallback_fit(x, yd, base)

    # 面积：pseudo-Voigt 解析面积 = amp * fwhm * (η·π/2 + (1-η)·√(π/4ln2))
    area = amp * fw * (eta * math.pi / 2.0 + (1.0 - eta) * math.sqrt(math.pi / (4.0 * math.log(2.0))))
    return PeakFit(two_theta=cen, fwhm=fw, height=amp, area=area,
                   eta=eta, r2=float(r2), two_theta_raw=center0)


def _fwhm_direct(x: np.ndarray, yd: np.ndarray) -> float:
    """半高宽直读（线性插值），用作拟合初值与兜底。"""
    i = int(np.argmax(yd))
    half = yd[i] / 2.0
    if half <= 0:
        return float((x[-1] - x[0]) / 10.0)

    def walk(direction: int) -> float:
        j = i
        while 0 < j < len(yd) - 1 and yd[j] > half:
            j += direction
            if j <= 0 or j >= len(yd) - 1:
                break
        # 在 j 与 j-direction 之间插值
        j0 = j - direction
        if not (0 <= j0 < len(yd)) or not (0 <= j < len(yd)):
            return float(x[i])
        y0, y1 = yd[j0], yd[j]
        if y1 == y0:
            return float(x[j])
        t = (half - y0) / (y1 - y0)
        return float(x[j0] + t * (x[j] - x[j0]))

    left = walk(-1)
    right = walk(1)
    fw = abs(right - left)
    return fw if fw > 1e-6 else float((x[-1] - x[0]) / 10.0)


def _fallback_fit(x: np.ndarray, yd: np.ndarray, base: np.ndarray) -> PeakFit:
    """拟合退化时的稳健估计：峰位取极大处抛物线顶点，FWHM 直读。"""
    i = int(np.argmax(yd))
    cen = float(x[i])
    if 0 < i < len(x) - 1:
        y0, y1, y2 = yd[i - 1], yd[i], yd[i + 1]
        denom = (y0 - 2 * y1 + y2)
        if denom != 0:
            off = 0.5 * (y0 - y2) / denom
            if abs(off) < 1.0:
                step = (x[i + 1] - x[i - 1]) / 2.0
                cen = float(x[i] + off * step)
    fw = _fwhm_direct(x, yd)
    amp = float(yd[i])
    area = amp * fw * 0.9
    return PeakFit(two_theta=cen, fwhm=fw, height=amp, area=area,
                   eta=float("nan"), r2=float("nan"), two_theta_raw=float(x[i]))


def find_peaks(x: np.ndarray, y: np.ndarray,
               min_height_ratio: float = 0.01,
               min_distance_deg: float = 0.25,
               smooth_window: int = 5,
               prominence_ratio: float = 0.01) -> list[PeakFit]:
    """自动寻峰（局部极大 + 相对强度/突出度阈值 + 最小间距抑制）。

    返回按 2θ 升序排列的单峰列表，每个峰已做 pseudo-Voigt 拟合以给出
    峰位与 FWHM。阈值均为相对最大值（0..1）的比例。
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 9:
        return []
    ys = moving_average(y, smooth_window)
    span = float(ys.max() - ys.min()) or 1.0
    thr = float(ys.min()) + min_height_ratio * span

    candidates: list[int] = []
    for i in range(1, len(ys) - 1):
        if ys[i] >= ys[i - 1] and ys[i] > ys[i + 1] and ys[i] >= thr:
            # 突出度：与左右各 20 点内最低值的差
            lo = max(0, i - 20)
            hi = min(len(ys), i + 21)
            prom = ys[i] - min(ys[lo:i].min() if i > lo else ys[i],
                               ys[i + 1:hi].min() if hi > i + 1 else ys[i])
            if prom >= prominence_ratio * span:
                candidates.append(i)

    # 最小间距抑制：保留更强者
    if candidates:
        candidates.sort(key=lambda i: -ys[i])
        kept: list[int] = []
        for i in candidates:
            if all(abs(x[i] - x[j]) >= min_distance_deg for j in kept):
                kept.append(i)
        candidates = sorted(kept, key=lambda i: x[i])

    dx = float(np.abs(np.diff(x)).mean()) if x.size > 1 else 0.01
    fits: list[PeakFit] = []
    for idx, i in enumerate(candidates):
        left = candidates[idx - 1] if idx > 0 else 0
        right = candidates[idx + 1] if idx + 1 < len(candidates) else len(x) - 1
        # 窗口取相邻峰之间的中点（保证单峰拟合），并留出背底段
        l = max(left, i - max(3, int(0.6 / max(dx, 1e-6))))
        r = min(right, i + max(3, int(0.6 / max(dx, 1e-6))))
        l = max(0, min(l, i - 2))
        r = min(len(x) - 1, max(r, i + 2))
        if r - l < 6:
            continue
        try:
            fit = fit_pseudo_voigt(x[l:r + 1], y[l:r + 1])
        except Exception:  # noqa: BLE001 —— 单峰失败不影响整谱
            continue
        fit.two_theta_raw = float(x[i])
        if i > 0 and i < len(x) - 1:
            y0, y1, y2 = ys[i - 1], ys[i], ys[i + 1]
            denom = (y0 - 2 * y1 + y2)
            if denom != 0:
                off = 0.5 * (y0 - y2) / denom
                if abs(off) < 1.0:
                    fit.two_theta = float(x[i] + off * (x[i + 1] - x[i - 1]) / 2.0)
        fits.append(fit)
    return fits


def fit_at_position(pattern: Pattern, two_theta: float,
                    half_window: float = 0.6) -> PeakFit:
    """在**指定 2θ 附近**定向拟合单峰（用于弱峰，如石墨 (110)）。

    自动寻峰依赖相对强度阈值，而石墨 (110) 的强度常只有 (002) 的百分之几，
    容易被阈值滤掉；本函数改用「理论/预期位置 + 局部窗口」策略，只要窗口内
    存在高于基线噪声的极大值即给出峰位与 FWHM。

    Raises:
        ValueError: 窗口内点太少或找不到可拟合的峰。
    """
    x, y = pattern.two_theta, pattern.intensity
    lo, hi = two_theta - half_window, two_theta + half_window
    m = (x >= lo) & (x <= hi)
    if int(m.sum()) < 9:
        raise ValueError(f"{two_theta:.2f}° 附近数据点不足，无法定向拟合")
    xw, yw = x[m], y[m]
    i = int(np.argmax(yw))
    # 以极大值为中心取对称窗口，保证两侧背底可估
    half = max(5, int(len(xw) * 0.42))
    l = max(0, i - half)
    r = min(len(xw) - 1, i + half)
    if r - l < 9:
        l, r = 0, len(xw) - 1
    fit = fit_pseudo_voigt(xw[l:r + 1], yw[l:r + 1], center=float(xw[i]))
    if not (lo <= fit.two_theta <= hi):
        raise ValueError(f"{two_theta:.2f}° 附近未拟合出有效峰")
    fit.two_theta_raw = float(xw[i])
    return fit


def estimate_noise(y: np.ndarray) -> float:
    """由二阶差分的 MAD 估计噪声标准差（对峰不敏感，抗离群）。"""
    y = np.asarray(y, dtype=float)
    if y.size < 5:
        return 0.0
    d2 = np.diff(y, 2)
    mad = float(np.median(np.abs(d2 - np.median(d2))))
    return mad * 1.4826 / math.sqrt(6.0)


def match_instrument_peaks(pattern: Pattern, wavelength_nm: float,                           a: float = SI_A,
                           window_deg: float = 0.45,
                           min_height_ratio: float = 0.01) -> list[dict]:
    """在 Si 标样谱上按理论峰位逐个找峰并拟合 FWHM。

    返回 [{'hkl','two_theta_theory','two_theta_obs','delta','fwhm','height','r2'}]，
    只保留窗口内确实找到显著峰的反射。
    """
    table = si_reference_table(wavelength_nm, a=a, two_theta_max=pattern.span[1] + 1.0)
    x, y = pattern.two_theta, pattern.intensity
    base_span = float(y.max() - y.min()) or 1.0
    out = []
    for row in table:
        lo, hi = row["two_theta"] - window_deg, row["two_theta"] + window_deg
        m = (x >= lo) & (x <= hi)
        if int(m.sum()) < 7:
            continue
        xw, yw = x[m], y[m]
        i = int(np.argmax(yw))
        if (yw[i] - yw.min()) < min_height_ratio * base_span:
            continue
        # 窗口取峰值两侧对称，保证背底可估
        half = max(4, int(len(xw) * 0.45))
        l = max(0, i - half)
        r = min(len(xw) - 1, i + half)
        try:
            fit = fit_pseudo_voigt(xw[l:r + 1], yw[l:r + 1], center=float(xw[i]))
        except Exception:  # noqa: BLE001
            continue
        if not (lo <= fit.two_theta <= hi):
            continue
        out.append({
            "hkl": row["hkl"],
            "two_theta_theory": row["two_theta"],
            "two_theta_obs": fit.two_theta,
            "delta": row["two_theta"] - fit.two_theta,
            "fwhm": fit.fwhm,
            "height": fit.height,
            "r2": fit.r2,
        })
    return out


# ------------------------------------------------------------------------------
# 全流程计算
# ------------------------------------------------------------------------------
@dataclass
class AnalysisInput:
    """一次石墨化度分析的输入（角度单位 °，波长 nm）。"""
    wavelength: float = WAVELENGTHS[DEFAULT_WAVELENGTH_KEY]
    d002_obs: float = 0.0            # C(002) 实测 2θ
    fwhm002_obs: float = 0.0         # C(002) 实测 FWHM
    si111_obs: float | None = None   # Si(111) 实测 2θ（内标，可空）
    si111_ref: float | None = None   # Si(111) 标准 2θ（可空 → 按 a 计算）
    la_peak: str = "110"             # "110" | "100" | "none"
    la_obs: float = 0.0
    fwhm_la_obs: float = 0.0
    inst_mode: str = "caglioti"      # "caglioti" | "table" | "none"
    caglioti: CagliotiFit | None = None
    inst_fwhm_002: float = 0.0       # table 模式下直接给的仪器 FWHM
    inst_fwhm_la: float = 0.0
    sub_mode: str = "gauss"          # "gauss" | "lorentz" | "none"
    k_lc: float = K_LC
    k_la: float = K_LA_110
    sample: str = ""
    client: str = ""
    operator: str = ""
    note: str = ""


@dataclass
class AnalysisResult:
    # 校正
    delta_two_theta: float = 0.0
    d002_obs: float = 0.0
    d002_corr: float = 0.0
    two_theta_002_corr: float = 0.0
    # 石墨化度
    d002_nm: float = 0.0
    g_percent: float = 0.0
    # Lc
    beta002_obs: float = 0.0
    beta002_inst: float = 0.0
    beta002_corr: float = 0.0
    lc_nm: float = 0.0
    # La
    la_peak: str = ""
    la_two_theta_corr: float = 0.0
    la_d_nm: float = 0.0
    beta_la_obs: float = 0.0
    beta_la_inst: float = 0.0
    beta_la_corr: float = 0.0
    la_nm: float = 0.0
    # 参数留痕
    wavelength: float = 0.0
    k_lc: float = 0.0
    k_la: float = 0.0
    sub_mode: str = ""
    warnings: list[str] = field(default_factory=list)


def analyze(inp: AnalysisInput) -> AnalysisResult:
    """按输入完成 2θ 校正 → d002 → g → Lc / La 全链路计算。"""
    res = AnalysisResult(wavelength=inp.wavelength, k_lc=inp.k_lc,
                         k_la=inp.k_la, sub_mode=inp.sub_mode)
    if inp.d002_obs <= 0:
        raise ValueError("请先输入 C(002) 实测 2θ")

    # ---- 1) 2θ 校正 ----
    delta = 0.0
    if inp.si111_obs and inp.si111_ref:
        delta = zero_shift(inp.si111_obs, inp.si111_ref)
    elif inp.si111_obs:
        delta = zero_shift(inp.si111_obs, si_two_theta((1, 1, 1), inp.wavelength))
    res.delta_two_theta = delta
    res.two_theta_002_corr = apply_shift(inp.d002_obs, delta)
    res.d002_obs = d_from_two_theta(inp.d002_obs, inp.wavelength)
    res.d002_corr = d_from_two_theta(res.two_theta_002_corr, inp.wavelength)

    # ---- 2) 石墨化度 ----
    res.d002_nm = res.d002_corr
    res.g_percent = graphitization_degree(res.d002_nm)
    if not (0.0 <= res.g_percent <= 100.0):
        if res.g_percent < 0:
            res.warnings.append(
                "d002 大于完全无序值 0.3440 nm（g < 0）：峰位偏低（2θ 偏小）、"
                "内标校正方向错误或样品含低角杂峰，请核对。")
        else:
            res.warnings.append(
                "d002 小于理想石墨值 0.3354 nm（g > 100%）：峰位偏高（2θ 偏大），"
                "请核对内标与峰位识别。")

    # ---- 3) Lc ----
    res.beta002_obs = inp.fwhm002_obs
    res.beta002_inst = _inst_fwhm(inp, res.two_theta_002_corr, kind="lc")
    res.beta002_corr = correct_fwhm(res.beta002_obs, res.beta002_inst, inp.sub_mode)
    if res.beta002_obs > 0 and res.beta002_corr > 0:
        res.lc_nm = scherrer_size(res.beta002_corr, res.two_theta_002_corr,
                                  inp.wavelength, inp.k_lc)
    if res.beta002_obs > 0 and res.beta002_corr <= 0:
        res.warnings.append("C(002) 实测半高宽不大于仪器宽化，Lc 无法给出（请检查标样或扫描条件）。")

    # ---- 4) La ----
    if inp.la_peak in ("110", "100") and inp.la_obs > 0:
        res.la_peak = inp.la_peak
        res.la_two_theta_corr = apply_shift(inp.la_obs, delta)
        res.la_d_nm = d_from_two_theta(res.la_two_theta_corr, inp.wavelength)
        res.beta_la_obs = inp.fwhm_la_obs
        res.beta_la_inst = _inst_fwhm(inp, res.la_two_theta_corr, kind="la")
        res.beta_la_corr = correct_fwhm(res.beta_la_obs, res.beta_la_inst, inp.sub_mode)
        if res.beta_la_corr > 0:
            res.la_nm = scherrer_size(res.beta_la_corr, res.la_two_theta_corr,
                                      inp.wavelength, inp.k_la)
        else:
            res.warnings.append("La 峰实测半高宽不大于仪器宽化，La 无法给出。")

        # 峰位与理论值偏离提示（判据：>0.5° 认为可能选错峰）
        ref = graphite_reference_table(inp.wavelength)["110" if inp.la_peak == "110" else "100"]
        if abs(res.la_two_theta_corr - ref["two_theta"]) > 0.5:
            res.warnings.append(
                f"La 峰校正后 2θ={res.la_two_theta_corr:.4f}° 与石墨 ({inp.la_peak}) "
                f"理论值 {ref['two_theta']:.4f}° 相差超过 0.5°，请确认选峰是否正确。")
    elif inp.la_peak in ("110", "100"):
        res.warnings.append("未输入 La 峰的实测 2θ，La 未计算。")

    # ---- 5) 建议性提示 ----
    if inp.la_peak == "100":
        res.warnings.append(
            "La 使用 (100) 峰（2θ ≈ 42.4°）计算：条件允许时建议改测 72–82° 的 (110) 峰，"
            "(110) 峰强度低但无相邻峰干扰、角度分辨率更高，是碳材料规范的优先选择。")
    if res.beta002_inst <= 0 and inp.inst_mode != "none":
        res.warnings.append("仪器宽化参数为空，Lc/La 未扣除仪器展宽（结果会偏小）。")
    return res


def _inst_fwhm(inp: AnalysisInput, two_theta: float, kind: str) -> float:
    if inp.inst_mode == "none":
        return 0.0
    if inp.inst_mode == "caglioti" and inp.caglioti is not None:
        return inp.caglioti.fwhm(two_theta)
    return inp.inst_fwhm_002 if kind == "lc" else inp.inst_fwhm_la


# ------------------------------------------------------------------------------
# 报告导出
# ------------------------------------------------------------------------------
def result_rows(inp: AnalysisInput, res: AnalysisResult) -> list[tuple[str, str, str]]:
    """报告表体：(项目, 数值, 单位)。供界面表格与文本报告共用。"""
    rows = [
        ("波长 λ", f"{res.wavelength:.7f}", "nm"),
        ("C(002) 实测 2θ", f"{inp.d002_obs:.4f}", "°"),
        ("内标校正 Δ2θ", f"{res.delta_two_theta:+.4f}", "°"),
        ("C(002) 校正 2θ", f"{res.two_theta_002_corr:.4f}", "°"),
        ("层间距 d002", f"{res.d002_nm:.5f}", "nm"),
        ("石墨化度 g", f"{res.g_percent:.2f}", "%"),
        ("C(002) 实测 FWHM", f"{res.beta002_obs:.4f}", "°"),
        ("仪器宽化 (002)", f"{res.beta002_inst:.4f}", "°"),
        ("纯宽化 β(002)", f"{res.beta002_corr:.4f}", "°"),
        ("堆叠厚度 Lc", f"{res.lc_nm:.3f}", "nm"),
    ]
    if res.la_peak:
        rows += [
            (f"La 峰 ({res.la_peak}) 校正 2θ", f"{res.la_two_theta_corr:.4f}", "°"),
            (f"La 峰 d({res.la_peak})", f"{res.la_d_nm:.5f}", "nm"),
            (f"La 峰实测 FWHM", f"{res.beta_la_obs:.4f}", "°"),
            (f"仪器宽化 ({res.la_peak})", f"{res.beta_la_inst:.4f}", "°"),
            (f"纯宽化 β({res.la_peak})", f"{res.beta_la_corr:.4f}", "°"),
            ("微晶尺寸 La", f"{res.la_nm:.3f}", "nm"),
        ]
    return rows


def build_report_text(inp: AnalysisInput, res: AnalysisResult,
                      app_name: str = "PolyXRD Graphite",
                      version: str = "") -> str:
    """生成可粘贴/存档的纯文本报告（含参数与判据留痕）。"""
    lines = [
        f"{app_name} {('v' + version) if version else ''}".strip(),
        "=" * 62,
    ]
    meta = [("样品", inp.sample), ("委托单位", inp.client),
            ("测试人", inp.operator), ("备注", inp.note)]
    for k, v in meta:
        if v:
            lines.append(f"{k}：{v}")
    lines.append("")
    lines.append(f"{'项目':<22}{'数值':>14}  {'单位'}")
    lines.append("-" * 62)
    for name, val, unit in result_rows(inp, res):
        lines.append(f"{name:<22}{val:>14}  {unit}")
    sub_label = {"gauss": "平方差（高斯）", "lorentz": "直接相减（洛伦兹）",
                 "none": "不扣除"}.get(res.sub_mode, res.sub_mode)
    lines += [
        "-" * 62,
        "石墨化度公式：g = (0.3440 − d002) / (0.3440 − 0.3354) × 100%",
        f"Scherrer：L = Kλ / (β cosθ)，K(Lc)={res.k_lc:.2f}，K(La)={res.k_la:.2f}",
        f"仪器宽化扣除：{sub_label}",
    ]
    if inp.inst_mode == "caglioti" and inp.caglioti is not None:
        lines.append(f"Caglioti：{inp.caglioti.as_text()}")
    if res.warnings:
        lines.append("")
        lines.append("提示：")
        for w in res.warnings:
            lines.append(f"  · {w}")
    return "\n".join(lines)


def write_report_csv(path: str | Path, inp: AnalysisInput, res: AnalysisResult) -> None:
    """把结果写为 CSV（UTF-8 BOM，Excel 直接打开不乱码）。"""
    p = Path(path)
    lines = ["项目,数值,单位"]
    for name, val, unit in result_rows(inp, res):
        lines.append(f'"{name}","{val}","{unit}"')
    lines.append("")
    lines.append('"样品","%s",""' % inp.sample)
    lines.append('"委托单位","%s",""' % inp.client)
    lines.append('"波长(nm)","%s",""' % f"{res.wavelength:.7f}")
    lines.append('"K(Lc)","%s",""' % f"{res.k_lc:.2f}")
    lines.append('"K(La)","%s",""' % f"{res.k_la:.2f}")
    p.write_text("\ufeff" + "\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------------------------
# 自检（命令行：python graphite_engine.py）
# ------------------------------------------------------------------------------
def _selfcheck() -> None:
    lam = WAVELENGTHS["Cu Kα1"]
    print("== 文档算例复算（章斌《石墨化度的测定》，岛津 XRD-6100） ==")
    si_ref = si_two_theta((1, 1, 1), lam)
    print(f"  Si(111) 理论 2θ (a={SI_A} nm) = {si_ref:.5f}°   [文档取值 28.44135°]")
    delta = zero_shift(28.4541, 28.44135)
    tt = apply_shift(26.5584, delta)
    d = d_from_two_theta(tt, lam)
    print(f"  Δ2θ = {delta:+.5f}° ; C(002) {26.5584}° → {tt:.5f}°")
    print(f"  d002 = {d:.5f} nm   g = {graphitization_degree(d):.2f}%   [文档 0.33551 nm / 98.8%]")
    g_ref = graphite_reference_table(lam)
    print(f"  理论峰位：002 {g_ref['002']['two_theta']:.3f}° · "
          f"100 {g_ref['100']['two_theta']:.3f}° (d={g_ref['100']['d']:.4f} nm) · "
          f"110 {g_ref['110']['two_theta']:.3f}° (d={g_ref['110']['d']:.4f} nm)")
    print("\n== Scherrer 与宽化扣除自检 ==")
    print(f"  β=0.20° @26.55°, K=0.89 → Lc = {scherrer_size(0.20, 26.55, lam, K_LC):.2f} nm")
    print(f"  β=0.30° @77.50°, K=1.84 → La = {scherrer_size(0.30, 77.50, lam, K_LA_110):.2f} nm")
    print(f"  平方差扣除：obs 0.30°, inst 0.12° → {correct_fwhm(0.30, 0.12, 'gauss'):.4f}°")
    fit = fit_caglioti([(28.44, 0.10), (47.30, 0.12), (56.12, 0.14), (76.38, 0.18)])
    print(f"  Caglioti 自检：{fit.as_text()}")
    print(f"  外推 26.55° → {fit.fwhm(26.55):.4f}°")


if __name__ == "__main__":
    _selfcheck()
