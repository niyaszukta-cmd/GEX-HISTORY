#!/usr/bin/env python3
"""
Simple One-Month GEX Data Collector
Fetches historical data from Dhan Rolling API and generates graphs
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
import time

# ============================================================================
# CONFIGURATION - UPDATE YOUR CREDENTIALS HERE
# ============================================================================

DHAN_CLIENT_ID = "1100480354"
DHAN_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY1OTYzMzk2LCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTY1ODc2OTk2LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IkFQUCIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAwNDgwMzU0In0.K93qVFYO2XrMJ-Jn4rY2autNZ444tc-AzYtaxVUsjRfsjW7NhfQom58vzuSMVI6nRMMB_sa7fCtWE5JIvk75yw"

# Symbol to analyze
SYMBOL = "NIFTY"  # Options: NIFTY, BANKNIFTY, FINNIFTY

# Date range (last 30 days)
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=30)

# ============================================================================
# DHAN API CONFIGURATION
# ============================================================================

DHAN_SECURITY_IDS = {
    "NIFTY": 13,
    "BANKNIFTY": 25,
    "FINNIFTY": 27,
}

SYMBOL_CONFIG = {
    "NIFTY": {"contract_size": 25, "strike_interval": 50},
    "BANKNIFTY": {"contract_size": 15, "strike_interval": 100},
    "FINNIFTY": {"contract_size": 40, "strike_interval": 50},
}

# ============================================================================
# DATA FETCHER
# ============================================================================

class SimpleGEXFetcher:
    def __init__(self, client_id, access_token):
        self.headers = {
            'access-token': access_token,
            'client-id': client_id,
            'Content-Type': 'application/json',
        }
        self.base_url = "https://api.dhan.co/v2"
        self.risk_free_rate = 0.07
    
    def calculate_gamma(self, S, K, T, r, sigma):
        """Calculate Gamma using Black-Scholes"""
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
            return norm.pdf(d1) / (S * sigma * np.sqrt(T))
        except:
            return 0
    
    def fetch_rolling_data(self, symbol, from_date, to_date, strike_type="ATM", option_type="CALL"):
        """Fetch rolling options data from Dhan API"""
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            
            payload = {
                "exchangeSegment": "NSE_FNO",
                "interval": "60",  # 1-hour intervals for monthly data
                "securityId": security_id,
                "instrument": "OPTIDX",
                "expiryFlag": "MONTH",
                "expiryCode": 1,
                "strike": strike_type,
                "drvOptionType": option_type,
                "requiredData": ["open", "high", "low", "close", "volume", "oi", "iv", "strike", "spot"],
                "fromDate": from_date,
                "toDate": to_date
            }
            
            print(f"  Fetching {option_type} {strike_type}...")
            
            response = requests.post(
                f"{self.base_url}/charts/rollingoption",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                print(f"  Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  Error: {str(e)}")
            return None
    
    def process_data(self, symbol, from_date, to_date, strikes=None):
        """Process data for multiple strikes and calculate GEX"""
        
        if strikes is None:
            strikes = ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"]
        
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        
        all_data = []
        
        print(f"\n📊 Fetching {symbol} data from {from_date} to {to_date}")
        print(f"Strikes: {', '.join(strikes)}\n")
        
        for strike_type in strikes:
            print(f"Processing {strike_type}...")
            
            # Fetch CALL data
            call_data = self.fetch_rolling_data(symbol, from_date, to_date, strike_type, "CALL")
            time.sleep(1)  # Rate limiting
            
            # Fetch PUT data
            put_data = self.fetch_rolling_data(symbol, from_date, to_date, strike_type, "PUT")
            time.sleep(1)  # Rate limiting
            
            if not call_data or not put_data:
                continue
            
            ce_data = call_data.get('ce', {})
            pe_data = put_data.get('pe', {})
            
            if not ce_data:
                continue
            
            timestamps = ce_data.get('timestamp', [])
            
            for i, ts in enumerate(timestamps):
                try:
                    dt = datetime.fromtimestamp(ts)
                    
                    spot_price = ce_data.get('spot', [0])[i] if i < len(ce_data.get('spot', [])) else 0
                    strike_price = ce_data.get('strike', [0])[i] if i < len(ce_data.get('strike', [])) else 0
                    
                    if spot_price == 0 or strike_price == 0:
                        continue
                    
                    # Get data
                    call_oi = ce_data.get('oi', [0])[i] if i < len(ce_data.get('oi', [])) else 0
                    put_oi = pe_data.get('oi', [0])[i] if i < len(pe_data.get('oi', [])) else 0
                    call_iv = ce_data.get('iv', [15])[i] if i < len(ce_data.get('iv', [])) else 15
                    put_iv = pe_data.get('iv', [15])[i] if i < len(pe_data.get('iv', [])) else 15
                    
                    # Calculate Greeks
                    time_to_expiry = 7 / 365  # Approximate
                    call_iv_dec = call_iv / 100 if call_iv > 1 else call_iv
                    put_iv_dec = put_iv / 100 if put_iv > 1 else put_iv
                    
                    call_gamma = self.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                    put_gamma = self.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                    
                    # Calculate GEX
                    call_gex = (call_oi * call_gamma * spot_price**2 * contract_size) / 1e9
                    put_gex = -(put_oi * put_gamma * spot_price**2 * contract_size) / 1e9
                    net_gex = call_gex + put_gex
                    
                    all_data.append({
                        'timestamp': dt,
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M'),
                        'spot_price': spot_price,
                        'strike': strike_price,
                        'strike_type': strike_type,
                        'call_oi': call_oi,
                        'put_oi': put_oi,
                        'call_gex': call_gex,
                        'put_gex': put_gex,
                        'net_gex': net_gex
                    })
                    
                except Exception as e:
                    continue
            
            print(f"  ✓ {strike_type} completed\n")
        
        if not all_data:
            print("❌ No data collected!")
            return None
        
        df = pd.DataFrame(all_data)
        print(f"\n✅ Data collection complete!")
        print(f"Total records: {len(df):,}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Unique days: {df['date'].nunique()}")
        
        return df

# ============================================================================
# VISUALIZATION
# ============================================================================

def create_gex_charts(df, symbol):
    """Create comprehensive GEX visualization charts"""
    
    # Aggregate by timestamp
    daily_gex = df.groupby('timestamp').agg({
        'net_gex': 'sum',
        'spot_price': 'first',
        'date': 'first'
    }).reset_index()
    
    daily_gex = daily_gex.sort_values('timestamp')
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f'{symbol} Net GEX Over Time (Last 30 Days)',
            f'{symbol} Spot Price Movement',
            'GEX Distribution by Strike'
        ),
        vertical_spacing=0.12,
        row_heights=[0.4, 0.3, 0.3]
    )
    
    # Chart 1: Net GEX Time Series
    colors = ['#10b981' if x > 0 else '#ef4444' for x in daily_gex['net_gex']]
    
    fig.add_trace(
        go.Bar(
            x=daily_gex['timestamp'],
            y=daily_gex['net_gex'],
            marker_color=colors,
            name='Net GEX',
            hovertemplate='%{x}<br>Net GEX: %{y:.2f}B<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1, row=1, col=1)
    
    # Chart 2: Spot Price
    fig.add_trace(
        go.Scatter(
            x=daily_gex['timestamp'],
            y=daily_gex['spot_price'],
            mode='lines',
            line=dict(color='#3b82f6', width=2),
            name='Spot Price',
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ),
        row=2, col=1
    )
    
    # Chart 3: GEX by Strike (Latest data)
    latest_date = df['date'].max()
    latest_data = df[df['date'] == latest_date].groupby('strike')['net_gex'].sum().reset_index()
    latest_data = latest_data.sort_values('strike')
    
    strike_colors = ['#10b981' if x > 0 else '#ef4444' for x in latest_data['net_gex']]
    
    fig.add_trace(
        go.Bar(
            x=latest_data['strike'],
            y=latest_data['net_gex'],
            marker_color=strike_colors,
            name='GEX by Strike',
            hovertemplate='Strike: %{x}<br>GEX: %{y:.2f}B<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"<b>{symbol} GEX Analysis - Last 30 Days</b>",
            font=dict(size=20, color='#1f2937')
        ),
        showlegend=False,
        height=1000,
        template='plotly_white',
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Net GEX (₹ Billions)", row=1, col=1)
    fig.update_yaxes(title_text="Spot Price (₹)", row=2, col=1)
    fig.update_yaxes(title_text="Net GEX (₹ Billions)", row=3, col=1)
    
    return fig

def create_summary_stats(df, symbol):
    """Create summary statistics chart"""
    
    daily_stats = df.groupby('date').agg({
        'net_gex': ['mean', 'min', 'max'],
        'spot_price': 'first'
    }).reset_index()
    
    daily_stats.columns = ['date', 'avg_gex', 'min_gex', 'max_gex', 'spot_price']
    
    # Calculate statistics
    stats = {
        'Total Days': len(daily_stats),
        'Avg Net GEX': f"{daily_stats['avg_gex'].mean():.2f}B",
        'Max Positive GEX': f"{daily_stats['max_gex'].max():.2f}B",
        'Max Negative GEX': f"{daily_stats['min_gex'].min():.2f}B",
        'Positive GEX Days': f"{(daily_stats['avg_gex'] > 0).sum()} ({(daily_stats['avg_gex'] > 0).sum()/len(daily_stats)*100:.1f}%)",
        'Negative GEX Days': f"{(daily_stats['avg_gex'] < 0).sum()} ({(daily_stats['avg_gex'] < 0).sum()/len(daily_stats)*100:.1f}%)",
        'Spot Price Range': f"{daily_stats['spot_price'].min():.0f} - {daily_stats['spot_price'].max():.0f}",
        'Price Change': f"{((daily_stats['spot_price'].iloc[-1] / daily_stats['spot_price'].iloc[0] - 1) * 100):+.2f}%"
    }
    
    return stats

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*70)
    print("  NYZTrade - One Month GEX Data Collector")
    print("="*70)
    
    # Initialize fetcher
    fetcher = SimpleGEXFetcher(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
    
    # Format dates for API
    from_date = START_DATE.strftime('%Y-%m-%d')
    to_date = END_DATE.strftime('%Y-%m-%d')
    
    # Fetch data
    df = fetcher.process_data(SYMBOL, from_date, to_date)
    
    if df is None:
        print("\n❌ Failed to collect data. Please check:")
        print("  1. API credentials are correct")
        print("  2. Internet connection is working")
        print("  3. Date range is valid (not future dates)")
        return
    
    # Save to CSV
    filename = f"{SYMBOL}_GEX_data_{from_date}_{to_date}.csv"
    df.to_csv(filename, index=False)
    print(f"\n💾 Data saved to: {filename}")
    
    # Calculate summary statistics
    print("\n" + "="*70)
    print("  SUMMARY STATISTICS")
    print("="*70)
    stats = create_summary_stats(df, SYMBOL)
    for key, value in stats.items():
        print(f"{key:.<30} {value}")
    
    # Create visualizations
    print("\n📊 Generating charts...")
    fig = create_gex_charts(df, SYMBOL)
    
    # Save chart
    chart_filename = f"{SYMBOL}_GEX_charts_{from_date}_{to_date}.html"
    fig.write_html(chart_filename)
    print(f"📈 Charts saved to: {chart_filename}")
    
    # Show chart in browser
    print("\n🌐 Opening charts in browser...")
    fig.show()
    
    print("\n✅ Complete! Files generated:")
    print(f"  📄 Data: {filename}")
    print(f"  📊 Charts: {chart_filename}")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
