// ============================================================
// DEMANDPULSE DASHBOARD
// ============================================================


const COLORS = {

    blue: "#2563eb",

    cyan: "#06b6d4",

    green: "#10b981",

    orange: "#f59e0b",

    purple: "#6366f1",

    gray: "#94a3b8"

};


// ============================================================
// FORMAT NUMBER
// ============================================================

function formatNumber(value) {

    value = Number(value);


    if (!Number.isFinite(value)) {

        return "0";

    }


    if (value >= 1000000000) {

        return (
            value / 1000000000
        ).toFixed(2) + "B";

    }


    if (value >= 1000000) {

        return (
            value / 1000000
        ).toFixed(2) + "M";

    }


    if (value >= 1000) {

        return (
            value / 1000
        ).toFixed(1) + "K";

    }


    return value.toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 2
        }
    );
}


// ============================================================
// FILTER QUERY
// ============================================================

function queryString() {

    const params =
        new URLSearchParams();


    const start =
        document.getElementById(
            "startDate"
        ).value;


    const end =
        document.getElementById(
            "endDate"
        ).value;


    const store =
        document.getElementById(
            "store"
        ).value;


    const family =
        document.getElementById(
            "family"
        ).value;


    const promotion =
        document.getElementById(
            "promotion"
        ).value;


    if (start) {

        params.append(
            "start",
            start
        );

    }


    if (end) {

        params.append(
            "end",
            end
        );

    }


    if (store !== "all") {

        params.append(
            "store",
            store
        );

    }


    if (family !== "all") {

        params.append(
            "family",
            family
        );

    }


    if (promotion !== "all") {

        params.append(
            "promotion",
            promotion
        );

    }


    const result =
        params.toString();


    return result
        ? "?" + result
        : "";
}


// ============================================================
// API
// ============================================================

async function getAPI(url) {

    const response =
        await fetch(
            url + queryString()
        );


    if (!response.ok) {

        throw new Error(
            `API error: ${url}`
        );

    }


    return await response.json();
}


// ============================================================
// BASE LAYOUT
// ============================================================

function layout(height = 350) {

    return {

        height: height,

        margin: {

            l: 55,

            r: 20,

            t: 15,

            b: 55

        },

        paper_bgcolor:
            "transparent",

        plot_bgcolor:
            "transparent",

        font: {

            family:
                "Inter, Arial",

            color:
                "#0f172a",

            size: 10

        },

        xaxis: {

            gridcolor:
                "#eef2f7",

            zeroline:
                false,

            tickfont: {

                color:
                    "#64748b",

                size: 9

            }

        },

        yaxis: {

            gridcolor:
                "#eef2f7",

            zeroline:
                false,

            tickfont: {

                color:
                    "#64748b",

                size: 9

            }

        },

        hoverlabel: {

            bgcolor:
                "#0f172a",

            font: {

                color:
                    "white"

            }

        }

    };

}


const config = {

    responsive: true,

    displayModeBar: false

};


// ============================================================
// FILTERS
// ============================================================

async function loadFilters() {

    const data =
        await fetch(
            "/api/filters"
        )
        .then(
            response =>
                response.json()
        );


    const store =
        document.getElementById(
            "store"
        );


    data.stores.forEach(
        value => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                value;


            option.textContent =
                `Store ${value}`;


            store.appendChild(
                option
            );

        }
    );


    const family =
        document.getElementById(
            "family"
        );


    data.families.forEach(
        value => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                value;


            option.textContent =
                value;


            family.appendChild(
                option
            );

        }
    );


    document.getElementById(
        "startDate"
    ).min =
        data.min_date;


    document.getElementById(
        "startDate"
    ).max =
        data.max_date;


    document.getElementById(
        "endDate"
    ).min =
        data.min_date;


    document.getElementById(
        "endDate"
    ).max =
        data.max_date;


    document.getElementById(
        "coverageText"
    ).textContent =
        `${data.min_date.substring(0, 4)} – ${data.max_date.substring(0, 4)}`;
}


// ============================================================
// SUMMARY
// ============================================================

async function loadSummary() {

    const data =
        await getAPI(
            "/api/summary"
        );


    document.getElementById(
        "total"
    ).textContent =
        formatNumber(
            data.total
        );


    document.getElementById(
        "average"
    ).textContent =
        formatNumber(
            data.average
        );


    document.getElementById(
        "peak"
    ).textContent =
        formatNumber(
            data.peak
        );


    document.getElementById(
        "stores"
    ).textContent =
        data.stores;
}


// ============================================================
// DAILY LINE CHART
// ============================================================

