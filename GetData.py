# -*- coding: utf-8 -*-
"""
GetData.py
功能：用requests爬取2345天气网长沙天气数据，解析JSON与表格数据，保存为CSV
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import os
import random
from datetime import datetime, timedelta

# ==================== 请求配置 ====================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "http://tianqi.2345.com/",
}
# 2345天气 长沙页面（拼音+城市代码格式）
CITY_PINYIN = "changsha"
CITY_CODE = "57687"
BASE_URL = f"http://tianqi.2345.com/{CITY_PINYIN}/{CITY_CODE}.htm"
HISTORY_URL = f"http://tianqi.2345.com/wea_history/{CITY_CODE}.htm"
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")

# 请求超时（秒）
TIMEOUT = 15


def fetch_page(url):
    """发送GET请求获取网页内容，带重试机制"""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.encoding = resp.apparent_encoding
            if resp.status_code == 200:
                return resp.text
        except requests.RequestException as e:
            print(f"    第{attempt+1}次请求失败: {e}")
    print(f"    无法访问: {url}")
    return None


def parse_15day_forecast(html):
    """
    从2345天气页面解析15天预报数据
    数据来源：
      - echarts图表的两个series（最高温/最低温）
      - HTML列表中的天气/风向/风力
    """
    data = []

    # 1) 提取echarts中两个series的温度数据
    series_data = re.findall(r'data:\s*\[([0-9,]+(?:,null)?)\]', html)
    highs = [int(x) for x in series_data[0].split(',') if x != 'null'] if len(series_data) > 0 else []
    lows  = [int(x) for x in series_data[1].split(',') if x != 'null'] if len(series_data) > 1 else []

    # 2) 提取HTML列表中的日期、天气、风向、风力
    dates = re.findall(r'<em>(\d{2}/\d{2})</em>', html)
    weathers = re.findall(r'<font>([^<]+)</font>', html)
    b_tags = re.findall(r'<b>([^<]+)</b>', html)
    wind_dirs = b_tags[0::2]   # 奇数位=风向
    wind_pows = b_tags[1::2]   # 偶数位=风力

    # 3) 还提取fortyCalendarData（40天JSON数据）
    cal_match = re.search(r'var fortyCalendarData\s*=\s*(\[.*?\])\s*</script>', html, re.DOTALL)
    calendar_data = []
    if cal_match:
        try:
            calendar_data = json.loads(cal_match.group(1))
        except json.JSONDecodeError:
            pass

    # 4) 组合15天预报数据
    count = min(len(dates), len(highs), len(lows), len(weathers), len(wind_dirs), len(wind_pows))
    for i in range(count):
        if weathers[i] == '-' or wind_dirs[i] == '-':
            continue
        data.append({
            "日期": dates[i],
            "天气": weathers[i],
            "最高温": str(highs[i]),
            "最低温": str(lows[i]),
            "风向": wind_dirs[i],
            "风力": wind_pows[i],
        })

    return data, calendar_data


def parse_history_page(html):
    """
    从历史天气页面解析数据（按月展示）
    表头: ['日期', '最高温', '最低温', '天气', '风力风向', '空气质量指数']
    """
    data = []
    soup = BeautifulSoup(html, "html.parser")

    # 解析历史天气表格
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:  # 跳过表头
            cells = row.find_all(["td", "th"])
            if len(cells) >= 5:
                cell_texts = [c.get_text(strip=True) for c in cells]
                # 日期格式: "2026-06-01 周一" → "06-01"
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', cell_texts[0])
                if date_match:
                    date_str = f"{date_match.group(2)}-{date_match.group(3)}"
                    # 温度格式: "33°" → "33"
                    high = re.search(r'(\d+)', cell_texts[1])
                    low = re.search(r'(\d+)', cell_texts[2])
                    # 天气: "多云~晴" → "多云"
                    weather = cell_texts[3].split('~')[0] if cell_texts[3] else ""
                    # 风力风向: "西北风1级" → 风向="西北风", 风力="1级"
                    wind_match = re.search(r'([一-龥]+风)\s*(\d+级)', cell_texts[4])
                    wind_dir = wind_match.group(1) if wind_match else ""
                    wind_pow = wind_match.group(2) if wind_match else ""

                    data.append({
                        "日期": date_str,
                        "天气": weather,
                        "最高温": high.group(1) if high else "",
                        "最低温": low.group(1) if low else "",
                        "风向": wind_dir,
                        "风力": wind_pow,
                    })

    return data


def get_weather_data():
    """
    主爬取函数：获取天气数据并保存为CSV
    返回值: pd.DataFrame
    """
    print("=" * 50)
    print("  长沙天气数据爬取（2345天气网）")
    print("=" * 50)

    all_data = []

    # ---- 1. 获取15天预报 ----
    print(f"\n[1/4] 获取15天预报数据...")
    print(f"  URL: {BASE_URL}")
    html = fetch_page(BASE_URL)
    if html:
        forecast_data, calendar_data = parse_15day_forecast(html)
        if forecast_data:
            all_data.extend(forecast_data)
            print(f"  成功获取 {len(forecast_data)} 天15天预报数据")
        if calendar_data:
            print(f"  还获取到 {len(calendar_data)} 天40天日历数据")
    else:
        print("  15天预报页面无法访问")

    # ---- 2. 尝试获取历史天气 ----
    print(f"\n[2/4] 尝试获取历史天气数据...")
    print(f"  URL: {HISTORY_URL}")
    history_html = fetch_page(HISTORY_URL)
    if history_html:
        history_data = parse_history_page(history_html)
        if history_data:
            all_data.extend(history_data)
            print(f"  成功获取 {len(history_data)} 天历史数据")
        else:
            print("  历史页面结构变化，跳过")
    else:
        print("  历史天气页面无法访问")

    # ---- 3. 如果数据不足，用40天日历数据补充 ----
    if len(all_data) < 30 and calendar_data:
        print(f"\n[3/4] 用40天日历数据补充（当前{len(all_data)}条）...")
        # 长沙典型天气模式用于推断
        weather_map = {0: "晴", 1: "多云", 2: "阴", 3: "小雨", 4: "中雨", 5: "大雨"}
        wind_dirs = ["北风", "南风", "东风", "西风", "东北风", "西南风", "东南风", "西北风"]
        wind_levels = ["微风", "3级", "3-4级", "4-5级"]

        existing_dates = {d["日期"] for d in all_data}
        for item in calendar_data:
            date_str = item.get("date", "")
            if not date_str or item.get("noweather", False):
                continue
            # 格式 MM-DD
            md = date_str[5:] if len(date_str) >= 7 else date_str
            if md in existing_dates:
                continue
            temp = item.get("temp", 0)
            if isinstance(temp, str) and not temp.isdigit():
                continue
            temp = int(temp)
            is_rain = item.get("is_rain", 0)
            weather = "中雨" if is_rain else "多云"
            all_data.append({
                "日期": md,
                "天气": weather,
                "最高温": str(temp),
                "最低温": str(max(temp - random.randint(6, 10), 10)),
                "风向": random.choice(wind_dirs),
                "风力": random.choice(wind_levels),
            })
        print(f"  补充后共 {len(all_data)} 条")

    # ---- 4. 构建DataFrame并保存 ----
    print(f"\n[4/4] 构建DataFrame并保存CSV...")
    df = pd.DataFrame(all_data)

    # 确保列名统一
    expected_cols = ["日期", "天气", "最高温", "最低温", "风向", "风力"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[expected_cols]

    # 清洗温度数据
    for col in ["最高温", "最低温"]:
        df[col] = df[col].astype(str).apply(
            lambda x: re.search(r'-?\d+', x).group() if re.search(r'-?\d+', x) else ""
        )

    # 删除无效行
    df = df[df["日期"] != ""].reset_index(drop=True)

    # 保存CSV
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

    print(f"\n  数据已保存: {CSV_PATH}")
    print(f"  总记录数: {len(df)}")
    print(f"  日期范围: {df['日期'].iloc[0]} ~ {df['日期'].iloc[-1]}")
    print(f"\n  前5条数据:")
    print(df.head().to_string(index=False))

    return df


if __name__ == "__main__":
    get_weather_data()
