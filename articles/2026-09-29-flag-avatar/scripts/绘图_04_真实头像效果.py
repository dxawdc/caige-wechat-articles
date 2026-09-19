# -*- coding: utf-8 -*-
"""
真实头像效果生成：方案一渐变覆盖 + 方案三整体半透明。
国旗保持 3:2 原始比例（五星不压缩），等比缩放后垂直居中铺满头像。

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
OUT = os.path.join(os.path.dirname(BASE), "素材")

RED = (222, 41, 34)


def make_flag_layer(flag_path, target_size, star_pos=0.55):
    """国旗等比缩放到 target_size=(w,h)，五星比例保真，五星区落在可见范围。"""
    flag = Image.open(flag_path).convert("RGB")
    fw, fh = flag.size
    w, h = target_size
    new_w = w
    new_h = round(fh * w / fw)
    if new_h > h:
        new_h = h
        new_w = round(fw * h / fh)
    flag = flag.resize((new_w, new_h), Image.LANCZOS)
    star_center_in_flag = 0.28
    flag_left = round(star_pos * w - star_center_in_flag * new_w)
    flag_top = (h - new_h) // 2
    canvas = Image.new("RGB", (w, h), RED)
    canvas.paste(flag, (flag_left, flag_top))
    return canvas


def make_alpha_gradient(w, h, transparent_until=0.25):
    """前半段透明露出头像，后半段线性过渡到不透明，五星落在清晰区间。"""
    n = w
    start = int(transparent_until * n)
    ramp_len = n - start
    ramp = np.linspace(0, 255, ramp_len, dtype=np.uint8)
    gradient = np.zeros(n, dtype=np.uint8)
    gradient[start:] = ramp
    return np.tile(gradient, (h, 1))


def gradient_overlay(avatar, flag_layer):
    """方案一：putalpha 渐变覆盖。"""
    w, h = avatar.size
    alpha = make_alpha_gradient(w, h)
    flag = flag_layer.convert("RGBA")
    flag.putalpha(Image.fromarray(alpha))
    out = avatar.copy()
    out.paste(flag, (0, 0), flag)
    return out


def blend_overlay(avatar, flag_layer, a=0.45):
    """方案三：Image.blend 整体半透明。"""
    return Image.blend(avatar, flag_layer, alpha=a)


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
        avatar = avatar.resize((1200, 1200), Image.LANCZOS)

    flag_layer = make_flag_layer(os.path.join(BASE, "五星红旗.png"), avatar.size)
    os.makedirs(OUT, exist_ok=True)

    gradient_overlay(avatar, flag_layer).save(os.path.join(OUT, "真实头像_渐变效果.png"))
    blend_overlay(avatar, flag_layer).save(os.path.join(OUT, "真实头像_半透明效果.png"))
    print("已生成 素材/真实头像_渐变效果.png 与 素材/真实头像_半透明效果.png")


if __name__ == "__main__":
    main()
