# -*- coding: utf-8 -*-
"""
性能对比：2021 年版逐像素 putpixel vs 2026 现代 numpy 向量化。
同一张 900x900 头像尺寸的国旗渐变任务，各跑多次取平均。
"""
import os
import time
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))


def old_loop(quyu):
    """2021 年版：逐像素 getpixel/putpixel 双重循环。"""
    w, h = quyu.size
    for i in range(w):
        for j in range(h):
            color = quyu.getpixel((i, j))
            alpha = 255 - i // 3
            if alpha < 0:
                alpha = 0
            color = color[:-1] + (alpha,)
            quyu.putpixel((i, j), color)
    return quyu


def new_numpy(flag):
    """2026 年版：numpy 向量化生成 alpha 通道。"""
    w, h = flag.size
    gradient = np.linspace(0, 255, w, dtype=np.uint8)
    alpha = np.tile(gradient, (h, 1))
    flag.putalpha(Image.fromarray(alpha, mode="L"))
    return flag


def bench(fn, img, n=5):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn(img.copy())
        times.append(time.perf_counter() - t0)
    return sum(times) / len(times)


def main():
    # 准备 900x900 RGBA 测试图
    flag = Image.new("RGBA", (900, 900), (222, 41, 34, 255))

    t_old = bench(old_loop, flag)
    t_new = bench(new_numpy, flag)

    print(f"900x900 渐变 alpha 设置，5 次平均：")
    print(f"  2021 版 逐像素循环 : {t_old*1000:8.1f} ms")
    print(f"  2026 版 numpy向量  : {t_new*1000:8.1f} ms")
    print(f"  提升倍数           : {t_old/t_new:8.1f} x")

    # 顺便测 2000x2000 大图
    big = Image.new("RGBA", (2000, 2000), (222, 41, 34, 255))
    t_old_b = bench(old_loop, big, n=3)
    t_new_b = bench(new_numpy, big, n=3)
    print(f"2000x2000 渐变 alpha 设置，3 次平均：")
    print(f"  2021 版 逐像素循环 : {t_old_b*1000:8.1f} ms")
    print(f"  2026 版 numpy向量  : {t_new_b*1000:8.1f} ms")
    print(f"  提升倍数           : {t_old_b/t_new_b:8.1f} x")


if __name__ == "__main__":
    main()
