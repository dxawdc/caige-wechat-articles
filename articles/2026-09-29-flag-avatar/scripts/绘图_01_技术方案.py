# -*- coding: utf-8 -*-
"""
五星红旗半透明渐变头像 —— 现代技术实现（三种方案）
对比 2021 年版逐像素 putpixel 双重循环，展示更简洁高效的写法。

方案一：PIL 原生 putalpha + resize（推荐，简洁）
方案二：numpy 向量化 alpha 渐变（性能最优）
方案三：Image.blend 全局混合（统一透明度）

运行环境：PIL(Pillow) + numpy
"""
import os
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(BASE), "素材")

RED = (222, 41, 34)   # 国旗红（与绘图_00 一致，用于留白填色）


def make_flag_square(flag_path, target_size=None):
    """
    读取国旗并处理成正方形图层，保持国旗 3:2 原始比例，五星不被拉伸。

    做法：国旗按『宽度对齐』等比缩放（宽 = 目标边长，高 = 边长 × 2/3），
    再居中垂直放置到正方形画布上（上下留白填红），五星比例与位置完全保真。
    若 target_size 为 None，则返回裁剪好的正方形国旗（供独立展示用）。
    """
    flag = Image.open(flag_path).convert("RGB")
    fw, fh = flag.size

    if target_size is None:
        side = min(fw, fh)
        return flag.crop((0, 0, side, side))

    side = target_size
    # 等比缩放：以边长为目标宽度，高度按 3:2 比例（实际按国旗自身比例）
    new_w = side
    new_h = round(fh * side / fw)
    flag = flag.resize((new_w, new_h), Image.LANCZOS)

    # 放到正方形画布，垂直居中（上下用国旗红补齐，视觉无缝）
    canvas = Image.new("RGB", (side, side), RED)
    top = (side - new_h) // 2
    canvas.paste(flag, (0, top))
    return canvas


def make_flag_layer(flag_path, target_size, star_pos=0.55):
    """
    把国旗等比缩放到 target_size=(w,h)，五星比例与位置保真。

    国旗 3:2，五星集中在旗面左侧约 16%~40% 宽度的区域。为保证五星落在
    头像的可见范围（而不是被渐变透明区遮没），这里把国旗等比缩放成『宽度
    与头像一致』后，再按 star_pos 决定五星区在头像中的横向落点：

      - 国旗等比缩放，宽 = w，高 = w * 2/3
      - 五星区中心对齐到头像 x = star_pos * w 处
      - 上下垂直居中，留白用国旗红补齐（视觉无缝）

    star_pos 默认 0.55，让五星整体落在画面中部、横跨“头像→国旗”的渐变
    过渡带，五星完整可见，是最接近经典渐变头像的构图。
    """
    flag = Image.open(flag_path).convert("RGB")
    fw, fh = flag.size
    w, h = target_size

    # 等比缩放：以宽度对齐
    new_w = w
    new_h = round(fh * w / fw)
    if new_h > h:                       # 极端情况改按高度对齐
        new_h = h
        new_w = round(fw * h / fh)
    flag = flag.resize((new_w, new_h), Image.LANCZOS)

    # 五星区在国旗中的横向中心（约 0.28 处，取 5格~12格中心）
    star_center_in_flag = 0.28
    # 目标：五星区中心落在头像 x = star_pos * w
    flag_left = round(star_pos * w - star_center_in_flag * new_w)
    flag_top = (h - new_h) // 2

    canvas = Image.new("RGB", (w, h), RED)
    canvas.paste(flag, (flag_left, flag_top))
    return canvas


def make_alpha_gradient(w, h, transparent_until=0.25):
    """
    生成从左到右渐变的 alpha 通道 (h, w)。

    前半段（0 ~ transparent_until）保持 alpha=0，完整露出头像；
    后半段线性过渡到 255（不透明），五星区正好落在中高 alpha 区间，清晰可见。
    """
    n = w
    start = int(transparent_until * n)
    ramp_len = n - start
    ramp = np.linspace(0, 255, ramp_len, dtype=np.uint8)
    gradient = np.zeros(n, dtype=np.uint8)
    gradient[start:] = ramp
    return np.tile(gradient, (h, 1))


