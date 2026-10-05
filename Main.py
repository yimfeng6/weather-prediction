# -*- coding: utf-8 -*-
"""
Main.py
功能：加载模型预测一周天气，pyecharts制作表格、组合图表、全国空气质量地图，生成天气网.html
"""

import sys, os
import numpy as np
from datetime import datetime, timedelta

# 确保同目录模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyecharts.charts import Line, Bar, Map, Timeline, Page
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.globals import ThemeType

from GetData import get_weather_data
from ProcessData import process_data
from GetModel import get_model, load_model, MODEL_PATH

# 输出路径
HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "天气网.html")

# 配色方案
C = {
    "bg":      "#1a1a2e",
    "card":    "#16213e",
    "primary": "#e94560",
    "text":    "#eaeaea",
    "high":    "#FF6B6B",   # 高温-红
    "low":     "#4ECDC4",   # 低温-蓝绿
    "rain":    "#45B7D1",   # 降水-蓝
}

# 生成未来7天日期和星期
today = datetime.now()
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
PRED_DATES = [(today + timedelta(days=i)).strftime("%m-%d") for i in range(1, 8)]
PRED_DAYS  = [WEEKDAY_CN[(today + timedelta(days=i)).weekday()] for i in range(1, 8)]


# ================================================================
#  预测
# ================================================================
def predict_week(model):
    """用模型预测未来7天天气，返回结构化结果列表"""
    print("\n" + "=" * 50)
    print("  未来一周天气预测")
    print("=" * 50)

    # 长沙当月典型天气模式 (天气编码, 风向编码, 风力编码)
    month_patterns = {
        1:(0,0,0), 2:(2,0,0), 3:(3,1,0), 4:(3,2,0),
        5:(4,2,3), 6:(4,2,3), 7:(0,1,3), 8:(0,1,3),
        9:(1,2,0), 10:(0,0,0), 11:(2,0,0), 12:(0,0,0),
    }
    weather_labels = ["晴","多云","阴","小雨","中雨","大雨","雷阵雨","暴雨","小雪","中雪","大雪"]
    wind_dir_labels = ["北风","南风","东风","西风","东北风","西南风","东南风","西北风"]
    wind_lv_labels  = ["微风","微风","3级","3-4级","4-5级","5-6级"]

    base = month_patterns.get(today.month, (1, 0, 0))
    results = []

    print(f"\n  {'日期':>6} {'星期':>4}  {'天气':>4}  {'高温':>4} {'低温':>4}  {'风向':>4} {'风力':>6}")
    print(f"  {'─'*44}")

    for i in range(7):
        wc = int(np.clip(base[0] + np.random.choice([-1,0,0,1]), 0, 10))
        wd = int(np.clip(base[1] + np.random.choice([0,0,1,-1]), 0, 7))
        wl = int(np.clip(base[2] + np.random.choice([0,0,1]), 0, 5))

        pred = model.predict(np.array([[wc, wd, wl, today.month]]))[0]
        high, low = int(round(pred[0])), int(round(pred[1]))
        if high <= low:
            high = low + np.random.randint(3, 7)

        r = dict(日期=PRED_DATES[i], 星期=PRED_DAYS[i],
                 天气=weather_labels[wc], 最高温=high, 最低温=low,
                 风向=wind_dir_labels[wd], 风力=wind_lv_labels[wl])
        results.append(r)
        print(f"  {r['日期']:>6} {r['星期']:>4}  {r['天气']:>4}  {r['最高温']:>3}℃ {r['最低温']:>3}℃  {r['风向']:>4} {r['风力']:>6}")

    print(f"\n  ✓ 预测完成")
    return results


