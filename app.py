from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
import os
import urllib.request

app = Flask(__name__)


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# DATA FILES
# =========================================================

DATA_FILE = os.path.join(
    BASE_DIR,
    "Data",
    "train.csv"
)

DATASET_URL = "https://github.com/deevisahithi/Dynamic-Demand-Analytics/releases/download/v1.0.0/train.csv"

if not os.path.exists(DATA_FILE):
    print("train.csv not found. Downloading dataset...")
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    urllib.request.urlretrieve(
        DATASET_URL,
        DATA_FILE
    )

    print("train.csv downloaded successfully.")

HOLIDAY_FILE = os.path.join(
    BASE_DIR,
    "Data",
    "holidays_events.csv"
)

MODEL_OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "model_output"
)


# =========================================================
# LOAD DATA ONCE
# =========================================================

print("Loading dataset...")

df = pd.read_csv(
    DATA_FILE,
    usecols=[
        "id",
        "date",
        "store_nbr",
        "family",
        "sales",
        "onpromotion"
    ],
    dtype={
        "id": "int32",
        "store_nbr": "int16",
        "family": "category",
        "sales": "float32",
        "onpromotion": "int16"
    },
    parse_dates=["date"]
)

df["year"] = df["date"].dt.year.astype("int16")

df["month"] = df["date"].dt.month.astype("int8")

df["month_name"] = (
    df["date"]
    .dt.strftime("%b")
    .astype("category")
)

df["day_name"] = (
    df["date"]
    .dt.day_name()
    .astype("category")
)


# =========================================================
# LOAD HOLIDAY DATA
# =========================================================

holiday_df = pd.read_csv(
    HOLIDAY_FILE
)

holiday_df["date"] = pd.to_datetime(
    holiday_df["date"],
    errors="coerce"
)


print("Dataset loaded successfully")

print(
    "Rows:",
    len(df)
)

print(
    "Date range:",
    df["date"].min(),
    "to",
    df["date"].max()
)


# =========================================================
# FILTER FUNCTION
# =========================================================

def filtered_data():

    data = df

    store = request.args.get(
        "store",
        "all"
    )

    family = request.args.get(
        "family",
        "all"
    )

    promotion = request.args.get(
        "promotion",
        "all"
    )

    start = request.args.get(
        "start",
        ""
    )

    end = request.args.get(
        "end",
        ""
    )


    if store != "all":

        data = data[
            data["store_nbr"] == int(store)
        ]


    if family != "all":

        data = data[
            data["family"] == family
        ]


    if promotion == "yes":

        data = data[
            data["onpromotion"] > 0
        ]

    elif promotion == "no":

        data = data[
            data["onpromotion"] == 0
        ]


    if start:

        data = data[
            data["date"] >= pd.to_datetime(start)
        ]


    if end:

        data = data[
            data["date"] <= pd.to_datetime(end)
        ]


    return data


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# FILTERS
# =========================================================

@app.route("/api/filters")
def filters():

    return jsonify({

        "stores":
            sorted(
                df["store_nbr"]
                .unique()
                .tolist()
            ),

        "families":
            sorted(
                df["family"]
                .unique()
                .tolist()
            ),

        "min_date":
            df["date"]
            .min()
            .strftime("%Y-%m-%d"),

        "max_date":
            df["date"]
            .max()
            .strftime("%Y-%m-%d")
    })


# =========================================================
# SUMMARY
# =========================================================

@app.route("/api/summary")
def summary():

    data = filtered_data()


    return jsonify({

        "total":
            float(
                data["sales"].sum()
            ),

        "average":
            float(
                data["sales"].mean()
            ),

        "peak":
            float(
                data["sales"].max()
            ),

        "stores":
            int(
                data["store_nbr"].nunique()
            )
    })


# =========================================================
# DAILY DEMAND
# =========================================================

