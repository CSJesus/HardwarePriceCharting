from dash import Dash, html, dcc, Input, Output, State, ALL, callback_context
#Dash,html and dcc are needed to building the web app
#Input,Output are used to handle any callback errors
from dash.exceptions import PreventUpdate
#prevent update has been used by me to skip any updates to the layout during any callback
from dash import no_update
import plotly.graph_objects as go
#the above module is used for creating line charts and candle charts
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

app = Dash(__name__, suppress_callback_exceptions=True)
#this initializes the dash app and also suppress_callback exceptions has been used in order to allow callbacks
#to work even if associated layout elements are not present



def load_and_merge_data():
    files = [
        "assets/Average_Price_By_Day_AMD_CPU.csv",
        "assets/Average_Prices_By_Day_AMD_GPU.csv",
        "assets/Average_Prices_By_Day_Intel_CPU.csv",
        "assets/Average_Prices_By_Day_NVIDIA_GPU.csv",
    ]
    dataframes = [pd.read_csv(file) for file in files]
    merged_df = pd.concat(dataframes, ignore_index=True)
    return merged_df

#The first step is to load the data
data = load_and_merge_data()

def calculate_30_day_stats(df, product_name):
    """""the function filters the dataset for any specific product and also
        converts date columns and calculates the statistics of the product over the last 30 days.
    """
    product_data = df[df["CPU Name"] == product_name].iloc[0, 1:]
    #filters the data frame for the selected product name

    dates = pd.to_datetime(product_data.index, errors='coerce')
    # converting column indexes to datetime objects
    prices = product_data.astype(float)
    price_df = pd.DataFrame({
        'date': dates,
        'price': prices
    }).dropna()
    # in the above block of code we are creating a new dataframe with date and price columns
    #and dropping rows with missing values

    price_df = price_df.sort_values('date', ascending=False)
    last_30_days = price_df.head(30)

    stats = {
        'low': last_30_days['price'].min(),
        'high': last_30_days['price'].max(),
        'average': last_30_days['price'].mean(),
        'current': last_30_days.iloc[0]['price'],
        'previous': last_30_days.iloc[1]['price'] if len(last_30_days) > 1 else None
    }
    #after computing the statistics we return the calculated statistics as a dictionary

    return stats

def create_line_chart(df, product_names):
    """the function will create the line chart
    and will filter the dataset for the product selected
    We have used dark mode and dynamic coloring
    """
    fig = go.Figure()
    # initializing an empty Plotly figure

    if isinstance(product_names, str):
        product_names = [product_names]
    elif product_names is None:
        product_names = []
    # converting product in string to list

    colors = ['#4457ec', '#10B981', '#EF4444', '#F59E0B', '#6366F1']
    all_dates = set()
    product_data_dict = {} #hold price of each product

    for idx, product_name in enumerate(product_names):
        try:
            product_rows = df[df["CPU Name"].str.contains(product_name, case=False, na=False)]
            # the above line filters the DataFrame for rows where the product name matches
            if len(product_rows) == 0:
                print(f"Could not find data for product: {product_name}")
                continue

            product_data = product_rows.iloc[0, 1:]
            #the above code selects the price data for the first matching row.
            dates = pd.to_datetime(product_data.index, errors='coerce')
            prices = product_data.astype(float)

            price_df = pd.DataFrame({
                'date': dates,
                'price': prices
            }).dropna().sort_values('date')

            all_dates.update(price_df['date'])
            product_data_dict[product_name] = price_df

        except Exception as e:
            print(f"Error processing {product_name}: {str(e)}")
            continue

    start_date = pd.Timestamp('2024-09-01')
    end_date = pd.Timestamp.now()
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    for idx, (product_name, price_df) in enumerate(product_data_dict.items()):
        full_df = price_df.set_index('date').reindex(date_range)
        full_df = full_df.ffill().bfill()
        # reindexing is done to the dataframe in order to fill any gaps in the date range with ffill and bfill

        fig.add_trace(go.Scatter(
            x=full_df.index,
            y=full_df['price'],
            mode='lines',
            name=product_name,
            line=dict(color=colors[idx % len(colors)], width=2),
            hovertemplate='$%{y:.2f}<extra>%{x|%b %d, %Y}</extra>'
        ))

    fig.update_layout(
        plot_bgcolor='#1e293b',
        paper_bgcolor='#1e293b',
        font=dict(color='white', size=10),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            tickformat='%b %d\n%Y',
            tickangle=45,
            tickmode='auto',
            nticks=15,
            title_text=None,
            tickfont=dict(size=10),
            rangeslider=dict(visible=False),
            type='date',
            dtick='M1',
            ticklabelmode='period'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            tickprefix='$',
            title_text=None,
            tickfont=dict(size=10),
            zeroline=False
        ),
        margin=dict(l=50, r=20, t=10, b=50),
        height=600,
        width=1200,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(255,255,255,0.1)',
            borderwidth=1,
            font=dict(size=10),
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )

    return fig