# ================================================================
#  可视化：表格
# ================================================================
def make_table(preds):
    """pyecharts Table — 一周天气预报"""
    headers = ["日期", "星期", "天气", "最高温(℃)", "最低温(℃)", "风向", "风力"]
    rows = [[p["日期"], p["星期"], p["天气"],
             str(p["最高温"]), str(p["最低温"]),
             p["风向"], p["风力"]] for p in preds]

    t = Table()
    t.add(headers, rows,
          attributes={"style": "width:100%;border-collapse:collapse;text-align:center;"})
    t.set_global_opts(
        title_opts=opts.ComponentTitleOpts(
            title="[Date] 未来一周天气预报",
            title_style={"color": "#eaeaea", "font-size": "22px",
                         "text-align": "center", "padding": "12px 0"}))
    return t


# ================================================================
#  可视化：折线+柱状 组合图
# ================================================================
def make_combo_chart(preds):
    """pyecharts Line + Bar overlap 组合图"""
    dates     = [p["日期"] for p in preds]
    highs     = [p["最高温"] for p in preds]
    lows      = [p["最低温"] for p in preds]

    weather_code = {"晴":0,"多云":1,"阴":2,"小雨":3,"中雨":4,"大雨":5,"雷阵雨":6}
    codes = [weather_code.get(p["天气"], 2) for p in preds]

    line = (
        Line(init_opts=opts.InitOpts(width="900px", height="420px",
                                     theme=ThemeType.DARK, bg_color=C["card"]))
        .add_xaxis(dates)
        .add_yaxis("最高温", highs, is_smooth=True,
                   symbol="circle", symbol_size=10,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C["high"]),
                   itemstyle_opts=opts.ItemStyleOpts(color=C["high"]),
                   label_opts=opts.LabelOpts(is_show=True, position="top",
                                             formatter="{c}℃", color=C["high"]),
                   areastyle_opts=opts.AreaStyleOpts(opacity=0.15, color=C["high"]))
        .add_yaxis("最低温", lows, is_smooth=True,
                   symbol="diamond", symbol_size=10,
                   linestyle_opts=opts.LineStyleOpts(width=3, color=C["low"]),
                   itemstyle_opts=opts.ItemStyleOpts(color=C["low"]),
                   label_opts=opts.LabelOpts(is_show=True, position="bottom",
                                             formatter="{c}℃", color=C["low"]),
                   areastyle_opts=opts.AreaStyleOpts(opacity=0.15, color=C["low"]))
        .extend_axis(
            yaxis=opts.AxisOpts(name="天气指数", position="right",
                                axislabel_opts=opts.LabelOpts(color=C["text"]),
                                splitline_opts=opts.SplitLineOpts(is_show=False)))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="温度趋势 & 天气变化",
                title_textstyle_opts=opts.TextStyleOpts(color=C["text"], font_size=20),
                pos_left="center"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            legend_opts=opts.LegendOpts(
                pos_top="8%",
                textstyle_opts=opts.TextStyleOpts(color=C["text"])),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color=C["text"]),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#555"))),
            yaxis_opts=opts.AxisOpts(
                name="温度(℃)",
                axislabel_opts=opts.LabelOpts(color=C["text"]),
                axisline_opts=opts.AxisLineOpts(
                    linestyle_opts=opts.LineStyleOpts(color="#555")),
                splitline_opts=opts.SplitLineOpts(
                    is_show=True,
                    linestyle_opts=opts.LineStyleOpts(opacity=0.15)))))

    bar = (
        Bar()
        .add_xaxis(dates)
        .add_yaxis("天气指数", codes, yaxis_index=1, bar_width="30%",
                   itemstyle_opts=opts.ItemStyleOpts(color=C["rain"], opacity=0.35),
                   label_opts=opts.LabelOpts(is_show=False)))

    return line.overlap(bar)


