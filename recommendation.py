import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_PATH = "data/train.csv"
PREDICTION_PATH = "model_output/predictions.csv"

OUTPUT_DIR = "model_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\n======================================")
print("LEVEL 3 - RECOMMENDATION ENGINE")
print("======================================")

print("\nLoading historical sales data...")

train = pd.read_csv(TRAIN_PATH)

train["date"] = pd.to_datetime(train["date"])

print("Historical data loaded.")
print("Rows:", len(train))


print("\nLoading model predictions...")

predictions = pd.read_csv(PREDICTION_PATH)

predictions["date"] = pd.to_datetime(
    predictions["date"]
)

print("Predictions loaded.")
print("Rows:", len(predictions))


# ============================================================
# 2. CALCULATE HISTORICAL BASELINE
# ============================================================

print("\nCalculating historical demand baseline...")

historical_average = (
    train
    .groupby(["store_nbr", "family"])["sales"]
    .mean()
    .reset_index()
)

historical_average = historical_average.rename(
    columns={
        "sales": "historical_avg_demand"
    }
)


# ============================================================
# 3. MERGE HISTORICAL BASELINE WITH PREDICTIONS
# ============================================================

print("Combining predicted and historical demand...")

recommendations = predictions.merge(
    historical_average,
    on=["store_nbr", "family"],
    how="left"
)


# ============================================================
# 4. CALCULATE DEMAND CHANGE
# ============================================================

recommendations["demand_ratio"] = (
    recommendations["predicted_sales"]
    / recommendations["historical_avg_demand"]
)


recommendations["demand_change_percent"] = (
    (recommendations["predicted_sales"]
     - recommendations["historical_avg_demand"])
    / recommendations["historical_avg_demand"]
) * 100


# ============================================================
# 5. CREATE RECOMMENDATION RULES
# ============================================================

def generate_recommendation(row):

    ratio = row["demand_ratio"]

    if pd.isna(ratio):
        return "Insufficient historical data"

    elif ratio >= 1.25:
        return "Increase inventory attention"

    elif ratio >= 1.10:
        return "Maintain higher stock level"

    elif ratio >= 0.90:
        return "Maintain regular stock"

    elif ratio >= 0.75:
        return "Avoid excess inventory"

    else:
        return "Review / reduce inventory allocation"


recommendations["recommendation"] = (
    recommendations.apply(
        generate_recommendation,
        axis=1
    )
)


# ============================================================
# 6. ADD DEMAND STATUS
# ============================================================

def demand_status(row):

    ratio = row["demand_ratio"]

    if pd.isna(ratio):
        return "Unknown"

    elif ratio >= 1.25:
        return "Very High"

    elif ratio >= 1.10:
        return "High"

    elif ratio >= 0.90:
        return "Normal"

    elif ratio >= 0.75:
        return "Low"

    else:
        return "Very Low"


recommendations["demand_status"] = (
    recommendations.apply(
        demand_status,
        axis=1
    )
)


# ============================================================
# 7. CREATE PRIORITY
# ============================================================

def priority_level(status):

    if status == "Very High":
        return "HIGH PRIORITY"

    elif status == "High":
        return "MEDIUM PRIORITY"

    elif status == "Normal":
        return "NORMAL"

    elif status == "Low":
        return "LOW PRIORITY"

    elif status == "Very Low":
        return "LOW PRIORITY"

    return "REVIEW"


recommendations["priority"] = (
    recommendations["demand_status"]
    .apply(priority_level)
)


# ============================================================
# 8. SELECT OUTPUT COLUMNS
# ============================================================

final_recommendations = recommendations[
    [
        "date",
        "store_nbr",
        "family",
        "sales",
        "predicted_sales",
        "historical_avg_demand",
        "demand_change_percent",
        "demand_status",
        "priority",
        "recommendation"
    ]
].copy()


# ============================================================
# 9. ROUND NUMBERS
# ============================================================

final_recommendations[
    "predicted_sales"
] = final_recommendations[
    "predicted_sales"
].round(2)


final_recommendations[
    "historical_avg_demand"
] = final_recommendations[
    "historical_avg_demand"
].round(2)


final_recommendations[
    "demand_change_percent"
] = final_recommendations[
    "demand_change_percent"
].round(2)


# ============================================================
# 10. SAVE ALL RECOMMENDATIONS
# ============================================================

output_path = os.path.join(
    OUTPUT_DIR,
    "demand_recommendations.csv"
)

final_recommendations.to_csv(
    output_path,
    index=False
)

print(
    f"\nRecommendations saved to:"
    f"\n{output_path}"
)


# ============================================================
# 11. SHOW TOP HIGH-DEMAND RECOMMENDATIONS
# ============================================================

print("\n======================================")
print("TOP HIGH-DEMAND RECOMMENDATIONS")
print("======================================")

high_demand = final_recommendations[
    final_recommendations["demand_status"]
    == "Very High"
].sort_values(
    "predicted_sales",
    ascending=False
)


if len(high_demand) > 0:

    print(
        high_demand[
            [
                "date",
                "store_nbr",
                "family",
                "predicted_sales",
                "demand_change_percent",
                "recommendation"
            ]
        ].head(10).to_string(
            index=False
        )
    )

else:

    print(
        "No very-high-demand cases found."
    )


# ============================================================
# 12. RECOMMENDATION SUMMARY
# ============================================================

print("\n======================================")
print("RECOMMENDATION SUMMARY")
print("======================================")

summary = (
    final_recommendations[
        "recommendation"
    ]
    .value_counts()
)


print(summary.to_string())


# ============================================================
# 13. PRIORITY SUMMARY
# ============================================================

print("\n======================================")
print("PRIORITY SUMMARY")
print("======================================")

priority_summary = (
    final_recommendations[
        "priority"
    ]
    .value_counts()
)


print(priority_summary.to_string())


# ============================================================
# 14. FINAL MESSAGE
# ============================================================

print("\n======================================")
print("LEVEL 3 COMPLETED")
print("======================================")

print(
    "\nThe system has converted predicted demand"
    " into actionable inventory-planning recommendations."
)

print(
    "\nOutput file:"
    "\nmodel_output/demand_recommendations.csv"
)