# PolyXRD Graphite

<div align="center">
  <img src="resources/logo-horizontal.png" alt="PolyXRD Graphite" width="420">
</div>

石墨材料 XRD 分析小工具 —— 由 C(002) 峰位给出**石墨化度 g**（以层间距 d002 表达）
与**堆叠厚度 Lc**，由 **(110)**（优先，2θ ≈ 77.5°，需扫到 72–82°）或 **(100)**
（备用，2θ ≈ 42.4°，d ≈ 0.213 nm）给出**微晶尺寸 La**；并用掺入的 Si 内标校正 2θ、
用 Si 标样的全角度谱反算 Caglioti 参数以扣除仪器宽化。

提供两种发行形态：**Setup 安装版**（对外发布，含注册机制）与
**单文件内部评估版**（免安装，内部使用，无注册机制）。

> 当前版本 **v1.0.0** · 界面支持 **简体中文 / English / 日本語**，
> 通过菜单栏「语言」菜单可在软件运行中即时切换（选择记忆在本地）。
>
> Current version **v1.0.0** · UI available in **简体中文 / English / 日本語**,
> switchable at runtime from the **Language** menu (top-right); the choice is remembered locally.
>
> バージョン **v1.0.0** · UI は **简体中文 / English / 日本語** に対応、
> 「言語」メニューから実行中に切り替え可能（設定はローカルに保存）。