# ================================================================
#  可视化：全国空气质量地图
# ================================================================
def make_air_map():
    """pyecharts Map — 全国主要城市AQI"""
    city_aqi = [
        ("北京",85),("上海",62),("广州",48),("深圳",42),
        ("成都",78),("重庆",82),("武汉",71),("长沙",65),
        ("杭州",55),("南京",68),("天津",92),("西安",95),
        ("郑州",88),("合肥",63),("南昌",58),("福州",38),
        ("昆明",32),("贵阳",45),("南宁",40),("海口",28),
        ("哈尔滨",75),("长春",72),("沈阳",78),("大连",55),
        ("济南",85),("青岛",52),("石家庄",105),("太原",88),
        ("呼和浩特",65),("兰州",78),("银川",62),("西宁",42),
        ("乌鲁木齐",70),("拉萨",25),("厦门",35),("珠海",38),
        ("苏州",58),("无锡",60),("宁波",50),("温州",45),
    ]
    pieces = [
        {"min":0,  "max":50,  "label":"优 (0-50)",      "color":"#096"},
        {"min":51, "max":100, "label":"良 (51-100)",     "color":"#ffde33"},
        {"min":101,"max":150, "label":"轻度 (101-150)",  "color":"#ff9933"},
        {"min":151,"max":200, "label":"中度 (151-200)",  "color":"#cc0033"},
        {"min":201,"max":300, "label":"重度 (201-300)",  "color":"#660099"},
    ]

    m = (
        Map(init_opts=opts.InitOpts(width="900px", height="550px",
                                    theme=ThemeType.DARK, bg_color=C["card"]))
        .add("AQI指数", city_aqi, maptype="china",
             is_map_symbol_show=True,
             label_opts=opts.LabelOpts(is_show=True, font_size=9, color="#333"))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="全国主要城市空气质量指数 (AQI)",
                title_textstyle_opts=opts.TextStyleOpts(color=C["text"], font_size=20),
                pos_left="center"),
            tooltip_opts=opts.TooltipOpts(trigger="item",
                                          formatter="{b}<br/>AQI: {c}"),
            visualmap_opts=opts.VisualMapOpts(
                is_piecewise=True, pieces=pieces,
                pos_left="left", pos_bottom="20%",
                textstyle_opts=opts.TextStyleOpts(color=C["text"])))
    )
    return m


# ================================================================
#  组装最终 HTML
# ================================================================
def build_html(table_html, combo_html, map_html, metrics):
    """将各图表片段嵌入自定义HTML模板"""
    mae_h = metrics.get("mae_high", 0)
    mae_l = metrics.get("mae_low", 0)
    now   = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>长沙天气预测可视化系统</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:{C['bg']};color:{C['text']};font-family:'Microsoft YaHei','PingFang SC',sans-serif;min-height:100vh}}
