"""
================================================================================
  Electricity Consumption Prediction — Linear Regression
================================================================================
  This script loads a household electricity dataset from an Excel file,
  cleans & preprocesses the data, trains a Linear Regression model,
  evaluates its performance, and visualises the results.

  Each step is explained in simple terms so a beginner can follow along.

  Author : SAI RAJU ANDEY
  Date   : 2026-04-24
================================================================================
"""

# ──────────────────────────────────────────────────────────────────────────────
# STEP 0 — Import Libraries
# ──────────────────────────────────────────────────────────────────────────────
# Python libraries we will use:
#   • pandas       – to load and manipulate tabular (spreadsheet-like) data
#   • numpy        – for fast numerical operations (math on arrays)
#   • sklearn      – a toolkit full of machine-learning algorithms & helpers
#   • matplotlib   – for drawing charts and graphs
#   • seaborn      – builds on matplotlib to make prettier statistical plots

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split   # splits data into train / test
from sklearn.linear_model import LinearRegression      # the ML model we will use
from sklearn.preprocessing import LabelEncoder         # converts text labels → numbers
from sklearn.metrics import mean_squared_error, r2_score  # evaluation metrics

# Make plots look professional with a clean white grid
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)

# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load the Dataset
# ──────────────────────────────────────────────────────────────────────────────
# We read the Excel file (.xlsx) using pandas.  The 'openpyxl' engine handles
# the .xlsx format.  If the file isn't found, we print a helpful message and
# exit so the user knows what to fix.
#
# WHY EXCEL?  In many real-world projects, data comes in Excel rather than CSV.
# pandas handles both seamlessly.

EXCEL_FILE = "Household_Electricity_Dataset.xlsx"   # ← Update this path if your file differs

print("=" * 65)
print("  STEP 1 : Loading the dataset")
print("=" * 65)

try:
    # engine="openpyxl" is needed for .xlsx files
    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
    print(f"  [OK] Loaded '{EXCEL_FILE}' -- {df.shape[0]} rows x {df.shape[1]} columns\n")
except FileNotFoundError:
    print(f"  [ERROR] File '{EXCEL_FILE}' not found.")
    print("      Place the Excel file in the same folder as this script,")
    print("      or update the EXCEL_FILE variable at the top of the code.")
    sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Could not read the file: {e}")
    sys.exit(1)

# Show the first 5 rows so we can understand the shape of the data
print("  -- Preview of the first 5 rows:")
print(df.head().to_string(index=False))
print()

# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Clean the Data
# ──────────────────────────────────────────────────────────────────────────────
# Real-world Excel files are often messy.  Common issues:
#   • Extra whitespace in column names  → "  Bill " instead of "Bill"
#   • Summary / total rows at the bottom that aren't real data
#   • Missing values (blank cells)
#   • Non-numeric entries in numeric columns
# We tackle each of these below.

print("=" * 65)
print("  STEP 2 : Cleaning the data")
print("=" * 65)

# 2a — Normalise column names
#      Strip whitespace and convert to Title Case for consistency.
df.columns = df.columns.str.strip().str.title()
print(f"  [OK] Cleaned column headers -> {list(df.columns)}\n")

# 2b — Identify the target column
#      We look for a column that contains the word "bill".
#      This makes the script resilient to slight naming variations.
TARGET = None
for col in df.columns:
    if "bill" in col.lower():
        TARGET = col
        break

if TARGET is None:
    print("  [ERROR] Could not find a target column containing 'bill'.")
    print(f"      Available columns: {list(df.columns)}")
    sys.exit(1)

print(f"  [OK] Target column identified: '{TARGET}'")

# 2c — Remove summary / non-numeric junk rows
#      Strategy: force-convert the target column to numeric.  Any row whose
#      target value can't be converted (e.g. "Total", "Average") becomes NaN,
#      and we drop it.
df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
rows_before = len(df)
df.dropna(subset=[TARGET], inplace=True)
rows_after = len(df)
dropped = rows_before - rows_after
if dropped:
    print(f"  [OK] Dropped {dropped} non-numeric / summary row(s)")
else:
    print("  [OK] No summary rows detected")

