import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output, State
from scipy.stats import norm
from connector import fetch_data_as_dataframe

# Dummy data for testing
dummy_data = {
    'uuid': [f'uuid{i}' for i in range(1, 11)],
    'order_id': [f'order{i}' for i in range(1, 11)],
    'order_type': ['buy'] * 10,
    'bid_value': np.random.rand(10) * 100,
    'ask_value': np.random.rand(10) * 100,
    'quantity': [100, 10, 6, 12, 8, 15, 5, 20, 7, 14],
    'created_at': pd.date_range(start='2024-07-30T17:16:21', periods=10, freq='h'),
    'asset': ['AAPL'] * 10
}

dummy_user_data = {
    'user_id': [f'order{i}' for i in range(1, 11)],
    'username': [f'user{i}' for i in range(1, 11)]
}

order_df = pd.DataFrame(dummy_data)
user_df = pd.DataFrame(dummy_user_data)

# Fetch data from Supabase
def fetch_data():
    # Uncomment these lines to fetch data from Supabase
    # order_df = fetch_data_as_dataframe('Orders', ['uuid', 'order_id', 'order_type', 'bid_value', 'ask_value', 'quantity', 'created_at', 'asset'])
    # user_df = fetch_data_as_dataframe("USER", ['user_id', 'username'])
    return order_df, user_df

# Create a Dash app
app = dash.Dash(__name__)

# Define the CSS styles
styles = {
    'table': {
        'width': '100%',
        'borderCollapse': 'collapse',
    },
    'th': {
        'border': '1px solid #dddddd',
        'textAlign': 'left',
        'padding': '8px',
        'backgroundColor': '#f2f2f2'
    },
    'td': {
        'border': '1px solid #dddddd',
        'textAlign': 'left',
        'padding': '8px'
    },
    'tr:nth-child(even)': {
        'backgroundColor': '#f9f9f9'
    }
}

def calculate_parametric_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    mean = returns.mean()
    std_dev = returns.std()
    z_score = norm.ppf(1 - confidence_level)
    var = mean + z_score * std_dev
    return var

def check_threshold_exceedance(df, user_df, threshold=0.05):
    exceedance_logs = []
    df['created_at'] = pd.to_datetime(df['created_at'], format='ISO8601')
    df = df.sort_values('created_at')
    
    for asset in df['asset'].unique():
        asset_df = df[df['asset'] == asset].copy()
        cumulative_quantity = 0
        
        for index, row in asset_df.iterrows():
            cumulative_quantity += row['quantity']
            if row['quantity'] > cumulative_quantity * threshold:
                user_info = user_df[user_df['user_id'] == row['order_id']]
                if not user_info.empty:
                    user_info = user_info.iloc[0]
                    percentage_increase = (row['quantity'] / cumulative_quantity) * 100
                    log_entry = {
                        'date': row['created_at'],
                        'asset': row['asset'],
                        'quantity': row['quantity'],
                        'user_id': row['order_id'],
                        'username': user_info['username'],
                        'order_id': row['order_id'],
                        'uuid': row['uuid'],
                        'order_type': row['order_type'],
                        'percentage_increase': percentage_increase,
                        'message': f"Exceeds threshold: {row['quantity']} shares bought, more than 5% increase of cumulative shares."
                    }
                    exceedance_logs.append(log_entry)
    
    return exceedance_logs

# Layout of the app
app.layout = html.Div([
    html.H1("Market Maker Risk Management Dashboard"),
    
    dcc.Dropdown(
        id='market-maker-dropdown',
        options=[{'label': asset, 'value': asset} for asset in order_df['asset'].unique()],
        value=order_df['asset'].unique()[0],
        multi=False,
        style={'width': '50%'}
    ),
    
    dcc.Graph(id='exposure-chart'),
    dcc.Graph(id='pnl-chart'),
    dcc.Graph(id='volume-chart'),
    dcc.Graph(id='live-update-graph'),
    html.Div(id='var-display'),
    html.Table([
        html.Thead(html.Tr([html.Th(col, style=styles['th']) for col in ['UUID', 'Order ID', 'Order Type', 'Quantity', '% Increase']])),
        html.Tbody(id='exceedance-logs')
    ], style=styles['table']),
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
     Output('var-display', 'children'),
     Output('exceedance-logs', 'children')],
    [Input('market-maker-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_charts(selected_market_maker, n_intervals):
    try:
        order_df, user_df = fetch_data()
        filtered_df = order_df[order_df['asset'] == selected_market_maker].copy()
        
        # Convert created_at to datetime with ISO8601 format
        filtered_df['created_at'] = pd.to_datetime(filtered_df['created_at'], format='ISO8601')
        
        # Exposure chart
        exposure_fig = px.line(filtered_df, x='created_at', y='ask_value', title='Exposure Over Time')
        
        # PnL chart
        pnl_fig = px.line(filtered_df, x='created_at', y='bid_value', title='PnL Over Time')
        
        # Volume chart
        volume_fig = px.line(filtered_df, x='created_at', y='quantity', title='Trading Volume Over Time')

        # Calculate returns based on bid and ask values
        returns = pd.Series(filtered_df['ask_value'] - filtered_df['bid_value'])
        VaR = calculate_parametric_var(returns)

        Var_fig = go.Figure()
        Var_fig.add_trace(go.Scatter(x=filtered_df['created_at'], y=filtered_df['quantity'], mode='lines+markers', name='Orders'))
        var_display = f"Parametric Value at Risk (VaR): {VaR:.2f}"
        
        # Check for threshold exceedances
        exceedance_logs = check_threshold_exceedance(order_df, user_df)
        
        exceedance_display = [
            html.Tr([html.Td(log[col], style=styles['td']) for col in ['uuid', 'order_id', 'order_type', 'quantity', 'percentage_increase']], style=styles['tr:nth-child(even)'])
            for log in exceedance_logs
        ]
        
        return exposure_fig, pnl_fig, volume_fig, Var_fig, var_display, exceedance_display
    except Exception as e:
        print(f"Error in callback: {e}")
        return {}, {}, {}, {}, "Error", [html.Div(f"Error: {e}")]

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
