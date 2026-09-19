# -*- coding: utf-8 -*-
"""
AI 抠图 + 国旗合成：rembg 最小示例
================================

把头像主体从背景里抠出来，再合成到国旗背景上——"人站在国旗前"的效果。

安装（首次运行前）：
    pip install rembg onnxruntime pillow numpy

说明：
- rembg 底层是 U2Net 分割模型，首次运行会自动下载模型权重（约170MB），
  之后走本地缓存，无需联网。
- 只做本地处理，不上传照片。
"""
import os
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    from rembg import remove  # 延迟导入，未安装时给出友好提示

    # 1. 读取头像与国旗（都缩放到 900x900）
    avatar = Image.open(os.path.join(BASE, "真实头像.jpg")).convert("RGB")
    avatar = avatar.resize((900, 900))
    flag = Image.open(os.path.join(BASE, "五星红旗.png")).convert("RGB")
    fw, fh = flag.size
    side = min(fw, fh)
    flag = flag.crop((0, 0, side, side)).resize((900, 900))

    # 2. AI 抠图：remove() 返回带 alpha 通道的前景图
    cutout = remove(avatar)  # RGBA，背景透明

    # 3. 合成：国旗铺底，人物叠在上面（可选：给人物加白色描边更出效果）
    result = flag.convert("RGBA")
    result.alpha_composite(cutout)

    # 4. 保存
    result.convert("RGB").save(os.path.join(BASE, "国旗前景合成效果.png"))
    print("完成：国旗前景合成效果.png")


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("请先安装依赖：pip install rembg onnxruntime pillow numpy")
