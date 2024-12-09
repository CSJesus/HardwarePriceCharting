from dash import Dash, html, dcc, Input, Output, State, ALL, callback_context
import plotly.graph_objects as go
import pandas as pd
import logging

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Helper function to load and merge all CSV files
def load_and_merge_data():
    files = [
        "Average_Price_By_Day_AMD_CPU.csv",
        "Average_Prices_By_Day_AMD_GPU.csv",
        "Average_Prices_By_Day_Intel_CPU.csv",
        "Average_Prices_By_Day_NVIDIA_GPU.csv",
    ]
    try:
        dataframes = [pd.read_csv(file) for file in files]
        merged_df = pd.concat(dataframes, ignore_index=True)
        merged_df.fillna(0, inplace=True)  # Fill missing values
        return merged_df
    except Exception as e:
        logging.error(f"Error loading CSV files: {e}")
        return pd.DataFrame()

# Load the data at the start
data = load_and_merge_data()

# Functions for chart creation
def create_line_chart(df, product_name):
    fig = go.Figure()
    try:
        product_data = df[df["CPU Name"] == product_name]
        dates = pd.to_datetime(product_data.columns[1:], errors='coerce').strftime('%d-%b-%Y')
        prices = product_data.iloc[0, 1:].astype(float).fillna(method="ffill")
        fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines+markers", name=product_name))
    except Exception as e:
        logging.error(f"Error in creating line chart: {e}")

    fig.update_layout(
        title="Price History",
        xaxis=dict(title="Date", tickangle=45),
        yaxis_title="Price ($)",
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font_color="white",
        height=600  # Increased size
    )
    return fig

def create_candlestick_chart(df, product_name):
    product_data = df[df["CPU Name"] == product_name]
    dates = pd.to_datetime(product_data.columns[1:], errors='coerce').strftime('%d-%b-%Y')
    prices = product_data.iloc[0, 1:].astype(float).fillna(method="ffill")

    weekly_high = prices.rolling(7, min_periods=1).max()
    weekly_low = prices.rolling(7, min_periods=1).min()
    weekly_open = prices.rolling(7, min_periods=1).apply(lambda x: x[0])
    weekly_close = prices.rolling(7, min_periods=1).apply(lambda x: x[-1])

    fig = go.Figure(data=[go.Candlestick(
        x=dates,
        open=weekly_open,
        high=weekly_high,
        low=weekly_low,
        close=weekly_close,
        increasing_line_color="#10B981",
        decreasing_line_color="#EF4444"
    )])

    fig.update_layout(
        title="Weekly Price Ranges",
        xaxis=dict(title="Date", tickangle=45),
        yaxis_title="Price ($)",
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font_color="white",
        height=500  # Increased size
    )
    return fig

def create_product_page(df, product_name):
    product_data = df[df["CPU Name"] == product_name].iloc[0, 1:].astype(float).fillna(method="ffill")
    current_price = product_data.iloc[-1]
    last_30_days = product_data[-30:]

    return html.Div([
        html.Div([
            html.Div([
                html.H1(product_name, className="product-title"),
                html.Div([
                    html.H3("Current Price", className="stat-title"),
                    html.Div(f"${current_price:.2f}", className="stat-value"),
                ], className="price-container"),
            ], className="product-header-content")
        ], className="product-header"),

        html.Div([
            html.Div([
                html.H3("30-Day Low", className="stat-title"),
                html.Div(f"${last_30_days.min():.2f}", className="stat-value"),
            ], className="stat-card"),
            html.Div([
                html.H3("30-Day High", className="stat-title"),
                html.Div(f"${last_30_days.max():.2f}", className="stat-value"),
            ], className="stat-card"),
            html.Div([
                html.H3("30-Day Average", className="stat-title"),
                html.Div(f"${last_30_days.mean():.2f}", className="stat-value"),
            ], className="stat-card"),
        ], className="stats-container"),

        html.Div([
            html.Div([
                html.H3("Compare with other products", className="compare-title"),
                dcc.Dropdown(
                    id="compare-dropdown",
                    options=[{"label": prod, "value": prod} for prod in df["CPU Name"].unique()],
                    placeholder="Select products to compare...",
                    multi=True,
                    className="compare-dropdown",
                )
            ], className="compare-section"),
            dcc.Graph(figure=create_line_chart(df, product_name)),
            dcc.Graph(figure=create_candlestick_chart(df, product_name)),
        ], className="charts-container")
    ])

# App Layout
app.layout = html.Div([
    html.Nav([
        html.Div([
            html.H1("Hardware Price Tracker", className="nav-title"),
            html.Div([
                dcc.Dropdown(
                    id="product-search",
                    options=[{"label": product, "value": product} for product in data["CPU Name"].unique()],
                    placeholder="Search for a product...",
                    className="search-input",
                    searchable=True,
                    clearable=True,
                )
            ], className="search-container"),
        ], className="nav-content"),
    ], className="navbar"),
    html.Main([
        html.Div([
            html.H2("Welcome to Hardware Price Tracker", className="welcome-title"),
            html.Div([
                html.H3("Popular CPU Products", className="section-title"),
                html.Div([
                    html.Button(product, id={"type": "product-button", "index": i}, className="popular-product")
                    for i, product in enumerate(data["CPU Name"].unique()[:6])
                ], className="popular-products"),
                html.H3("Popular GPU Products", className="section-title"),
                html.Div([
                    html.Button(product, id={"type": "product-button", "index": i+6}, className="popular-product")
                    for i, product in enumerate(data["CPU Name"].unique()[6:12])
                ], className="popular-products"),
            ], className="welcome-section"),
        ], id="page-content", className="main-content")
    ]),
])

# Callbacks
@app.callback(
    Output("page-content", "children"),
    [Input("product-search", "value"),
     Input({"type": "product-button", "index": ALL}, "n_clicks")],
)
def update_page(selected_product, n_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return html.Div([
            html.H2("Welcome to Hardware Price Tracker", className="welcome-title"),
            html.Div([html.H3("Select a product to view detailed price analysis and history.")])
        ])

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if "product-button" in triggered_id:
        index = int(eval(triggered_id)["index"])
        selected_product = data["CPU Name"].unique()[index]

    if selected_product:
        return create_product_page(data, selected_product)
    return html.Div([html.H3("Please select a valid product.")])

if __name__ == "__main__":
    app.run_server(debug=True)
