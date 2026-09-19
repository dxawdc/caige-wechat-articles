# -*- coding: utf-8 -*-
"""
真实头像效果生成：方案一渐变覆盖 + 方案三整体半透明。

用法：
    python 绘图_04_真实头像效果.py [头像路径]

不传参数时默认使用同目录下的 头像.jpg（可先运行 绘图_00_测试素材.py 生成
演示头像，或换成你自己的任意头像照片）。
"""
import os
import sys
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(BASE), "images")


def make_flag_square():
    """从当前目录的五星红旗.png 裁出左侧正方形（保留完整五星）。"""
    flag = Image.open(os.path.join(BASE, "五星红旗.png")).convert("RGB")
    w, h = flag.size
    side = min(w, h)
    return flag.crop((0, 0, side, side))


def gradient_overlay(avatar, flag_square):
    """方案一：putalpha 渐变覆盖。"""
    w, h = avatar.size
    flag = flag_square.resize((w, h))
    gradient = np.linspace(0, 255, w, dtype=np.uint8)
    alpha = np.tile(gradient, (h, 1))
    flag = flag.convert("RGBA")
    flag.putalpha(Image.fromarray(alpha))
    out = avatar.copy()
    out.paste(flag, (0, 0), flag)
    return out


def blend_overlay(avatar, flag_square, a=0.45):
    """方案三：Image.blend 整体半透明。"""
    w, h = avatar.size
    flag = flag_square.resize((w, h))
    return Image.blend(avatar, flag, alpha=a)


def center_square(img):
    """头像居中裁剪成正方形。"""
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def main():
    avatar_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "头像.jpg")
    avatar = Image.open(avatar_path).convert("RGB")
    avatar = center_square(avatar)
    if avatar.size[0] > 1200:
        avatar = avatar.resize((1200, 1200))

    fs = make_flag_square()
    os.makedirs(OUT, exist_ok=True)

    gradient_overlay(avatar, fs).save(os.path.join(OUT, "头像_渐变效果.png"))
    blend_overlay(avatar, fs).save(os.path.join(OUT, "头像_半透明效果.png"))
    print("已生成 images/头像_渐变效果.png 与 images/头像_半透明效果.png")


if __name__ == "__main__":
    main()