def create_candlestick_chart(df, product_name):
    """creates a candlestick chart and it will handle exceptions too by returning an empty figure
    in case any error occurs
    """
    try:
        product_rows = df[df["CPU Name"].str.contains(product_name, case=False, na=False)]
        if len(product_rows) == 0:
            raise ValueError(f"Product not found: {product_name}")

        product_data = product_rows.iloc[0, 1:]
        dates = pd.to_datetime(product_data.index, errors='coerce')
        prices = product_data.astype(float)

        price_df = pd.DataFrame({
            'date': dates,
            'price': prices
        }).dropna().sort_values('date')

        weekly = price_df.set_index('date').resample('W').agg({
            'price': ['first', 'max', 'min', 'last']
        }).dropna()

        weekly.columns = ['open', 'high', 'low', 'close']

        fig = go.Figure(data=[go.Candlestick(
            x=weekly.index,
            open=weekly['open'],
            high=weekly['high'],
            low=weekly['low'],
            close=weekly['close'],
            increasing_line_color='#10B981',
            decreasing_line_color='#EF4444',
            name=product_name
        )])

        fig.update_layout(
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            font=dict(color='white', size=10),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                tickformat='%b %d\n%Y',
                tickangle=45,
                nticks=20,
                tickmode='auto',
                title_text=None,
                tickfont=dict(size=10),
                rangeslider=dict(visible=False),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                tickprefix='$',
                title_text=None,
                tickfont=dict(size=10),
                zeroline=False
            ),
            margin=dict(l=50, r=20, t=10, b=50),
            height=500,
            width=1000,
            hovermode='x unified'
        )

        return fig
    except Exception as e:
        print(f"Error creating candlestick chart for {product_name}: {str(e)}")
        return go.Figure()