PolyXRD 家族成员：[PolyXRD](https://github.com/PolyXRD)（数据分析）·
PolyXRD-Converter（格式转换）· PolyXRD-SynthPattern（谱图合成）·
PolyXRD-RutAna（TiO₂ 晶型比）· **Graphite（石墨化度 / Lc / La）**

## 功能

**① 计算页**
- 样品信息（样品名 / 委托单位 / 测试人 / 备注）直接写入报告
- 靶材与波长：Cu/Co/Mo/Fe/Cr 的 Kα1、Kα2、Kα 平均，或自定义 λ
  （Cu Kα1 同时提供 1.5405929 CODATA 与 1.54056 传统值，便于复现既有报告）
- 峰输入：C(002) 的 2θ 与 FWHM、Si(111) 内标实测与标准 2θ、La 峰（(110) / (100) / 不计算）
- 结果卡：g、Lc、La、d002；明细表逐项留痕（含 Δ2θ、各峰仪器宽化、纯宽化 β）
- 判据提示：g 越界（<0 或 >100%）、La 峰位与理论值偏离 >0.5°、仪器宽化缺失等
- 报告导出：TXT（含公式、K 值、宽化模型与提示）/ CSV（UTF-8 BOM，Excel 直接打开）

**② 谱图与寻峰**
- 读取两列文本谱（`.txt` / `.xy` / `.dat` / `.csv` / `.asc` / `.prn`，自动跳过注释与表头）
- 自动寻峰 + 每峰 pseudo-Voigt 拟合（峰位、FWHM、峰高、相对强度、η、R²）
- **定点拟合**：石墨 (110) 强度常低于 (002) 的 5%，易被阈值滤掉；输入 2θ 即在该位置
  定向拟合，弱峰也能得到 FWHM
- 一键把选中峰填入计算页（C(002) / La 峰 / Si(111)）

**③ Si 标样 / 仪器宽化**
- 读入纯 Si（或 LaB₆）标样谱，按理论峰位自动识别 111/220/311/400/331/422…
  并逐峰拟合 FWHM
- 最小二乘拟合 Caglioti：FWHM² = U·tan²θ + V·tanθ + W，给出 RMS 与点数
- 拟合后自动用于 C(002) 与 (110) 两处的仪器宽化，无需重复测标样

**④ 方法与判据**：公式、操作流程、常见问题与参考文献（按当前语言显示）

**⑤ 右上角小提示图标（?）**：页签栏右端常驻，任何页签下点开即见一页「测试与计算要点」——
两段扫描方案（25–29.5° / 72–82° / 标样 20–90°）、计算链（Bragg → Franklin → Scherer）、
仪器宽化扣除模型、适用边界（未分离微观应变宽化）与辐射波长。与「帮助 → 测试与计算要点」同一入口。

## 计算公式与参数依据

| 项目 | 公式 / 取值 | 依据 |
|---|---|---|
| 石墨化度 g | g = (0.3440 − d002) / (0.3440 − 0.3354) × 100% | Franklin, *Acta Cryst.* 1951, 4, 253（原文以 c₀/2 表述，本工具统一改写为 d002，二者数值等价） |
| d002 | d = λ / (2 sinθ)，θ 取**内标校正后**的峰位 | Bragg |
| 2θ 校正 | Δ2θ = 2θ(Si,标准) − 2θ(Si,实测)，同量加到 C(002) 与 La 峰 | 内标法 |
| Lc | Lc = 0.89 λ / (β cosθ) | Iwashita et al., *Carbon* 2004, 42, 701（碳材料 XRD 标准规程） |
| La | La = 1.84 λ / (β cosθ)，优先用 (110) | 同上；Warren, *Phys. Rev.* 1941, 59, 693（hk 带） |
| 仪器宽化 | 高斯：β = √(βobs² − βinst²)；洛伦兹：β = βobs − βinst | 二选一，同批样品必须一致并在报告注明 |
| β 的单位 | 输入为 °，Scherrer 内部转弧度 | — |

**为什么 La 必须用 (110)/(100)**：La 反映石墨层内的晶畴尺寸，需 hk0 型反射。(002)
给出的是层堆叠方向（Lc），不能用来算 La。72–82° 的 (110) 峰角度高、同一 Δd 对应的
Δ2θ 更大（分辨率更高），且该区间没有其他强石墨峰叠加；42.4° 的 (100) 峰强度更高，
但与相邻三维反射靠近，分峰误差更大，故仅作备用。

**为什么必须掺 Si 内标**：C(002) 位于 26.5° 附近，装样高度、表面离焦、透明效应都会
整体推移峰位；这类几何误差对同一谱图上的所有峰近似相同，用内标点对点扣除最有效。
0.01° 的峰位偏差约带来 0.15 个百分点的 g 偏差，因此内标不是可选项。

## 推荐测试条件

| 目标 | 扫描范围 | 步长 | 停留 |
|---|---|---|---|
| C(002) → g, Lc | 24–30° | ≤ 0.02° | ≥ 1 s |
| (110) → La（优先） | **72–82°** | ≤ 0.02° | ≥ 2 s（峰弱） |
| (100) → La（备用） | 40–45° | ≤ 0.02° | ≥ 1 s |
| Si 标样（全角度） | 20–120° | 与样品一致 | 与样品一致 |

装样：石墨中掺入约 10–20 wt% Si 粉混匀，填池、刮平、轻压；Si 标样单独制样，
狭缝与扫描参数须与样品一致。

## 构建

```bat
REM 单文件内部评估版（无注册机制，状态栏显示「内部评估版本」）
build_exe.bat

REM Setup 安装版（含注册机制；需 Inno Setup 6）
build_installer.bat
```

产物：

- `dist\PolyXRD-Graphite-v1.0.0-internal.exe`（版本化归档）
- `dist\PolyXRD-Graphite-internal.exe`（最新版固定名）
- `dist\PolyXRD-Graphite-Setup-v1.0.0.exe`（安装版）

内部评估版的判定方式与家族一致：构建时打入 `packaging\internal_eval.marker`，
`graphite_app._detect_variant()` 检测该文件存在与否。

## 注册码（安装版）

注册码由开发方按「单位部门名称」生成，离线校验、无需机器码，
同一注册码可在同一单位多台电脑使用：

```bash
python make_reg_code.py "XX大学材料学院"          # 生成
python make_reg_code.py --verify PXRD1-XXXX-...   # 校验并回显单位名
```

格式 `PXRD1-XXXX-XXXX-...`，内容为 Base32(UTF8(单位名) + 0x00 + HMAC-SHA256[:8])。
安全级别为离线混淆级（密钥随软件分发），适用于「告知版权 + 自助注册」场景。

**安装版运行行为**（`setup` 变体，未打 `internal_eval.marker`）：

- 未注册：每次启动弹一次版权提示，确定后功能不受限（不锁功能，只做告知）；
- 「帮助 → 输入注册码」，注册成功后状态栏最右侧显示「已注册：〈单位部门名称〉」；
- 注册状态存于 `%APPDATA%\PolyXRD\Registration\Graphite.json`，启动时重新校验，
  手改或伪造的文件一律按未注册处理。

## 开发与测试

```bash
python graphite_engine.py            # 计算内核自检（含文档算例复算）
python -m pytest tests -q            # 单元测试（引擎 + 三语 + 注册码）
python tools/smoke_gui.py            # GUI 离屏冒烟（无人工点击）
python tools/make_assets.py          # 重新生成图标 / splash / logo
```

`tests/test_engine.py` 里锁定了岛津应用数据集 AP_XRD-001《石墨化度的测定》的算例：
Si(111) 实测 28.4541°（标准 28.44135°）→ C(002) 26.5584° 校正为 26.54565°、
d002 = 0.33551 nm、g ≈ 98.8%（波长取传统值 1.54056 时为 98.8%，取 CODATA
1.5405929 时为 98.7%，差异全部来自波长取值）。

## 目录结构

```
graphite_engine.py     计算内核（Bragg / 石墨化度 / Scherrer / Caglioti / 寻峰 / 报告）
graphite_app.py        主程序（PySide6，单文件发行）
i18n.py                三语文案 + 方法说明页 + 小提示页（测试与计算要点）
registration.py        家族统一注册机制
make_reg_code.py       注册码生成（开发方用）
resources/             app-icon.png/.ico、splash-screen.png、logo-horizontal.png
tools/                 make_assets.py、smoke_gui.py、build_assets.sh
packaging/             internal_eval.marker、installer.iss、ChineseSimplified.isl
tests/                 test_engine.py、test_i18n.py
```

## 许可证

双许可（学术 / 商业），详见 [LICENSE](LICENSE) 与 [LICENSE-CN](LICENSE-CN)。
学术许可仅限非商业学术研究与教学；商业用途须另行取得书面授权。