# Also try to convert other columns that should be numeric
for col in df.columns:
    if col == TARGET:
        continue
    # Attempt numeric conversion; leave as-is if it fails
    converted = pd.to_numeric(df[col], errors="coerce")
    # Only accept the conversion if the majority of values survived
    if converted.notna().sum() >= 0.5 * len(df):
        df[col] = converted

# 2d — Handle missing values
#      • Numeric columns  → fill with the MEDIAN  (robust to outliers)
#      • Categorical cols → fill with the MODE    (most frequent value)
missing_before = df.isnull().sum().sum()
print(f"\n  Missing values before imputation : {missing_before}")

for col in df.columns:
    if df[col].dtype in ("float64", "int64", "Float64", "Int64"):
        df[col].fillna(df[col].median(), inplace=True)
    else:
        mode_val = df[col].mode()
        if not mode_val.empty:
            df[col].fillna(mode_val.iloc[0], inplace=True)

missing_after = df.isnull().sum().sum()
print(f"  Missing values after  imputation : {missing_after}")

# Drop any rows that still have NaN (safety net)
df.dropna(inplace=True)
print(f"  Final dataset size: {len(df)} rows x {len(df.columns)} columns\n")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — Preprocessing (Encode Categorical Features)
# ──────────────────────────────────────────────────────────────────────────────
# Machine-learning models work only with numbers, not text.
# Columns like "Location_Type" (Urban / Rural) need to be converted to
# numbers.  We use *Label Encoding*:  Urban → 1, Rural → 0 (for example).
#
# We also store the encoders so we can decode later if needed.

print("=" * 65)
print("  STEP 3 : Preprocessing (encoding categorical features)")
print("=" * 65)

label_encoders = {}

for col in df.select_dtypes(include=["object"]).columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le
    print(f"  [OK] Encoded '{col}' -> {dict(zip(le.classes_, le.transform(le.classes_)))}")

if not label_encoders:
    print("  [INFO] No categorical columns found -- nothing to encode.")

print()

# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — Split Features & Target
# ──────────────────────────────────────────────────────────────────────────────
# X = all the input features (everything EXCEPT the bill)
# y = the target we want to predict (the bill)

print("=" * 65)
print("  STEP 4 : Splitting into features (X) and target (y)")
print("=" * 65)

X = df.drop(columns=[TARGET])
y = df[TARGET]

print(f"  Features (X) shape : {X.shape}  <- {list(X.columns)}")
print(f"  Target   (y) shape : {y.shape}\n")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Train / Test Split
# ──────────────────────────────────────────────────────────────────────────────
# We keep 80 % of the data for training and hold out 20 % for testing.
# The model will NEVER see the test data during training — this lets us
# measure how well it generalises to new, unseen data.
#
# random_state=42 ensures you get the same split every time you run the script,
# which makes results reproducible.

print("=" * 65)
print("  STEP 5 : Train / Test split (80 / 20)")
print("=" * 65)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

print(f"  Training samples : {X_train.shape[0]}")
print(f"  Testing  samples : {X_test.shape[0]}\n")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 6 — Train the Model
# ──────────────────────────────────────────────────────────────────────────────
# Linear Regression finds the best-fit line (or hyperplane in higher
# dimensions) that minimises the sum of squared differences between the
# predicted values and the actual values.
#
# Think of it like drawing the "best straight line" through a scatter plot
# so the total distance between the dots and the line is as small as possible.

print("=" * 65)
print("  STEP 6 : Training the Linear Regression model")
print("=" * 65)

model = LinearRegression()
model.fit(X_train, y_train)
print("  [OK] Model training complete!\n")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 7 — Make Predictions
# ──────────────────────────────────────────────────────────────────────────────
# We feed the test features (X_test) into the trained model and get predicted
# bill values.  Then we compare them side-by-side with the real values.

print("=" * 65)
print("  STEP 7 : Making predictions on the test set")
print("=" * 65)

y_pred = model.predict(X_test)

# Show a side-by-side comparison (first 10 rows)
comparison = pd.DataFrame({
    "Actual":    y_test.values[:10],
    "Predicted": np.round(y_pred[:10], 2),
    "Error":     np.round(y_test.values[:10] - y_pred[:10], 2),
})
print(comparison.to_string(index=False))
print()

