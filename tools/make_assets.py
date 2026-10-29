# -*- coding: utf-8 -*-
"""生成 PolyXRD Graphite 的品牌资源（与 PolyXRD 家族视觉体系一致）。

产物（写入 resources/）：
  app-icon.png        512×512  圆角方底 + 六边形 mark + 石墨层 + 衍射峰
  app-icon.ico        多尺寸（16/24/32/48/64/128/256）Windows 图标
  splash-screen.png   960×540  深色渐变 + 白色六边形 mark + 标题/版本/副标题
  logo-horizontal.png 512×160  横向 logo（白底，用于「关于」对话框）

设计语言（对齐 PolyXRD-RutAna / SynthPattern）：
  深 navy #0b1e30 → #14405c 渐变底；六边形描边 mark；白色科技术语字体；
  产品名用青色 #2ea3d6 与家族名 "PolyXRD" 区分。
  内部图形为石墨层状结构 + (002) 衍射峰，直指本工具主题。

两种运行方式
------------
1) 常规：``python tools/make_assets.py``  —— 直接写 PNG/ICO。
2) 受限环境（Python 进程被禁止写文件）：``python tools/make_assets.py --emit app-icon.png``
   —— 把该资源以 base64 输出到 stdout，由 shell 侧 ``base64 -d`` 落盘
   （见 tools/build_assets.sh）。
"""
from __future__ import annotations

import base64
import io
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "resources"
RES.mkdir(exist_ok=True)

NAVY_TOP = (18, 56, 79)
NAVY_BOT = (9, 26, 41)
CYAN = (62, 192, 234)
CYAN_DARK = (15, 111, 156)
INK = (14, 32, 51)
GREY = (122, 137, 154)
WHITE = (255, 255, 255)

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"

SS = 4  # 超采样倍数


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size * SS)


def hexagon(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    """尖顶朝上的正六边形顶点（与家族 mark 一致）。"""
    pts = []
    for k in range(6):
        ang = math.radians(-90 + 60 * k)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def draw_mark(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float,
              stroke: tuple[int, int, int] = WHITE, width: float = 13,
              layer: tuple[int, int, int] = CYAN,
              peak: tuple[int, int, int] = WHITE,
              scale: float | None = None) -> None:
    """六边形 + 石墨层 + (002) 衍射峰。

    坐标为**设计尺寸**下的值，内部统一乘 ``scale``（默认超采样倍数 SS），
    这样同一套坐标可用在不同分辨率的画布上。
    """
    s = SS if scale is None else scale
    lw = max(1, int(width * s))
    pts = hexagon(cx, cy, r)
    # 用 polygon 描边（line 在闭合点会产生接缝尖刺）
    d.polygon([(x * s, y * s) for x, y in pts], outline=stroke, width=lw)

    # 石墨层：三条平行层线（长度不等，示意层堆叠）
    lw_layer = max(1, int(width * 0.70 * s))
    rr = max(1, int(width * 0.38 * s))
    for dy, half in ((-0.32, 0.50), (-0.16, 0.60), (0.00, 0.56)):
        y = (cy + dy * r) * s
        d.line([((cx - half * r) * s, y), ((cx + half * r) * s, y)],
               fill=layer, width=lw_layer)
        for sx in (-1, 1):
            x = (cx + sx * half * r) * s
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=layer)

    # 底部 (002) 衍射峰：基线 + 尖峰
    base_y = cy + 0.44 * r
    lw_peak = max(1, int(width * 0.60 * s))
    d.line([((cx - 0.56 * r) * s, base_y * s), ((cx - 0.19 * r) * s, base_y * s)],
           fill=peak, width=lw_peak)
    d.line([((cx + 0.21 * r) * s, base_y * s), ((cx + 0.56 * r) * s, base_y * s)],
           fill=peak, width=lw_peak)
    top = base_y - 0.28 * r
    d.line([((cx - 0.19 * r) * s, base_y * s),
            ((cx - 0.050 * r) * s, (base_y - 0.17 * r) * s),
            (cx * s, top * s),
            ((cx + 0.050 * r) * s, (base_y - 0.17 * r) * s),
            ((cx + 0.21 * r) * s, base_y * s)],
           fill=peak, width=lw_peak, joint="curve")


def vgradient(size: tuple[int, int], top: tuple[int, int, int],
              bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    grad = Image.new("RGB", (1, h))
    px = grad.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return grad.resize((w, h), Image.BILINEAR)


# ------------------------------------------------------------------------------
# 三个资源
# ------------------------------------------------------------------------------
def build_icon() -> tuple[Image.Image, dict]:
    size = 512
    img = vgradient((size * SS, size * SS), NAVY_TOP, NAVY_BOT).convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1],
                                           radius=int(96 * SS), fill=255)
    img.putalpha(mask)
    draw_mark(ImageDraw.Draw(img), 256, 258, 176, WHITE, 13, scale=SS)
    return img.resize((size, size), Image.LANCZOS), {}