def create_product_page(df, product_name, compare_products=None):
    """this function will diaplay all the main features of the product"""
    stats = calculate_30_day_stats(df, product_name)
    # this calculates 30-day stats for the selected product.
    price_change = ((stats['current'] - stats['previous']) / stats['previous'] * 100) if stats['previous'] else 0
    #the lines of codes below basically create a header for displaying the product name and its price info
    #and also displays the low high and average price of the product
    return html.Div([
        html.Div([
            html.Div([
                html.H1(product_name, className="product-title"),
                html.Div([
                    html.H2(f"${stats['current']:.2f}", className="current-price"),
                    html.Div([
                        html.Span(
                            f"{'+' if price_change >= 0 else ''}{price_change:.2f}% vs previous",
                            className=f"price-change {'positive' if price_change >= 0 else 'negative'}"
                        )
                    ], className="price-change-container")
                ], className="price-info")
            ], className="product-header-content")
        ], className="product-header"),

        html.Div([
            html.Div([
                html.H3("30-Day Low", className="stat-title"),
                html.Div(f"${stats['low']:.2f}", className="stat-value"),
                html.Div("Last 30 days", className="stat-subtitle")
            ], className="stat-card"),
            html.Div([
                html.H3("30-Day High", className="stat-title"),
                html.Div(f"${stats['high']:.2f}", className="stat-value"),
                html.Div("Last 30 days", className="stat-subtitle")
            ], className="stat-card"),
            html.Div([
                html.H3("30-Day Average", className="stat-title"),
                html.Div(f"${stats['average']:.2f}", className="stat-value"),
                html.Div("Last 30 days", className="stat-subtitle")
            ], className="stat-card"),
        ], className="stats-container"),

        html.Div([
            html.H3("Compare with other products", className="section-title"),
            dcc.Dropdown(
                id='compare-dropdown',
                options=[{'label': p, 'value': p} for p in df['CPU Name'].unique()],
                value=compare_products,
                multi=True,
                className="compare-dropdown",
                placeholder="Select products to compare..."
            ),
        ], className="compare-section"),

        html.Div([
            html.Div([
                html.H3("Price History", className="chart-title"),
                dcc.Graph(
                    figure=create_line_chart(
                        df,
                        [product_name] + (compare_products if compare_products else [])
                    ),
                    className="price-chart",
                    config={'displayModeBar': False}
                )
            ], className="chart-container"),

            html.Div([
                html.H3("Weekly Price Ranges", className="chart-title"),
                dcc.Graph(
                    figure=create_candlestick_chart(df, product_name),
                    className="candlestick-chart",
                    config={'displayModeBar': False}
                )
            ], className="chart-container")
        ], className="charts-container")
    ], className="product-page")

# Main app layout
app.layout = html.Div([
    dcc.Store(id='current-product-store'),
    html.Header([
        html.Div([
            html.H1("Hardware Price Tracker", className="nav-title-large"),
            dcc.Dropdown(
                id="product-search",
                options=[{"label": product, "value": product}
                         for product in data["CPU Name"].unique()],
                placeholder="Search for a product...",
                className="search-dropdown",
                searchable=True,
                clearable=True,
            )
        ], className="header-content")
    ], className="header"),

    html.Main([
        html.Div([
            html.H2("Welcome to Hardware Price Tracker", className="welcome-title"),
            html.P("Select a product to view detailed price analysis and history.",
                  className="welcome-subtitle"),

            html.Div([
                html.H3("Popular CPU Products", className="section-title"),
                html.P("Explore a selection of the latest and most powerful CPU options from leading manufacturers.",
                      className="section-description"),
                html.Div([
                    html.Div([
                        html.H4(product, className="product-title"),
                        html.P("High-performance CPU with advanced features for demanding workloads.",
                              className="product-description"),
                        html.Button("View Details", id={"type": "product-button", "index": i},
                                  className="product-button")
                    ], className="product-card")
                    for i, product in enumerate([
                        'AMD Ryzen 7 5800X',
                        'Intel Core i7-12700K',
                        'AMD Ryzen 9 5950X'
                    ])
                ], className="product-grid"),
            ], className="product-section"),

            html.Div(style={"height": "3rem"}),

            html.Div([
                html.H3("Popular GPU Products", className="section-title"),
                html.P("Check out the latest and most powerful graphics cards for gaming, content creation, and beyond.",
                      className="section-description"),
                html.Div([
                    html.Div([
                        html.H4(product, className="product-title"),
                        html.P("Cutting-edge GPU with advanced ray tracing and powerful features.",
                              className="product-description"),
                        html.Button("View Details", id={"type": "product-button", "index": i + 3},
                                  className="product-button")
                    ], className="product-card")
                    for i, product in enumerate([
                        'GeForce RTX 4090',
                        'Radeon RX 7900 XTX',
                        'GeForce RTX 4080'
                    ])
                ], className="product-grid"),
            ], className="product-section"),

            html.Div(style={"height": "3rem"}),

            html.Div([
                html.H2("Featured Hardware", className="section-title"),
                html.Div([
                    html.Div([
                        html.H4('Intel Core i9-13900K', className="product-title"),
                        html.P("High-performance CPU with 12 cores for demanding workloads.",
                              className="product-description"),
                        html.Button("View Details", id={"type": "featured-button", "index": 0},
                                  className="product-button")
                    ], className="product-card"),
                    html.Div([
                        html.H4('GeForce RTX 4070 Ti', className="product-title"),
                        html.P("Powerful GPU with advanced features.", className="product-description"),
                        html.Button("View Details", id={"type": "featured-button", "index": 1},
                                  className="product-button")
                    ], className="product-card")], className="product-grid")
            ], className="featured-section"),
            html.Div(style={"height": "3rem"}),

            html.Div([
                html.H2("Latest Hardware News", className="section-title news-title"),
                html.Div([
                    html.Div([
                        html.H3("NVIDIA Announces New GeForce RTX 5000 Series", className="news-title"),
                        html.P(
                            "The latest GPUs promise even more powerful performance for gaming and content creation.",
                            className="news-description"),
                        html.A("Read More", href="#", className="news-link")
                    ], className="news-item"),
                    html.Div([
                        html.H3("AMD Unveils Ryzen 7000 CPUs with New Zen 4 Architecture", className="news-title"),
                        html.P("The new Ryzen CPUs offer significant improvements in processing power and efficiency.",
                               className="news-description"),
                        html.A("Read More", href="#", className="news-link")
                    ], className="news-item"),
                    html.Div([
                        html.H3("Intel Launches 13th Gen Core Processors", className="news-title"),
                        html.P(
                            "Intel's latest CPUs deliver enhanced performance and power efficiency for various workloads.",
                            className="news-description"),
                        html.A("Read More", href="#", className="news-link")
                    ], className="news-item")
                ], className="news-grid")
            ], className="news-section")
        ], id="page-content", className="main-content")
    ]),
])