# ──────────────────────────────────────────────────────────────────────────────
# STEP 8 — Evaluate the Model
# ──────────────────────────────────────────────────────────────────────────────
# We use three standard metrics:
#
#   MSE  (Mean Squared Error)
#       → Average of (actual − predicted)².  Lower is better.
#
#   RMSE (Root Mean Squared Error)
#       → Square root of MSE.  Same unit as the target (₹ or kWh), so it's
#         easier to interpret.  "On average, our prediction is off by ≈ RMSE."
#
#   R²   (R-Squared / Coefficient of Determination)
#       → How much of the variance in the target our model explains.
#         1.0 = perfect, 0.0 = no better than guessing the mean.

print("=" * 65)
print("  STEP 8 : Model Evaluation")
print("=" * 65)

mse  = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2   = r2_score(y_test, y_pred)

print(f"  MSE  : {mse:.4f}")
print(f"  RMSE : {rmse:.4f}")
print(f"  R2   : {r2:.4f}")

if r2 >= 0.8:
    print("  [RESULT] Great fit -- the model explains most of the variance.\n")
elif r2 >= 0.5:
    print("  [RESULT] Moderate fit -- consider adding more features or trying other models.\n")
else:
    print("  [RESULT] Weak fit -- the relationship may not be linear, or key features are missing.\n")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 9 — Model Coefficients (Weights) and Intercept
# ──────────────────────────────────────────────────────────────────────────────
# Each coefficient tells us:
#   "When this feature increases by 1 unit (holding everything else constant),
#    the predicted bill changes by <coefficient> units."
#
# The intercept is the base prediction when every feature is 0.

print("=" * 65)
print("  STEP 9 : Model Coefficients (Weights)")
print("=" * 65)

coef_df = pd.DataFrame({
    "Feature":     X.columns,
    "Coefficient": np.round(model.coef_, 4),
})
coef_df = coef_df.reindex(coef_df["Coefficient"].abs().sort_values(ascending=False).index)
print(coef_df.to_string(index=False))
print(f"\n  Intercept (bias) : {model.intercept_:.4f}")
print("  → This is the baseline bill when all feature values are 0.\n")

# ──────────────────────────────────────────────────────────────────────────────
# STEP 10 — Visualisations
# ──────────────────────────────────────────────────────────────────────────────
# Two plots:
#   (a) Actual vs Predicted scatter plot — dots near the red line = good.
#   (b) Error distribution — should be centred around 0 (bell-shaped).

print("=" * 65)
print("  STEP 10 : Generating plots ...")
print("=" * 65)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# --- 10a. Actual vs Predicted ---
ax1 = axes[0]
scatter = ax1.scatter(
    y_test, y_pred,
    alpha=0.65, edgecolors="k", linewidths=0.5, s=60,
    c=y_test, cmap="viridis"
)
# Perfect-prediction reference line
mn = min(y_test.min(), y_pred.min())
mx = max(y_test.max(), y_pred.max())
ax1.plot([mn, mx], [mn, mx], "r--", linewidth=2, label="Perfect prediction")
ax1.set_xlabel("Actual Bill", fontsize=12)
ax1.set_ylabel("Predicted Bill", fontsize=12)
ax1.set_title("Actual vs Predicted Electricity Bill", fontsize=14, fontweight="bold")
ax1.legend(fontsize=10)
plt.colorbar(scatter, ax=ax1, label="Actual Bill")

# --- 10b. Error Distribution ---
errors = y_test.values - y_pred
ax2 = axes[1]
sns.histplot(errors, kde=True, bins=25, color="steelblue", ax=ax2, edgecolor="white")
ax2.axvline(0, color="red", linestyle="--", linewidth=1.5, label="Zero error")
ax2.set_xlabel("Prediction Error (Actual - Predicted)", fontsize=12)
ax2.set_ylabel("Frequency", fontsize=12)
ax2.set_title("Error Distribution", fontsize=14, fontweight="bold")
ax2.legend(fontsize=10)

plt.tight_layout()

# Save plot to disk
plot_path = "results_plot.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"  [OK] Plot saved -> {plot_path}")
plt.show()

print("\n*** All done! Review the plots and metrics above. ***")
print("=" * 65)
