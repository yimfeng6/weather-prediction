# -*- coding: utf-8 -*-
"""
ProcessData.py
功能：从 CSV 构造特征与标签，按时间顺序切分训练集/验证集

────────────────────────────────────────────────────────
这次改了两件事
────────────────────────────────────────────────────────

【一】加了滞后特征

原来的特征是这四个：
    天气编码、风向编码、风力编码、月份

**没有包含前几天的温度。** 而气温是高度自相关的 —— 昨天几度，
是预测今天几度最有力的信息，比风向风力加起来都管用。
用那四个特征预测温度，MAE 只能做到 4~6°C，属于「模型在瞎猜」。

现在加了：
    今日/昨日最高低温、前3天均温、前7天均温

【二】切分改成按时间顺序

原来是 train_test_split(shuffle=True)。对时间序列来说这是**数据泄漏** ——
会把「8月20日」放进训练集、拿「8月15日」当验证集，模型等于提前看到了答案。
报出来的 MAE 会虚高，看着好看但没意义。

时间序列只有一种切法：**用过去训练，用未来验证。**

────────────────────────────────────────────────────────
"""

import os

import numpy as np
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")


def load_data(csv_path: str = CSV_PATH) -> pd.DataFrame:
    """加载 CSV。"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)
    print(f"  数据加载完成: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"  日期范围: {df['日期'].iloc[0].date()} ~ {df['日期'].iloc[-1].date()}")
    return df


def build_features(df: pd.DataFrame):
    """
    构造特征矩阵和标签。

    任务定义：**用今天和过去几天的信息，预测明天**
    所以第 T 行是「T 日的已知信息 → T+1 日的温度」。

    返回: (带特征的 DataFrame, 特征列名列表)
    """
    print("\n  --- 构造特征 ---")
    out = df.copy()

    # ---- 1. 滞后特征：过去几天的温度 ----
    #
    # 这是这次修改的核心。气温的日内/日间延续性极强，
    # 不加这几个特征，模型基本是在瞎猜。
    out["今日最高温"] = out["最高温"]
    out["今日最低温"] = out["最低温"]

    out["昨日最高温"] = out["最高温"].shift(1)
    out["昨日最低温"] = out["最低温"].shift(1)

    # 前 3 天 / 前 7 天的滑动平均 —— 抹掉单日波动，看趋势
    out["近3日均温"] = out["最高温"].rolling(3).mean()
    out["近7日均温"] = out["最高温"].rolling(7).mean()

    # ---- 2. 时间特征：让模型知道「现在是几月/一年中的第几天」 ----
    #
    # 季节性是气温最强的规律之一，不给这个特征模型学不到年周期。
    out["月份"] = out["日期"].dt.month
    doy = out["日期"].dt.dayofyear
    # 用 sin/cos 表示周期，而不是直接用「第几天」——
    # 否则 12月31日(365) 和 1月1日(1) 在数值上差 364，但实际只差一天
    out["年内sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["年内cos"] = np.cos(2 * np.pi * doy / 365.25)

    # ---- 3. 气象特征 ----
    out["降水量"] = out["降水量"]
    out["风速"] = out["风速"]
    # 风向同理：0° 和 359° 在数值上差 359，实际只差 1 度。
    # 直接喂角度是经典错误，要转成 sin/cos。
    rad = np.deg2rad(out["风向"])
    out["风向sin"] = np.sin(rad)
    out["风向cos"] = np.cos(rad)

    # ---- 4. 标签：明天的温度 ----
    out["明日最高温"] = out["最高温"].shift(-1)
    out["明日最低温"] = out["最低温"].shift(-1)

    feature_cols = [
        "今日最高温", "今日最低温",
        "昨日最高温", "昨日最低温",
        "近3日均温", "近7日均温",
        "月份", "年内sin", "年内cos",
        "降水量", "风速", "风向sin", "风向cos",
    ]
    target_cols = ["明日最高温", "明日最低温"]

    # 首尾会因 shift/rolling 产生空值，丢掉
    before = len(out)
    out = out.dropna(subset=feature_cols + target_cols).reset_index(drop=True)
    print(f"  构造完成: {len(out)} 个可用样本（丢掉首尾 {before - len(out)} 行）")
    print(f"  特征 {len(feature_cols)} 个: {', '.join(feature_cols)}")
    print(f"  标签: 明日最高温 / 明日最低温")

    return out, feature_cols, target_cols


def split_dataset(df: pd.DataFrame, feature_cols: list, target_cols: list,
                  test_size: float = 0.2):
    """
    按时间顺序切分 —— **不打乱**。

    前 80% 训练、后 20% 验证。这样验证集是「训练时没见过的未来」，
    得到的 MAE 才是真实的预测能力。
    """
    X = df[feature_cols].to_numpy(dtype=float)
    y = df[target_cols].to_numpy(dtype=float)

    n = len(df)
    cut = int(n * (1 - test_size))

    X_train, X_val = X[:cut], X[cut:]
    y_train, y_val = y[:cut], y[cut:]

    print(f"\n  --- 切分（按时间，不打乱）---")
    print(f"  训练集: {X_train.shape[0]} 天  "
          f"({df['日期'].iloc[0].date()} ~ {df['日期'].iloc[cut-1].date()})")
    print(f"  验证集: {X_val.shape[0]} 天  "
          f"({df['日期'].iloc[cut].date()} ~ {df['日期'].iloc[-1].date()})")

    return X_train, X_val, y_train, y_val


def process_data(csv_path: str = CSV_PATH):
    """主流程：加载 → 构造特征 → 按时间切分。"""
    print("=" * 58)
    print("  天气数据预处理")
    print("=" * 58)

    df = load_data(csv_path)
    df_feat, feature_cols, target_cols = build_features(df)
    X_train, X_val, y_train, y_val = split_dataset(df_feat, feature_cols, target_cols)

    return X_train, X_val, y_train, y_val, feature_cols


if __name__ == "__main__":
    X_train, X_val, y_train, y_val, feat = process_data()
    print("\n  ✓ 预处理完成")
    print(f"     X_train {X_train.shape}   y_train {y_train.shape}")
    print(f"     X_val   {X_val.shape}   y_val   {y_val.shape}")


def build_horizon_dataset(df_feat, feature_cols, max_h: int = 7):
    """
    为「直接多步预测」准备数据。

    为什么要这个东西
        一开始写的是递归预测：用模型预测明天 → 把明天的预测值喂回去预测后天。
        结果**收敛成一个常数**：模型的头号特征是"今日最高温"（重要性 75%），
        它学到的本质是"明天≈今天"，递归下去就变成一个固定点，七天报同一个值。

        这是"持续性型模型 + 递归"的固有毛病，不是代码写错了。

    换个思路：**每个步长单独训一个模型**。
        模型 h=1 学「今天 → 明天」
        模型 h=2 学「今天 → 后天」
        ...
        模型 h=7 学「今天 → 第 7 天」
        预测时全部用"最后一天的真实数据"当输入，不做任何递归。

        这叫直接多步预测（direct multi-step）。好处是没有误差累积，
        代价是要训 7 个模型，而且远处的模型本质上是在学"气候平均"。

    返回: {1: (X, y), 2: (X, y), ..., max_h: (X, y)}
          其中 X 是当天的特征，y 是 h 天后的 [最高温, 最低温]
    """
    X_all = df_feat[feature_cols].to_numpy(dtype=float)
    base = df_feat[["今日最高温", "今日最低温"]].to_numpy(dtype=float)

    dataset = {}
    for h in range(1, max_h + 1):
        y = np.roll(base, -h, axis=0)
        y[-h:] = np.nan          # 末尾 h 行没有未来数据
        valid = ~np.isnan(y).any(axis=1)
        dataset[h] = (X_all[valid], y[valid])
    return dataset