# callbacks
@app.callback(
    [Output("page-content", "children"),
     Output("current-product-store", "data")],
    [Input("product-search", "value"),
     Input({"type": "product-button", "index": ALL}, "n_clicks"),
     Input({"type": "featured-button", "index": ALL}, "n_clicks")],
    prevent_initial_call=True
)
def update_page(search_value, product_button_clicks, featured_button_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return app.layout.children[1].children, None

    trigger_id = ctx.triggered[0]["prop_id"]
    current_product = None

    try:
        if trigger_id == "product-search.value" and search_value:
            current_product = search_value
            return create_product_page(data, current_product), current_product

        elif "product-button" in trigger_id:
            button_index = int(eval(trigger_id.split('.')[0])["index"])
            if any(n for n in product_button_clicks if n):
                all_products = [
                    'AMD Ryzen 7 5800X',
                    'Core i7-12700K',
                    'AMD Ryzen 9 5950X',
                    'GeForce RTX 4090',
                    'Radeon RX 7900 XTX',
                    'GeForce RTX 4080'
                ]

                if button_index < len(all_products):
                    current_product = all_products[button_index]
                    return create_product_page(data, current_product), current_product

        elif "featured-button" in trigger_id:
            button_index = int(eval(trigger_id.split('.')[0])["index"])
            if any(n for n in featured_button_clicks if n):
                featured_products = [
                    'Core i9-13900K',
                    'GeForce RTX 4070 Ti'
                ]
                if button_index < len(featured_products):
                    current_product = featured_products[button_index]
                    return create_product_page(data, current_product), current_product

        return app.layout.children[1].children, None
    except Exception as e:
        print(f"Error in update_page: {str(e)}")
        return app.layout.children[1].children, None


@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    [Input("compare-dropdown", "value")],
    [State("current-product-store", "data")],
    prevent_initial_call=True
)
def update_comparison(compare_products, current_product):
    if not current_product:
        raise PreventUpdate

    return create_product_page(data, current_product, compare_products)


if __name__ == '__main__':
    app.run_server(debug=True)