async function loadDailyChart() {

    const data =
        await getAPI(
            "/api/daily"
        );


    const traces = [

        {

            x: data.dates,

            y: data.sales,

            type: "scatter",

            mode: "lines",

            name:
                "Daily Demand",

            line: {

                color:
                    COLORS.blue,

                width: 2

            },

            fill:
                "tozeroy",

            fillcolor:
                "rgba(37,99,235,0.08)"

        },


        {

            x: data.dates,

            y: data.average,

            type: "scatter",

            mode: "lines",

            name:
                "7-Day Average",

            line: {

                color:
                    COLORS.cyan,

                width: 2,

                dash:
                    "dash"

            }

        }

    ];


    const chartLayout =
        layout(430);


    chartLayout.showlegend =
        true;


    chartLayout.legend = {

        orientation:
            "h",

        x: 0,

        y: 1.08

    };


    Plotly.react(

        "dailyChart",

        traces,

        chartLayout,

        config

    );
}


// ============================================================
// PRODUCT BAR
// ============================================================

async function loadProductChart() {

    const data =
        await getAPI(
            "/api/products"
        );


    const trace = {

        x:
            data.sales,

        y:
            data.families,

        type:
            "bar",

        orientation:
            "h",

        marker: {

            color:
                COLORS.blue

        },

        hovertemplate:
            "%{y}<br>" +
            "Demand: %{x:,.0f}" +
            "<extra></extra>"

    };


    const chartLayout =
        layout(350);


    chartLayout.margin.l =
        125;


    Plotly.react(

        "productChart",

        [trace],

        chartLayout,

        config

    );
}


// ============================================================
// MONTHLY BAR
// ============================================================

async function loadMonthlyChart() {

    const data =
        await getAPI(
            "/api/monthly"
        );


    const trace = {

        x:
            data.months,

        y:
            data.sales,

        type:
            "bar",

        marker: {

            color:
                COLORS.cyan

        },

        hovertemplate:
            "%{x}<br>" +
            "Demand: %{y:,.0f}" +
            "<extra></extra>"

    };


    const chartLayout =
        layout(350);


    chartLayout.xaxis.tickangle =
        -45;


    Plotly.react(

        "monthlyChart",

        [trace],

        chartLayout,

        config

    );
}


// ============================================================
// YEARLY BAR
// ============================================================

async function loadYearlyChart() {

    const data =
        await getAPI(
            "/api/yearly"
        );


    const trace = {

        x:
            data.years,

        y:
            data.sales,

        type:
            "bar",

        marker: {

            color:
                COLORS.purple

        },

        hovertemplate:
            "Year: %{x}<br>" +
            "Demand: %{y:,.0f}" +
            "<extra></extra>"

    };


    Plotly.react(

        "yearlyChart",

        [trace],

        layout(350),

        config

    );
}


// ============================================================
// STORE BAR
// ============================================================

async function loadStoreChart() {

    const data =
        await getAPI(
            "/api/stores"
        );


    const trace = {

        x:
            data.sales,

        y:
            data.stores,

        type:
            "bar",

        orientation:
            "h",

        marker: {

            color:
                COLORS.green

        },

        hovertemplate:
            "Store %{y}<br>" +
            "Demand: %{x:,.0f}" +
            "<extra></extra>"

    };


    const chartLayout =
        layout(350);


    chartLayout.margin.l =
        75;


    Plotly.react(

        "storeChart",

        [trace],

        chartLayout,

        config

    );
}


// ============================================================
// WEEKDAY BAR
// ============================================================

async function loadWeekdayChart() {

    const data =
        await getAPI(
            "/api/weekdays"
        );


    const trace = {

        x:
            data.days,

        y:
            data.sales,

        type:
            "bar",

        marker: {

            color:
                COLORS.purple

        },

        hovertemplate:
            "%{x}<br>" +
            "Average: %{y:,.2f}" +
            "<extra></extra>"

    };


    const chartLayout =
        layout(350);


    chartLayout.xaxis.tickangle =
        -30;


    Plotly.react(

        "weekdayChart",

        [trace],

        chartLayout,

        config

    );
}


// ============================================================
// PROMOTION BAR
// ============================================================

async function loadPromotionChart() {

    const data =
        await getAPI(
            "/api/promotions"
        );


    const trace = {

        x:
            data.categories,

        y:
            data.sales,

        type:
            "bar",

        marker: {

            color: [

                COLORS.gray,

                COLORS.blue

            ]

        },

        hovertemplate:
            "%{x}<br>" +
            "Average Demand: %{y:,.2f}" +
            "<extra></extra>"

    };


    Plotly.react(

        "promotionChart",

        [trace],

        layout(350),

        config

    );
}


