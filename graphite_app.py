# -*- coding: utf-8 -*-
"""PolyXRD Graphite —— 石墨化度 / Lc / La 测定小工具（PySide6，单文件发行）。

工具定位
--------
面向石墨类负极材料、人造石墨、炭素制品的常规 XRD 分析：由 C(002) 峰位给出
**石墨化度 g**（层间距 d002 表达）与 **Lc**，由 (110)（优先，2θ ≈ 77.5°）或
(100)（备用，2θ ≈ 42.4°）给出 **La**；并用掺入的 Si 内标校正 2θ、用 Si 标样
谱反算的 Caglioti 参数扣除仪器宽化。

构建变体（与 PolyXRD 家族一致，见 BUILD_VARIANT）
------------------------------------------------
* ``"setup"``    —— 安装版（默认）：含注册机制（帮助菜单「输入注册码」、
  启动未注册提示、状态栏右侧显示注册单位名称）。
* ``"internal"`` —— 内部评估版（单文件 exe）：无注册机制，状态栏右侧显示
  「内部评估版本」。构建时由 build_exe.bat 打入 packaging/internal_eval.marker。

界面支持 简体中文 / English / 日本語，运行时可在「语言」菜单热切换。
"""
from __future__ import annotations

import datetime as _dt
import math
import sys
from pathlib import Path

import numpy as np

from PySide6.QtCore import QPointF, QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import (QAction, QActionGroup, QBrush, QColor, QFont, QIcon,
                           QKeySequence, QPainter, QPen, QPixmap, QShortcut)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QSplitter, QSplashScreen, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextBrowser, QTextEdit, QToolButton, QVBoxLayout, QWidget,
)

import graphite_engine as eng
import i18n as T
import registration
from i18n import tr

APP_NAME = "PolyXRD Graphite"
APP_VERSION = "1.2.0"
ORG_NAME = "PolyXRD"
APP_ID = "Graphite"

CONTACT_EMAIL = registration.CONTACT_EMAIL


