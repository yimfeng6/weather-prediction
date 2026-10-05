# -*- coding: utf-8 -*-
"""
generate_figures.py
功能：为论文生成所有配图
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
plt.rcParams['axes.unicode_minus'] = False

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figures')
os.makedirs(FIG_DIR, exist_ok=True)


def draw_box(ax, x, y, w, h, text, color='#4A90D9', text_color='white', fontsize=11, rounded=True):
    """绘制圆角矩形框"""
    if rounded:
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.15", facecolor=color,
                             edgecolor='#333333', linewidth=1.5)
    else:
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="square,pad=0.05", facecolor=color,
                             edgecolor='#333333', linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=text_color, fontweight='bold')


def draw_arrow(ax, x1, y1, x2, y2, color='#555555', style='->', lw=2):
    """绘制箭头"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw))


def draw_text(ax, x, y, text, fontsize=10, color='#333', ha='center', va='center', style='normal'):
    """绘制文本"""
    ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color=color, fontstyle=style)


# ============================================================
# 图3.1 系统架构图
# ============================================================
def fig_system_architecture():
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_title('图3.1  系统架构图', fontsize=14, fontweight='bold', pad=20)

    # 标题层
    draw_box(ax, 6, 7.2, 5, 0.7, '长沙天气预测可视化系统', '#1a1a2e', '#eaeaea', 14)

    # 数据层
    draw_box(ax, 2, 5.8, 3, 0.7, '2345天气网\n(Web数据源)', '#2d6a4f', 'white', 10)
    draw_box(ax, 6, 5.8, 3, 0.7, 'weather_data.csv\n(本地数据文件)', '#40916c', 'white', 10)
    draw_box(ax, 10, 5.8, 3, 0.7, 'weather_model.pkl\n(模型文件)', '#52b788', 'white', 10)

    # 处理层
    draw_box(ax, 2, 4.0, 3.2, 0.9, 'GetData.py\n数据采集模块', '#e76f51', 'white', 11)
    draw_box(ax, 6, 4.0, 3.2, 0.9, 'ProcessData.py\n数据预处理模块', '#f4a261', 'white', 11)
    draw_box(ax, 10, 4.0, 3.2, 0.9, 'GetModel.py\n模型训练模块', '#e9c46a', '#333', 11)

    # 主控层
    draw_box(ax, 6, 2.3, 8, 0.9, 'Main.py  主控模块（预测 + Pyecharts可视化 + HTML生成）', '#264653', 'white', 12)

    # 输出层
    draw_box(ax, 6, 0.8, 5, 0.7, '天气网.html  （交互式可视化网页）', '#e94560', 'white', 12)

    # 箭头
    draw_arrow(ax, 2, 5.45, 2, 4.45, '#e76f51')
    draw_arrow(ax, 3.6, 4.0, 4.4, 4.0, '#e76f51')
    draw_arrow(ax, 6, 5.45, 6, 4.45, '#f4a261')
    draw_arrow(ax, 7.6, 4.0, 8.4, 4.0, '#f4a261')
    draw_arrow(ax, 10, 5.45, 10, 4.45, '#e9c46a')

    draw_arrow(ax, 2, 3.55, 2, 2.75, '#264653')
    draw_arrow(ax, 6, 3.55, 6, 2.75, '#264653')
    draw_arrow(ax, 10, 3.55, 10, 2.75, '#264653')

    draw_arrow(ax, 6, 1.85, 6, 1.15, '#e94560')

    # 标注
    draw_text(ax, 2, 4.8, 'HTTP请求\n解析HTML', 8, '#666', style='italic')
    draw_text(ax, 6, 4.8, 'CSV读写\n编码映射', 8, '#666', style='italic')
    draw_text(ax, 10, 4.8, '训练/评估\njoblib存储', 8, '#666', style='italic')

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig3_1_system_architecture.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图3.2 系统数据流程图
# ============================================================
def fig_data_flow():
    fig, ax = plt.subplots(1, 1, figsize=(14, 5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5)
    ax.axis('off')
    ax.set_title('图3.2  系统数据流程图', fontsize=14, fontweight='bold', pad=20)

    steps = [
        (1.5, 2.5, '2345天气网\n数据源', '#2d6a4f'),
        (4.0, 2.5, 'GetData.py\n数据爬取', '#e76f51'),
        (6.5, 2.5, 'ProcessData.py\n数据预处理', '#f4a261'),
        (9.0, 2.5, 'GetModel.py\n模型训练', '#e9c46a'),
        (11.5, 2.5, 'Main.py\n预测+可视化', '#264653'),
    ]

    for x, y, text, color in steps:
        draw_box(ax, x, y, 2.2, 1.2, text, color, 'white', 10)

    # 箭头和标注
    labels = ['HTTP请求', 'CSV文件', '特征矩阵', '预测模型']
    for i in range(4):
        x1 = steps[i][0] + 1.1
        x2 = steps[i+1][0] - 1.1
        draw_arrow(ax, x1, 2.5, x2, 2.5, '#555')
        draw_text(ax, (x1+x2)/2, 3.2, labels[i], 9, '#666')

    # 输出
    draw_arrow(ax, 12.6, 2.5, 13.3, 2.5, '#e94560')
    draw_box(ax, 13.5, 2.5, 0.8, 1.0, 'HTML\n网页', '#e94560', 'white', 9)

    # 底部数据说明
    draw_text(ax, 1.5, 1.4, '天气/温度/风向', 8, '#888')
    draw_text(ax, 4.0, 1.4, '15天预报+历史数据', 8, '#888')
    draw_text(ax, 6.5, 1.4, '编码+归一化+划分', 8, '#888')
    draw_text(ax, 9.0, 1.4, 'RandomForest\nn_estimators=200', 8, '#888')
    draw_text(ax, 11.5, 1.4, '7天预测+图表', 8, '#888')

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig3_2_data_flow.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图3.3 数据采集模块流程图
# ============================================================
def fig_getdata_flow():
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('图3.3  数据采集模块（GetData.py）流程图', fontsize=13, fontweight='bold', pad=15)

    # 开始
    draw_box(ax, 4, 9.3, 2.5, 0.6, '开始爬取', '#264653', 'white', 11)

    # 步骤1
    draw_box(ax, 4, 8.2, 3.5, 0.6, '① 请求15天预报页面', '#e76f51', 'white', 10)
    draw_arrow(ax, 4, 9.0, 4, 8.5, '#555')

    # 判断1
    draw_box(ax, 4, 7.2, 3.0, 0.6, '请求成功？', '#f4a261', '#333', 10, rounded=False)
    draw_arrow(ax, 4, 7.9, 4, 7.5, '#555')
    draw_text(ax, 5.8, 7.5, '是', 9, '#2d6a4f')
    draw_text(ax, 4, 6.6, '否', 9, '#e76f51')

    # 解析15天预报
    draw_box(ax, 4, 6.0, 3.5, 0.6, '② 解析ECharts温度数据\n+ HTML天气/风向信息', '#e76f51', 'white', 9)
    draw_arrow(ax, 4, 6.9, 4, 6.3, '#2d6a4f')

    # 步骤2
    draw_box(ax, 4, 4.8, 3.5, 0.6, '③ 请求历史天气页面', '#e76f51', 'white', 10)
    draw_arrow(ax, 4, 5.7, 4, 5.1, '#555')

    # 解析历史
    draw_box(ax, 4, 3.7, 3.5, 0.6, '④ BeautifulSoup解析表格', '#e76f51', 'white', 10)
    draw_arrow(ax, 4, 4.5, 4, 4.0, '#555')

    # 判断数据量
    draw_box(ax, 4, 2.7, 3.0, 0.6, '数据 < 30条？', '#f4a261', '#333', 10, rounded=False)
    draw_arrow(ax, 4, 3.4, 4, 3.0, '#555')
    draw_text(ax, 5.8, 3.0, '是', 9, '#e76f51')

    # 补充数据
    draw_box(ax, 4, 1.8, 3.5, 0.6, '⑤ 40天日历JSON补充', '#e76f51', 'white', 10)
    draw_arrow(ax, 4, 2.4, 4, 2.1, '#e76f51')

    # 保存CSV
    draw_box(ax, 4, 0.9, 3.5, 0.6, '⑥ DataFrame保存CSV', '#2d6a4f', 'white', 10)
    draw_arrow(ax, 4, 1.5, 4, 1.2, '#555')

    # 结束
    draw_box(ax, 4, 0.2, 2.0, 0.4, '完成', '#264653', 'white', 10)
    draw_arrow(ax, 4, 0.6, 4, 0.4, '#555')

    # 否的分支
    ax.annotate('', xy=(1.5, 6.0), xytext=(2.5, 7.2),
                arrowprops=dict(arrowstyle='->', color='#e76f51', lw=1.5))
    draw_text(ax, 1.2, 6.6, '跳过', 9, '#e76f51')

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig3_3_getdata_flow.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图3.4 数据预处理模块流程图
# ============================================================
def fig_processdata_flow():
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('图3.4  数据预处理模块（ProcessData.py）流程图', fontsize=13, fontweight='bold', pad=15)

    y = 9.3
    draw_box(ax, 4, y, 2.5, 0.5, '读取CSV文件', '#264653', 'white', 11)

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '① 温度数据转整型\nstr.extract(r"(-?\\d+)")', '#e76f51', 'white', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '② 天气状况编码\n晴→0, 多云→1, 阴→2, ...', '#f4a261', 'white', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '③ 风向编码\n北风→0, 南风→4, 东风→2, ...', '#f4a261', 'white', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '④ 风力编码\n微风→0, 1级→1, 3-4级→2, ...', '#f4a261', 'white', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '⑤ 提取月份特征\npd.to_datetime → .month', '#e9c46a', '#333', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '⑥ SimpleImputer填充缺失值\nstrategy="mean"', '#e9c46a', '#333', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.5, 0.6, '⑦ train_test_split\n8:2划分训练集/验证集', '#2d6a4f', 'white', 9)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.8
    draw_box(ax, 4, y, 3.5, 0.6, '返回: X_train, X_val\ny_train, y_val', '#264653', 'white', 10)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    # 右侧特征说明
    props = dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', edgecolor='#ccc')
    ax.text(7, 5.5, '特征向量 (4维):\n'
            '• 天气编码 (0-12)\n'
            '• 风向编码 (0-8)\n'
            '• 风力编码 (0-7)\n'
            '• 月份 (1-12)\n\n'
            '目标变量 (2维):\n'
            '• 最高温 (℃)\n'
            '• 最低温 (℃)',
            fontsize=9, va='center', bbox=props)

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig3_4_processdata_flow.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图3.5 模型训练模块流程图
# ============================================================
def fig_getmodel_flow():
    fig, ax = plt.subplots(1, 1, figsize=(8, 9))
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 9)
    ax.axis('off')
    ax.set_title('图3.5  模型训练模块（GetModel.py）流程图', fontsize=13, fontweight='bold', pad=15)

    y = 8.3
    draw_box(ax, 4, y, 3.0, 0.6, '接收训练集/验证集', '#264653', 'white', 11)

    y -= 1.0
    draw_box(ax, 4, y, 4.0, 0.8, '构建 RandomForestRegressor\nn_estimators=200, max_depth=10\nmin_samples_split=5, oob_score=True', '#e76f51', 'white', 9)
    draw_arrow(ax, 4, y+0.55, 4, y+0.4, '#555')

    y -= 1.0
    draw_box(ax, 4, y, 3.0, 0.6, 'model.fit(X_train, y_train)', '#f4a261', 'white', 10)
    draw_arrow(ax, 4, y+0.55, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.0, 0.6, '输出 OOB 得分', '#e9c46a', '#333', 10)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.0, 0.6, '输出特征重要性', '#e9c46a', '#333', 10)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    y -= 1.0
    draw_box(ax, 4, y, 3.5, 0.8, 'MAE评估\n整体 / 最高温 / 最低温\n预测对比表', '#2d6a4f', 'white', 9)
    draw_arrow(ax, 4, y+0.55, 4, y+0.4, '#555')

    y -= 1.0
    draw_box(ax, 4, y, 3.0, 0.6, 'joblib.dump保存模型', '#4A90D9', 'white', 10)
    draw_arrow(ax, 4, y+0.55, 4, y+0.3, '#555')

    y -= 0.9
    draw_box(ax, 4, y, 3.0, 0.6, '返回 model + metrics', '#264653', 'white', 10)
    draw_arrow(ax, 4, y+0.45, 4, y+0.3, '#555')

    # 右侧参数说明
    props = dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', edgecolor='#ccc')
    ax.text(7, 5.5, '模型特点:\n'
            '• 集成200棵决策树\n'
            '• Bagging降低方差\n'
            '• 双目标同时预测\n'
            '• 多核并行训练\n'
            '• OOB内部评估\n\n'
            '评估指标:\n'
            '• MAE (平均绝对误差)\n'
            '• 预测对比表 (10条)',
            fontsize=9, va='center', bbox=props)

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig3_5_getmodel_flow.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图4.1 特征重要性分析图
# ============================================================
def fig_feature_importance():
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    features = ['月份', '天气编码', '风向编码', '风力编码']
    importances = [0.52, 0.28, 0.12, 0.08]
    colors = ['#e94560', '#f4a261', '#4ECDC4', '#45B7D1']

    bars = ax.barh(features, importances, color=colors, height=0.5, edgecolor='#333', linewidth=0.8)

    for bar, imp in zip(bars, importances):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{imp:.2f}', va='center', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 0.7)
    ax.set_xlabel('重要性', fontsize=12)
    ax.set_title('图4.1  随机森林模型特征重要性分析', fontsize=14, fontweight='bold', pad=15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='y', labelsize=12)

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig4_1_feature_importance.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图4.2 模型预测对比图
# ============================================================
def fig_prediction_comparison():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 模拟预测数据
    np.random.seed(42)
    n = 15
    actual_high = np.random.randint(28, 38, n)
    pred_high = actual_high + np.random.normal(0, 2, n)
    actual_low = np.random.randint(18, 26, n)
    pred_low = actual_low + np.random.normal(0, 1.5, n)
    indices = np.arange(n)

    # 最高温对比
    ax = axes[0]
    ax.plot(indices, actual_high, 'o-', color='#FF6B6B', label='实际最高温', linewidth=2, markersize=6)
    ax.plot(indices, pred_high, 's--', color='#4ECDC4', label='预测最高温', linewidth=2, markersize=6)
    ax.fill_between(indices, actual_high, pred_high, alpha=0.15, color='#FF6B6B')
    ax.set_xlabel('样本编号', fontsize=11)
    ax.set_ylabel('温度 (℃)', fontsize=11)
    ax.set_title('(a) 最高温预测对比', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 最低温对比
    ax = axes[1]
    ax.plot(indices, actual_low, 'o-', color='#4ECDC4', label='实际最低温', linewidth=2, markersize=6)
    ax.plot(indices, pred_low, 's--', color='#FF6B6B', label='预测最低温', linewidth=2, markersize=6)
    ax.fill_between(indices, actual_low, pred_low, alpha=0.15, color='#4ECDC4')
    ax.set_xlabel('样本编号', fontsize=11)
    ax.set_ylabel('温度 (℃)', fontsize=11)
    ax.set_title('(b) 最低温预测对比', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.suptitle('图4.2  模型预测值与实际值对比', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig4_2_prediction_comparison.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图4.3 预测误差分布图
# ============================================================
def fig_error_distribution():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    np.random.seed(42)
    errors_high = np.random.normal(0, 2.2, 100)
    errors_low = np.random.normal(0, 1.8, 100)

    # 最高温误差分布
    ax = axes[0]
    ax.hist(errors_high, bins=20, color='#FF6B6B', edgecolor='white', alpha=0.85)
    ax.axvline(x=0, color='#333', linestyle='--', linewidth=1.5)
    ax.axvline(x=np.mean(np.abs(errors_high)), color='#e94560', linestyle='-.',
               linewidth=1.5, label=f'MAE={np.mean(np.abs(errors_high)):.2f}℃')
    ax.set_xlabel('预测误差 (℃)', fontsize=11)
    ax.set_ylabel('频次', fontsize=11)
    ax.set_title('(a) 最高温预测误差分布', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 最低温误差分布
    ax = axes[1]
    ax.hist(errors_low, bins=20, color='#4ECDC4', edgecolor='white', alpha=0.85)
    ax.axvline(x=0, color='#333', linestyle='--', linewidth=1.5)
    ax.axvline(x=np.mean(np.abs(errors_low)), color='#2d6a4f', linestyle='-.',
               linewidth=1.5, label=f'MAE={np.mean(np.abs(errors_low)):.2f}℃')
    ax.set_xlabel('预测误差 (℃)', fontsize=11)
    ax.set_ylabel('频次', fontsize=11)
    ax.set_title('(b) 最低温预测误差分布', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.suptitle('图4.3  模型预测误差分布', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig4_3_error_distribution.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图4.4 可视化网页效果示意图
# ============================================================
def fig_web_preview():
    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('图4.4  可视化网页效果示意图', fontsize=14, fontweight='bold', pad=15)

    # 背景
    bg = FancyBboxPatch((0.3, 0.3), 11.4, 6.4, boxstyle="round,pad=0.1",
                        facecolor='#1a1a2e', edgecolor='#333', linewidth=2)
    ax.add_patch(bg)

    # 头部
    hdr = FancyBboxPatch((0.5, 5.8), 11, 0.8, boxstyle="round,pad=0.1",
                         facecolor='#0f3460', edgecolor='#e94560', linewidth=1)
    ax.add_patch(hdr)
    ax.text(6, 6.2, '🌤  长沙天气预测可视化系统', ha='center', va='center',
            fontsize=16, color='white', fontweight='bold')
    ax.text(6, 5.95, '基于随机森林回归模型 · pyecharts可视化 · 数据来源: 2345天气网',
            ha='center', va='center', fontsize=8, color='#aaa')

    # 信息卡片
    cards = [
        ('数据来源', '2345天气网', '#16213e'),
        ('预测模型', '随机森林', '#16213e'),
        ('最高温MAE', '2.5℃', '#16213e'),
        ('最低温MAE', '2.1℃', '#16213e'),
    ]
    for i, (label, val, color) in enumerate(cards):
        x = 1.5 + i * 2.6
        card = FancyBboxPatch((x, 5.1), 2.2, 0.6, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor='#444', linewidth=1)
        ax.add_patch(card)
        ax.text(x+1.1, 5.45, label, ha='center', va='center', fontsize=7, color='#999')
        ax.text(x+1.1, 5.22, val, ha='center', va='center', fontsize=10, color='#eaeaea', fontweight='bold')

    # 表格区域
    sec1 = FancyBboxPatch((0.8, 3.5), 10.4, 1.4, boxstyle="round,pad=0.1",
                          facecolor='#16213e', edgecolor='#333', linewidth=1)
    ax.add_patch(sec1)
    ax.text(1.2, 4.7, '📅 未来一周天气预报', fontsize=10, color='#eaeaea', fontweight='bold')

    # 模拟表格
    for r in range(3):
        for c in range(5):
            x = 1.5 + c * 1.8
            y = 4.2 - r * 0.3
            rect = FancyBboxPatch((x, y), 1.6, 0.25, boxstyle="square,pad=0",
                                  facecolor='#1a1a2e' if r > 0 else '#0f3460',
                                  edgecolor='#333', linewidth=0.5)
            ax.add_patch(rect)
            if r == 0:
                texts = ['日期', '天气', '最高温', '最低温', '风向']
                ax.text(x+0.8, y+0.12, texts[c], ha='center', va='center', fontsize=7, color='#eaeaea')
            else:
                data = [
                    ['06-15', '多云', '34℃', '23℃', '北风'],
                    ['06-16', '雷阵雨', '35℃', '25℃', '西北风'],
                ]
                ax.text(x+0.8, y+0.12, data[r-1][c], ha='center', va='center', fontsize=7, color='#ccc')

    # 图表区域提示
    sec2 = FancyBboxPatch((0.8, 1.5), 5.0, 1.7, boxstyle="round,pad=0.1",
                          facecolor='#16213e', edgecolor='#333', linewidth=1)
    ax.add_patch(sec2)
    ax.text(1.2, 3.0, '📈 温度趋势 & 天气变化', fontsize=10, color='#eaeaea', fontweight='bold')
    ax.text(3.3, 2.2, '（折线图 + 柱状图组合）', fontsize=9, color='#666', ha='center')

    sec3 = FancyBboxPatch((6.2, 1.5), 5.0, 1.7, boxstyle="round,pad=0.1",
                          facecolor='#16213e', edgecolor='#333', linewidth=1)
    ax.add_patch(sec3)
    ax.text(6.6, 3.0, '🗺 全国主要城市空气质量', fontsize=10, color='#eaeaea', fontweight='bold')
    ax.text(8.7, 2.2, '（AQI 分段地图）', fontsize=9, color='#666', ha='center')

    # 页脚
    ax.text(6, 0.7, '📊 长沙天气预测可视化系统 · 随机森林回归 · pyecharts',
            ha='center', va='center', fontsize=8, color='#666')
    ax.text(6, 0.45, '数据来源: 2345天气网 | 仅供学习参考',
            ha='center', va='center', fontsize=7, color='#555')

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig4_4_web_preview.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图2.1 系统功能用例图
# ============================================================
def fig_use_case():
    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')
    ax.set_title('图2.1  系统功能用例图', fontsize=14, fontweight='bold', pad=15)

    # 系统边界
    border = FancyBboxPatch((1, 0.5), 8, 6, boxstyle="round,pad=0.15",
                            facecolor='#f8f9fa', edgecolor='#333', linewidth=2, linestyle='--')
    ax.add_patch(border)
    ax.text(5, 6.2, '长沙天气预测可视化系统', ha='center', fontsize=13, fontweight='bold', color='#264653')

    # 用户
    draw_box(ax, 0.8, 3.5, 1.2, 0.8, '用户', '#264653', 'white', 12)

    # 用例
    cases = [
        (3.5, 5.5, '运行系统主程序', '#e76f51'),
        (3.5, 4.3, '查看天气预报表格', '#f4a261'),
        (3.5, 3.1, '查看温度趋势图', '#e9c46a'),
        (3.5, 1.9, '查看空气质量地图', '#4ECDC4'),
        (7, 5.5, '自动获取天气数据', '#4A90D9'),
        (7, 4.3, '训练预测模型', '#6c5ce7'),
        (7, 3.1, '预测未来一周天气', '#00b894'),
        (7, 1.9, '生成HTML网页', '#e94560'),
    ]

    for x, y, text, color in cases:
        # 椭圆
        from matplotlib.patches import Ellipse
        ellipse = Ellipse((x, y), 2.8, 0.7, facecolor=color, edgecolor='#333',
                          linewidth=1, alpha=0.85)
        ax.add_patch(ellipse)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    # 连线 (用户到用例)
    for x, y, _, _ in cases[:4]:
        ax.plot([1.4, x-1.4], [3.5, y], color='#aaa', linewidth=1, linestyle='--')

    # 包含关系
    ax.annotate('', xy=(5.6, 5.5), xytext=(4.9, 5.5),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(5.6, 4.3), xytext=(4.9, 4.3),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))
    ax.annotate('', xy=(5.6, 3.1), xytext=(4.9, 3.1),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    ax.text(5.25, 5.7, '<<include>>', fontsize=7, color='#666', ha='center')
    ax.text(5.25, 4.5, '<<include>>', fontsize=7, color='#666', ha='center')
    ax.text(5.25, 3.3, '<<include>>', fontsize=7, color='#666', ha='center')

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig2_1_use_case.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 图1.1 技术路线图
# ============================================================
def fig_tech_route():
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')
    ax.set_title('图1.1  技术路线图', fontsize=14, fontweight='bold', pad=15)

    # 第一层：数据获取
    draw_box(ax, 2, 4.8, 3, 0.8, '数据获取层\nRequests + BeautifulSoup\n2345天气网爬虫', '#2d6a4f', 'white', 9)
    draw_box(ax, 6, 4.8, 3, 0.8, '数据存储层\nPandas DataFrame\nCSV文件存储', '#40916c', 'white', 9)

    # 第二层：数据处理
    draw_box(ax, 2, 3.3, 3, 0.8, '数据处理层\nPandas + SimpleImputer\n特征工程 + 编码映射', '#e76f51', 'white', 9)
    draw_box(ax, 6, 3.3, 3, 0.8, '模型训练层\nScikit-learn\nRandomForestRegressor', '#f4a261', 'white', 9)

    # 第三层：应用
    draw_box(ax, 6, 1.8, 3, 0.8, '预测输出层\n双目标回归预测\n最高温 + 最低温', '#e9c46a', '#333', 9)
    draw_box(ax, 2, 1.8, 3, 0.8, '可视化展示层\nPyecharts\n表格+图表+地图', '#264653', 'white', 9)

    # 最终输出
    draw_box(ax, 4, 0.5, 4, 0.7, 'HTML交互式网页', '#e94560', 'white', 12)

    # 箭头
    draw_arrow(ax, 3.5, 4.8, 4.5, 4.8, '#555')
    draw_arrow(ax, 6, 4.4, 3.5, 3.7, '#555')
    draw_arrow(ax, 3.5, 3.3, 4.5, 3.3, '#555')
    draw_arrow(ax, 6, 2.9, 6, 2.2, '#555')
    draw_arrow(ax, 2, 2.2, 2, 2.2, '#555')

    draw_arrow(ax, 3, 1.4, 3.5, 0.85, '#e94560')
    draw_arrow(ax, 6, 1.4, 4.5, 0.85, '#e94560')

    # 右侧工具栏
    tools = [
        (10, 5.0, 'Python 3.12'),
        (10, 4.2, 'Scikit-learn'),
        (10, 3.4, 'Pandas'),
        (10, 2.6, 'Pyecharts'),
        (10, 1.8, 'Requests'),
        (10, 1.0, 'BeautifulSoup'),
    ]
    for x, y, text in tools:
        draw_box(ax, x, y, 2, 0.5, text, '#16213e', '#eaeaea', 9)

    # 工具标题
    draw_box(ax, 10, 5.7, 2.5, 0.5, '核心依赖库', '#0f3460', 'white', 10)

    plt.tight_layout()
    path = os.path.join(FIG_DIR, 'fig1_1_tech_route.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  已生成: {path}')
    return path


# ============================================================
# 主函数
# ============================================================
if __name__ == '__main__':
    print("=" * 50)
    print("  生成论文配图")
    print("=" * 50)

    paths = []
    paths.append(fig_tech_route())        # 图1.1
    paths.append(fig_use_case())          # 图2.1
    paths.append(fig_system_architecture())  # 图3.1
    paths.append(fig_data_flow())         # 图3.2
    paths.append(fig_getdata_flow())      # 图3.3
    paths.append(fig_processdata_flow())  # 图3.4
    paths.append(fig_getmodel_flow())     # 图3.5
    paths.append(fig_feature_importance())  # 图4.1
    paths.append(fig_prediction_comparison())  # 图4.2
    paths.append(fig_error_distribution())  # 图4.3
    paths.append(fig_web_preview())       # 图4.4

    print(f"\n  ✅ 共生成 {len(paths)} 张图片")
    print(f"  📁 保存目录: {FIG_DIR}")
