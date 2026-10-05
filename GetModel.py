# -*- coding: utf-8 -*-
"""
GetModel.py
功能：随机森林回归训练天气预测模型，joblib保存模型，MAE评估
"""

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os

# 模型保存路径
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_model.pkl")


def build_and_train(X_train, y_train, n_estimators=200, max_depth=10):
    """
    构建并训练随机森林回归模型
    参数:
        X_train: 训练集特征 (n_samples, n_features)
        y_train: 训练集目标 (n_samples, 2) — 同时预测最高温和最低温
    返回:
        训练好的模型
    """
    print("=" * 50)
    print("  随机森林回归模型训练")
    print("=" * 50)

    print(f"\n  模型参数:")
    print(f"    n_estimators = {n_estimators}  (决策树数量)")
    print(f"    max_depth    = {max_depth}    (最大深度)")
    print(f"    样本数       = {X_train.shape[0]}")
    print(f"    特征维度     = {X_train.shape[1]}")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,          # 全部CPU核心并行
        oob_score=True,     # 袋外评估
    )

    print("\n  正在训练...")
    model.fit(X_train, y_train)
    print(f"  ✓ 训练完成！")
    print(f"  OOB得分: {model.oob_score_:.4f}")

    # 特征重要性
    feature_names = ["天气编码", "风向编码", "风力编码", "月份"]
    print(f"\n  特征重要性:")
    for name, imp in sorted(zip(feature_names, model.feature_importances_), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"    {name:<8}: {imp:.4f} {bar}")

    return model


def evaluate_model(model, X_val, y_val):
    """
    用MAE评估模型
    返回: dict (mae_total, mae_high, mae_low)
    """
    print(f"\n{'=' * 50}")
    print("  模型评估 (MAE)")
    print("=" * 50)

    y_pred = model.predict(X_val)

    mae_total = mean_absolute_error(y_val, y_pred)
    mae_high  = mean_absolute_error(y_val[:, 0], y_pred[:, 0])
    mae_low   = mean_absolute_error(y_val[:, 1], y_pred[:, 1])

    print(f"\n  整体 MAE : {mae_total:.2f}°C")
    print(f"  最高温 MAE: {mae_high:.2f}°C")
    print(f"  最低温 MAE: {mae_low:.2f}°C")

    # 预测对比表
    print(f"\n  {'实际高温':>8} {'预测高温':>8} {'误差':>6}  │  {'实际低温':>8} {'预测低温':>8} {'误差':>6}")
    print(f"  {'─'*28}┼{'─'*28}")
    for i in range(min(10, len(y_val))):
        rh, ph = y_val[i, 0], y_pred[i, 0]
        rl, pl = y_val[i, 1], y_pred[i, 1]
        print(f"  {rh:>8.0f} {ph:>8.1f} {ph-rh:>+6.1f}  │  {rl:>8.0f} {pl:>8.1f} {pl-rl:>+6.1f}")

    return {"mae_total": mae_total, "mae_high": mae_high, "mae_low": mae_low}


def save_model(model, path=MODEL_PATH):
    """用joblib保存模型到本地"""
    joblib.dump(model, path)
    print(f"\n  ✓ 模型已保存: {path} ({os.path.getsize(path)/1024:.1f} KB)")


def load_model(path=MODEL_PATH):
    """加载本地模型"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"模型文件不存在: {path}，请先运行训练")
    model = joblib.load(path)
    print(f"  ✓ 模型已加载: {path}")
    return model


def get_model(X_train, y_train, X_val, y_val):
    """
    模型训练主流程：训练 → 评估 → 保存
    返回: model, metrics
    """
    model = build_and_train(X_train, y_train)
    metrics = evaluate_model(model, X_val, y_val)
    save_model(model)
    return model, metrics


if __name__ == "__main__":
    print("请通过 Main.py 运行完整流程")