# ---------- 方案一：PIL 原生 alpha 渐变 ----------
def method_putalpha(avatar_path, flag_path):
    """
    思路：把国旗等比铺成头像尺寸，再盖一层『从左到右透明度递增』的 alpha 通道。
    透明度从 0（左侧全透明，露出头像）到 255（右侧不透明，纯国旗）。
    不再逐像素 putpixel，用 putalpha 一步完成。
    """
    avatar = Image.open(avatar_path).convert("RGB")
    w, h = avatar.size
    flag = make_flag_layer(flag_path, (w, h))

    alpha = make_alpha_gradient(w, h)

    flag_rgba = flag.convert("RGBA")
    flag_rgba.putalpha(Image.fromarray(alpha, mode="L"))

    avatar.paste(flag_rgba, (0, 0), flag_rgba)  # 第三参作为 mask，保留透明
    return avatar


# ---------- 方案二：numpy 向量化融合 ----------
def method_numpy(avatar_path, flag_path):
    """
    思路：直接用 numpy 按 alpha 权重做像素融合，全程向量化，无 Python 层循环。
    result = avatar * (1 - a) + flag * a
    其中 a 从左到右从 0 升到 1，等价于国旗从透明渐变为不透明。
    """
    avatar = Image.open(avatar_path).convert("RGB")
    w, h = avatar.size
    flag = make_flag_layer(flag_path, (w, h))

    a = make_alpha_gradient(w, h).astype(np.float32) / 255.0   # 0~1 权重
    a = a[:, :, None]

    av = np.asarray(avatar, dtype=np.float32)
    fl = np.asarray(flag, dtype=np.float32)
    out = av * (1.0 - a) + fl * a                              # 线性融合
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ---------- 方案三：Image.blend 全局半透明 ----------
def method_blend(avatar_path, flag_path, alpha=0.45):
    """
    思路：直接把国旗整体以固定透明度 alpha 覆盖到头像上。
    Image.blend 是 PIL 内置的 alpha 混合，比手动逐像素快得多，但只能做统一透明度。
    """
    avatar = Image.open(avatar_path).convert("RGB")
    w, h = avatar.size
    flag = make_flag_layer(flag_path, (w, h))
    return Image.blend(avatar, flag, alpha=alpha)


def main():
    avatar_path = os.path.join(BASE, "头像.jpg")
    flag_path = os.path.join(BASE, "五星红旗.png")

    # 确保测试图存在（若无则生成占位头像，便于跑通）
    if not os.path.exists(avatar_path):
        img = Image.new("RGB", (900, 900), (70, 130, 180))
        img.save(avatar_path)
    if not os.path.exists(flag_path):
        # 简易红底黄星国旗占位（真实使用请换成标准五星红旗素材）
        img = Image.new("RGB", (1800, 1200), (222, 38, 35))
        img.save(flag_path)

    flag_square = make_flag_square(flag_path)   # 独立展示用的正方形国旗

    r1 = method_putalpha(avatar_path, flag_path)
    r1.save(os.path.join(OUT, "方案一_putalpha渐变.png"))

    r2 = method_numpy(avatar_path, flag_path)
    r2.save(os.path.join(OUT, "方案二_numpy渐变.png"))

    r3 = method_blend(avatar_path, flag_path, alpha=0.45)
    r3.save(os.path.join(OUT, "方案三_blend半透明.png"))

    # 独立保存一张正方形国旗（用于文章展示素材，比例保真）
    flag_square.resize((900, 900), Image.LANCZOS).save(os.path.join(OUT, "五星红旗_正方形.png"))

    print("生成完成：方案一/二/三 已保存到素材目录")


if __name__ == "__main__":
    main()
