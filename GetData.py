# -*- coding: utf-8 -*-
"""
GetData.py
功能：从 Open-Meteo 历史天气 API 获取长沙逐日天气数据，保存为 CSV

────────────────────────────────────────────────────────
为什么换掉原来的数据源
────────────────────────────────────────────────────────

原来爬的是 2345 天气网。但那个页面只有 15 天预报 + 少量历史，
数据量根本不够训练。于是代码里加了一段 fallback：数据不够就用
random 生成补上 —— 结果 67 行里约 50 行是随机的。

证据（在旧 CSV 里能直接看出来）：
    · 日期格式前后不一致：真数据是 "07/13"，生成的是 "08-14"
    · 87% 的行温差落在 6~10 度 —— 正好是 random.randint(6, 10) 的范围
    · 生成的行天气只有「中雨」「多云」两种值

**训练数据里掺随机数，等于让模型学噪声。**

而且它不报错、不警告，报告里的 MAE 看起来还挺正常。
这又是一个「静默的错误」—— 比抛异常危险得多。

换成 Open-Meteo：
    · 免费、不用申请 key
    · 有多年逐日历史数据（不是预报，是真实观测）
    · 返回结构化 JSON，不用解析 HTML（原来那套正则解析本身就脆）

────────────────────────────────────────────────────────
"""

import os
from datetime import date, timedelta

import pandas as pd
import requests

# ==================== 配置 ====================
# 长沙坐标
LATITUDE = 28.23
LONGITUDE = 112.94

# 取多少年历史。数据越多，模型越稳；但 5 年足够看季节规律了
YEARS_BACK = 5

API_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARS = [
    "temperature_2m_max",           # 日最高温 °C
    "temperature_2m_min",           # 日最低温 °C
    "precipitation_sum",            # 日降水量 mm
    "wind_speed_10m_max",           # 日最大风速 km/h
    "wind_direction_10m_dominant",  # 主导风向 °
    "weather_code",                 # WMO 天气代码
]

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")

TIMEOUT = 30
RETRIES = 3


def fetch_history(start: str, end: str) -> dict:
    """调 Open-Meteo 拿逐日历史数据。失败自动重试。"""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start,
        "end_date": end,
        "daily": ",".join(DAILY_VARS),
        "timezone": "Asia/Shanghai",
    }

    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(API_URL, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            print(f"    第 {attempt}/{RETRIES} 次失败: {type(e).__name__}: {e}")

    raise RuntimeError(f"取数据失败（重试 {RETRIES} 次）: {last_err}")


def get_weather_data(start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """
    主函数：取历史天气 → 整理成 DataFrame → 存 CSV

    参数不给就用默认范围（今天往前 YEARS_BACK 年）。
    返回: pd.DataFrame
    """
    print("=" * 58)
    print("  长沙历史天气数据获取（Open-Meteo）")
    print("=" * 58)

    if end is None:
        end = (date.today() - timedelta(days=1)).isoformat()
    if start is None:
        start = (date.today() - timedelta(days=365 * YEARS_BACK)).isoformat()

    print(f"\n  坐标: {LATITUDE}, {LONGITUDE}")
    print(f"  区间: {start} ~ {end}")
    print(f"  变量: {', '.join(DAILY_VARS)}")

    print(f"\n  正在请求...")
    data = fetch_history(start, end)
    daily = data["daily"]

    df = pd.DataFrame({
        "日期":      daily["time"],
        "最高温":    daily["temperature_2m_max"],
        "最低温":    daily["temperature_2m_min"],
        "降水量":    daily["precipitation_sum"],
        "风速":      daily["wind_speed_10m_max"],
        "风向":      daily["wind_direction_10m_dominant"],
        "天气代码":  daily["weather_code"],
    })

    # ---- 数据质量检查：不合格就报错停下，绝不拿假数据往下走 ----
    #
    # 这一段是这次修改里最关键的。原来那段 fallback 的出发点是好的
    # （"数据不够就补"），但**用随机数补且不告诉任何人**是最糟的选择。
    # 缺数据只有一个正确处理方式：报错停下，让人去想办法。
    print(f"\n  --- 数据质量检查 ---")
    print(f"  总天数: {len(df)}")

    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)

    missing_rate = df.isnull().mean()
    worst = missing_rate[missing_rate > 0]
    if len(worst):
        print(f"  缺失情况:\n{worst.to_string()}")
    else:
        print(f"  无缺失值")

    # 温度缺失超过 5% 说明数据源有问题，直接停下
    if df["最高温"].isnull().mean() > 0.05 or df["最低温"].isnull().mean() > 0.05:
        raise RuntimeError(
            f"温度缺失过多（最高温 {df['最高温'].isnull().mean():.1%}），"
            f"数据源可能有问题，不继续"
        )

    # 样本太少也停下 —— 这是原来那段 fallback 该做而没做的事
    if len(df) < 365:
        raise RuntimeError(
            f"只有 {len(df)} 天数据，不足以训练（至少需要 365 天）。"
            f"检查一下日期区间，或者换个数据源 —— 不要用随机数补"
        )

    # 温度范围合理性（长沙历史极端温度大约 -10 ~ 45）
    tmax, tmin = df["最高温"].max(), df["最低温"].min()
    if not (-15 < tmin and tmax < 50):
        raise RuntimeError(f"温度范围异常: {tmin} ~ {tmax}，数据可能有问题")

    print(f"  温度范围: {df['最低温'].min():.1f} ~ {df['最高温'].max():.1f} °C")
    print(f"  日期范围: {df['日期'].iloc[0].date()} ~ {df['日期'].iloc[-1].date()}")
    print(f"  ✓ 检查通过")

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"\n  已保存: {CSV_PATH}")
    print(f"\n  前 5 行:")
    print(df.head().to_string(index=False))

    return df


if __name__ == "__main__":
    get_weather_data()
