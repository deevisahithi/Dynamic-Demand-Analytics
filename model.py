import os
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "data/train.csv"
MODEL_DIR = "model_output"

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\nLoading sales data...")

df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully!")
print("Rows:", len(df))
print("Columns:", list(df.columns))


# ============================================================
# 2. DATA PREPARATION
# ============================================================

print("\nPreparing data...")

df["date"] = pd.to_datetime(df["date"])

# Sort is extremely important for lag features
df = df.sort_values(
    ["store_nbr", "family", "date"]
).reset_index(drop=True)


# ============================================================
# 3. FEATURE ENGINEERING
# ============================================================

print("Creating features...")


# Calendar features
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day
df["day_of_week"] = df["date"].dt.dayofweek
df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)


# ------------------------------------------------------------
# Previous demand
# ------------------------------------------------------------

# Previous day demand
df["lag_1"] = df.groupby(
    ["store_nbr", "family"]
)["sales"].shift(1)


# Previous week demand
df["lag_7"] = df.groupby(
    ["store_nbr", "family"]
)["sales"].shift(7)


# Previous 14 days demand
df["lag_14"] = df.groupby(
    ["store_nbr", "family"]
)["sales"].shift(14)


# ------------------------------------------------------------
# Rolling averages
# ------------------------------------------------------------

# 7-day average based on previous observations
df["rolling_7"] = df.groupby(
    ["store_nbr", "family"]
)["sales"].transform(
    lambda x: x.shift(1).rolling(7).mean()
)


# 14-day average
df["rolling_14"] = df.groupby(
    ["store_nbr", "family"]
)["sales"].transform(
    lambda x: x.shift(1).rolling(14).mean()
)


# ------------------------------------------------------------
# Promotion feature
# ------------------------------------------------------------

df["onpromotion"] = df["onpromotion"].fillna(0)


# ============================================================
# 4. ENCODE PRODUCT FAMILY
# ============================================================

print("Encoding product families...")

# Convert product family to numerical values
family_codes = {
    family: index
    for index, family in enumerate(
        sorted(df["family"].unique())
    )
}

df["family_code"] = df["family"].map(family_codes)


# ============================================================
# 5. REMOVE ROWS WITH MISSING LAG VALUES
# ============================================================

df = df.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "lag_14",
        "rolling_7",
        "rolling_14"
    ]
).reset_index(drop=True)


print("Rows after feature engineering:", len(df))


# ============================================================
# 6. SELECT FEATURES
# ============================================================

features = [
    "store_nbr",
    "family_code",
    "onpromotion",
    "year",
    "month",
    "day",
    "day_of_week",
    "week_of_year",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_7",
    "rolling_14"
]

target = "sales"


X = df[features]
y = df[target]


# ============================================================
# 7. TIME-BASED TRAIN / TEST SPLIT
# ============================================================

print("\nCreating time-based train/test split...")

# We do NOT randomly split time-series data.
# The latest 30 days are used for testing.

max_date = df["date"].max()

test_start_date = max_date - pd.Timedelta(days=30)

train_data = df[
    df["date"] < test_start_date
]

test_data = df[
    df["date"] >= test_start_date
]


X_train = train_data[features]
y_train = train_data[target]

X_test = test_data[features]
y_test = test_data[target]


print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


# ============================================================
# 8. REDUCE TRAINING SIZE IF DATA IS VERY LARGE
# ============================================================

# The Store Sales dataset contains more than 3 million rows.
# Random Forest can require a lot of RAM.
#
# We use a maximum of 250,000 training rows.

MAX_TRAIN_ROWS = 250000

if len(X_train) > MAX_TRAIN_ROWS:

    print(
        f"\nLarge dataset detected."
        f"\nUsing {MAX_TRAIN_ROWS:,} training rows."
    )

    sample_indices = np.random.RandomState(
        42
    ).choice(
        len(X_train),
        size=MAX_TRAIN_ROWS,
        replace=False
    )

    X_train = X_train.iloc[sample_indices]
    y_train = y_train.iloc[sample_indices]


# ============================================================
# 9. BUILD RANDOM FOREST MODEL
# ============================================================

