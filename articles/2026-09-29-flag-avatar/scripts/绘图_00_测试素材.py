# -*- coding: utf-8 -*-
"""
生成测试素材：按《国旗法》附件规范比例绘制五星红旗（30x20 网格）+ 测试头像。

规范要点（GB 12982-2004 / 国旗法附件）：
- 旗面长高比 3:2，划分为 30x20 个方格
- 大五角星中心 (5,5)，外接圆半径 3 格
- 四颗小星中心 (10,2)、(12,4)、(12,7)、(10,9)，外接圆半径 1 格
- 每颗小星有一个角尖正对大星中心

仅用于本地演示跑通脚本；正式使用请使用标准国旗素材。
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))

RED = (222, 41, 34)      # 国旗红（近似标准红）
YELLOW = (255, 222, 0)   # 星黄（近似标准黄）


def _star_points(cx, cy, r, rot_deg):
    """外接圆半径 r、旋转 rot_deg 的五角星 10 个顶点。"""
    pts = []
    for k in range(5):
        a_out = math.radians(-90 + rot_deg + k * 72)
        pts.append((cx + r * math.cos(a_out), cy + r * math.sin(a_out)))
        a_in = math.radians(-90 + rot_deg + 36 + k * 72)
        pts.append((cx + r * math.sin(math.pi / 10) / math.sin(3 * math.pi / 10) * math.cos(a_in),
                    cy + r * math.sin(math.pi / 10) / math.sin(3 * math.pi / 10) * math.sin(a_in)))
    return pts


def make_flag(path, width=1500):
    height = int(width * 2 / 3)
    cell = width / 30.0  # 每格像素
    img = Image.new("RGB", (width, height), RED)
    d = ImageDraw.Draw(img)

    def star(gx, gy, gr, point_to=None):
        cx, cy = gx * cell, gy * cell
        r = gr * cell
        if point_to is None:
            rot = 0.0
        else:
            tx, ty = point_to
            rot = math.degrees(math.atan2(ty - cy, tx - cx)) + 90
        d.polygon(_star_points(cx, cy, r, rot), fill=YELLOW)

    big_center = (5 * cell, 5 * cell)
    star(5, 5, 3)                                   # 大星
    star(10, 2, 1, point_to=big_center)             # 小星1
    star(12, 4, 1, point_to=big_center)             # 小星2
    star(12, 7, 1, point_to=big_center)             # 小星3
    star(10, 9, 1, point_to=big_center)             # 小星4

    img.save(path)
    print("国旗已生成:", path)


def make_avatar(path, size=900):
    """生成一个简洁的卡通测试头像（圆形人物剪影，便于看清覆盖效果）。"""
    img = Image.new("RGB", (size, size), (245, 246, 250))
    d = ImageDraw.Draw(img)
    # 背景渐变
    for i in range(size):
        t = i / size
        d.line([(i, 0), (i, size)], fill=(int(120 + 60 * t), int(170 - 40 * t), int(230 - 60 * t)))
    # 人物：头 + 肩
    d.ellipse([size*0.33, size*0.18, size*0.67, size*0.52], fill=(255, 224, 189))   # 脸
    d.ellipse([size*0.30, size*0.12, size*0.70, size*0.42], fill=(70, 60, 55))      # 头发
    d.rounded_rectangle([size*0.18, size*0.58, size*0.82, size*1.1], radius=size*0.18,
                        fill=(60, 90, 160))                                          # 肩/衣服
    img = img.filter(ImageFilter.SMOOTH)
    img.save(path)
    print("头像已生成:", path)


if __name__ == "__main__":
    make_flag(os.path.join(BASE, "五星红旗.png"))
    make_avatar(os.path.join(BASE, "头像.jpg"))