// ============================================================
// HOLIDAY BAR
// ============================================================

async function loadHolidayChart() {

    const data =
        await getAPI(
            "/api/holidays"
        );


    const trace = {

        x:
            data.categories,

        y:
            data.sales,

        type:
            "bar",

        marker: {

            color: [

                "#cbd5e1",

                COLORS.orange

            ]

        },

        hovertemplate:
            "%{x}<br>" +
            "Average Demand: %{y:,.2f}" +
            "<extra></extra>"

    };


    Plotly.react(

        "holidayChart",

        [trace],

        layout(350),

        config

    );
}


// ============================================================
// SPIKE BAR
// ============================================================

async function loadSpikeChart() {

    const data =
        await getAPI(
            "/api/spikes"
        );


    const trace = {

        x:
            data.sales,

        y:
            data.dates,

        type:
            "bar",

        orientation:
            "h",

        marker: {

            color:
                COLORS.orange

        },

        hovertemplate:
            "%{y}<br>" +
            "Demand: %{x:,.0f}" +
            "<extra></extra>"

    };


    const chartLayout =
        layout(350);


    chartLayout.margin.l =
        100;


    Plotly.react(

        "spikeChart",

        [trace],

        chartLayout,

        config

    );
}


// ============================================================
// BUSINESS INSIGHTS
// ============================================================

async function loadInsights() {

    const data =
        await getAPI(
            "/api/insights"
        );


    document.getElementById(
        "highestMonth"
    ).textContent =
        `Highest observed demand occurred in ${data.highest_month}.`;


    document.getElementById(
        "topProduct"
    ).textContent =
        `${data.top_product} recorded the highest total demand.`;


    document.getElementById(
        "topStore"
    ).textContent =
        `Store ${data.top_store} recorded the highest total demand.`;


    document.getElementById(
        "bestDay"
    ).textContent =
        `${data.best_day} had the highest average demand.`;
}


// ============================================================
// LEVEL 2 - MODEL RESULTS
// ============================================================

async function loadModelResults() {

    try {

        console.log(
            "Loading Level 2 model results..."
        );


        const response =
            await fetch(
                "/api/model"
            );


        if (!response.ok) {

            throw new Error(
                "Model API request failed"
            );

        }


        const data =
            await response.json();


        console.log(
            "Model results:",
            data
        );


        updateModelMetrics(
            data.metrics
        );


        drawActualVsPredicted(
            data.predictions
        );


        drawFeatureImportance(
            data.feature_importance
        );


    }

    catch (error) {

        console.error(
            "Level 2 loading failed:",
            error
        );

    }
}


// ============================================================
// MODEL METRICS
// ============================================================

function updateModelMetrics(
    metrics
) {

    const maeElement =
        document.getElementById(
            "modelMAE"
        );


    const rmseElement =
        document.getElementById(
            "modelRMSE"
        );


    const r2Element =
        document.getElementById(
            "modelR2"
        );


    if (!metrics) {

        return;

    }


    const mae =
        metrics.MAE ??
        metrics.mae ??
        metrics["Mean Absolute Error"] ??
        "-";


    const rmse =
        metrics.RMSE ??
        metrics.rmse ??
        metrics["Root Mean Squared Error"] ??
        "-";


    const r2 =
        metrics.R2 ??
        metrics.r2 ??
        metrics["R²"] ??
        metrics["R2 Score"] ??
        metrics["R-squared"] ??
        "-";


    if (maeElement) {

        maeElement.textContent =
            Number.isFinite(
                Number(mae)
            )
                ? Number(mae).toFixed(2)
                : mae;

    }


    if (rmseElement) {

        rmseElement.textContent =
            Number.isFinite(
                Number(rmse)
            )
                ? Number(rmse).toFixed(2)
                : rmse;

    }


    if (r2Element) {

        r2Element.textContent =
            Number.isFinite(
                Number(r2)
            )
                ? Number(r2).toFixed(3)
                : r2;

    }
}


// ============================================================
// ACTUAL VS PREDICTED
// ============================================================

