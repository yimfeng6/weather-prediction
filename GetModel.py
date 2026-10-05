# -*- coding: utf-8 -*-
"""
GetModel.py
功能：随机森林回归训练天气预测模型，joblib 保存，MAE 评估 + 基线对比

────────────────────────────────────────────────────────
这次加了一件重要的事：基线对比
────────────────────────────────────────────────────────

原来只报一个 MAE 数字。但**光看 MAE 是 3 度还是 2 度，判断不出模型有没有用**——
你得知道「什么都不学」能做到多少。

预测气温有个很强的朴素基线：**明天 = 今天**（持续性预测）。
长沙这种地方，它的 MAE 大约在 2~3°C。如果模型的 MAE 也是 2~3°C，
那说明模型什么都没学到，直接用今天的温度当明天的预报就行了。

所以下面每次评估都会算两行：
    · 基线（明天=今天）的 MAE
    · 模型的 MAE
    · 以及模型比基线好了多少

**模型跑不赢基线 = 这个模型没有存在价值。** 这句话值得贴在显示器上。

────────────────────────────────────────────────────────
"""

import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from ProcessData import build_horizon_dataset

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_model.pkl")


def baseline_mae(X_val, y_val):
    """
    持续性基线：直接拿「今天的温度」当「明天的预报」。

    X_val 的前两列是「今日最高温 / 今日最低温」（见 ProcessData.build_features 的顺序），
    y_val 是「明日最高温 / 明日最低温」。
    """
    today_high = X_val[:, 0]
    today_low = X_val[:, 1]

    return {
        "high": mean_absolute_error(y_val[:, 0], today_high),
        "low": mean_absolute_error(y_val[:, 1], today_low),
    }


def build_and_train(X_train, y_train, n_estimators=300, max_depth=14,
                    feature_names=None):
    """构建并训练随机森林回归模型。"""
    print("=" * 58)
    print("  随机森林回归模型训练")
    print("=" * 58)

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
        n_jobs=-1,
        oob_score=True,
    )

    print("\n  正在训练...")
    model.fit(X_train, y_train)
    print(f"  ✓ 训练完成")
    print(f"  OOB 得分: {model.oob_score_:.4f}")

    if feature_names:
        print(f"\n  特征重要性（前 8）:")
        pairs = sorted(zip(feature_names, model.feature_importances_),
                       key=lambda x: -x[1])
        for name, imp in pairs[:8]:
            bar = "█" * int(imp * 60)
            print(f"    {name:<10}: {imp:.4f} {bar}")

    return model


def evaluate_model(model, X_val, y_val):
    """评估：模型 MAE vs 持续性基线 MAE。"""
    print(f"\n{'=' * 58}")
    print("  模型评估")
    print("=" * 58)

    y_pred = model.predict(X_val)

    model_high = mean_absolute_error(y_val[:, 0], y_pred[:, 0])
    model_low = mean_absolute_error(y_val[:, 1], y_pred[:, 1])
    base = baseline_mae(X_val, y_val)

    def line(name, base_v, model_v):
        gain = base_v - model_v
        flag = "✓ 优于基线" if gain > 0 else "✗ 不如基线"
        print(f"  {name:<8}  基线 {base_v:>5.2f}°C   模型 {model_v:>5.2f}°C   "
              f"改善 {gain:>+5.2f}°C   {flag}")

    print()
    line("最高温", base["high"], model_high)
    line("最低温", base["low"], model_low)

    avg_base = (base["high"] + base["low"]) / 2
    avg_model = (model_high + model_low) / 2
    print(f"  {'平均':<8}  基线 {avg_base:>5.2f}°C   模型 {avg_model:>5.2f}°C   "
          f"改善 {avg_base - avg_model:>+5.2f}°C")

    if avg_model >= avg_base:
        print("\n  ⚠ 模型没有跑赢「明天=今天」这个朴素基线。")
        print("    这意味着它没学到东西 —— 别急着调参数，先检查特征。")

    # 逐条对比
    print(f"\n  验证集前 10 天:")
    print(f"  {'实际高':>7} {'预测高':>7} {'基线高':>7}  │  "
          f"{'实际低':>7} {'预测低':>7} {'基线低':>7}")
    print(f"  {'─' * 30}┼{'─' * 30}")
    for i in range(min(10, len(y_val))):
        print(f"  {y_val[i,0]:>7.1f} {y_pred[i,0]:>7.1f} {X_val[i,0]:>7.1f}  │  "
              f"{y_val[i,1]:>7.1f} {y_pred[i,1]:>7.1f} {X_val[i,1]:>7.1f}")

    return {
        "mae_high": model_high,
        "mae_low": model_low,
        "baseline_high": base["high"],
        "baseline_low": base["low"],
    }


def save_model(model, path: str = MODEL_PATH) -> None:
    """保存模型。"""
    joblib.dump(model, path)
    print(f"\n  ✓ 模型已保存: {path} ({os.path.getsize(path) / 1024:.1f} KB)")


def load_model(path: str = MODEL_PATH):
    """加载模型。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"模型文件不存在: {path}，请先运行训练")
    return joblib.load(path)


def get_model(X_train, y_train, X_val, y_val, feature_names=None):
    """训练 → 评估 → 保存。"""
    model = build_and_train(X_train, y_train, feature_names=feature_names)
    metrics = evaluate_model(model, X_val, y_val)
    save_model(model)
    return model, metrics


if __name__ == "__main__":
    print("请通过 Main.py 运行完整流程")


def train_horizon_models(df_feat, feature_cols, max_h: int = 7, test_size: float = 0.2):
    """
    直接多步预测：为每个步长单独训一个模型。

    和递归预测的区别
        递归：训一个 h=1 的模型，预测明天后把结果喂回去猜后天 —— 会收敛成常数。
        直接：训 7 个模型，每个直接学「今天 → h 天后」，互不干扰。

    这个表本身就是个好结果：**误差随步长怎么增长，一眼能看出来。**
    真实预报也是这个规律 —— 越远越不准，所以远处的数字只能当趋势看。
    """
    print("=" * 58)
    print("  训练多步预测模型（每个步长一个）")
    print("=" * 58)

    dataset = build_horizon_dataset(df_feat, feature_cols, max_h=max_h)
    models = {}

    print(f"\n  {'步长':>4} {'训练':>7} {'验证':>7} "
          f"{'模型MAE':>9} {'基线MAE':>9} {'改善':>8}")
    print(f"  {'─' * 52}")

    for h in range(1, max_h + 1):
        X, y = dataset[h]
        cut = int(len(X) * (1 - test_size))
        X_tr, X_va = X[:cut], X[cut:]
        y_tr, y_va = y[:cut], y[cut:]

        m = RandomForestRegressor(
            n_estimators=200, max_depth=12, min_samples_leaf=2,
            random_state=42, n_jobs=-1,
        )
        m.fit(X_tr, y_tr)
        models[h] = m

        pred = m.predict(X_va)
        mae_model = mean_absolute_error(y_va, pred)
        # 该步长的持续性基线：拿「今天」的温度当「h 天后」的预报
        mae_base = mean_absolute_error(y_va, X_va[:, :2])
        flag = "✓" if mae_model < mae_base else "✗"

        print(f"  {h:>3}天 {len(X_tr):>7} {len(X_va):>7} "
              f"{mae_model:>8.2f}°C {mae_base:>8.2f}°C "
              f"{mae_base - mae_model:>+7.2f} {flag}")

    print(f"\n  ✓ 共训练 {len(models)} 个模型")
    return models
