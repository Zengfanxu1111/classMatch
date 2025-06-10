import numpy as np
import matplotlib.pyplot as plt

from math import pi
from matplotlib import colormaps as cmaps # Use cmaps instead of cm

def plot_radar_chart(labels, values, title='人物属性'):
    # 计算每个轴的角度
    angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
    values += values[:1]  # 闭合图形
    angles += angles[:1]

    # 初始化极坐标图
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # 绘制数据
    ax.fill(angles, values, 'b', alpha=0.25)
    ax.plot(angles, values, 'b', linewidth=2)

    # 设置标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    # 添加标题
    plt.title(title)

    # 显示图表
    plt.show()


# 示例数据
labels = ['力量', '敏捷', '智力', '魅力', '耐力', '幸运', '速度', '技巧']
values = [3, 4, 4, 2, 5, 3, 4, 5]

# 调用函数
plot_radar_chart(labels, values)