"""
================================================================================
  Train & Save the Electricity Bill Prediction Model
================================================================================
  This script:
    1. Loads the Excel dataset
    2. Cleans & preprocesses the data
    3. Trains a Linear Regression model
    4. Evaluates performance (MSE, RMSE, R²)
    5. Saves the trained model to 'model.pkl' for the web app

  Author : SAI RAJU ANDEY
  Date   : 2026-04-24
================================================================================
"""

import sys
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# ── Configuration ─────────────────────────────────────────────────────────────
EXCEL_FILE = "Household_Electricity_Dataset.xlsx"
MODEL_FILE = "model.pkl"

# ── Step 1: Load ──────────────────────────────────────────────────────────────
print("=" * 65)
print("  STEP 1 : Loading the dataset")
print("=" * 65)

try:
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    print(f"  [OK] Loaded '{EXCEL_FILE}' -- {df.shape[0]} rows x {df.shape[1]} columns\n")
except FileNotFoundError:
    print(f"  [ERROR] File '{EXCEL_FILE}' not found.")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Could not read the file: {e}")
    sys.exit(1)

# ── Step 2: Clean ─────────────────────────────────────────────────────────────
print("=" * 65)
print("  STEP 2 : Cleaning the data")
print("=" * 65)

df.columns = df.columns.str.strip().str.lower()
print(f"  [OK] Columns: {list(df.columns)}")

# Identify target
TARGET = None
for col in df.columns:
    if "amount" in col or "bill" in col or "paid" in col:
        TARGET = col
        break

if TARGET is None:
    print("  [ERROR] Could not find a target column (bill/amount_paid).")
    print(f"      Available columns: {list(df.columns)}")
    sys.exit(1)

print(f"  [OK] Target column: '{TARGET}'")

# Force numeric conversion on target
df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
df.dropna(subset=[TARGET], inplace=True)

# Convert other columns to numeric where possible
for col in df.columns:
    if col == TARGET:
        continue
    converted = pd.to_numeric(df[col], errors="coerce")
    if converted.notna().sum() >= 0.5 * len(df):
        df[col] = converted

# Fill missing values
for col in df.columns:
    if df[col].dtype in ("float64", "int64"):
        df[col].fillna(df[col].median(), inplace=True)

df.dropna(inplace=True)
print(f"  [OK] Final dataset: {len(df)} rows x {len(df.columns)} columns\n")

# ── Step 3: Features & Target ─────────────────────────────────────────────────
FEATURES = [c for c in df.columns if c != TARGET]
X = df[FEATURES]
y = df[TARGET]

print("=" * 65)
print("  STEP 3 : Features & Target")
print("=" * 65)
print(f"  Features: {FEATURES}")
print(f"  Target  : {TARGET}")
print(f"  X shape : {X.shape}")
print(f"  y shape : {y.shape}\n")

# ── Step 4: Train / Test Split ────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
print(f"  Training samples: {X_train.shape[0]}")
print(f"  Testing  samples: {X_test.shape[0]}\n")

# ── Step 5: Train ─────────────────────────────────────────────────────────────
print("=" * 65)
print("  STEP 5 : Training Linear Regression")
print("=" * 65)

model = LinearRegression()
model.fit(X_train, y_train)
print("  [OK] Model trained!\n")

# ── Step 6: Evaluate ──────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
mse  = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2   = r2_score(y_test, y_pred)

print("=" * 65)
print("  STEP 6 : Evaluation Metrics")
print("=" * 65)
print(f"  MSE  : {mse:.4f}")
print(f"  RMSE : {rmse:.4f}")
print(f"  R²   : {r2:.4f}\n")

# ── Step 7: Prepare Chart Data ────────────────────────────────────────────────
print("=" * 65)
print("  STEP 7 : Preparing chart data")
print("=" * 65)

# 7a — Actual vs Predicted (for scatter plot)
actual_vs_pred = {
    "actual": [round(float(v), 2) for v in y_test.values],
    "predicted": [round(float(v), 2) for v in y_pred],
}

# 7b — Errors (for histogram)
errors = y_test.values - y_pred
error_list = [round(float(e), 2) for e in errors]

# 7c — Feature Importance (coefficients)
coefficients = {
    "features": FEATURES,
    "values": [round(float(c), 4) for c in model.coef_],
    "abs_values": [round(abs(float(c)), 4) for c in model.coef_],
    "intercept": round(float(model.intercept_), 4),
}

# 7d — Correlation matrix
corr_matrix = df[FEATURES + [TARGET]].corr()
correlation_data = {
    "labels": list(corr_matrix.columns),
    "matrix": [[round(float(v), 3) for v in row] for row in corr_matrix.values],
}

# 7e — Feature distributions (for box plots / violin)
feature_distributions = {}
for col in FEATURES:
    vals = df[col].dropna().tolist()
    q1 = float(np.percentile(vals, 25))
    q3 = float(np.percentile(vals, 75))
    feature_distributions[col] = {
        "min": float(np.min(vals)),
        "q1": round(q1, 2),
        "median": round(float(np.median(vals)), 2),
        "q3": round(q3, 2),
        "max": float(np.max(vals)),
        "mean": round(float(np.mean(vals)), 2),
        "std": round(float(np.std(vals)), 2),
        # Sampled values for scatter jitter (limit to 200 for performance)
        "samples": [round(float(v), 2) for v in np.random.choice(vals, min(200, len(vals)), replace=False)],
    }

# 7f — Target distribution
target_vals = df[TARGET].tolist()
target_distribution = {
    "values": [round(float(v), 2) for v in np.random.choice(target_vals, min(300, len(target_vals)), replace=False)],
    "min": round(float(np.min(target_vals)), 2),
    "max": round(float(np.max(target_vals)), 2),
    "mean": round(float(np.mean(target_vals)), 2),
    "median": round(float(np.median(target_vals)), 2),
}

# 7g — Residuals vs Predicted (for residual plot)
residuals_vs_pred = {
    "predicted": [round(float(v), 2) for v in y_pred],
    "residuals": error_list,
}

print(f"  [OK] Chart data prepared for {len(FEATURES)} features\n")

# ── Step 8: Save Model ────────────────────────────────────────────────────────
model_data = {
    "model": model,
    "features": FEATURES,
    "target": TARGET,
    "metrics": {"mse": mse, "rmse": rmse, "r2": r2},
    "feature_stats": {
        col: {
            "min": float(X[col].min()),
            "max": float(X[col].max()),
            "mean": float(X[col].mean()),
            "median": float(X[col].median()),
        }
        for col in FEATURES
    },
    # Chart data
    "charts": {
        "actual_vs_predicted": actual_vs_pred,
        "errors": error_list,
        "coefficients": coefficients,
        "correlation": correlation_data,
        "feature_distributions": feature_distributions,
        "target_distribution": target_distribution,
        "residuals_vs_predicted": residuals_vs_pred,
    },
}

joblib.dump(model_data, MODEL_FILE)
print(f"  [OK] Model + chart data saved -> {MODEL_FILE}")
print("=" * 65)
print("  All done! Now run 'py app.py' to start the web app.")
print("=" * 65)
