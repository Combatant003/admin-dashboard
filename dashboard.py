import dash
from dash import dcc
from dash import html
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
from scipy.stats import norm
from connector import fetch_data_as_dataframe

# Simulate some data
order_df = fetch_data_as_dataframe('Orders', ['order_id','bid_value', 'ask_value', 'quantity', 'created_at', 'asset'])
user_df = fetch_data_as_dataframe("USER", ['user_id', 'username'])
# Create a Dash app
app = dash.Dash(__name__)

def calculate_parametric_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    
    mean = returns.mean()
    std_dev = returns.std()
    
    z_score = norm.ppf(1 - confidence_level)
    
    var = mean + z_score * std_dev
    return var

# Layout of the app
app.layout = html.Div([
    html.H1("Market Maker Risk Management Dashboard"),
    
    dcc.Dropdown(
        id='market-maker-dropdown',
        options=[{'label': mm, 'value': mm} for mm in order_df['asset'].unique()],
        value=order_df['asset'].unique()[0],
        multi=False,
        style={'width': '50%'}
    ),
    
    dcc.Graph(id='exposure-chart'),
    dcc.Graph(id='pnl-chart'),
    dcc.Graph(id='volume-chart'),
    dcc.Graph(id='live-update-graph'),
    html.Div(id='var-display'),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
])

# Callbacks to update the charts based on the dropdown selection
@app.callback(
    [Output('exposure-chart', 'figure'),
     Output('pnl-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('live-update-graph', 'figure'),
     Output('var-display', 'children')],
    [Input('market-maker-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_charts(selected_market_maker, n_intervals):
    order_df = fetch_data_as_dataframe('Orders', ['order_id','bid_value', 'ask_value', 'quantity', 'created_at', 'asset', 'spread'])
    filtered_df = order_df[order_df['asset'] == selected_market_maker]
    
    # Exposure chart
    exposure_fig = px.line(filtered_df, x='created_at', y='ask_value', title='Exposure Over Time')
    
    # PnL chart
    pnl_fig = px.line(filtered_df, x='created_at', y='bid_value', title='PnL Over Time')
    
    # Volume chart
    volume_fig = px.line(filtered_df, x='created_at', y='quantity', title='Trading Volume Over Time')

    returns = pd.Series(filtered_df['spread'] * filtered_df['quantity'])
    VaR = calculate_parametric_var(returns)

    Var_fig = go.Figure()

    Var_fig.add_trace(go.Scatter(x=filtered_df['created_at'], y=filtered_df['quantity'], mode='lines+markers', name='Orders'))
    var_display = f"Parametric Value at Risk (VaR): {VaR:.2f}"

    
    return exposure_fig, pnl_fig, volume_fig, Var_fig, var_display

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
