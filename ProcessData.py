# -*- coding: utf-8 -*-
"""
ProcessData.py
功能：处理CSV天气数据，温度转整型，SimpleImputer填充缺失值，按8:2划分训练集与验证集
"""

import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
import os

# CSV文件路径
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")


def load_data(csv_path=CSV_PATH):
    """加载CSV天气数据"""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"  数据加载完成: {df.shape[0]}行 × {df.shape[1]}列")
    print(f"  列名: {list(df.columns)}")
    return df


def preprocess(df):
    """
    数据清洗与预处理
    步骤: 温度转整型 → 编码分类特征 → SimpleImputer填充缺失值
    """
    print("\n  --- 数据预处理 ---")

    # 1. 温度转为整型
    for col in ["最高温", "最低温"]:
        df[col] = (
            df[col].astype(str)
            .str.extract(r"(-?\d+)")[0]
            .astype(float)
        )
        print(f"  {col}: 均温{df[col].mean():.1f}°C, 范围[{df[col].min()}, {df[col].max()}]")

    # 2. 分类特征编码
    # 天气状况 → 数值
    weather_map = {
        "晴": 0, "多云": 1, "阴": 2, "小雨": 3,
        "中雨": 4, "大雨": 5, "雷阵雨": 6, "暴雨": 7,
        "小雪": 8, "中雪": 9, "大雪": 10, "雾": 11, "霾": 12,
    }
    # 处理"转"型天气（如"雷阵雨转多云"），取第一个天气类型
    def map_weather(w):
        if not isinstance(w, str):
            return 2
        w = w.split("转")[0].strip()
        return weather_map.get(w, 2)
    df["天气编码"] = df["天气"].apply(map_weather)

    # 风向 → 数值
    wind_dir_map = {
        "北风": 0, "东北风": 1, "东风": 2, "东南风": 3,
        "南风": 4, "西南风": 5, "西风": 6, "西北风": 7, "无持续风向": 8,
    }
    df["风向编码"] = df["风向"].map(wind_dir_map).fillna(0)

    # 风力 → 数值
    wind_level_map = {
        "微风": 0, "<3级": 1, "3-4级": 2, "4-5级": 3,
        "5-6级": 4, "6-7级": 5, "7-8级": 6, "8-9级": 7,
        "1级": 1, "2级": 2, "3级": 3, "4级": 4, "5级": 5, "6级": 6,
    }
    df["风力编码"] = df["风力"].map(wind_level_map).fillna(0)

    # 提取月份作为季节特征
    df["月份"] = pd.to_datetime(
        "2025-" + df["日期"].astype(str).str.strip(),
        format="%Y-%m-%d", errors="coerce"
    ).dt.month
    df["月份"] = df["月份"].fillna(df["月份"].median())

    # 3. 构建特征矩阵
    feature_cols = ["天气编码", "风向编码", "风力编码", "月份"]
    target_cols = ["最高温", "最低温"]
    all_cols = feature_cols + target_cols

    # 统计缺失值
    missing = df[all_cols].isnull().sum()
    if missing.sum() > 0:
        print(f"\n  缺失值:\n{missing[missing > 0].to_string()}")
    else:
        print("  无缺失值")

    # 4. SimpleImputer 填充缺失值（均值策略）
    imputer = SimpleImputer(strategy="mean")
    df_imputed = pd.DataFrame(
        imputer.fit_transform(df[all_cols]),
        columns=all_cols
    )

    # 温度转为整型
    for col in target_cols:
        df_imputed[col] = df_imputed[col].round().astype(int)

    print(f"  预处理完成: {df_imputed.shape[0]}样本 × {len(feature_cols)}特征")
    return df_imputed, feature_cols


def split_dataset(df, feature_cols, test_size=0.2):
    """
    按8:2划分训练集与验证集
    返回: X_train, X_val, y_train, y_val
    """
    X = df[feature_cols].values
    y = df[["最高温", "最低温"]].values  # 双目标回归

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=True
    )

    print(f"\n  训练集: X{X_train.shape}  y{y_train.shape}")
    print(f"  验证集: X{X_val.shape}  y{y_val.shape}")
    print(f"  特征列: {feature_cols}")

    return X_train, X_val, y_train, y_val


def process_data(csv_path=CSV_PATH):
    """
    数据处理主函数
    返回: X_train, X_val, y_train, y_val, feature_cols
    """
    print("=" * 50)
    print("  天气数据预处理")
    print("=" * 50)

    # 加载
    df = load_data(csv_path)

    # 预处理
    df_clean, feature_cols = preprocess(df)

    # 划分
    X_train, X_val, y_train, y_val = split_dataset(df_clean, feature_cols)

    return X_train, X_val, y_train, y_val, feature_cols


if __name__ == "__main__":
    X_train, X_val, y_train, y_val, feature_cols = process_data()
    print("\n  ✓ 预处理完成！")
