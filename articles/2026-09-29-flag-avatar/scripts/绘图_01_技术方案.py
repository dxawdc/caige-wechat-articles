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


def make_flag_square(flag_path):
    """读取国旗并裁剪成正方形（从左侧裁剪，保留完整大星与四颗小星）。"""
    flag = Image.open(flag_path).convert("RGB")
    w, h = flag.size
    side = min(w, h)
    return flag.crop((0, 0, side, side))


# ---------- 方案一：PIL 原生 alpha 渐变 ----------
def method_putalpha(avatar_path, flag_square):
    """
    思路：把国旗裁剪成头像大小，再给它盖一层『从左到右透明度递增』的 alpha 通道。
    透明度从 0（左侧全透明，露出头像）到 255（右侧不透明，纯国旗）。
    不再逐像素 putpixel，用 putalpha 一步完成。
    """
    avatar = Image.open(avatar_path).convert("RGB")
    w, h = avatar.size
    flag = flag_square.resize((w, h))

    # 构造 alpha 通道：形状 (h, w)，每列的值 = 列号在 0..255 之间的线性映射
    # 用 256 级渐变，右侧 alpha=255（不透明），左侧 alpha=0（透明）
    gradient = np.linspace(0, 255, w, dtype=np.uint8)          # 形状 (w,)
    alpha = np.tile(gradient, (h, 1))                          # 广播成 (h, w)

    flag_rgba = flag.convert("RGBA")
    flag_rgba.putalpha(Image.fromarray(alpha, mode="L"))

    avatar.paste(flag_rgba, (0, 0), flag_rgba)  # 第三参作为 mask，保留透明
    return avatar


# ---------- 方案二：numpy 向量化融合 ----------
def method_numpy(avatar_path, flag_square):
    """
    思路：直接用 numpy 按 alpha 权重做像素融合，全程向量化，无 Python 层循环。
    result = avatar * (1 - a) + flag * a
    其中 a 从左到右从 0 升到 1，等价于国旗从透明渐变为不透明。
    """
    avatar = Image.open(avatar_path).convert("RGB")
    w, h = avatar.size
    flag = flag_square.resize((w, h))

    a = np.linspace(0.0, 1.0, w, dtype=np.float32)             # 每列权重 (w,)
    a = np.tile(a, (h, 1))[:, :, None]                          # 广播成 (h, w, 1)

    av = np.asarray(avatar, dtype=np.float32)
    fl = np.asarray(flag, dtype=np.float32)
    out = av * (1.0 - a) + fl * a                              # 线性融合
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# ---------- 方案三：Image.blend 全局半透明 ----------
def method_blend(avatar_path, flag_square, alpha=0.45):
    """
    思路：直接把国旗整体以固定透明度 alpha 覆盖到头像上。
    Image.blend 是 PIL 内置的 alpha 混合，比手动逐像素快得多，但只能做统一透明度。
    """
    avatar = Image.open(avatar_path).convert("RGB")
    w, h = avatar.size
    flag = flag_square.resize((w, h))
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

    flag_square = make_flag_square(flag_path)

    r1 = method_putalpha(avatar_path, flag_square)
    r1.save(os.path.join(OUT, "方案一_putalpha渐变.png"))

    r2 = method_numpy(avatar_path, flag_square)
    r2.save(os.path.join(OUT, "方案二_numpy渐变.png"))

    r3 = method_blend(avatar_path, flag_square, alpha=0.45)
    r3.save(os.path.join(OUT, "方案三_blend半透明.png"))

    print("生成完成：方案一/二/三 已保存到素材目录")


if __name__ == "__main__":
    main()
