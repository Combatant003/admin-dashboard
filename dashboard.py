import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output
from connector import fetch_data_as_dataframe

# Simulate some data
order_df = fetch_data_as_dataframe('Orders', ['order_id','bid_value', 'ask_value', 'quantity', 'created_at', 'asset'])
user_df = fetch_data_as_dataframe("USER", ['user_id', 'username'])
# Create a Dash app
app = dash.Dash(__name__)

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
     Output('volume-chart', 'figure')],
    [Input('market-maker-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_charts(selected_market_maker, n_intervals):
    filtered_df = order_df[order_df['asset'] == selected_market_maker]
    
    # Exposure chart
    exposure_fig = px.line(filtered_df, x='created_at', y='ask_value', title='Exposure Over Time')
    
    # PnL chart
    pnl_fig = px.line(filtered_df, x='created_at', y='bid_value', title='PnL Over Time')
    
    # Volume chart
    volume_fig = px.line(filtered_df, x='created_at', y='quantity', title='Trading Volume Over Time')
    
    return exposure_fig, pnl_fig, volume_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