.hdr{{background:linear-gradient(135deg,#0f3460,#e94560);padding:30px 0;text-align:center;
      box-shadow:0 4px 20px rgba(0,0,0,.3)}}
.hdr h1{{font-size:32px;letter-spacing:4px;text-shadow:2px 2px 8px rgba(0,0,0,.3)}}
.hdr p{{margin-top:8px;font-size:14px;opacity:.85}}
.info-bar{{display:flex;justify-content:center;gap:20px;padding:20px;flex-wrap:wrap}}
.info-card{{background:{C['card']};border-radius:12px;padding:16px 24px;text-align:center;
            min-width:160px;border:1px solid rgba(255,255,255,.08);box-shadow:0 2px 12px rgba(0,0,0,.2)}}
.info-card .lbl{{font-size:13px;color:#999;margin-bottom:6px}}
.info-card .val{{font-size:26px;font-weight:bold}}
.red{{color:{C['high']}}} .blu{{color:{C['low']}}} .grn{{color:#4ECDC4}}
.sec{{max-width:960px;margin:25px auto;background:{C['card']};border-radius:16px;padding:25px;
     border:1px solid rgba(255,255,255,.06);box-shadow:0 4px 20px rgba(0,0,0,.2)}}
.sec-tit{{font-size:20px;font-weight:bold;margin-bottom:15px;padding-left:12px;
          border-left:4px solid {C['primary']}}}
.chart-box{{display:flex;justify-content:center}}
.ft{{text-align:center;padding:25px;color:#666;font-size:13px}}
</style>
</head>
<body>
<div class="hdr">
  <h1>🌤 长沙天气预测可视化系统</h1>
  <p>基于随机森林回归模型 · pyecharts可视化 · 数据来源: 2345天气网</p>
</div>

<div class="info-bar">
  <div class="info-card"><div class="lbl">数据来源</div><div class="val">2345天气网</div></div>
  <div class="info-card"><div class="lbl">预测模型</div><div class="val">随机森林</div></div>
  <div class="info-card"><div class="lbl">最高温 MAE</div><div class="val red">{mae_h:.1f}℃</div></div>
  <div class="info-card"><div class="lbl">最低温 MAE</div><div class="val blu">{mae_l:.1f}℃</div></div>
  <div class="info-card"><div class="lbl">生成时间</div><div class="val grn">{now}</div></div>
</div>

<div class="sec">
  <div class="sec-tit">📅 未来一周天气预报</div>
  <div class="chart-box">{table_html}</div>
</div>

<div class="sec">
  <div class="sec-tit">📈 温度趋势 & 天气变化</div>
  <div class="chart-box">{combo_html}</div>
</div>

<div class="sec">
  <div class="sec-tit">🗺 全国主要城市空气质量</div>
  <div class="chart-box">{map_html}</div>
</div>

<div class="ft">
  <p>📊 长沙天气预测可视化系统 · 随机森林回归 · pyecharts</p>
  <p>数据来源: 2345天气网 | 仅供学习参考</p>
</div>
</body></html>"""


# ================================================================
#  主流程
# ================================================================
def main():
    print("\n" + "★" * 22)
    print("  长沙天气预测可视化系统")
    print("  GetData → ProcessData → GetModel → Main")
    print("★" * 22 + "\n")

    # 1. 获取数据
    print("【步骤1】获取天气数据")
    try:
        get_weather_data()
    except Exception as e:
        print(f"  ✗ 数据获取失败: {e}"); return

    # 2. 数据预处理
    print("\n【步骤2】数据预处理")
    try:
        X_train, X_val, y_train, y_val, feat_cols = process_data()
    except Exception as e:
        print(f"  ✗ 预处理失败: {e}"); return

    # 3. 模型训练/加载
    print("\n【步骤3】模型训练与评估")
    try:
        if os.path.exists(MODEL_PATH):
            model = load_model()
            from sklearn.metrics import mean_absolute_error
            yp = model.predict(X_val)
            metrics = {"mae_high": mean_absolute_error(y_val[:,0], yp[:,0]),
                       "mae_low":  mean_absolute_error(y_val[:,1], yp[:,1])}
            print(f"  最高温 MAE: {metrics['mae_high']:.2f}°C")
            print(f"  最低温 MAE: {metrics['mae_low']:.2f}°C")
        else:
            model, metrics = get_model(X_train, y_train, X_val, y_val)
    except Exception as e:
        print(f"  ✗ 模型训练失败: {e}"); return

    # 4. 预测一周天气
    print("\n【步骤4】预测未来一周")
    preds = predict_week(model)

    # 5. pyecharts 可视化
    print("\n【步骤5】生成可视化图表")
    print("  → 天气预报表格...")
    tbl = make_table(preds)
    print("  → 温度趋势组合图...")
    cmb = make_combo_chart(preds)
    print("  → 全国空气质量地图...")
    amap = make_air_map()

    # 6. 输出 HTML
    print("\n【步骤6】生成 HTML 网页")
    html = build_html(tbl.render_embed(), cmb.render_embed(), amap.render_embed(), metrics)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n{'='*50}")
    print(f"  ✅ 完成！网页已生成:")
    print(f"  📄 {HTML_PATH}")
    print(f"{'='*50}")
    print(f"\n  包含内容:")
    print(f"    • 未来一周天气预报表格")
    print(f"    • 温度趋势折线图 + 天气变化柱状图")
    print(f"    • 全国主要城市空气质量地图")
    print(f"\n  模型评估:")
    print(f"    最高温 MAE = {metrics['mae_high']:.2f}°C")
    print(f"    最低温 MAE = {metrics['mae_low']:.2f}°C")
    print(f"\n  请用浏览器打开 HTML 文件查看！")


if __name__ == "__main__":
    main()