# ------------------------------------------------------------------------------
# 资源与构建变体
# ------------------------------------------------------------------------------
def res_path(name: str) -> Path:
    """资源文件路径（兼容 PyInstaller onefile 的 sys._MEIPASS 解包目录）。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "resources" / name


def bundle_path(name: str) -> Path:
    """包内根目录文件路径（源码运行 = 本文件所在目录；打包后 = sys._MEIPASS）。"""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / name


def _detect_variant() -> str:
    """检测构建变体: "internal" (内部评估) / "setup" (安装版, 默认)。"""
    return "internal" if bundle_path("internal_eval.marker").exists() else "setup"


BUILD_VARIANT = _detect_variant()


def variant_name() -> str:
    """关于框里显示的构建变体名（内部评估版 / 安装版）。"""
    return tr("status.internal_eval") if BUILD_VARIANT == "internal" else tr("variant.setup")


# ------------------------------------------------------------------------------
# 坐标轴刻度：取 1 / 2 / 2.5 / 5 ×10^k 的"整"步长
# ------------------------------------------------------------------------------
def _nice_step(span: float, target: int = 5) -> float:
    """按目标格数给出规整步长（1、2、2.5、5 的 10 次幂倍）。"""
    if not np.isfinite(span) or span <= 0:
        return 1.0
    raw = span / max(int(target), 1)
    mag = 10.0 ** math.floor(math.log10(raw))
    for mult in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= mult * mag:
            return mult * mag
    return 10.0 * mag


def _nice_ticks(lo: float, hi: float, target: int = 5) -> list[float]:
    """返回落在 [lo, hi] 内的规整刻度序列。"""
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi <= lo:
        return [lo]
    step = _nice_step(hi - lo, target)
    v = math.ceil(lo / step - 1e-9) * step
    out: list[float] = []
    while v <= hi + step * 1e-6 and len(out) < 40:
        out.append(round(v, 10))
        v += step
    return out or [lo]


def _tick_decimals(values: list[float]) -> int:
    """刻度标签小数位：步长 ≥1 取整数，≥0.1 取 1 位，否则 2 位。"""
    if len(values) < 2:
        return 0
    step = abs(values[1] - values[0])
    if step >= 1 - 1e-9:
        return 0
    return 1 if step >= 0.1 - 1e-9 else 2


# ------------------------------------------------------------------------------
# 轻量绘图（QPainter，无 matplotlib 依赖）
# ------------------------------------------------------------------------------
class PlotCanvas(QWidget):
    """2θ–强度谱图绘制：曲线 + 识别峰 2θ 标签 + 理论峰位虚线 + 选中峰高亮。

    识别峰不再画小圆点，改为在峰顶用引线挂一枚角度标签（``26.417°``）：
    峰多时标签按「正上方 → 右上 → 左上 → 抬高一层」的顺序自动避让，
    并收敛在绘图区内，避免压到边框或其他标签。

    大数据量按像素分箱抽稀（保留每箱极值），保证数万点谱拖动时不卡顿。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bg = QColor("#ffffff")
        self.axis = QColor("#5b6470")
        self.gridc = QColor("#e8ecf2")
        self.curve = QColor("#0f6f9c")
        self.peak_color = QColor("#d1495b")
        self.centroid_color = QColor("#b7791f")
        self.theory_color = QColor("#8d99ae")
        self.sel_color = QColor("#1f9d55")
        self._pattern: eng.Pattern | None = None
        self._peaks: list[eng.PeakFit] = []
        self._markers: list[tuple[float, str]] = []
        self._selected = -1
        self._centroids: list[float | None] = []
        self.show_labels = True
        self.show_centroid = True
        self.empty_text = ""
        self.x_label = "2θ (°)"
        self.y_label = "Intensity"

    # ---- 数据 ----
    def set_pattern(self, pattern: eng.Pattern | None) -> None:
        self._pattern = pattern
        self.update()

    def set_peaks(self, peaks: list[eng.PeakFit]) -> None:
        self._peaks = list(peaks)
        self.update()

    def set_markers(self, markers: list[tuple[float, str]]) -> None:
        self._markers = list(markers)
        self.update()

    def set_centroids(self, centroids: list[float | None]) -> None:
        """质心 2θ 列表（与 peaks 同序；None 表示该峰算不出质心）。"""
        self._centroids = list(centroids)
        self.update()

    def set_selected(self, index: int) -> None:
        self._selected = index
        self.update()

    # ---- 绘制 ----
    def paintEvent(self, event):  # noqa: N802 (Qt 命名)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), self.bg)

        if self._pattern is None or len(self._pattern) < 2:
            painter.setPen(self.axis)
            painter.drawText(self.rect(), Qt.AlignCenter, self.empty_text)
            painter.end()
            return

        ml, mr, mt, mb = 62, 16, 26, 40
        x = self._pattern.two_theta
        y = self._pattern.intensity
        xmin, xmax = float(x.min()), float(x.max())
        ymin = min(0.0, float(y.min()))
        # 顶部按"固定像素"预留峰角度标签的位置：不论画布多高，最高峰的标签
        # 都能放在峰顶正上方，不会被上边框裁掉；画布过矮时退回 6% 余量。
        px_h = float(h - mt - mb)
        # 只在有峰角度标签时才预留顶部空间（关掉标注后让曲线吃满画布）
        reserve = 34.0 if (self.show_labels and self._peaks) else 8.0
        span = float(y.max()) - ymin
        if span > 0 and px_h > reserve * 2.5:
            # 预留空间按像素给，避免"最高峰标签被顶出画布"随窗口高度漂移
            ymax = ymin + span * px_h / (px_h - reserve)
        else:
            ymax = float(y.max()) * 1.06 or 1.0
        if xmax <= xmin:
            xmax = xmin + 1.0
        if ymax <= ymin:
            ymax = ymin + 1.0

        def tx(v: float) -> float:
            return ml + (v - xmin) / (xmax - xmin) * (w - ml - mr)

        def ty(v: float) -> float:
            return h - mb - (v - ymin) / (ymax - ymin) * (h - mt - mb)

        # 网格与刻度（2θ 取规整步长，强度取整刻度）
        painter.setFont(QFont("Consolas", 8))
        xticks = _nice_ticks(xmin, xmax, 5)
        yticks = _nice_ticks(ymin, ymax, 5)
        xdec = _tick_decimals(xticks)
        ydec = _tick_decimals(yticks)
        for gx in xticks:
            painter.setPen(QPen(self.gridc, 1))
            painter.drawLine(QPointF(tx(gx), mt), QPointF(tx(gx), h - mb))
            painter.setPen(self.axis)
            bx = min(max(tx(gx) - 24.0, 0.0), w - 48.0)  # 贴边刻度不越出控件
            painter.drawText(QRectF(bx, h - mb + 4.0, 48.0, 14.0),
                             Qt.AlignHCenter | Qt.AlignTop, f"{gx:.{xdec}f}")
        for gy in yticks:
            painter.setPen(QPen(self.gridc, 1))
            painter.drawLine(QPointF(ml, ty(gy)), QPointF(w - mr, ty(gy)))
            painter.setPen(self.axis)
            painter.drawText(QRectF(2.0, ty(gy) - 7.0, ml - 9.0, 14.0),
                             Qt.AlignRight | Qt.AlignVCenter, f"{gy:.{ydec}f}")

        painter.setPen(QPen(self.axis, 1.2))
        painter.drawRect(ml, mt, w - ml - mr, h - mt - mb)
        painter.drawText(w // 2 - 20, h - 6, self.x_label)
        # y 轴说明：绘图区上方左对齐（旋转竖排在小尺寸下会互相挤压）
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(ml, mt - 8, self.y_label)

        # 理论峰位虚线（顶部小标签同时记入障碍区，峰角度标签会绕开它）
        obstacles: list[QRectF] = []
        if self._markers:
            painter.setFont(QFont("Segoe UI", 7))
            mfm = painter.fontMetrics()
            for tt, label in self._markers:
                if not (xmin <= tt <= xmax):
                    continue
                painter.setPen(QPen(self.theory_color, 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(tx(tt), mt + 4), QPointF(tx(tt), h - mb))
                # 顶部用浅底小标签压住网格，避免与刻度线混杂
                tw = mfm.horizontalAdvance(label) + 6
                th = mfm.height()
                lx = tx(tt) + 3
                if lx + tw > w - mr - 2:
                    lx = tx(tt) - 3 - tw
                box = QRectF(lx, mt + 4, tw, th)
                obstacles.append(box)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 225)))
                painter.drawRect(box)
                painter.setPen(self.theory_color)
                painter.setBrush(Qt.NoBrush)
                painter.drawText(box, Qt.AlignCenter, label)

        # 曲线（按像素分箱抽稀）
        pts = self._decimate(x, y, w, ml, mr, tx, ty)
        painter.setPen(QPen(self.curve, 1.1))
        for i in range(1, len(pts)):
            painter.drawLine(pts[i - 1], pts[i])

        # 质心位置（可选）：横轴下短标记；选中峰再加一条虚线 + 数值
        if self.show_centroid and self._centroids:
            for cen in self._centroids:
                if cen is None or not (xmin <= cen <= xmax):
                    continue
                painter.setPen(QPen(self.centroid_color, 1.4))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(tx(cen), h - mb), QPointF(tx(cen), h - mb + 5))
            sel_c = (self._centroids[self._selected]
                     if 0 <= self._selected < len(self._centroids) else None)
            if sel_c is not None and xmin <= sel_c <= xmax:
                px = tx(sel_c)
                painter.setPen(QPen(QColor(183, 121, 31, 150), 1.0, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(px, mt + 2), QPointF(px, h - mb))
                painter.setFont(QFont("Consolas", 8))
                cfm = painter.fontMetrics()
                txt = tr("pat.centroid_tag", tt=sel_c)
                tw = cfm.horizontalAdvance(txt) + 9.0
                th = cfm.height() + 4.0
                bx = min(max(px - tw / 2.0, ml + 2.0), w - mr - tw - 2.0)
                box = QRectF(bx, h - mb - th - 4.0, tw, th)
                painter.setPen(QPen(QColor(183, 121, 31, 170), 1.0))
                painter.setBrush(QBrush(QColor(255, 252, 244, 240)))
                painter.drawRoundedRect(box, 3.0, 3.0)
                painter.setPen(self.centroid_color)
                painter.setBrush(Qt.NoBrush)
                painter.drawText(box, Qt.AlignCenter, txt)

        # 峰标注：峰顶挂 2θ 角度标签（不画小圆点）
        self._draw_peak_labels(painter, xmin, xmax, ml, mt, w, h, mr, mb, tx, ty,
                               obstacles)
        painter.end()

    def _draw_peak_labels(self, painter, xmin, xmax, ml, mt, w, h, mr, mb, tx, ty,
                          obstacles=()):
        """在识别峰顶标注 2θ 角度：细引线 + 圆角标签，自动避让、不越界。

        落位策略（选中峰优先，其余按 2θ 递增，保证结果稳定不跳动）：
        正上方 → 逐级抬高 → 右上 / 左上 逐级抬高 → 左右同高（峰顶已贴近上边框时用）。
        峰距很近时靠"逐级抬高"把标签叠成阶梯，而不是互相压字；
        顶部理论峰位的小标签也计入障碍区，峰标签不会盖住它。
        """
        if not self.show_labels or not self._peaks:
            return
        plot = QRectF(ml + 3.0, mt + 3.0, w - ml - mr - 6.0, h - mt - mb - 6.0)
        lab_font = QFont("Consolas")
        lab_font.setPointSizeF(8.5)
        painter.setFont(lab_font)
        fm = painter.fontMetrics()
        gap, pad = 11.0, 2.5
        placed: list[QRectF] = list(obstacles)

        order = sorted(range(len(self._peaks)), key=lambda i: self._peaks[i].two_theta)
        if 0 <= self._selected < len(self._peaks):
            order.sort(key=lambda i: 0 if i == self._selected else 1)

        for k in order:
            p = self._peaks[k]
            if not (xmin <= p.two_theta <= xmax):
                continue
            cx, cy = tx(p.two_theta), ty(p.height)
            txt = f"{p.two_theta:.3f}°"
            lw = fm.horizontalAdvance(txt) + 12.0
            lh = fm.height() + 4.0
            step = lh + 3.0
            candidates: list[tuple[float, float]] = []
            for s in range(5):                              # 正上方，逐级抬高
                candidates.append((cx - lw / 2.0, cy - gap - lh - s * step))
            for s in range(3):                              # 右上
                candidates.append((cx + 8.0, cy - gap * 0.4 - lh - s * step))
            for s in range(3):                              # 左上
                candidates.append((cx - lw - 8.0, cy - gap * 0.4 - lh - s * step))
            for dy in (0.0, -lh - 4.0):                     # 右侧同高 / 左侧同高
                candidates.append((cx + 8.0, cy - lh / 2.0 + dy))
                candidates.append((cx - lw - 8.0, cy - lh / 2.0 + dy))
            rect = None
            for lx, ly in candidates:
                r = QRectF(lx, ly, lw, lh)
                if not plot.contains(r):
                    continue
                if any(r.adjusted(-pad, -pad, pad, pad).intersects(q) for q in placed):
                    continue
                rect = r
                break
            if rect is None:  # 兜底：贴着峰顶并夹在绘图区内
                rect = QRectF(min(max(cx - lw / 2.0, plot.left()), plot.right() - lw),
                              max(cy - gap - lh, plot.top()), lw, lh)
            placed.append(rect)

            is_sel = (k == self._selected)
            if is_sel:
                line_col, box_col = self.sel_color, QColor("#ffffff")
            else:
                line_col, box_col = QColor(209, 73, 91, 140), QColor("#b03a49")

            # 引线：峰顶 → 标签最近的边（上方=竖线，侧方=横线）
            if rect.bottom() <= cy + 1.0:                   # 标签在峰顶上方
                ax = min(max(cx, rect.left() + 3.0), rect.right() - 3.0)
                ay = rect.bottom()
            elif rect.top() >= cy - 1.0:                    # 标签在峰顶下方
                ax = min(max(cx, rect.left() + 3.0), rect.right() - 3.0)
                ay = rect.top()
            else:                                           # 标签在峰顶侧方
                ax = rect.left() if rect.center().x() > cx else rect.right()
                ay = min(max(cy, rect.top() + 3.0), rect.bottom() - 3.0)
            painter.setPen(QPen(line_col, 1.0))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(QPointF(cx, cy), QPointF(ax, ay))

            if is_sel:
                painter.setPen(QPen(self.sel_color, 1.2))
                painter.setBrush(QBrush(self.sel_color))
            else:
                painter.setPen(QPen(QColor(209, 73, 91, 110), 1.0))
                painter.setBrush(QBrush(QColor(255, 255, 255, 236)))
            painter.drawRoundedRect(rect, 3.0, 3.0)

            painter.setPen(box_col)
            painter.setBrush(Qt.NoBrush)
            painter.drawText(rect, Qt.AlignCenter, txt)

    def _decimate(self, x, y, w, ml, mr, tx, ty):
        """按像素列取 min/max，避免数万点逐点 drawLine。"""
        n = len(x)
        cols = max(int(w - ml - mr), 10)
        if n <= cols * 2:
            return [QPointF(tx(float(xi)), ty(float(yi))) for xi, yi in zip(x, y)]
        idx = np.linspace(0, n - 1, cols).astype(int)
        pts = []
        step = max(1, n // cols)
        for i in idx:
            lo = max(0, i - step // 2)
            hi = min(n, i + step // 2 + 1)
            seg = y[lo:hi]
            if seg.size:
                pts.append(QPointF(tx(float(x[i])), ty(float(seg.min()))))
                pts.append(QPointF(tx(float(x[i])), ty(float(seg.max()))))
        return pts


# ------------------------------------------------------------------------------
# 小工具
# ------------------------------------------------------------------------------
def _spin(minv: float, maxv: float, val: float, step: float, dec: int = 4,
          suffix: str = "") -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(minv, maxv)
    s.setDecimals(dec)
    s.setSingleStep(step)
    s.setValue(val)
    if suffix:
        s.setSuffix(suffix)
    s.setKeyboardTracking(False)
    return s


def _label(text: str = "", bold: bool = False, small: bool = False) -> QLabel:
    lb = QLabel(text)
    lb.setWordWrap(True)
    if bold:
        f = lb.font()
        f.setBold(True)
        lb.setFont(f)
    if small:
        f = lb.font()
        f.setPointSizeF(max(f.pointSizeF() - 1.2, 7.5))
        lb.setFont(f)
    return lb


def _hint(text: str = "") -> QLabel:
    lb = _label(text, small=True)
    lb.setObjectName("hintLabel")
    return lb


class _Metric(QFrame):
    """结果大数字卡。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(2)
        self.title = QLabel("")
        self.title.setObjectName("metricLabel")
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        lay.addWidget(self.title)
        lay.addWidget(self.value)

    def set_value(self, text: str) -> None:
        self.value.setText(text)


# ------------------------------------------------------------------------------
# 主窗口
# ------------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1300, 880)
        self.setMinimumSize(1080, 720)

        # ---- 运行状态 ----
        self.pattern: eng.Pattern | None = None
        self.peaks: list[eng.PeakFit] = []
        self.centroids: list[eng.PeakCentroid | None] = []
        self.si_pattern: eng.Pattern | None = None
        self.si_peaks: list[dict] = []
        self.caglioti: eng.CagliotiFit | None = None
        self.result: eng.AnalysisResult | None = None
        self._si_ref_auto = True
        self._tr_items: list[tuple] = []      # (widget|action, key, kind)
        self._reg = None
        self._reg_label = None

        # ---- 防抖重算 ----
        self._calc_timer = QTimer(self)
        self._calc_timer.setSingleShot(True)
        self._calc_timer.setInterval(220)
        self._calc_timer.timeout.connect(self._recalc)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        self.tabs = tabs
        self.tab_calc = self._build_tab_calc()
        self.tab_pattern = self._build_tab_pattern()
        self.tab_inst = self._build_tab_inst()
        self.tab_method = self._build_tab_method()
        tabs.addTab(self.tab_calc, "")
        tabs.addTab(self.tab_pattern, "")
        tabs.addTab(self.tab_inst, "")
        tabs.addTab(self.tab_method, "")

        # 页签栏右上角的小提示图标：任何页签下都能点开「测试与计算要点」
        self.btn_hint = QToolButton()
        self.btn_hint.setObjectName("hintIcon")
        self.btn_hint.setText("?")
        self.btn_hint.setCursor(Qt.PointingHandCursor)
        self.btn_hint.setFixedSize(22, 22)
        self.btn_hint.clicked.connect(self._show_brief)
        _corner = QWidget()
        _cl = QHBoxLayout(_corner)
        _cl.setContentsMargins(0, 1, 8, 1)
        _cl.setSpacing(0)
        _cl.addWidget(self.btn_hint)
        tabs.setCornerWidget(_corner, Qt.TopRightCorner)

        # 注册机制（仅安装版；内部评估版无注册概念）
        if BUILD_VARIANT == "setup":
            registration.set_language(T.current_language())
            self._reg = registration.RegistrationManager(
                APP_NAME, registration.default_state_path(APP_ID))

        self._build_menus()
        self._build_statusbar()
        self._apply_style()
        self._retranslate()
        self._sync_lambda_widgets()
        self._refresh_broadening_state()
        QTimer.singleShot(60, self._recalc)

    # ================================================================ 样式
    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget { font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 9.5pt; }
            QGroupBox {
                font-weight: 600; border: 1px solid #d7dde6; border-radius: 8px;
                margin-top: 12px; padding-top: 8px; background: #fbfcfe;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #16283d; }
            #resultCard { background: #f6f9fc; border: 1px solid #dce4ee; border-radius: 10px; }
            #metricLabel { color: #5a6675; font-size: 8.5pt; }
            #metricValue { color: #0b6b8f; font-size: 20pt; font-weight: 700; }
            #hintLabel { color: #6b7787; }
            #warnBox { background: #fffaf0; border: 1px solid #efdcb4; border-radius: 6px; }
            #bannerOk { background: #eaf7ef; border: 1px solid #b7e0c4; border-radius: 6px; color: #1d6b3c; padding: 4px 6px; }
            #bannerWarn { background: #fff4e5; border: 1px solid #f0cfa0; border-radius: 6px; color: #8a5a13; padding: 4px 6px; }
            #bannerInfo { background: #eef4fb; border: 1px solid #c8d8ea; border-radius: 6px; color: #2a4a6b; padding: 4px 6px; }
            QPushButton {
                background: #0f6f9c; color: white; border: none; border-radius: 5px;
                padding: 6px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #1285bb; }
            QPushButton:disabled { background: #b6c2cf; }
            QPushButton#ghost {
                background: #eef2f7; color: #1d3247; border: 1px solid #d3dbe6;
            }
            QPushButton#ghost:hover { background: #e3eaf3; }
            QToolButton#hintIcon {
                background: #e6f0fa; color: #0f6f9c; border: 1px solid #a9c6e0;
                border-radius: 11px; font-size: 10pt; font-weight: 700; padding: 0;
            }
            QToolButton#hintIcon:hover { background: #d2e4f5; border-color: #6f9fc7; }
            QToolButton#hintIcon:pressed { background: #c1d7ee; }
            QTableWidget { gridline-color: #e6ebf2; selection-background-color: #dbeaf6;
                           selection-color: #10283d; }
            QHeaderView::section { background: #eff3f8; border: none; padding: 4px 6px;
                                   font-weight: 600; color: #2a3b4f; }
            QStatusBar { background: #f4f6fa; color: #47586b; }
            /* 内部评估版提示：状态栏居中、加粗、红色（字号沿用全局，不另设） */
            QLabel#statusEval { color: #c62828; font-weight: 700; }
        """)

    # ================================================================ 计算页
    def _build_tab_calc(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 10, 10, 10)

        self.banner = QLabel("")
        self.banner.setObjectName("bannerInfo")
        self.banner.setWordWrap(True)
        self.banner.setMinimumHeight(30)
        outer.addWidget(self.banner)

        split = QSplitter(Qt.Horizontal)
        outer.addWidget(split, 1)

        # ---------------- 左：输入 ----------------
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 6, 0)
        left_lay.setSpacing(8)
        l_scroll = QScrollArea()
        l_scroll.setWidgetResizable(True)
        l_scroll.setFrameShape(QFrame.NoFrame)
        l_container = QWidget()
        l_form = QVBoxLayout(l_container)
        l_form.setContentsMargins(2, 2, 8, 2)
        l_form.setSpacing(8)
        l_scroll.setWidget(l_container)

        # 样品信息
        g_s = QGroupBox()
        gs = QGridLayout(g_s)
        gs.setHorizontalSpacing(8)
        gs.setVerticalSpacing(6)
        self.ed_sample = QLineEdit()
        self.ed_client = QLineEdit()
        self.ed_operator = QLineEdit()
        self.ed_note = QLineEdit()
        self._tr_items += [(g_s, "group.sample", "group")]
        for row, (key, w) in enumerate((("sample.name", self.ed_sample),
                                        ("sample.client", self.ed_client),
                                        ("sample.operator", self.ed_operator),
                                        ("sample.note", self.ed_note))):
            lb = _label()
            self._tr_items.append((lb, key, "text"))
            gs.addWidget(lb, row, 0)
            gs.addWidget(w, row, 1)
        gs.setColumnStretch(1, 1)
        l_form.addWidget(g_s)

        # 仪器与参数
        g_i = QGroupBox()
        gi = QGridLayout(g_i)
        gi.setHorizontalSpacing(8)
        gi.setVerticalSpacing(6)
        self._tr_items += [(g_i, "group.instrument", "group")]
        self.cb_target = QComboBox()
        self.cb_target.addItems(list(eng.WAVELENGTHS.keys()) + ["自定义"])
        self.sp_lambda = _spin(0.05, 3.0, eng.WAVELENGTHS[eng.DEFAULT_WAVELENGTH_KEY],
                               0.0000001, 8)
        self.sp_lambda.setEnabled(False)
        self.sp_k_lc = _spin(0.1, 5.0, eng.K_LC, 0.01, 3)
        self.sp_k_la = _spin(0.1, 5.0, eng.K_LA_110, 0.01, 3)
        rows = [("inst.target", self.cb_target), ("inst.lambda", self.sp_lambda),
                ("inst.k_lc", self.sp_k_lc), ("inst.k_la", self.sp_k_la)]
        for row, (key, w) in enumerate(rows):
            lb = _label()
            self._tr_items.append((lb, key, "text"))
            gi.addWidget(lb, row, 0)
            gi.addWidget(w, row, 1)
        self.lb_k_hint = _hint()
        self._tr_items.append((self.lb_k_hint, "inst.k_hint", "text"))
        gi.addWidget(self.lb_k_hint, len(rows), 0, 1, 2)
        gi.setColumnStretch(1, 1)
        l_form.addWidget(g_i)

        # 峰位与半高宽
        g_p = QGroupBox()
        gp = QGridLayout(g_p)
        gp.setHorizontalSpacing(8)
        gp.setVerticalSpacing(6)
        self._tr_items += [(g_p, "group.peaks", "group")]

        self.chk_si = QCheckBox()
        self.chk_si.setChecked(True)
        self._tr_items.append((self.chk_si, "peak.enable_si", "text"))

        self.sp_tt002 = _spin(0.0, 160.0, 0.0, 0.001, 4)
        self.sp_fw002 = _spin(0.0, 10.0, 0.0, 0.005, 4)
        self.sp_si = _spin(0.0, 160.0, 0.0, 0.001, 4)
        self.sp_si_ref = _spin(0.0, 160.0, 28.44186, 0.001, 5)
        self.cb_la = QComboBox()
        self.sp_la = _spin(0.0, 160.0, 0.0, 0.001, 4)
        self.sp_fw_la = _spin(0.0, 10.0, 0.0, 0.005, 4)
        for w in (self.sp_tt002, self.sp_fw002, self.sp_si, self.sp_la, self.sp_fw_la):
            w.setSpecialValueText("—")   # 0 显示为占位符：提示尚未输入实测值

        gp.addWidget(_label(), 0, 0)                 # 占位：表头行由 retranslate 填
        hdr_tt = _label(); hdr_fw = _label()
        self._tr_items += [(hdr_tt, "peak.two_theta", "text"), (hdr_fw, "peak.fwhm", "text")]
        gp.addWidget(hdr_tt, 0, 1)
        gp.addWidget(hdr_fw, 0, 2)

        lab_002 = _label(); lab_si = _label(); lab_si_ref = _label()
        lab_la = _label()
        self._tr_items += [(lab_002, "peak.c002", "text"), (lab_si, "peak.si111", "text"),
                           (lab_si_ref, "peak.si_ref", "text"), (lab_la, "peak.la", "text")]
        gp.addWidget(lab_002, 1, 0); gp.addWidget(self.sp_tt002, 1, 1); gp.addWidget(self.sp_fw002, 1, 2)
        gp.addWidget(self.chk_si, 2, 0, 1, 3)
        gp.addWidget(lab_si, 3, 0); gp.addWidget(self.sp_si, 3, 1)
        gp.addWidget(lab_si_ref, 4, 0); gp.addWidget(self.sp_si_ref, 4, 1)
        gp.addWidget(self.cb_la, 5, 0, 1, 1)
        gp.addWidget(self.sp_la, 5, 1); gp.addWidget(self.sp_fw_la, 5, 2)

        self.lb_hint_002 = _hint()
        self.lb_hint_si = _hint()
        self._tr_items += [(self.lb_hint_002, "peak.hint_002", "text"),
                           (self.lb_hint_si, "peak.hint_si", "text")]
        gp.addWidget(self.lb_hint_002, 6, 0, 1, 3)
        gp.addWidget(self.lb_hint_si, 7, 0, 1, 3)
        gp.setColumnStretch(1, 1)
        gp.setColumnStretch(2, 1)
        l_form.addWidget(g_p)

        # 仪器宽化
        g_b = QGroupBox()
        gb = QGridLayout(g_b)
        gb.setHorizontalSpacing(8)
        gb.setVerticalSpacing(6)
        self._tr_items += [(g_b, "group.broadening", "group")]
        self.cb_br_mode = QComboBox()
        self.sp_inst_002 = _spin(0.0, 5.0, 0.1000, 0.005, 4)
        self.sp_inst_la = _spin(0.0, 5.0, 0.1600, 0.005, 4)
        self.cb_sub = QComboBox()
        for row, (key, w) in enumerate((("br.mode", self.cb_br_mode),
                                        ("br.inst002", self.sp_inst_002),
                                        ("br.instla", self.sp_inst_la),
                                        ("br.sub_mode", self.cb_sub))):
            lb = _label()
            self._tr_items.append((lb, key, "text"))
            gb.addWidget(lb, row, 0)
            gb.addWidget(w, row, 1)
        self.lb_cag = _hint()
        gb.addWidget(self.lb_cag, 5, 0, 1, 2)
        gb.setColumnStretch(1, 1)
        l_form.addWidget(g_b)
        l_form.addStretch(1)

        left_lay.addWidget(l_scroll, 1)
        split.addWidget(left)

        # ---------------- 右：结果 ----------------
        right = QWidget()
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(6, 0, 0, 0)
        r_lay.setSpacing(8)

        self.lb_result_title = _label(bold=True)
        self._tr_items.append((self.lb_result_title, "result.title", "text"))
        r_lay.addWidget(self.lb_result_title)

        cards = QHBoxLayout()
        cards.setSpacing(8)
        self.card_g = _Metric()
        self.card_lc = _Metric()
        self.card_la = _Metric()
        self.card_d = _Metric()
        for c, key in ((self.card_g, "result.g"), (self.card_lc, "result.lc"),
                       (self.card_la, "result.la"), (self.card_d, "result.d002")):
            c.title.setText(tr(key))
            self._tr_items.append((c.title, key, "text"))
            cards.addWidget(c, 1)
        r_lay.addLayout(cards)

        self.lb_formula = _hint()
        self._tr_items.append((self.lb_formula, "result.formula", "text"))
        r_lay.addWidget(self.lb_formula)

        self.lb_detail = _label(bold=True)
        self._tr_items.append((self.lb_detail, "result.detail", "text"))
        r_lay.addWidget(self.lb_detail)
        self.tbl_detail = QTableWidget(0, 3)
        self.tbl_detail.verticalHeader().setVisible(False)
        self.tbl_detail.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_detail.setSelectionMode(QTableWidget.NoSelection)
        self.tbl_detail.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_detail.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tbl_detail.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tbl_detail.setColumnWidth(1, 132)
        self.tbl_detail.setColumnWidth(2, 62)
        r_lay.addWidget(self.tbl_detail, 3)

        self.lb_warn = _label(bold=True)
        self._tr_items.append((self.lb_warn, "result.warnings", "text"))
        r_lay.addWidget(self.lb_warn)
        self.txt_warn = QTextEdit()
        self.txt_warn.setObjectName("warnBox")
        self.txt_warn.setReadOnly(True)
        self.txt_warn.setMinimumHeight(96)
        r_lay.addWidget(self.txt_warn, 1)

        btns = QHBoxLayout()
        self.btn_calc = QPushButton()
        self.btn_copy = QPushButton(); self.btn_copy.setObjectName("ghost")
        self.btn_txt = QPushButton(); self.btn_txt.setObjectName("ghost")
        self.btn_csv = QPushButton(); self.btn_csv.setObjectName("ghost")
        self.btn_reset = QPushButton(); self.btn_reset.setObjectName("ghost")
        for b, key in ((self.btn_calc, "btn.calculate"), (self.btn_copy, "btn.copy"),
                       (self.btn_txt, "btn.export_txt"), (self.btn_csv, "btn.export_csv"),
                       (self.btn_reset, "btn.reset")):
            self._tr_items.append((b, key, "text"))
            btns.addWidget(b)
        btns.insertStretch(0, 1)
        r_lay.addLayout(btns)

        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([560, 720])

        # ---- 信号 ----
        self.cb_target.currentIndexChanged.connect(self._on_target_changed)
        self.sp_lambda.valueChanged.connect(self._on_lambda_changed)
        self.sp_k_lc.valueChanged.connect(self._schedule_calc)
        self.sp_k_la.valueChanged.connect(self._schedule_calc)
        self.sp_tt002.valueChanged.connect(self._schedule_calc)
        self.sp_fw002.valueChanged.connect(self._schedule_calc)
        self.sp_si.valueChanged.connect(self._schedule_calc)
        self.sp_si_ref.valueChanged.connect(self._on_si_ref_edited)
        self.chk_si.toggled.connect(self._schedule_calc)
        self.cb_la.currentIndexChanged.connect(self._on_la_mode_changed)
        self.sp_la.valueChanged.connect(self._schedule_calc)
        self.sp_fw_la.valueChanged.connect(self._schedule_calc)
        self.cb_br_mode.currentIndexChanged.connect(self._on_br_mode_changed)
        self.sp_inst_002.valueChanged.connect(self._schedule_calc)
        self.sp_inst_la.valueChanged.connect(self._schedule_calc)
        self.cb_sub.currentIndexChanged.connect(self._schedule_calc)
        self.btn_calc.clicked.connect(self._recalc)
        self.btn_copy.clicked.connect(self._copy_report)
        self.btn_txt.clicked.connect(lambda: self._export_report("txt"))
        self.btn_csv.clicked.connect(lambda: self._export_report("csv"))
        self.btn_reset.clicked.connect(self._reset_inputs)
        for w in (self.ed_sample, self.ed_client, self.ed_operator, self.ed_note):
            w.textChanged.connect(self._schedule_calc)
        return page

    # ================================================================ 谱图页
    def _build_tab_pattern(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        bar = QHBoxLayout()
        self.btn_open = QPushButton()
        self._tr_items.append((self.btn_open, "pat.open", "text"))
        self.lb_pat_info = _hint()
        self.lb_min_h = _label(); self.lb_min_d = _label()
        self._tr_items += [(self.lb_min_h, "pat.min_height", "text"),
                           (self.lb_min_d, "pat.min_dist", "text")]
        self.sp_min_h = _spin(0.0, 1.0, 0.01, 0.005, 3)
        self.sp_min_d = _spin(0.05, 5.0, 0.30, 0.05, 2)
        self.btn_find = QPushButton()
        self._tr_items.append((self.btn_find, "pat.find", "text"))
        bar.addWidget(self.btn_open)
        bar.addSpacing(10)
        bar.addWidget(self.lb_min_h); bar.addWidget(self.sp_min_h)
        bar.addWidget(self.lb_min_d); bar.addWidget(self.sp_min_d)
        bar.addWidget(self.btn_find)
        bar.addStretch(1)
        lay.addLayout(bar)
        lay.addWidget(self.lb_pat_info)

        # 定点拟合（弱峰专用：石墨 (110) 强度常低于 (002) 的 5%，易被阈值滤掉）
        bar2 = QHBoxLayout()
        self.lb_direct = _label()
        self.sp_direct = _spin(0.0, 160.0, 77.5040, 0.001, 4)
        self.btn_direct = QPushButton()
        self.btn_direct.setObjectName("ghost")
        self._tr_items += [(self.lb_direct, "pat.direct", "text"),
                           (self.btn_direct, "pat.direct_btn", "text")]
        bar2.addWidget(self.lb_direct)
        bar2.addWidget(self.sp_direct)
        bar2.addWidget(self.btn_direct)
        bar2.addStretch(1)
        lay.addLayout(bar2)

        split = QSplitter(Qt.Vertical)
        self.canvas = PlotCanvas()
        self.canvas.empty_text = tr("pat.empty")
        split.addWidget(self.canvas)

        bottom = QWidget()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(0, 4, 0, 0)
        bl.setSpacing(6)
        hdr = QHBoxLayout()
        self.lb_peaks = _label(bold=True)
        self._tr_items.append((self.lb_peaks, "pat.peaks", "text"))
        hdr.addWidget(self.lb_peaks)
        hdr.addStretch(1)
        self.chk_labels = QCheckBox()
        self.chk_labels.setChecked(True)
        self._tr_items.append((self.chk_labels, "pat.show_labels", "text"))
        hdr.addWidget(self.chk_labels)
        hdr.addSpacing(6)
        self.chk_centroid = QCheckBox()
        self.chk_centroid.setChecked(True)
        self._tr_items.append((self.chk_centroid, "pat.show_centroid", "text"))
        self._tr_items.append((self.chk_centroid, "pat.centroid_tip", "tooltip"))
        hdr.addWidget(self.chk_centroid)
        hdr.addSpacing(8)
        self.lb_marker_hint = _hint()
        self.lb_marker_hint.setWordWrap(False)  # 一行显示，避免挤压峰表标题
        self._tr_items.append((self.lb_marker_hint, "pat.hint_marker", "text"))
        hdr.addWidget(self.lb_marker_hint)
        bl.addLayout(hdr)

        self.tbl_peaks = QTableWidget(0, 8)
        self.tbl_peaks.verticalHeader().setVisible(False)
        self.tbl_peaks.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_peaks.setSelectionBehavior(QTableWidget.SelectRows)
        self.tbl_peaks.setSelectionMode(QTableWidget.SingleSelection)
        self.tbl_peaks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_peaks.setMinimumHeight(190)
        bl.addWidget(self.tbl_peaks, 1)

        row = QHBoxLayout()
        self.btn_use002 = QPushButton(); self.btn_use002.setObjectName("ghost")
        self.btn_usela = QPushButton(); self.btn_usela.setObjectName("ghost")
        self.btn_usesi = QPushButton(); self.btn_usesi.setObjectName("ghost")
        self.btn_cen002 = QPushButton(); self.btn_cen002.setObjectName("ghost")
        self.btn_censi = QPushButton(); self.btn_censi.setObjectName("ghost")
        for b in (self.btn_cen002, self.btn_censi):
            self._tr_items.append((b, "pat.centroid_tip", "tooltip"))
        self.btn_del_peak = QPushButton(); self.btn_del_peak.setObjectName("ghost")
        for b, key in ((self.btn_use002, "pat.use_002"), (self.btn_usela, "pat.use_la"),
                       (self.btn_usesi, "pat.use_si"),
                       (self.btn_cen002, "pat.cen_002"), (self.btn_censi, "pat.cen_si"),
                       (self.btn_del_peak, "pat.del_peak")):
            self._tr_items.append((b, key, "text"))
            row.addWidget(b)
        row.addStretch(1)
        bl.addLayout(row)
        split.addWidget(bottom)
        split.setSizes([400, 340])
        lay.addWidget(split, 1)

        self.btn_open.clicked.connect(self._open_pattern)
        self.btn_find.clicked.connect(self._do_find_peaks)
        self.btn_direct.clicked.connect(self._fit_at_direct)
        self.tbl_peaks.itemSelectionChanged.connect(self._on_peak_selected)
        self.chk_labels.toggled.connect(self._toggle_peak_labels)
        self.btn_use002.clicked.connect(lambda: self._use_peak("002"))
        self.btn_usela.clicked.connect(lambda: self._use_peak("la"))
        self.btn_usesi.clicked.connect(lambda: self._use_peak("si"))
        self.chk_centroid.toggled.connect(self._toggle_centroid)
        self.btn_cen002.clicked.connect(lambda: self._use_centroid("002"))
        self.btn_censi.clicked.connect(lambda: self._use_centroid("si"))
        self.btn_del_peak.clicked.connect(self._delete_peak)
        # 峰表里按 Delete 等同"删除选中峰"
        QShortcut(QKeySequence.Delete, self.tbl_peaks,
                  context=Qt.WidgetShortcut, activated=self._delete_peak)
        return page

    # ================================================================ Si 标样页
    def _build_tab_inst(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        bar = QHBoxLayout()
        self.btn_open_std = QPushButton()
        self._tr_items.append((self.btn_open_std, "inststd.open", "text"))
        self.btn_detect = QPushButton(); self.btn_detect.setObjectName("ghost")
        self.btn_fit = QPushButton()
        self._tr_items += [(self.btn_detect, "inststd.auto", "text"),
                           (self.btn_fit, "inststd.fit", "text")]
        bar.addWidget(self.btn_open_std)
        bar.addWidget(self.btn_detect)
        bar.addWidget(self.btn_fit)
        bar.addStretch(1)
        lay.addLayout(bar)

        self.lb_std_info = _hint()
        self._tr_items.append((self.lb_std_info, "inststd.empty", "text"))
        lay.addWidget(self.lb_std_info)

        self.tbl_si = QTableWidget(0, 5)
        self.tbl_si.verticalHeader().setVisible(False)
        self.tbl_si.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_si.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for c in range(1, 5):
            self.tbl_si.horizontalHeader().setSectionResizeMode(c, QHeaderView.Stretch)
        lay.addWidget(self.tbl_si, 1)

        self.lb_cag_result = _label(bold=True)
        lay.addWidget(self.lb_cag_result)
        self.lb_cag_hint = _hint()
        lay.addWidget(self.lb_cag_hint)

        row = QHBoxLayout()
        self.btn_apply_cag = QPushButton()
        self._tr_items.append((self.btn_apply_cag, "inststd.apply", "text"))
        row.addWidget(self.btn_apply_cag)
        row.addStretch(1)
        lay.addLayout(row)

        self.btn_open_std.clicked.connect(self._open_std_pattern)
        self.btn_detect.clicked.connect(self._detect_si_peaks)
        self.btn_fit.clicked.connect(self._fit_caglioti)
        self.btn_apply_cag.clicked.connect(self._apply_caglioti)
        return page

    # ================================================================ 方法页
    def _build_tab_method(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        self.txt_method = QTextBrowser()
        self.txt_method.setOpenExternalLinks(False)
        self.txt_method.setStyleSheet("QTextBrowser { background: #ffffff; border: 1px solid #e2e8f0;"
                                      " border-radius: 8px; padding: 8px; }")
        lay.addWidget(self.txt_method)
        return page

    # ================================================================ 菜单 / 状态栏
    def _build_menus(self) -> None:
        mb = self.menuBar()

        self.m_file = mb.addMenu("")
        self._tr_items.append((self.m_file, "menu.file", "menu"))
        self.act_open = QAction(self)
        self.act_open.triggered.connect(self._open_pattern)
        self._tr_items.append((self.act_open, "menu.open_pattern", "text"))
        self.m_file.addAction(self.act_open)
        self.m_file.addSeparator()
        self.act_txt = QAction(self); self.act_txt.triggered.connect(lambda: self._export_report("txt"))
        self.act_csv = QAction(self); self.act_csv.triggered.connect(lambda: self._export_report("csv"))
        self._tr_items += [(self.act_txt, "menu.export_txt", "text"),
                           (self.act_csv, "menu.export_csv", "text")]
        self.m_file.addAction(self.act_txt)
        self.m_file.addAction(self.act_csv)
        self.m_file.addSeparator()
        self.act_exit = QAction(self); self.act_exit.triggered.connect(self.close)
        self._tr_items.append((self.act_exit, "menu.exit", "text"))
        self.m_file.addAction(self.act_exit)

        self.m_lang = mb.addMenu("")
        self._tr_items.append((self.m_lang, "menu.language", "menu"))
        grp = QActionGroup(self)
        grp.setExclusive(True)
        self._lang_actions = {}
        for code in T.LANGS:
            act = QAction(T.LANG_NAMES[code], self, checkable=True)
            act.setChecked(code == T.current_language())
            act.triggered.connect(lambda _c=False, code=code: self._switch_language(code))
            grp.addAction(act)
            self.m_lang.addAction(act)
            self._lang_actions[code] = act

        self.m_help = mb.addMenu("")
        self._tr_items.append((self.m_help, "menu.help", "menu"))
        self.act_brief = QAction(self); self.act_brief.triggered.connect(self._show_brief)
        self.act_method = QAction(self); self.act_method.triggered.connect(self._show_method)
        self.act_example = QAction(self); self.act_example.triggered.connect(self._load_example)
        self.act_about = QAction(self); self.act_about.triggered.connect(self._show_about)
        self.act_copyr = QAction(self); self.act_copyr.triggered.connect(self._show_copyright)
        self.act_qt = QAction(self); self.act_qt.triggered.connect(self._show_about_qt)
        self._tr_items += [(self.act_brief, "menu.brief", "text"),
                           (self.act_method, "menu.method", "text"),
                           (self.act_example, "menu.example", "text"),
                           (self.act_about, "menu.about", "text"),
                           (self.act_copyr, "menu.copyright", "text"),
                           (self.act_qt, "menu.about_qt", "text")]
        self.m_help.addAction(self.act_brief)
        self.m_help.addAction(self.act_method)
        self.m_help.addAction(self.act_example)
        self.m_help.addSeparator()
        self.m_help.addAction(self.act_about)
        self.m_help.addAction(self.act_copyr)
        self.m_help.addAction(self.act_qt)
        self.act_reg = None
        if self._reg is not None:
            self.m_help.addSeparator()
            self._reg.add_help_action(self.m_help, self)

    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        self.lb_status = QLabel("")
        if self._reg is not None:
            # 安装版：消息在左，注册状态右对齐（沿用家族模块的默认排布）
            sb.addWidget(self.lb_status)
            self._reg_label = self._reg.attach_status_label(sb, self)
        else:
            # 内部评估版：评估提示居中于整条状态栏。
            # 左消息与右侧等宽占位各占 stretch 1，标签夹在中间即真正居中。
            box = QWidget()
            lay = QHBoxLayout(box)
            lay.setContentsMargins(4, 0, 4, 0)
            lay.setSpacing(0)
            lay.addWidget(self.lb_status, 1)
            self._reg_label = QLabel("")
            self._reg_label.setObjectName("statusEval")
            self._reg_label.setAlignment(Qt.AlignCenter)
            lay.addWidget(self._reg_label, 0)
            lay.addWidget(QWidget(), 1)
            sb.addPermanentWidget(box, 1)

    # ================================================================ 语言
    def _retranslate(self) -> None:
        self.setWindowTitle(tr("app.title"))
        self.btn_hint.setToolTip(tr("hint.tooltip"))
        for item in self._tr_items:
            widget, key, kind = item
            if kind == "group":
                widget.setTitle(tr(key))
            elif kind == "menu":
                widget.setTitle(tr(key))
            elif kind == "text":
                text = tr(key)
                if isinstance(widget, QAction):
                    widget.setText(text)
                else:
                    widget.setText(text)
            elif kind == "tooltip":
                widget.setToolTip(tr(key))

        self.tabs.setTabText(0, tr("tab.calc"))
        self.tabs.setTabText(1, tr("tab.pattern"))
        self.tabs.setTabText(2, tr("tab.inst"))
        self.tabs.setTabText(3, tr("tab.method"))

        # 动态文案
        self.act_about.setText(tr("menu.about", app=APP_NAME))
        self.btn_open.setText(tr("pat.open"))
        self.btn_open_std.setText(tr("inststd.open"))
        self.canvas.empty_text = tr("pat.empty")
        self.canvas.x_label = "2θ (°)"
        self.canvas.y_label = "Intensity"
        self._fill_la_combo()
        self._fill_br_combo()
        self._fill_target_combo()
        self._fill_headers()
        self.txt_method.setHtml(tr("method.html"))
        if self._reg_label is not None and self._reg is None:
            self._reg_label.setText(tr("status.internal_eval"))
        self.lb_status.setText(tr("status.ready"))
        self._refresh_broadening_state()
        self._refresh_banner()
        self._refresh_result()

    def _switch_language(self, code: str) -> None:
        if code == T.current_language():
            return
        T.set_language(code)
        registration.set_language(code)
        try:
            QSettings(ORG_NAME, APP_ID).setValue("language", code)
        except Exception:  # noqa: BLE001 —— 设置写入失败不影响使用
            pass
        self._retranslate()
        self.lb_status.setText(tr("msg.lang_switch", lang=T.LANG_NAMES[code]))
        if self.peaks:
            self._fill_peak_table()

    # ================================================================ 下拉框与表头
    def _fill_target_combo(self) -> None:
        cur = self.cb_target.currentIndex()
        self.cb_target.blockSignals(True)
        self.cb_target.clear()
        self.cb_target.addItems(list(eng.WAVELENGTHS.keys()) + ["自定义"])
        self.cb_target.setCurrentIndex(max(cur, 0))
        self.cb_target.blockSignals(False)

    def _fill_la_combo(self) -> None:
        cur = self.cb_la.currentIndex()
        self.cb_la.blockSignals(True)
        self.cb_la.clear()
        self.cb_la.addItems([tr("la.peak.110"), tr("la.peak.100"), tr("la.peak.none")])
        self.cb_la.setCurrentIndex(cur if cur >= 0 else 0)
        self.cb_la.blockSignals(False)

    def _fill_br_combo(self) -> None:
        i_mode = self.cb_br_mode.currentIndex()
        i_sub = self.cb_sub.currentIndex()
        for cb, items, cur in (
            (self.cb_br_mode, [tr("br.mode.caglioti"), tr("br.mode.direct"), tr("br.mode.none")], i_mode),
            (self.cb_sub, [tr("br.sub.gauss"), tr("br.sub.lorentz"), tr("br.sub.none")], i_sub),
        ):
            cb.blockSignals(True)
            cb.clear()
            cb.addItems(items)
            cb.setCurrentIndex(max(cur, 0))
            cb.blockSignals(False)

    def _fill_headers(self) -> None:
        self.tbl_detail.setHorizontalHeaderLabels(
            [tr("common.name"), tr("common.value"), tr("common.unit")])
        self.tbl_peaks.setHorizontalHeaderLabels(
            [tr("pat.col.two_theta"), tr("pat.col.d"), tr("pat.col.fwhm"),
             tr("pat.col.height"), tr("pat.col.rel"), tr("pat.col.eta"), tr("pat.col.r2"),
             tr("pat.col.centroid")])
        self.tbl_si.setHorizontalHeaderLabels(
            [tr("inststd.col.hkl"), tr("inststd.col.theory"), tr("inststd.col.obs"),
             tr("inststd.col.delta"), tr("inststd.col.fwhm")])

    # ================================================================ 参数联动
    def _on_target_changed(self) -> None:
        idx = self.cb_target.currentIndex()
        keys = list(eng.WAVELENGTHS.keys())
        custom = idx >= len(keys)
        self.sp_lambda.setEnabled(custom)
        if not custom and 0 <= idx < len(keys):
            self.sp_lambda.blockSignals(True)
            self.sp_lambda.setValue(eng.WAVELENGTHS[keys[idx]])
            self.sp_lambda.blockSignals(False)
        self._sync_lambda_widgets()
        self._schedule_calc()

    def _on_lambda_changed(self) -> None:
        self._sync_lambda_widgets()
        self._schedule_calc()

    def _sync_lambda_widgets(self) -> None:
        """波长变化时刷新 Si(111) 标准 2θ（除非用户手动改过）与理论标记线。"""
        lam = self.sp_lambda.value()
        if self._si_ref_auto:
            self.sp_si_ref.blockSignals(True)
            self.sp_si_ref.setValue(eng.si_two_theta((1, 1, 1), lam))
            self.sp_si_ref.blockSignals(False)
        try:
            ref = eng.graphite_reference_table(lam)
            self.canvas.set_markers([(ref["002"]["two_theta"], "C(002)"),
                                     (ref["100"]["two_theta"], "C(100)"),
                                     (ref["110"]["two_theta"], "C(110)")])
            mode = self._la_mode()
            if mode in ("110", "100"):
                self.sp_direct.blockSignals(True)
                self.sp_direct.setValue(ref[mode]["two_theta"])
                self.sp_direct.blockSignals(False)
        except Exception:  # noqa: BLE001 —— 极端波长下不更新标记
            pass

    def _on_si_ref_edited(self) -> None:
        self._si_ref_auto = False
        self._schedule_calc()

    def _on_la_mode_changed(self) -> None:
        mode = self._la_mode()
        enabled = mode in ("110", "100")
        self.sp_la.setEnabled(enabled)
        self.sp_fw_la.setEnabled(enabled)
        if enabled:
            try:
                ref = eng.graphite_reference_table(self.sp_lambda.value())[mode]
                self.sp_la.blockSignals(True)
                if self.sp_la.value() <= 0 or abs(self.sp_la.value() - ref["two_theta"]) > 3.0:
                    self.sp_la.setValue(ref["two_theta"])
                self.sp_la.blockSignals(False)
                self.sp_direct.blockSignals(True)
                self.sp_direct.setValue(ref["two_theta"])
                self.sp_direct.blockSignals(False)
            except Exception:  # noqa: BLE001
                pass
        self._refresh_banner()
        self._schedule_calc()

    def _on_br_mode_changed(self) -> None:
        mode = self.cb_br_mode.currentIndex()
        self.sp_inst_002.setEnabled(mode == 1)
        self.sp_inst_la.setEnabled(mode == 1)
        self._refresh_broadening_state()
        self._schedule_calc()

    def _la_mode(self) -> str:
        return {0: "110", 1: "100"}.get(self.cb_la.currentIndex(), "none")

    def _schedule_calc(self) -> None:
        self._calc_timer.start()

    # ================================================================ 计算
    def _build_input(self) -> eng.AnalysisInput:
        br_mode = {0: "caglioti", 1: "table", 2: "none"}.get(self.cb_br_mode.currentIndex(), "caglioti")
        sub = {0: "gauss", 1: "lorentz", 2: "none"}.get(self.cb_sub.currentIndex(), "gauss")
        # 0 表示「未输入」，不能当作实测值参与校正/计算
        si_obs = self.sp_si.value() if (self.chk_si.isChecked() and self.sp_si.value() > 0) else None
        la_mode = self._la_mode()
        la_obs = self.sp_la.value() if la_mode != "none" else 0.0
        la_fw = self.sp_fw_la.value() if la_mode != "none" else 0.0
        return eng.AnalysisInput(
            wavelength=self.sp_lambda.value(),
            d002_obs=self.sp_tt002.value(),
            fwhm002_obs=self.sp_fw002.value(),
            si111_obs=si_obs,
            si111_ref=self.sp_si_ref.value() if si_obs else None,
            la_peak=la_mode if la_obs > 0 else "none",
            la_obs=la_obs,
            fwhm_la_obs=la_fw,
            inst_mode=br_mode,
            caglioti=self.caglioti if br_mode == "caglioti" else None,
            inst_fwhm_002=self.sp_inst_002.value(),
            inst_fwhm_la=self.sp_inst_la.value(),
            sub_mode=sub,
            k_lc=self.sp_k_lc.value(),
            k_la=self.sp_k_la.value(),
            sample=self.ed_sample.text().strip(),
            client=self.ed_client.text().strip(),
            operator=self.ed_operator.text().strip(),
            note=self.ed_note.text().strip(),
        )

    def _recalc(self) -> None:
        try:
            inp = self._build_input()
            res = eng.analyze(inp)
        except Exception as exc:  # noqa: BLE001 —— 缺输入时静默降级
            self.result = None
            if self.sp_tt002.value() <= 0:
                self._refresh_result()          # 尚未输入：显示引导文案，不报错
                self.lb_status.setText(tr("status.ready"))
            else:
                self._refresh_result(error=str(exc))
            return
        self.result = res
        self._refresh_result()
        self.lb_status.setText(tr("status.calc_done", g=f"{res.g_percent:.1f}",
                                  lc=f"{res.lc_nm:.2f}"))
        self._refresh_banner()

    def _refresh_result(self, error: str = "") -> None:
        res = self.result
        if res is None or error:
            for c in (self.card_g, self.card_lc, self.card_la, self.card_d):
                c.set_value("—")
            self.tbl_detail.setRowCount(0)
            self.txt_warn.setPlainText(tr("result.empty") if not error else
                                       tr("msg.calc_fail", err=error))
            return

        self.card_g.set_value(f"{res.g_percent:.1f} %")
        self.card_lc.set_value(f"{res.lc_nm:.2f} nm" if res.lc_nm else "—")
        self.card_la.set_value(f"{res.la_nm:.2f} nm" if res.la_nm else "—")
        self.card_d.set_value(f"{res.d002_nm:.5f} nm")

        inp = self._build_input()
        rows = eng.result_rows(inp, res)
        self.tbl_detail.setRowCount(len(rows))
        for i, (name, val, unit) in enumerate(rows):
            self.tbl_detail.setItem(i, 0, QTableWidgetItem(name))
            it_v = QTableWidgetItem(val)
            it_v.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_detail.setItem(i, 1, it_v)
            self.tbl_detail.setItem(i, 2, QTableWidgetItem(unit))

        self._warn_lines = list(res.warnings)
        if res.warnings:
            self.txt_warn.setPlainText("\n".join(f"· {w}" for w in res.warnings))
        else:
            self.txt_warn.setPlainText(tr("result.no_warning"))

    def _refresh_banner(self) -> None:
        """顶部横幅：按当前配置给出 (110)/(100) 与 Si 标样是否到位的判据。"""
        mode = self._la_mode()
        la_tt = self.sp_la.value() if mode != "none" else 0.0
        lo, hi = eng.TT_110_WINDOW
        scan_hi = self.pattern.span[1] if self.pattern is not None else None

        if mode in ("110", "100") and la_tt <= 0:
            # 尚未输入 La 峰实测值：只给测试建议，不做判据结论
            self.banner.setObjectName("bannerInfo")
            text = tr("peak.hint_la")
        elif mode == "110":
            if lo <= la_tt <= hi:
                self.banner.setObjectName("bannerOk")
                key = "banner.ok_110" if self.caglioti else "banner.ok_110_nobr"
                text = tr(key, tt=la_tt)
            else:
                self.banner.setObjectName("bannerWarn")
                text = tr("banner.warn_110_out", tt=la_tt)
        elif mode == "100":
            self.banner.setObjectName("bannerWarn")
            text = tr("banner.warn_100")
        else:
            self.banner.setObjectName("bannerInfo")
            text = tr("peak.hint_la")

        if scan_hi is not None and mode == "110" and scan_hi < hi:
            text += tr("banner.scan_short", hi=scan_hi)
        self.banner.setText(text)
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)

    def _refresh_broadening_state(self) -> None:
        if self.caglioti is None:
            self.lb_cag.setText(tr("br.caglioti_empty"))
            self.lb_cag_result.setText(tr("inststd.result_empty"))
            self.lb_cag_hint.setText(tr("inststd.result_empty"))
        else:
            self.lb_cag.setText(tr("br.caglioti_state", text=self.caglioti.as_text()))
            self.lb_cag_result.setText(tr("inststd.result", text=self.caglioti.as_text()))
            self.lb_cag_hint.setText(tr("inststd.applied"))

    def _reset_inputs(self) -> None:
        self.sp_tt002.setValue(0.0)
        self.sp_fw002.setValue(0.0)
        self.sp_si.setValue(0.0)
        self.sp_la.setValue(0.0)
        self.sp_fw_la.setValue(0.0)
        for e in (self.ed_sample, self.ed_client, self.ed_operator, self.ed_note):
            e.clear()
        self._recalc()

    # ================================================================ 谱图
    def _open_pattern(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg.open_pattern"), "",
                                              tr("filter.pattern"))
        if not path:
            return
        try:
            pat = eng.read_pattern(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.error"), str(exc))
            return
        self.pattern = pat
        self.peaks = []
        self.centroids = []
        self.canvas.set_pattern(pat)
        self.canvas.set_peaks([])
        self.canvas.set_centroids([])
        self.canvas.set_selected(-1)
        self.tbl_peaks.setRowCount(0)
        lo, hi = pat.span
        step = float(np.median(np.diff(pat.two_theta))) if len(pat) > 1 else 0.0
        self.lb_pat_info.setText(tr("pat.info_loaded", name=pat.name, n=len(pat),
                                    lo=lo, hi=hi, step=step))
        self.lb_status.setText(tr("status.pattern_loaded", name=pat.name, n=len(pat),
                                  lo=lo, hi=hi))
        self.tabs.setCurrentIndex(1)
        self._do_find_peaks()

    def _do_find_peaks(self) -> None:
        if self.pattern is None:
            return
        self.peaks = eng.find_peaks(self.pattern.two_theta, self.pattern.intensity,
                                    min_height_ratio=self.sp_min_h.value(),
                                    min_distance_deg=self.sp_min_d.value(),
                                    prominence_ratio=max(0.002, self.sp_min_h.value() * 0.5))
        lam = self.sp_lambda.value()
        for p in self.peaks:
            p.d = eng.d_from_two_theta(p.two_theta, lam)
        self.canvas.set_peaks(self.peaks)
        self.canvas.set_selected(-1)
        self._fill_peak_table()

        # 弱峰提醒：La 用的 (110)/(100) 常低于寻峰阈值，未命中时给出定向拟合入口
        mode = self._la_mode()
        if mode in ("110", "100"):
            try:
                ref = eng.graphite_reference_table(lam)[mode]["two_theta"]
                lo, hi = self.pattern.span
                covered = lo <= ref <= hi
                hit = any(abs(p.two_theta - ref) < 0.6 for p in self.peaks)
                if covered and not hit:
                    self.lb_status.setText(tr("pat.direct_missing", tt=ref))
            except Exception:  # noqa: BLE001
                pass

    def _fit_at_direct(self) -> None:
        """在指定 2θ 附近定向拟合单峰（弱峰，如石墨 (110)）。"""
        if self.pattern is None:
            QMessageBox.information(self, APP_NAME, tr("pat.info"))
            return
        tt = self.sp_direct.value()
        try:
            fit = eng.fit_at_position(self.pattern, tt)
        except ValueError as exc:
            QMessageBox.information(self, APP_NAME, str(exc))
            return
        fit.d = eng.d_from_two_theta(fit.two_theta, self.sp_lambda.value())
        self.peaks = [p for p in self.peaks if abs(p.two_theta - fit.two_theta) > 0.20]
        self.peaks.append(fit)
        self.peaks.sort(key=lambda p: p.two_theta)
        self.canvas.set_peaks(self.peaks)
        self._fill_peak_table()
        for i, p in enumerate(self.peaks):
            if p is fit:
                self.tbl_peaks.selectRow(i)
                self.canvas.set_selected(i)
                break
        self.lb_status.setText(tr("pat.direct_ok", tt=fit.two_theta, fw=fit.fwhm))

    def _refresh_centroids(self) -> None:
        """重算全部识别峰的质心（重心法），并同步到峰表与谱图。"""
        if self.pattern is None or not self.peaks:
            self.centroids = []
        else:
            self.centroids = eng.peak_centroids(self.pattern, self.peaks)
        self.canvas.set_centroids([c.two_theta if c else None for c in self.centroids])

    def _fill_peak_table(self) -> None:
        lam = self.sp_lambda.value()
        self._refresh_centroids()
        ymax = max((p.height for p in self.peaks), default=0.0) or 1.0
        self.tbl_peaks.setRowCount(len(self.peaks))
        for i, p in enumerate(self.peaks):
            d = eng.d_from_two_theta(p.two_theta, lam)
            eta = "—" if not np.isfinite(p.eta) else f"{p.eta:.2f}"
            r2 = "—" if not np.isfinite(p.r2) else f"{p.r2:.4f}"
            cen = self.centroids[i] if i < len(self.centroids) else None
            ctxt = "—" if cen is None else f"{cen.two_theta:.4f}"
            vals = [f"{p.two_theta:.4f}", f"{d:.5f}", f"{p.fwhm:.4f}",
                    f"{p.height:.0f}", f"{100.0 * p.height / ymax:.1f}", eta, r2, ctxt]
            for j, v in enumerate(vals):
                it = QTableWidgetItem(v)
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_peaks.setItem(i, j, it)

    def _on_peak_selected(self) -> None:
        rows = self.tbl_peaks.selectionModel().selectedRows()
        if not rows:
            self.canvas.set_selected(-1)
            return
        self.canvas.set_selected(rows[0].row())

    def _toggle_centroid(self, on: bool) -> None:
        """质心显示开关：峰表 Centroid 列 + 谱图上的质心标记。"""
        self.tbl_peaks.setColumnHidden(7, not bool(on))
        self.canvas.show_centroid = bool(on)
        self.canvas.update()

    def _toggle_peak_labels(self, on: bool) -> None:
        """图上 2θ 角度标注开关（关掉后是一张不带任何标注的干净谱图）。"""
        self.canvas.show_labels = bool(on)
        self.canvas.update()

    def _delete_peak(self) -> None:
        """把误识别的峰从峰表与谱图上删掉（不改变原始谱数据）。"""
        rows = self.tbl_peaks.selectionModel().selectedRows()
        if not rows or rows[0].row() >= len(self.peaks):
            QMessageBox.information(self, APP_NAME, tr("pat.no_peak"))
            return
        i = rows[0].row()
        tt = self.peaks[i].two_theta
        del self.peaks[i]
        self.canvas.set_selected(-1)
        self.canvas.set_peaks(self.peaks)
        self.tbl_peaks.clearSelection()
        self._fill_peak_table()
        self.canvas.update()
        self.lb_status.setText(tr("pat.del_ok", tt=tt))

    def _selected_peak(self) -> eng.PeakFit | None:
        rows = self.tbl_peaks.selectionModel().selectedRows()
        if not rows or rows[0].row() >= len(self.peaks):
            QMessageBox.information(self, APP_NAME, tr("pat.no_peak"))
            return None
        return self.peaks[rows[0].row()]

    def _use_peak(self, kind: str) -> None:
        peak = self._selected_peak()
        if peak is None:
            return
        if kind == "002":
            self.sp_tt002.setValue(peak.two_theta)
            self.sp_fw002.setValue(peak.fwhm)
            if self.lb_pat_info.text():
                pass
        elif kind == "si":
            self.chk_si.setChecked(True)
            self.sp_si.setValue(peak.two_theta)
        else:
            mode = self._la_mode()
            if mode == "none":
                self.cb_la.setCurrentIndex(0)
                mode = "110"
            self.sp_la.setValue(peak.two_theta)
            self.sp_fw_la.setValue(peak.fwhm)
        self.tabs.setCurrentIndex(0)
        self._schedule_calc()
        self.lb_status.setText(tr("pat.filled", tt=peak.two_theta, fw=peak.fwhm))

    def _use_centroid(self, kind: str) -> None:
        """用选中峰的**质心** 2θ 填入计算页。

        与「设为 C(002) / 设为 Si(111)」并存：那一组用 pseudo-Voigt 拟合峰位
        （峰顶），这一组用重心法质心，两种口径都保留，便于对照与复现。
        质心只给出峰位，C(002) 的 FWHM 仍取该峰的拟合值。
        """
        rows = self.tbl_peaks.selectionModel().selectedRows()
        if not rows or rows[0].row() >= len(self.peaks):
            QMessageBox.information(self, APP_NAME, tr("pat.no_peak"))
            return
        i = rows[0].row()
        cen = self.centroids[i] if i < len(self.centroids) else None
        if cen is None:
            QMessageBox.information(self, APP_NAME, tr("pat.cen_missing"))
            return
        peak = self.peaks[i]
        if kind == "002":
            self.sp_tt002.setValue(cen.two_theta)
            self.sp_fw002.setValue(peak.fwhm)
            name = tr("pat.cen_name_002")
        else:
            self.chk_si.setChecked(True)
            self.sp_si.setValue(cen.two_theta)
            name = tr("pat.cen_name_si")
        self.tabs.setCurrentIndex(0)
        self._schedule_calc()
        self.lb_status.setText(tr("pat.cen_filled", name=name, tt=cen.two_theta))

    # ================================================================ Si 标样
    def _open_std_pattern(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg.open_pattern"), "",
                                              tr("filter.pattern"))
        if not path:
            return
        try:
            pat = eng.read_pattern(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.error"), str(exc))
            return
        self.si_pattern = pat
        self.lb_std_info.setText(tr("pat.info_loaded", name=pat.name, n=len(pat),
                                    lo=pat.span[0], hi=pat.span[1],
                                    step=float(np.median(np.diff(pat.two_theta)))))
        self._detect_si_peaks()

    def _detect_si_peaks(self) -> None:
        if self.si_pattern is None:
            return
        self.si_peaks = eng.match_instrument_peaks(self.si_pattern, self.sp_lambda.value())
        self.tbl_si.setRowCount(len(self.si_peaks))
        for i, r in enumerate(self.si_peaks):
            vals = [r["hkl"], f"{r['two_theta_theory']:.4f}", f"{r['two_theta_obs']:.4f}",
                    f"{r['delta']:+.4f}", f"{r['fwhm']:.4f}"]
            for j, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if j:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tbl_si.setItem(i, j, it)
        self.lb_status.setText(tr("inststd.loaded", name=self.si_pattern.name,
                                  n=len(self.si_peaks)))

    def _fit_caglioti(self) -> None:
        pts = [(r["two_theta_obs"], r["fwhm"]) for r in self.si_peaks if r["fwhm"] > 0]
        if len(pts) < 3:
            QMessageBox.warning(self, APP_NAME, tr("inststd.nofit"))
            return
        try:
            self.caglioti = eng.fit_caglioti(pts)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.error"), str(exc))
            return
        self._refresh_broadening_state()
        self.lb_cag_hint.setText(tr("inststd.applied"))
        self._schedule_calc()

    def _apply_caglioti(self) -> None:
        if self.caglioti is None:
            QMessageBox.information(self, APP_NAME, tr("inststd.need_fit"))
            return
        self.cb_br_mode.setCurrentIndex(0)
        self._refresh_broadening_state()
        self.tabs.setCurrentIndex(0)
        self._recalc()
        self.lb_status.setText(tr("inststd.applied"))

    # ================================================================ 报告
    def _copy_report(self) -> None:
        if self.result is None:
            QMessageBox.information(self, APP_NAME, tr("result.empty"))
            return
        text = eng.build_report_text(self._build_input(), self.result,
                                     app_name=APP_NAME, version=APP_VERSION)
        QApplication.clipboard().setText(text)
        self.lb_status.setText(tr("msg.copied"))

    def _export_report(self, kind: str) -> None:
        if self.result is None:
            QMessageBox.information(self, APP_NAME, tr("result.empty"))
            return
        sample = self.ed_sample.text().strip() or "graphite"
        stamp = _dt.datetime.now().strftime("%Y%m%d")
        default = f"{sample}_石墨化度_{stamp}.{kind}"
        filt = tr("filter.txt") if kind == "txt" else tr("filter.csv")
        path, _ = QFileDialog.getSaveFileName(self, tr("dlg.save_report"), default, filt)
        if not path:
            return
        try:
            if kind == "txt":
                text = eng.build_report_text(self._build_input(), self.result,
                                             app_name=APP_NAME, version=APP_VERSION)
                Path(path).write_text(text, encoding="utf-8")
            else:
                eng.write_report_csv(path, self._build_input(), self.result)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.error"), tr("msg.save_fail", err=exc))
            return
        self.lb_status.setText(tr("msg.saved", path=path))

    # ================================================================ 帮助
    def _build_brief_dialog(self) -> QDialog:
        """构造「测试与计算要点」提示对话框（只构造不显示，便于验证与复用）。"""
        dlg = QDialog(self)
        dlg.setObjectName("briefDialog")
        dlg.setWindowTitle(tr("hint.title"))
        dlg.resize(680, 700)
        dlg.setMinimumSize(520, 460)
        lay = QVBoxLayout(dlg)
        tb = QTextBrowser(dlg)
        tb.setObjectName("briefText")
        tb.setOpenExternalLinks(False)
        tb.setHtml(tr("hint.html"))
        lay.addWidget(tb, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        b = QPushButton(tr("btn.close"), dlg)
        b.clicked.connect(dlg.accept)
        row.addWidget(b)
        lay.addLayout(row)
        return dlg

    def _show_brief(self) -> None:
        """小提示图标 / 帮助菜单：一页说明扫描方案与计算链。"""
        self._build_brief_dialog().exec()

    def _show_method(self) -> None:
        self.tabs.setCurrentIndex(3)

    def _load_example(self) -> None:
        """载入岛津 AP_XRD-001 的算例数值，便于试用与培训。

        波长切到文档采用的 Cu Kα1 传统值 1.54056 nm，可精确复现 g = 98.8%；
        改用 CODATA 值（1.5405929）时结果为 98.7%，差异全部来自波长取值。
        """
        keys = list(eng.WAVELENGTHS.keys())
        self.cb_target.setCurrentIndex(keys.index("Cu Kα1 (传统 1.54056)"))
        self.sp_tt002.setValue(26.5584)
        self.sp_fw002.setValue(0.2400)
        self.chk_si.setChecked(True)
        self.sp_si.setValue(28.4541)
        self._si_ref_auto = False
        self.sp_si_ref.setValue(28.44135)
        self.cb_la.setCurrentIndex(0)
        self.sp_la.setValue(77.6200)
        self.sp_fw_la.setValue(0.3400)
        self.cb_br_mode.setCurrentIndex(1)      # 直接给定仪器 FWHM
        self.sp_inst_002.setValue(0.1000)
        self.sp_inst_la.setValue(0.1600)
        self.ed_sample.setText("示例 AP_XRD-001")
        self.ed_client.setText("岛津应用数据集")
        self.tabs.setCurrentIndex(0)
        self._recalc()
        self.lb_status.setText(tr("menu.example_done", g=f"{self.result.g_percent:.2f}"
                                  if self.result else "—"))

    def _show_about(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("menu.about", app=APP_NAME))
        dlg.setMinimumWidth(520)
        lay = QVBoxLayout(dlg)
        logo = res_path("logo-horizontal.png")
        if logo.exists():
            pm = QPixmap(str(logo))
            if not pm.isNull():
                lb = QLabel()
                lb.setPixmap(pm.scaledToWidth(min(420, pm.width()),
                                              Qt.SmoothTransformation))
                lay.addWidget(lb)
        title = _label(APP_NAME, bold=True)
        f = title.font(); f.setPointSizeF(f.pointSizeF() + 4); title.setFont(f)
        lay.addWidget(title)
        lay.addWidget(_label(tr("about.version", version=APP_VERSION, variant=variant_name())))
        lay.addWidget(_label(tr("about.desc")))
        lay.addWidget(_label(tr("about.features"), small=True))
        lay.addWidget(_label(f"{tr('about.contact')}{CONTACT_EMAIL}", small=True))
        lay.addWidget(_label(tr("about.copyright"), small=True))
        row = QHBoxLayout()
        row.addStretch(1)
        b = QPushButton(tr("btn.close"))
        b.clicked.connect(dlg.accept)
        row.addWidget(b)
        lay.addLayout(row)
        dlg.exec()

    def _show_copyright(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("copyright.title", app=APP_NAME))
        dlg.resize(720, 620)
        lay = QVBoxLayout(dlg)
        tb = QTextBrowser()
        tb.setHtml(f"<h3>{tr('copyright.heading')}</h3>"
                   + tr("copyright.license_zh")
                   + "<hr>" + tr("copyright.license_en")
                   + f"<p><b>{tr('copyright.contact')}</b>{CONTACT_EMAIL}</p>")
        lay.addWidget(tb, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        b = QPushButton(tr("btn.close"))
        b.clicked.connect(dlg.accept)
        row.addWidget(b)
        lay.addLayout(row)
        dlg.exec()

    def _show_about_qt(self) -> None:
        QMessageBox.aboutQt(self, tr("menu.about_qt"))

    # ================================================================ 注册
    def startup_registration(self) -> None:
        if self._reg is None:
            return
        self._reg.startup_check(self)
        self._refresh_reg_label()

    def _refresh_reg_label(self) -> None:
        if self._reg is None or self._reg_label is None:
            return
        registration.refresh_status_label(self._reg_label, self._reg.state)


# ------------------------------------------------------------------------------
# 发布物自检（打包后验证用）
# ------------------------------------------------------------------------------
def _selftest_report() -> str:
    """返回发布物自检文本（不弹窗、不依赖控制台，适合 windowed exe）。"""
    lines = [f"{APP_NAME} v{APP_VERSION}", f"variant = {BUILD_VARIANT}",
             f"frozen = {getattr(sys, 'frozen', False)}"]
    ok = True
    for name in ("app-icon.png", "app-icon.ico", "splash-screen.png", "logo-horizontal.png"):
        p = res_path(name)
        exist = p.exists()
        ok = ok and exist
        lines.append(f"resource {name:<22} {'OK' if exist else 'MISSING'} "
                     f"{p.stat().st_size if exist else 0} bytes")
    marker = bundle_path("internal_eval.marker").exists()
    lines.append(f"internal_eval.marker   {'present' if marker else 'absent'} "
                 f"(expect {'present' if BUILD_VARIANT == 'internal' else 'absent'})")
    if marker != (BUILD_VARIANT == "internal"):
        ok = False

    # 文档算例：Si(111) 28.4541（标准 28.44135）→ C(002) 26.54565 / d002 0.33551
    try:
        inp = eng.AnalysisInput(wavelength=eng.WAVELENGTHS["Cu Kα1 (传统 1.54056)"],
                                d002_obs=26.5584, fwhm002_obs=0.24,
                                si111_obs=28.4541, si111_ref=28.44135,
                                la_peak="110", la_obs=77.62, fwhm_la_obs=0.34,
                                inst_mode="table", inst_fwhm_002=0.10,
                                inst_fwhm_la=0.16, sample="SELFTEST")
        res = eng.analyze(inp)
        checks = [
            ("Δ2θ = -0.01275", abs(res.delta_two_theta + 0.01275) < 1e-6),
            ("2θ(corr) = 26.54565", abs(res.two_theta_002_corr - 26.54565) < 1e-4),
            ("d002 = 0.33551 nm", abs(res.d002_nm - 0.33551) < 3e-5),
            ("g ≈ 98.8%", abs(res.g_percent - 98.8) < 0.15),
            ("Lc > 0", res.lc_nm > 0),
            ("La > 0", res.la_nm > 0),
        ]
        for label, cond in checks:
            ok = ok and cond
            lines.append(f"check {label:<22} {'PASS' if cond else 'FAIL'}")
        report = eng.build_report_text(inp, res, app_name=APP_NAME, version=APP_VERSION)
        good = ("堆叠厚度 Lc" in report) and ("c0/2" not in report)
        ok = ok and good
        lines.append(f"check report content        {'PASS' if good else 'FAIL'}")
    except Exception as exc:  # noqa: BLE001
        ok = False
        lines.append(f"check analyze               FAIL {exc}")

    lines.append("")
    lines.append("RESULT: " + ("PASS" if ok else "FAIL"))
    return "\n".join(lines)


def _write_text_qt(path: Path, text: str) -> bool:
    """用 Qt 写文件（py2exe/受限环境下 Python io 可能被拦，QFile 更稳）。"""
    from PySide6.QtCore import QFile, QIODevice
    f = QFile(str(path))
    if not f.open(QIODevice.WriteOnly | QIODevice.Text):
        return False
    f.write(text.encode("utf-8"))
    f.close()
    return True


# ------------------------------------------------------------------------------
# 入口
# ------------------------------------------------------------------------------
def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    # 发布物自检模式：--selftest [输出路径]
    if "--selftest" in sys.argv:
        idx = sys.argv.index("--selftest")
        default = Path(sys.executable if getattr(sys, "frozen", False)
                       else __file__).resolve().parent / "selftest.log"
        out = Path(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else default
        text = _selftest_report()
        written = _write_text_qt(out, text)
        print(text)
        return 0 if ("RESULT: PASS" in text and written) else 1

    # 截图模式（验证打包后的真实渲染）：--shot <png 路径> [tab 索引]
    if "--shot" in sys.argv:
        idx = sys.argv.index("--shot")
        out = Path(sys.argv[idx + 1])
        tab = int(sys.argv[idx + 2]) if len(sys.argv) > idx + 2 else 0
        win = MainWindow()
        win.show()
        app.processEvents()
        win.tabs.setCurrentIndex(max(0, min(tab, win.tabs.count() - 1)))
        for _ in range(3):
            app.processEvents()
        ok = win.grab().save(str(out), "PNG")
        win.close()
        print(f"screenshot {'OK' if ok else 'FAIL'}: {out}")
        return 0 if ok else 1

    # 恢复上次语言
    try:
        saved = QSettings(ORG_NAME, APP_ID).value("language", "zh")
    except Exception:  # noqa: BLE001
        saved = "zh"
    T.set_language(saved if saved in T.LANGS else "zh")
    registration.set_language(T.current_language())

    icon_file = res_path("app-icon.png")
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))

    # 启动图：必须在主窗口 show() 之后才关闭（防止 quitOnLastWindowClosed 闪退）
    splash = None
    splash_file = res_path("splash-screen.png")
    if splash_file.exists():
        try:
            pm = QPixmap(str(splash_file))
            if not pm.isNull():
                if pm.width() > 960 or pm.height() > 540:
                    pm = pm.scaled(960, 540, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                splash = QSplashScreen(pm)
                splash.setWindowFlags(splash.windowFlags() | Qt.FramelessWindowHint)
                splash.show()
                app.processEvents()
        except Exception:  # noqa: BLE001
            splash = None

    win = MainWindow()
    win.show()

    if BUILD_VARIANT == "setup":
        QTimer.singleShot(300, win.startup_registration)

    if splash is not None:
        QTimer.singleShot(120, splash.close)
        QTimer.singleShot(900, splash.close)   # 兜底：一定收掉启动图

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
