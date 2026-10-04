"""
Jal Dharma AI
Demand Prediction Model  (ratio formulation)

Model
-----
    demand(t) = demand_7day_avg(t) * ratio(t)

    ratio(t)  = Ridge regression on weather features
                (temperature, humidity, rainy flag, rainy-yesterday flag)

Why a ratio?
    Predicting the *level* with raw lag features made the model extrapolate
    badly when the weather regime changed (summer -> monsoon). Predicting the
    ratio to the 7-day average means the model only learns the weather
    adjustment; the level always comes from recent observed demand.

Deployment strategy
    * Refit on ALL available data (rolling refit), not a fixed window.
    * Prediction intervals come from out-of-sample (walk-forward) residuals
      of the ratio over the last CALIB_DAYS days.

Evaluate with:   python -m src.prediction.models
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge


# ============================================================
# CONFIGURATION
# ============================================================

TARGET = "actual_demand_l"
BASE_COL = "demand_7day_avg_l"

WEATHER_FEATURES = ["temperature_c", "humidity", "rainy", "rainy_yday"]
# Try ["rainy", "rainy_yday"] to drop the (collinear-with-season)
# temperature/humidity features and compare.

RAIN_THRESHOLD_MM = 5.0
RIDGE_ALPHA = 1.0
INTERVAL_LEVEL = 0.90      # 90% prediction interval
CALIB_DAYS = 21            # days of walk-forward residuals used for intervals
MIN_TRAIN_DAYS = 14

# Legacy feature list (kept so validation.py / baseline_check.py still run)
FEATURES = [
    "population",
    "temperature_c",
    "rainfall_mm",
    "humidity",
    "previous_day_demand_l",
    "demand_7day_avg_l",
    "demand_30day_avg_l",
]


# ============================================================
# DATA
# ============================================================

def load_dataset(file_path):
    """Load the historical demand CSV, sorted by village and date."""
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)
    return df.sort_values(["village_id", "date"]).reset_index(drop=True)


def add_features(df):
    """Add rain_yday and the ratio target. Safe to call more than once."""
    df = df.sort_values(["village_id", "date"]).copy()
    df["rain_yday"] = (
        df.groupby("village_id")["rainfall_mm"].shift(1).fillna(0.0)
    )
    df["ratio"] = df[TARGET] / df[BASE_COL]
    return df


def _feature_frame(temperature_c, humidity, rainfall_mm, rainfall_yesterday_mm):
    """Single place where model inputs are built (train and predict)."""
    rain = np.asarray(rainfall_mm, dtype=float)
    rain_y = np.asarray(rainfall_yesterday_mm, dtype=float)
    temp = np.asarray(temperature_c, dtype=float)
    hum = np.asarray(humidity, dtype=float)

    n = max(rain.size, rain_y.size, temp.size, hum.size)
    return pd.DataFrame({
        "temperature_c": np.broadcast_to(temp, (n,)),
        "humidity": np.broadcast_to(hum, (n,)),
        "rainy": (np.broadcast_to(rain, (n,)) > RAIN_THRESHOLD_MM).astype(int),
        "rainy_yday": (np.broadcast_to(rain_y, (n,)) > RAIN_THRESHOLD_MM).astype(int),
    })[WEATHER_FEATURES]


# ============================================================
# FIT / PREDICT
# ============================================================

def fit_ratio_model(train_df, calib_residuals=None, level=INTERVAL_LEVEL):
    """
    Fit the ratio model on train_df (must contain add_features columns).

    calib_residuals : optional array of out-of-sample ratio residuals
        (actual_ratio - predicted_ratio). If None, in-sample residuals
        are used, which makes intervals slightly too narrow.
    """
    train = train_df.dropna(subset=["ratio"])

    X = _feature_frame(
        train["temperature_c"], train["humidity"],
        train["rainfall_mm"], train["rain_yday"],
    )
    mu = X.mean()
    sd = X.std().replace(0, 1).fillna(1)

    model = Ridge(alpha=RIDGE_ALPHA).fit((X - mu) / sd, train["ratio"])

    if calib_residuals is None:
        calib_residuals = train["ratio"].values - model.predict((X - mu) / sd)
        residual_source = "in-sample"
    else:
        residual_source = "walk-forward"

    tail = (1 - level) / 2
    return {
        "model": model,
        "mu": mu,
        "sd": sd,
        "q_lo": float(np.quantile(calib_residuals, tail)),
        "q_hi": float(np.quantile(calib_residuals, 1 - tail)),
        "level": level,
        "residual_source": residual_source,
        "n_train": int(len(train)),
        "train_end": pd.Timestamp(train["date"].max()),
    }


def predict_demand(bundle, base_demand, temperature_c, humidity,
                   rainfall_mm, rainfall_yesterday_mm):
    """
    Vectorised prediction.

    base_demand : 7-day average demand (litres), scalar or array.
    Returns a DataFrame with columns: ratio, point, lower, upper.
    """
    base = np.atleast_1d(np.asarray(base_demand, dtype=float))
    X = _feature_frame(temperature_c, humidity, rainfall_mm, rainfall_yesterday_mm)
    if len(X) == 1 and len(base) > 1:
        X = pd.concat([X] * len(base), ignore_index=True)

    ratio = bundle["model"].predict((X - bundle["mu"]) / bundle["sd"])

    return pd.DataFrame({
        "ratio": ratio,
        "point": np.clip(ratio * base, 0, None),
        "lower": np.clip((ratio + bundle["q_lo"]) * base, 0, None),
        "upper": np.clip((ratio + bundle["q_hi"]) * base, 0, None),
    })


# ============================================================
# WALK-FORWARD EVALUATION
# ============================================================

def walk_forward(df, start, end, min_train_days=MIN_TRAIN_DAYS):
    """
    For each day in [start, end]: refit on strictly earlier data, then
    predict that day. Returns one row per village-day.
    """
    df = add_features(df)
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    dates = [d for d in pd.to_datetime(df["date"].unique()).sort_values()
             if start <= d <= end]

    out = []
    for d in dates:
        train = df[df["date"] < d]
        if train["date"].nunique() < min_train_days:
            continue
        bundle = fit_ratio_model(train)
        day = df[df["date"] == d]
        p = predict_demand(
            bundle, day[BASE_COL].values, day["temperature_c"].values,
            day["humidity"].values, day["rainfall_mm"].values,
            day["rain_yday"].values,
        )
        res = pd.DataFrame({
            "date": day["date"].values,
            "village_id": day["village_id"].values,
            "actual": day[TARGET].values,
            "base": day[BASE_COL].values,
            "rainfall_mm": day["rainfall_mm"].values,
        })
        out.append(pd.concat([res.reset_index(drop=True), p], axis=1))

    if not out:
        raise ValueError("Not enough history for walk-forward evaluation.")
    return pd.concat(out, ignore_index=True)


# ============================================================
# FINAL (DEPLOYMENT) MODEL
# ============================================================

def train_final_model(df, calib_days=CALIB_DAYS):
    """
    Fit on ALL data. Interval residuals are out-of-sample, taken from a
    walk-forward run over the last `calib_days` days (falls back to
    in-sample residuals if the history is too short).
    """
    df = add_features(df)
    dates = pd.to_datetime(df["date"].unique()).sort_values()

    resid = None
    if len(dates) >= calib_days + MIN_TRAIN_DAYS:
        wf = walk_forward(df, dates[-calib_days], dates[-1])
        resid = (wf["actual"] / wf["base"] - wf["ratio"]).values

    bundle = fit_ratio_model(df, calib_residuals=resid)

    print("\n===================================")
    print("FINAL DEMAND MODEL (ratio / Ridge)")
    print("===================================")
    print("Training records :", bundle["n_train"])
    print("Trained through  :", bundle["train_end"].date())
    print("Features         :", WEATHER_FEATURES)
    print(f"Interval         : {int(bundle['level'] * 100)}% "
          f"({bundle['residual_source']} residuals)")
    print(f"Ratio band       : [{bundle['q_lo']:+.3f}, {bundle['q_hi']:+.3f}]")
    return bundle


# ============================================================
# LEGACY HELPERS (used by validation.py and baseline_check.py)
# ============================================================

def prepare_training_data(df):
    train_df = df[(df["date"] >= "2025-04-01") &
                  (df["date"] <= "2025-05-15")].copy()
    return train_df, train_df[FEATURES], train_df[TARGET]


def calculate_scaling_parameters(X_train):
    mean, std = X_train.mean(), X_train.std()
    std[std == 0] = 1
    return mean, std


def scale_features(X, train_mean, train_std):
    return (X - train_mean) / train_std


# ============================================================
# EVALUATION REPORT
# ============================================================

def _mape(a, p):
    a, p = np.asarray(a, float), np.asarray(p, float)
    return float(np.mean(np.abs((a - p) / a)) * 100)


if __name__ == "__main__":
    PATH = "data/synthetic/2_historical_water_demand_dataset.csv"
    START, END = "2025-06-01", "2025-06-29"

    df = load_dataset(PATH)
    wf = walk_forward(df, START, END)

    y = wf["actual"]
    first_week = wf["date"] < (pd.Timestamp(START) + pd.Timedelta(days=7))
    rainy = wf["rainfall_mm"] > RAIN_THRESHOLD_MM
    covered = (y >= wf["lower"]) & (y <= wf["upper"])

    print("\n=========== WALK-FORWARD EVALUATION ===========")
    print(f"Period: {START} to {END}   rows: {len(wf)}")
    print(f"7-day avg baseline MAPE : {_mape(y, wf['base']):.2f}%")
    print(f"Ratio model MAPE        : {_mape(y, wf['point']):.2f}%")
    print(f"  first week of June    : {_mape(y[first_week], wf['point'][first_week]):.2f}%"
          f"   (baseline {_mape(y[first_week], wf['base'][first_week]):.2f}%)")
    print(f"  rest of June          : {_mape(y[~first_week], wf['point'][~first_week]):.2f}%"
          f"   (baseline {_mape(y[~first_week], wf['base'][~first_week]):.2f}%)")
    print(f"  rainy days            : {_mape(y[rainy], wf['point'][rainy]):.2f}%")
    print(f"  dry days              : {_mape(y[~rainy], wf['point'][~rainy]):.2f}%")
    print(f"Interval coverage       : {covered.mean() * 100:.1f}%  "
          f"(target {int(INTERVAL_LEVEL * 100)}%)")