function drawActualVsPredicted(
    predictions
) {

    const chart =
        document.getElementById(
            "actualPredictedChart"
        );


    if (!chart) {

        return;

    }


    if (
        !predictions ||
        predictions.length === 0
    ) {

        chart.innerHTML = `
            <div style="
                padding:40px;
                text-align:center;
                color:#64748b;
                font-size:13px;
            ">
                Prediction data is not available.
            </div>
        `;

        return;

    }


    const dates =
        predictions.map(
            row => row.date
        );


    const actual =
        predictions.map(
            row =>
                Number(
                    row.actual_sales ?? 0
                )
        );


    const predicted =
        predictions.map(
            row =>
                Number(
                    row.predicted_sales ?? 0
                )
        );


    const traces = [

        {

            x:
                dates,

            y:
                actual,

            type:
                "scatter",

            mode:
                "lines",

            name:
                "Actual Demand",

            line: {

                color:
                    COLORS.blue,

                width:
                    2.5

            }

        },


        {

            x:
                dates,

            y:
                predicted,

            type:
                "scatter",

            mode:
                "lines",

            name:
                "Predicted Demand",

            line: {

                color:
                    COLORS.orange,

                width:
                    2.5,

                dash:
                    "dash"

            }

        }

    ];


    const chartLayout =
        layout(430);


    chartLayout.showlegend =
        true;


    chartLayout.legend = {

        orientation:
            "h",

        x:
            0,

        y:
            1.10

    };


    chartLayout.xaxis = {

        ...chartLayout.xaxis,

        title:
            "Date",

        tickangle:
            -30

    };


    chartLayout.yaxis = {

        ...chartLayout.yaxis,

        title:
            "Demand"

    };


    Plotly.react(

        "actualPredictedChart",

        traces,

        chartLayout,

        config

    );
}


// ============================================================
// FEATURE IMPORTANCE
// ============================================================

function drawFeatureImportance(
    features
) {

    const chart =
        document.getElementById(
            "featureImportanceChart"
        );


    if (!chart) {

        return;

    }


    if (
        !features ||
        features.length === 0
    ) {

        chart.innerHTML = `
            <div style="
                padding:40px;
                text-align:center;
                color:#64748b;
                font-size:13px;
            ">
                Feature importance data is not available.
            </div>
        `;

        return;

    }


    const sorted =
        [...features].sort(
            (a, b) =>
                Number(
                    b.importance
                ) -
                Number(
                    a.importance
                )
        );


    const names =
        sorted.map(
            row => row.feature
        );


    const values =
        sorted.map(
            row =>
                Number(
                    row.importance
                )
        );


    const trace = {

        x:
            values,

        y:
            names,

        type:
            "bar",

        orientation:
            "h",

        marker: {

            color:
                COLORS.blue

        },

        text:
            values.map(
                value =>
                    value.toFixed(3)
            ),

        textposition:
            "outside",

        hovertemplate:
            "%{y}<br>" +
            "Importance: %{x:.4f}" +
            "<extra></extra>"

    };


    const chartLayout =
        layout(450);


    chartLayout.margin.l =
        130;


    chartLayout.xaxis = {

        ...chartLayout.xaxis,

        title:
            "Importance"

    };


    chartLayout.yaxis = {

        ...chartLayout.yaxis,

        title:
            "Feature",

        automargin:
            true

    };


    Plotly.react(

        "featureImportanceChart",

        [trace],

        chartLayout,

        config

    );
}


// ============================================================
// LOAD ALL DASHBOARD DATA
// ============================================================

async function loadDashboard() {

    try {

        await Promise.all([

            loadSummary(),

            loadDailyChart(),

            loadProductChart(),

            loadMonthlyChart(),

            loadYearlyChart(),

            loadStoreChart(),

            loadWeekdayChart(),

            loadPromotionChart(),

            loadHolidayChart(),

            loadSpikeChart(),

            loadInsights(),

            loadModelResults()

        ]);


        console.log(
            "DemandPulse dashboard loaded successfully."
        );

    }

    catch (error) {

        console.error(
            "Dashboard loading failed:",
            error
        );

    }
}


// ============================================================
// FILTER EVENTS
// ============================================================

function setupFilters() {

    const controls = [

        "startDate",

        "endDate",

        "store",

        "family",

        "promotion"

    ];


    controls.forEach(
        id => {

            document.getElementById(id)
                .addEventListener(
                    "change",
                    loadDashboard
                );

        }
    );


    document.getElementById(
        "reset"
    ).addEventListener(

        "click",

        () => {

            document.getElementById(
                "startDate"
            ).value = "";


            document.getElementById(
                "endDate"
            ).value = "";


            document.getElementById(
                "store"
            ).value = "all";


            document.getElementById(
                "family"
            ).value = "all";


            document.getElementById(
                "promotion"
            ).value = "all";


            loadDashboard();

        }

    );
}


// ============================================================
// START APPLICATION
// ============================================================

document.addEventListener(

    "DOMContentLoaded",

    async () => {

        try {

            await loadFilters();

            setupFilters();

            await loadDashboard();

        }

        catch (error) {

            console.error(
                "Application startup failed:",
                error
            );

        }

    }

);