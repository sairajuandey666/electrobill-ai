"""
================================================================================
  Electricity Bill Prediction — Flask Web Application
================================================================================
  A beautiful web UI that lets you enter household data (like from an Excel
  sheet) and get a predicted electricity bill using the trained ML model.

  Also supports uploading an Excel file with multiple rows for batch prediction.

  Usage:
    1.  First train the model:   py train_model.py
    2.  Then start the web app:  py app.py
    3.  Open browser:            http://localhost:5000

  Author : SAI RAJU ANDEY
  Date   : 2026-04-24
================================================================================
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
from flask import Flask, render_template, request, jsonify

# ── Load the trained model ────────────────────────────────────────────────────
MODEL_FILE = "model.pkl"

if not os.path.exists(MODEL_FILE):
    print(f"[ERROR] '{MODEL_FILE}' not found. Run 'py train_model.py' first.")
    sys.exit(1)

model_data = joblib.load(MODEL_FILE)
model       = model_data["model"]
FEATURES    = model_data["features"]
TARGET      = model_data["target"]
METRICS     = model_data["metrics"]
FEAT_STATS  = model_data["feature_stats"]
CHARTS      = model_data.get("charts", {})

print(f"[OK] Model loaded.  Features: {FEATURES}")
print(f"[OK] Metrics -> R²: {METRICS['r2']:.4f}, RMSE: {METRICS['rmse']:.4f}")
print(f"[OK] Chart data: {list(CHARTS.keys()) if CHARTS else 'None (retrain with train_model.py)'}")

# ── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    """Render the main prediction page."""
    return render_template(
        "index.html",
        features=FEATURES,
        feature_stats=FEAT_STATS,
        metrics=METRICS,
    )


@app.route("/predict", methods=["POST"])
def predict():
    """Accept JSON input and return the predicted bill."""
    try:
        data = request.get_json()
        values = []
        for feat in FEATURES:
            val = data.get(feat)
            if val is None or val == "":
                return jsonify({"error": f"Missing value for '{feat}'"}), 400
            values.append(float(val))

        X_input = np.array(values).reshape(1, -1)
        prediction = model.predict(X_input)[0]

        return jsonify({
            "prediction": round(float(prediction), 2),
            "features_used": FEATURES,
            "input_values": values,
        })
    except ValueError as ve:
        return jsonify({"error": f"Invalid input: {ve}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict-batch", methods=["POST"])
def predict_batch():
    """Accept an uploaded Excel file and return predictions for each row."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename.endswith((".xlsx", ".xls")):
            return jsonify({"error": "Please upload an Excel file (.xlsx)"}), 400

        df = pd.read_excel(file, engine="openpyxl")
        df.columns = df.columns.str.strip().str.lower()

        # Check that all feature columns exist
        missing_cols = [f for f in FEATURES if f not in df.columns]
        if missing_cols:
            return jsonify({
                "error": f"Missing columns in file: {missing_cols}. Required: {FEATURES}"
            }), 400

        X_batch = df[FEATURES].apply(pd.to_numeric, errors="coerce")

        # Check for NaN
        if X_batch.isnull().any().any():
            nan_cols = X_batch.columns[X_batch.isnull().any()].tolist()
            return jsonify({
                "error": f"Non-numeric or missing values found in columns: {nan_cols}"
            }), 400

        predictions = model.predict(X_batch)
        df["predicted_bill"] = np.round(predictions, 2)

        # Return results as JSON
        results = []
        for i, row in df.iterrows():
            row_dict = {col: row[col] for col in FEATURES}
            row_dict["predicted_bill"] = float(row["predicted_bill"])
            results.append(row_dict)

        return jsonify({
            "predictions": results,
            "count": len(results),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/model-info")
def model_info():
    """Return model metadata."""
    return jsonify({
        "features": FEATURES,
        "target": TARGET,
        "metrics": METRICS,
        "feature_stats": FEAT_STATS,
        "coefficients": dict(zip(FEATURES, [round(c, 4) for c in model.coef_])),
        "intercept": round(float(model.intercept_), 4),
    })


@app.route("/api/charts")
def charts_api():
    """Return all pre-computed chart data for the frontend."""
    if not CHARTS:
        return jsonify({"error": "No chart data. Retrain with train_model.py"}), 404
    return jsonify(CHARTS)


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  Electricity Bill Predictor is running!")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 65 + "\n")
    app.run(debug=True, port=5000)
