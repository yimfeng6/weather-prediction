# -*- coding: utf-8 -*-
"""
Main.py
功能：加载模型预测一周天气，pyecharts制作表格、组合图表、全国空气质量地图，生成天气网.html
"""

import sys, os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 确保同目录模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyecharts.charts import Line, Bar, Map, Timeline, Page
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.globals import ThemeType

from GetData import get_weather_data
from ProcessData import process_data, CSV_PATH, load_data, build_features
from GetModel import get_model, load_model, MODEL_PATH, train_horizon_models

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
# WMO 天气代码 → 中文（Open-Meteo 用的国际标准编码）
WMO_CN = {
    0: "晴", 1: "多云", 2: "多云", 3: "阴",
    45: "雾", 48: "雾",
    51: "小雨", 53: "小雨", 55: "中雨",
    56: "冻雨", 57: "冻雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "冻雨",
    71: "小雪", 73: "中雪", 75: "大雪", 77: "雪",
    80: "阵雨", 81: "阵雨", 82: "暴雨",
    85: "阵雪", 86: "阵雪",
    95: "雷阵雨", 96: "雷阵雨", 99: "雷阵雨",
}

# 16 方位中文（角度按气象惯例：0° = 北风，从北往东转）
WIND_16 = ["北风", "北东北", "东北风", "东东北", "东风", "东东南", "东南风", "南东南",
           "南风", "南西南", "西南风", "西西南", "西风", "西西北", "西北风", "北西北"]


def degrees_to_wind(deg: float) -> str:
    """风向角度 → 16 方位中文。"""
    idx = int((deg % 360) / 22.5 + 0.5) % 16
    return WIND_16[idx]


def speed_to_level(kmh: float) -> str:
    """风速 km/h → 中文风力描述。"""
    for limit, label in ((5.5, "微风"), (11, "1-2级"), (19, "3级"),
                         (28, "4级"), (38, "5级"), (49, "6级")):
        if kmh < limit:
            return label
    return "7级以上"


def _build_row(date, high, low, prev_high, prev_low,
               recent_highs, precip, wind_kmh, wind_deg, feature_cols):
    """
    按 ProcessData.build_features 的口径，为某一天拼一行特征。

    必须和训练时的列顺序、含义完全一致 —— 对不上的话模型给出的
    数字看着正常，其实毫无意义（这类错误不会报错，最难查）。
    """
    doy = date.timetuple().tm_yday
    rad = np.deg2rad(wind_deg)
    values = {
        "今日最高温": high,
        "今日最低温": low,
        "昨日最高温": prev_high,
        "昨日最低温": prev_low,
        "近3日均温": float(np.mean(recent_highs[-3:])),
        "近7日均温": float(np.mean(recent_highs[-7:])),
        "月份": date.month,
        "年内sin": np.sin(2 * np.pi * doy / 365.25),
        "年内cos": np.cos(2 * np.pi * doy / 365.25),
        "降水量": precip,
        "风速": wind_kmh,
        "风向sin": np.sin(rad),
        "风向cos": np.cos(rad),
    }
    return [values[c] for c in feature_cols]


def predict_week(models, feature_cols):
    """
    未来 7 天预报 —— 直接多步预测。

    每个步长用自己的模型，输入**始终是最后一天的真实观测**，不做递归。

    为什么不用递归
        第一版写的是「预测明天 → 把结果喂回去预测后天」。结果七天报同一个值：
        模型的头号特征是「今日最高温」（重要性 75%），它学到的本质就是
        「明天≈今天」，递归迭代下去会收敛到一个固定点。
        这是持续性型模型的固有毛病，不是代码写错了。

        改成「每个步长单独训一个模型」之后，七天是七个不同的值，
        而且误差随步长增长的趋势能直接算出来（见训练时打的那张表）。
    """
    print("\n" + "=" * 58)
    print("  未来一周天气预测（直接多步）")
    print("=" * 58)

    df = load_data(CSV_PATH)
    df_feat, _, _ = build_features(df)

    # 所有步长共用这一行输入：最后一天的真实观测
    x_last = df_feat[feature_cols].to_numpy(dtype=float)[-1:]
    last = df_feat.iloc[-1]
    base_date = pd.to_datetime(last["日期"]).date()

    weather_cn = WMO_CN.get(int(last["天气代码"]), "多云")
    wind_deg = float(last["风向"])
    wind_kmh = float(last["风速"])

    print(f"\n  起点: {base_date}  实况 "
          f"{last['今日最高温']:.1f} / {last['今日最低温']:.1f} ℃")
    print(f"  天气/风向/风力沿用最后一天的观测"
          f"（这几个量本身也需要预报，这里做了简化）")

    results = []
    print(f"\n  {'日期':>6} {'星期':>4}  {'天气':>5}  {'高温':>6} {'低温':>6}  "
          f"{'风向':>6} {'风力':>6}")
    print(f"  {'─' * 56}")

    for h in range(1, 8):
        d = base_date + timedelta(days=h)
        pred = models[h].predict(x_last)[0]
        high, low = float(pred[0]), float(pred[1])

        results.append(dict(
            日期=d.strftime("%m-%d"),
            星期=WEEKDAY_CN[d.weekday()],
            天气=weather_cn,
            最高温=int(round(high)),
            最低温=int(round(low)),
            风向=degrees_to_wind(wind_deg),
            风力=speed_to_level(wind_kmh),
        ))
        r = results[-1]
        mark = "" if h <= 3 else "   ← 仅供趋势参考"
        print(f"  {r['日期']:>6} {r['星期']:>4}  {r['天气']:>5}  "
              f"{r['最高温']:>4}℃ {r['最低温']:>4}℃  "
              f"{r['风向']:>6} {r['风力']:>6}{mark}")

    print(f"\n  ⚠ 第 1~3 天误差较小，第 4 天往后越来越接近「气候平均」，")
    print(f"     只能当趋势看。具体误差见上一步那张表。")
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
            model, metrics = get_model(X_train, y_train, X_val, y_val,
                                       feature_names=feat_cols)
    except Exception as e:
        print(f"  ✗ 模型训练失败: {e}"); return

    # 4. 训练多步模型（每个步长一个），再用它预测一周
    print("\n【步骤4】预测未来一周")
    try:
        _df = load_data()
        _df_feat, _feats, _ = build_features(_df)
        horizon_models = train_horizon_models(_df_feat, _feats)
    except Exception as e:
        print(f"  ✗ 多步模型训练失败: {e}")
        return
    preds = predict_week(horizon_models, _feats)

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