print("\nBuilding Random Forest Regression model...")

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)


# ============================================================
# 10. TRAIN MODEL
# ============================================================

print("Training model...")

model.fit(
    X_train,
    y_train
)

print("Model training completed!")


# ============================================================
# 11. MAKE PREDICTIONS
# ============================================================

print("\nGenerating predictions...")

predictions = model.predict(X_test)


# ============================================================
# 12. MODEL EVALUATION
# ============================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

r2 = r2_score(
    y_test,
    predictions
)


print("\n======================================")
print("MODEL PERFORMANCE")
print("======================================")

print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")

print("======================================")


# ============================================================
# 13. SAVE MODEL
# ============================================================

model_path = os.path.join(
    MODEL_DIR,
    "demand_model.pkl"
)

joblib.dump(
    model,
    model_path
)

print(
    f"\nModel saved to: {model_path}"
)


# ============================================================
# 14. SAVE METRICS
# ============================================================

metrics = pd.DataFrame({
    "Metric": [
        "MAE",
        "RMSE",
        "R2"
    ],
    "Value": [
        mae,
        rmse,
        r2
    ]
})

metrics_path = os.path.join(
    MODEL_DIR,
    "model_metrics.csv"
)

metrics.to_csv(
    metrics_path,
    index=False
)


# ============================================================
# 15. SAVE ACTUAL VS PREDICTED
# ============================================================

results = test_data[
    [
        "date",
        "store_nbr",
        "family",
        "sales"
    ]
].copy()

results["predicted_sales"] = predictions

results_path = os.path.join(
    MODEL_DIR,
    "predictions.csv"
)

results.to_csv(
    results_path,
    index=False
)


# ============================================================
# 16. CREATE ACTUAL VS PREDICTED GRAPH
# ============================================================

print("\nCreating Actual vs Predicted graph...")


# Aggregate daily actual and predicted demand
daily_results = results.groupby(
    "date"
).agg(
    actual_demand=("sales", "sum"),
    predicted_demand=("predicted_sales", "sum")
).reset_index()


plt.figure(
    figsize=(14, 6)
)

plt.plot(
    daily_results["date"],
    daily_results["actual_demand"],
    label="Actual Demand"
)

plt.plot(
    daily_results["date"],
    daily_results["predicted_demand"],
    label="Predicted Demand"
)

plt.xlabel("Date")
plt.ylabel("Demand")

plt.title(
    "Actual vs Predicted Retail Demand"
)

plt.legend()

plt.xticks(rotation=45)

plt.tight_layout()


graph_path = os.path.join(
    MODEL_DIR,
    "actual_vs_predicted.png"
)

plt.savefig(
    graph_path,
    dpi=150
)

plt.close()


print(
    f"Graph saved to: {graph_path}"
)


# ============================================================
# 17. FEATURE IMPORTANCE
# ============================================================

print("\nCalculating feature importance...")

importance = pd.DataFrame({
    "Feature": features,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    "Importance",
    ascending=False
)


importance_path = os.path.join(
    MODEL_DIR,
    "feature_importance.csv"
)

importance.to_csv(
    importance_path,
    index=False
)


# Create feature importance graph

plt.figure(
    figsize=(10, 6)
)

top_features = importance.head(10)

plt.barh(
    top_features["Feature"][::-1],
    top_features["Importance"][::-1]
)

plt.xlabel(
    "Importance"
)

plt.title(
    "Random Forest Feature Importance"
)

plt.tight_layout()


importance_graph_path = os.path.join(
    MODEL_DIR,
    "feature_importance.png"
)

plt.savefig(
    importance_graph_path,
    dpi=150
)

plt.close()


# ============================================================
# 18. FINAL MESSAGE
# ============================================================

print("\n======================================")
print("MODEL BUILDING COMPLETED")
print("======================================")

print("\nGenerated files:")

print("1. demand_model.pkl")
print("2. model_metrics.csv")
print("3. predictions.csv")
print("4. actual_vs_predicted.png")
print("5. feature_importance.csv")
print("6. feature_importance.png")

print("\nYour Random Forest Demand Prediction Model is ready!")