def app_version() -> str:
    """从 graphite_app.py 读 APP_VERSION，避免 splash 上的版本号与源码脱节。"""
    try:
        text = (ROOT / "graphite_app.py").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else ""


def build_splash() -> tuple[Image.Image, dict]:
    W, H = 960, 540
    s = 2
    img = vgradient((W * s, H * s), (10, 24, 38), (16, 58, 84)).convert("RGBA")
    d = ImageDraw.Draw(img)
    grid = (255, 255, 255, 10)
    for x in range(0, W * s, 40):
        d.line([(x, 0), (x, H * s)], fill=grid, width=1)
    for y in range(0, H * s, 40):
        d.line([(0, y), (W * s, y)], fill=grid, width=1)

    draw_mark(d, 480, 176, 86, WHITE, 8, scale=2)

    f_title = ImageFont.truetype(FONT_BOLD, 46 * s)
    f_sub = ImageFont.truetype(FONT_REG, 21 * s)
    f_ver = ImageFont.truetype(FONT_REG, 19 * s)
    f_small = ImageFont.truetype(FONT_REG, 15 * s)

    def center(text: str, y: int, f, fill) -> None:
        box = d.textbbox((0, 0), text, font=f)
        d.text(((W * s - (box[2] - box[0])) / 2 - box[0], y * s), text, font=f, fill=fill)

    t1, t2 = "PolyXRD ", "Graphite"
    b1 = d.textbbox((0, 0), t1, font=f_title)
    b2 = d.textbbox((0, 0), t2, font=f_title)
    total = (b1[2] - b1[0]) + (b2[2] - b2[0])
    x0 = (W * s - total) / 2
    d.text((x0, 300 * s), t1, font=f_title, fill=WHITE)
    d.text((x0 + (b1[2] - b1[0]), 300 * s), t2, font=f_title, fill=CYAN)

    center("v" + app_version(), 366, f_ver, (186, 203, 219))
    center("石墨化度 · Lc · La 测定工具", 398, f_sub, (150, 172, 192))
    center("Graphitization degree · Lc · La   |   Si internal standard", 434,
           f_small, (110, 133, 155))
    return img.resize((W, H), Image.LANCZOS).convert("RGB"), {}


def build_logo() -> tuple[Image.Image, dict]:
    W, H = 512, 160
    img = Image.new("RGBA", (W * SS, H * SS), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    s = SS
    draw_mark(d, 80, 80, 54, INK, 7, CYAN_DARK, INK, scale=SS)

    f_name = ImageFont.truetype(FONT_BOLD, 34 * s)
    f_sub = ImageFont.truetype(FONT_REG, 15 * s)
    d.text((150 * s, 40 * s), "PolyXRD ", font=f_name, fill=INK)
    b = d.textbbox((150 * s, 40 * s), "PolyXRD ", font=f_name)
    d.text((b[2], 40 * s), "Graphite", font=f_name, fill=CYAN_DARK)
    d.text((152 * s, 96 * s), "石墨化度 / Lc / La 测定", font=f_sub, fill=GREY)
    return img.resize((W, H), Image.LANCZOS), {}


ASSETS = {
    "app-icon.png": (build_icon, "PNG", {}),
    "app-icon.ico": (build_icon, "ICO",
                     {"sizes": [(16, 16), (24, 24), (32, 32), (48, 48),
                                (64, 64), (128, 128), (256, 256)]}),
    "splash-screen.png": (build_splash, "PNG", {}),
    "logo-horizontal.png": (build_logo, "PNG", {}),
}


def render(name: str) -> bytes:
    builder, fmt, kw = ASSETS[name]
    img, extra = builder()
    buf = io.BytesIO()
    img.save(buf, format=fmt, **(kw | extra))
    return buf.getvalue()


def main(argv: list[str]) -> int:
    if "--emit" in argv:
        name = argv[argv.index("--emit") + 1]
        if name not in ASSETS:
            print(f"unknown asset: {name}", file=sys.stderr)
            return 2
        sys.stdout.write(base64.b64encode(render(name)).decode("ascii"))
        return 0

    for name in ASSETS:
        data = render(name)
        try:
            (RES / name).write_bytes(data)
            print(f"{name}  {len(data) / 1024:.1f} KB")
        except PermissionError:
            print(f"{name}  FAILED (PermissionError) —— 请用 --emit + base64 -d 落盘",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