@app.route("/api/daily")
def daily():

    data = filtered_data()


    result = (
        data.groupby("date")["sales"]
        .sum()
        .reset_index()
        .sort_values("date")
    )


    result["average"] = (
        result["sales"]
        .rolling(
            7,
            min_periods=1
        )
        .mean()
    )


    return jsonify({

        "dates":
            result["date"]
            .dt.strftime("%Y-%m-%d")
            .tolist(),

        "sales":
            result["sales"]
            .round(2)
            .tolist(),

        "average":
            result["average"]
            .round(2)
            .tolist()
    })


# =========================================================
# PRODUCT FAMILY
# =========================================================

@app.route("/api/products")
def products():

    data = filtered_data()


    result = (
        data.groupby("family")["sales"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
        .sort_values()
    )


    return jsonify({

        "families":
            result.index.tolist(),

        "sales":
            result.values
            .round(2)
            .tolist()
    })


# =========================================================
# MONTHLY DEMAND
# =========================================================

@app.route("/api/monthly")
def monthly():

    data = filtered_data()


    result = (
        data.groupby(
            data["date"]
            .dt.to_period("M")
        )["sales"]
        .sum()
        .reset_index()
    )


    result["date"] = (
        result["date"]
        .astype(str)
    )


    return jsonify({

        "months":
            result["date"].tolist(),

        "sales":
            result["sales"]
            .round(2)
            .tolist()
    })


# =========================================================
# YEARLY DEMAND
# =========================================================

@app.route("/api/yearly")
def yearly():

    data = filtered_data()


    result = (
        data.groupby("year")["sales"]
        .sum()
        .reset_index()
    )


    return jsonify({

        "years":
            result["year"]
            .astype(str)
            .tolist(),

        "sales":
            result["sales"]
            .round(2)
            .tolist()
    })


# =========================================================
# STORE DEMAND
# =========================================================

@app.route("/api/stores")
def stores():

    data = filtered_data()


    result = (
        data.groupby("store_nbr")["sales"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(10)
        .sort_values()
    )


    return jsonify({

        "stores":
            result.index
            .astype(str)
            .tolist(),

        "sales":
            result.values
            .round(2)
            .tolist()
    })


# =========================================================
# WEEKDAY DEMAND
# =========================================================

@app.route("/api/weekdays")
def weekdays():

    data = filtered_data()


    order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]


    # First aggregate total demand by date.
    # This avoids giving more weight to days simply
    # because the dataset contains many product rows.

    daily_data = (
        data.groupby(
            ["date", "day_name"]
        )["sales"]
        .sum()
        .reset_index()
    )


    result = (
        daily_data.groupby(
            "day_name"
        )["sales"]
        .mean()
        .reindex(order)
    )


    return jsonify({

        "days":
            result.index.tolist(),

        "sales":
            result.fillna(0)
            .round(2)
            .tolist()
    })


# =========================================================
# PROMOTION
# =========================================================

@app.route("/api/promotions")
def promotions():

    data = filtered_data()


    no_promo = data.loc[
        data["onpromotion"] == 0,
        "sales"
    ].mean()


    promo = data.loc[
        data["onpromotion"] > 0,
        "sales"
    ].mean()


    return jsonify({

        "categories": [
            "No Promotion",
            "With Promotion"
        ],

        "sales": [

            round(
                float(no_promo or 0),
                2
            ),

            round(
                float(promo or 0),
                2
            )
        ]
    })


# =========================================================
# HOLIDAY
# =========================================================

@app.route("/api/holidays")
def holidays():

    data = filtered_data().copy()


    holiday_dates = set(

        holiday_df["date"]
        .dropna()
        .dt.strftime(
            "%Y-%m-%d"
        )
    )


    data["is_holiday"] = (

        data["date"]
        .dt.strftime("%Y-%m-%d")
        .isin(holiday_dates)

    )


    regular = data.loc[
        ~data["is_holiday"],
        "sales"
    ].mean()


    holiday = data.loc[
        data["is_holiday"],
        "sales"
    ].mean()


    return jsonify({

        "categories": [
            "Regular Days",
            "Holiday / Event Days"
        ],

        "sales": [

            round(
                float(regular or 0),
                2
            ),

            round(
                float(holiday or 0),
                2
            )
        ]
    })


# =========================================================
# DEMAND SPIKES
# =========================================================

@app.route("/api/spikes")
def spikes():

    data = filtered_data()


    daily_data = (
        data.groupby("date")["sales"]
        .sum()
        .reset_index()
    )


    mean = daily_data["sales"].mean()

    std = daily_data["sales"].std()


    threshold = (
        mean + (2 * std)
    )


    result = (
        daily_data[
            daily_data["sales"] > threshold
        ]
        .sort_values(
            "sales",
            ascending=False
        )
        .head(10)
        .sort_values("sales")
    )


    return jsonify({

        "dates":
            result["date"]
            .dt.strftime("%Y-%m-%d")
            .tolist(),

        "sales":
            result["sales"]
            .round(2)
            .tolist()
    })


# =========================================================
# BUSINESS INSIGHTS
# =========================================================

@app.route("/api/insights")
def insights():

    data = filtered_data()


    monthly_data = (
        data.groupby(
            data["date"]
            .dt.to_period("M")
        )["sales"]
        .sum()
    )


    product_data = (
        data.groupby("family")["sales"]
        .sum()
        .sort_values(
            ascending=False
        )
    )


    store_data = (
        data.groupby("store_nbr")["sales"]
        .sum()
        .sort_values(
            ascending=False
        )
    )


    daily_data = (
        data.groupby(
            ["date", "day_name"]
        )["sales"]
        .sum()
        .reset_index()
    )


    weekday_data = (
        daily_data.groupby(
            "day_name"
        )["sales"]
        .mean()
        .sort_values(
            ascending=False
        )
    )


    return jsonify({

        "highest_month":
            str(
                monthly_data.idxmax()
            ),

        "lowest_month":
            str(
                monthly_data.idxmin()
            ),

        "top_product":
            product_data.index[0],

        "top_store":
            int(
                store_data.index[0]
            ),

        "best_day":
            weekday_data.index[0]
    })


# =========================================================
# LEVEL 2 - MODEL RESULTS
# =========================================================

@app.route("/api/model")
def model_results():

    metrics_file = os.path.join(
        MODEL_OUTPUT_DIR,
        "model_metrics.csv"
    )

    predictions_file = os.path.join(
        MODEL_OUTPUT_DIR,
        "predictions.csv"
    )

    importance_file = os.path.join(
        MODEL_OUTPUT_DIR,
        "feature_importance.csv"
    )


    result = {

        "metrics": {},

        "predictions": [],

        "feature_importance": []

    }


    # =====================================================
    # MODEL METRICS
    # =====================================================

    if os.path.exists(metrics_file):

        metrics_df = pd.read_csv(
            metrics_file
        )


        # IMPORTANT:
        #
        # Your CSV is:
        #
        # Metric,Value
        # MAE,63.7299
        # RMSE,....
        # R2,....
        #
        # So we must read EVERY ROW.
        # We must NOT use only iloc[0].

        if (
            "Metric" in metrics_df.columns
            and
            "Value" in metrics_df.columns
        ):

            for _, row in metrics_df.iterrows():

                metric_name = str(
                    row["Metric"]
                ).strip()

                try:

                    metric_value = float(
                        row["Value"]
                    )

                except Exception:

                    continue


                # Store the metric

                result["metrics"][
                    metric_name
                ] = metric_value


                # MAE

                if metric_name.upper() == "MAE":

                    result["metrics"]["MAE"] = (
                        metric_value
                    )


                # RMSE

                elif metric_name.upper() == "RMSE":

                    result["metrics"]["RMSE"] = (
                        metric_value
                    )


                # R2

                elif metric_name.upper() in [
                    "R2",
                    "R²"
                ]:

                    result["metrics"]["R2"] = (
                        metric_value
                    )

                    result["metrics"]["R²"] = (
                        metric_value
                    )


    # =====================================================
    # ACTUAL VS PREDICTED
    # =====================================================

    if os.path.exists(predictions_file):

        predictions_df = pd.read_csv(
            predictions_file
        )


        if "date" in predictions_df.columns:

            predictions_df["date"] = pd.to_datetime(
                predictions_df["date"],
                errors="coerce"
            )


        # -----------------------------------------------
        # Detect actual sales column
        # -----------------------------------------------

        actual_column = None


        possible_actual = [
            "actual_sales",
            "actual",
            "sales",
            "y_test",
            "target"
        ]


        for column in possible_actual:

            if column in predictions_df.columns:

                actual_column = column
                break


        # -----------------------------------------------
        # Detect predicted sales column
        # -----------------------------------------------

        predicted_column = None


        possible_predicted = [
            "predicted_sales",
            "predicted",
            "prediction",
            "y_pred"
        ]


        for column in possible_predicted:

            if column in predictions_df.columns:

                predicted_column = column
                break


        # -----------------------------------------------
        # CREATE CHART DATA
        # -----------------------------------------------

        if (
            actual_column is not None
            and
            predicted_column is not None
            and
            "date" in predictions_df.columns
        ):

            chart_df = predictions_df[
                [
                    "date",
                    actual_column,
                    predicted_column
                ]
            ].copy()


            chart_df[actual_column] = pd.to_numeric(
                chart_df[actual_column],
                errors="coerce"
            )


            chart_df[predicted_column] = pd.to_numeric(
                chart_df[predicted_column],
                errors="coerce"
            )


            chart_df = chart_df.dropna()


            # The prediction file contains
            # many store/product combinations.
            #
            # Aggregate them into daily demand.

            chart_df = (
                chart_df.groupby("date")
                .agg({
                    actual_column: "sum",
                    predicted_column: "sum"
                })
                .reset_index()
                .sort_values("date")
            )


            # Keep latest 90 days

            chart_df = chart_df.tail(90)


            result["predictions"] = [

                {
                    "date":
                        row["date"].strftime(
                            "%Y-%m-%d"
                        ),

                    "actual_sales":
                        round(
                            float(
                                row[actual_column]
                            ),
                            2
                        ),

                    "predicted_sales":
                        round(
                            float(
                                row[predicted_column]
                            ),
                            2
                        )
                }

                for _, row
                in chart_df.iterrows()
            ]


    # =====================================================
    # FEATURE IMPORTANCE
    # =====================================================

    if os.path.exists(importance_file):

        importance_df = pd.read_csv(
            importance_file
        )


        if not importance_df.empty:

            # Detect feature column

            feature_column = None


            for column in importance_df.columns:

                if (
                    "feature"
                    in column.lower()
                ):

                    feature_column = column
                    break


            # Detect importance column

            importance_column = None


            for column in importance_df.columns:

                if (
                    "importance"
                    in column.lower()
                ):

                    importance_column = column
                    break


            # Fallback for two-column CSV

            if (
                feature_column is None
                and
                len(importance_df.columns) >= 2
            ):

                feature_column = (
                    importance_df.columns[0]
                )


            if (
                importance_column is None
                and
                len(importance_df.columns) >= 2
            ):

                importance_column = (
                    importance_df.columns[1]
                )


            if (
                feature_column is not None
                and
                importance_column is not None
            ):

                importance_df[
                    importance_column
                ] = pd.to_numeric(
                    importance_df[
                        importance_column
                    ],
                    errors="coerce"
                )


                importance_df = (
                    importance_df
                    .dropna(
                        subset=[
                            importance_column
                        ]
                    )
                    .sort_values(
                        importance_column,
                        ascending=False
                    )
                    .head(10)
                )


                result[
                    "feature_importance"
                ] = [

                    {

                        "feature":
                            str(
                                row[
                                    feature_column
                                ]
                            ),

                        "importance":
                            round(
                                float(
                                    row[
                                        importance_column
                                    ]
                                ),
                                6
                            )

                    }

                    for _, row
                    in importance_df.iterrows()
                ]


    return jsonify(result)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )