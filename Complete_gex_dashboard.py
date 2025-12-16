# ============================================================================
# NYZTrade Simple GEX Dashboard - Complete Single File
# No external dependencies required - installs everything automatically
# ============================================================================

import subprocess
import sys

# Auto-install required packages
def install_packages():
    """Install required packages if not already installed"""
    required = {
        'streamlit': 'streamlit',
        'pandas': 'pandas', 
        'numpy': 'numpy',
        'plotly': 'plotly',
        'scipy': 'scipy',
        'requests': 'requests'
    }
    
    for package, pip_name in required.items():
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "-q"])

# Install packages first
install_packages()

# Now import everything
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
from datetime import datetime, timedelta
import requests
import time

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="NYZTrade GEX Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #3b82f6;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .success-box {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
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
# CALCULATOR
# ============================================================================

class GEXCalculator:
    def __init__(self):
        self.risk_free_rate = 0.07
    
    def calculate_gamma(self, S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
            return norm.pdf(d1) / (S * sigma * np.sqrt(T))
        except:
            return 0

# ============================================================================
# DATA FETCHER
# ============================================================================

class SimpleDhanFetcher:
    def __init__(self, client_id, access_token):
        self.headers = {
            'access-token': access_token,
            'client-id': client_id,
            'Content-Type': 'application/json',
        }
        self.base_url = "https://api.dhan.co/v2"
        self.calculator = GEXCalculator()
    
    def fetch_rolling_data(self, symbol, from_date, to_date, strike_type="ATM", option_type="CALL"):
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            
            payload = {
                "exchangeSegment": "NSE_FNO",
                "interval": "60",
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
            
            response = requests.post(
                f"{self.base_url}/charts/rollingoption",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('data', {})
            return None
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None
    
    def process_data(self, symbol, from_date, to_date, strikes, progress_bar=None):
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        all_data = []
        
        total_strikes = len(strikes) * 2  # CALL + PUT for each
        current = 0
        
        for strike_type in strikes:
            # Fetch CALL
            call_data = self.fetch_rolling_data(symbol, from_date, to_date, strike_type, "CALL")
            current += 1
            if progress_bar:
                progress_bar.progress(current / total_strikes)
            time.sleep(1)
            
            # Fetch PUT
            put_data = self.fetch_rolling_data(symbol, from_date, to_date, strike_type, "PUT")
            current += 1
            if progress_bar:
                progress_bar.progress(current / total_strikes)
            time.sleep(1)
            
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
                    
                    call_oi = ce_data.get('oi', [0])[i] if i < len(ce_data.get('oi', [])) else 0
                    put_oi = pe_data.get('oi', [0])[i] if i < len(pe_data.get('oi', [])) else 0
                    call_iv = ce_data.get('iv', [15])[i] if i < len(ce_data.get('iv', [])) else 15
                    put_iv = pe_data.get('iv', [15])[i] if i < len(pe_data.get('iv', [])) else 15
                    
                    time_to_expiry = 7 / 365
                    call_iv_dec = call_iv / 100 if call_iv > 1 else call_iv
                    put_iv_dec = put_iv / 100 if put_iv > 1 else put_iv
                    
                    call_gamma = self.calculator.calculate_gamma(spot_price, strike_price, time_to_expiry, 0.07, call_iv_dec)
                    put_gamma = self.calculator.calculate_gamma(spot_price, strike_price, time_to_expiry, 0.07, put_iv_dec)
                    
                    call_gex = (call_oi * call_gamma * spot_price**2 * contract_size) / 1e9
                    put_gex = -(put_oi * put_gamma * spot_price**2 * contract_size) / 1e9
                    net_gex = call_gex + put_gex
                    
                    all_data.append({
                        'timestamp': dt,
                        'date': dt.strftime('%Y-%m-%d'),
                        'spot_price': spot_price,
                        'strike': strike_price,
                        'net_gex': net_gex
                    })
                except:
                    continue
        
        if not all_data:
            return None
        
        return pd.DataFrame(all_data)

# ============================================================================
# VISUALIZATION
# ============================================================================

def create_gex_chart(df):
    daily_gex = df.groupby('timestamp').agg({
        'net_gex': 'sum',
        'spot_price': 'first'
    }).reset_index()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Net GEX Over Time', 'Spot Price Movement'),
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4]
    )
    
    colors = ['#10b981' if x > 0 else '#ef4444' for x in daily_gex['net_gex']]
    
    fig.add_trace(
        go.Bar(
            x=daily_gex['timestamp'],
            y=daily_gex['net_gex'],
            marker_color=colors,
            name='Net GEX',
            hovertemplate='%{x}<br>GEX: %{y:.2f}B<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1, row=1, col=1)
    
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
    
    fig.update_layout(
        height=700,
        showlegend=False,
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Net GEX (₹ Billions)", row=1, col=1)
    fig.update_yaxes(title_text="Spot Price (₹)", row=2, col=1)
    
    return fig

def calculate_statistics(df):
    daily = df.groupby('date')['net_gex'].sum()
    
    return {
        'avg_gex': daily.mean(),
        'max_gex': daily.max(),
        'min_gex': daily.min(),
        'positive_days': (daily > 0).sum(),
        'negative_days': (daily < 0).sum(),
        'total_days': len(daily)
    }

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown('<h1 class="main-title">📊 NYZTrade GEX Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Historical Gamma Exposure Analysis using Dhan Rolling API</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        client_id = st.text_input("Dhan Client ID", value="1100480354")
        access_token = st.text_input("Dhan Access Token", type="password", 
                                     value="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY1OTYzMzk2LCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2NTg3Njk5NiwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.K93qVFYO2XrMJ-Jn4rY2autNZ444tc-AzYtaxVUsjRfsjW7NhfQom58vzuSMVI6nRMMB_sa7fCtWE5JIvk75yw")
        
        st.markdown("---")
        
        symbol = st.selectbox("📈 Select Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
        
        days_back = st.slider("📅 Days of History", min_value=7, max_value=30, value=30)
        
        strikes = st.multiselect(
            "🎯 Select Strikes",
            ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2", "ATM+3", "ATM-3"],
            default=["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"]
        )
        
        st.markdown("---")
        
        fetch_button = st.button("🚀 Fetch Data", use_container_width=True, type="primary")
    
    # Main content
    if fetch_button:
        if not client_id or not access_token:
            st.error("❌ Please provide Dhan API credentials in the sidebar")
            return
        
        if not strikes:
            st.error("❌ Please select at least one strike")
            return
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        st.markdown(f"""
        <div class="info-box">
            <strong>📊 Fetching Data</strong><br>
            Symbol: {symbol}<br>
            Date Range: {from_date} to {to_date}<br>
            Strikes: {', '.join(strikes)}
        </div>
        """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Fetching data from Dhan API...")
        
        try:
            fetcher = SimpleDhanFetcher(client_id, access_token)
            df = fetcher.process_data(symbol, from_date, to_date, strikes, progress_bar)
            
            if df is None or len(df) == 0:
                st.error("❌ No data received. Please check your API credentials and try again.")
                return
            
            progress_bar.progress(100)
            status_text.empty()
            
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Data Fetched Successfully!</strong><br>
                Total Records: {len(df):,}<br>
                Date Range: {df['date'].min()} to {df['date'].max()}<br>
                Unique Days: {df['date'].nunique()}
            </div>
            """, unsafe_allow_html=True)
            
            # Calculate statistics
            stats = calculate_statistics(df)
            
            # Display metrics
            st.markdown("### 📊 Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg Net GEX", f"{stats['avg_gex']:.2f}B")
            with col2:
                st.metric("Max GEX", f"{stats['max_gex']:.2f}B")
            with col3:
                st.metric("Min GEX", f"{stats['min_gex']:.2f}B")
            with col4:
                pct = (stats['positive_days'] / stats['total_days'] * 100) if stats['total_days'] > 0 else 0
                st.metric("Positive Days", f"{stats['positive_days']} ({pct:.0f}%)")
            
            # Display chart
            st.markdown("### 📈 GEX Charts")
            fig = create_gex_chart(df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display data table
            with st.expander("📋 View Raw Data"):
                st.dataframe(df, use_container_width=True, height=400)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{symbol}_GEX_{from_date}_{to_date}.csv",
                mime="text/csv"
            )
            
            # Interpretation
            st.markdown("### 💡 Interpretation")
            
            if stats['avg_gex'] > 0:
                st.success(f"""
                **Positive Average GEX ({stats['avg_gex']:.2f}B)**
                - Market makers are in suppression mode
                - Volatility likely to be lower
                - Range-bound movement expected
                - Good for premium selling strategies
                """)
            else:
                st.warning(f"""
                **Negative Average GEX ({stats['avg_gex']:.2f}B)**
                - Market makers are in amplification mode
                - Volatility likely to be higher
                - Trending moves expected
                - Good for directional or long premium strategies
                """)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Please check your API credentials and try again")
    
    else:
        # Initial state
        st.info("""
        👋 **Welcome to NYZTrade GEX Dashboard!**
        
        This dashboard fetches historical Gamma Exposure (GEX) data from Dhan Rolling API.
        
        **Quick Start:**
        1. Enter your Dhan API credentials in the sidebar
        2. Select your preferred index (NIFTY/BANKNIFTY/FINNIFTY)
        3. Choose date range and strikes
        4. Click "Fetch Data" button
        
        **What is GEX?**
        - Positive GEX = Market makers suppress volatility (range-bound)
        - Negative GEX = Market makers amplify volatility (trending)
        - Zero GEX (Gamma Flip) = Critical support/resistance
        """)
        
        st.markdown("### 📚 How to Get Dhan API Credentials")
        st.markdown("""
        1. Login to your Dhan account
        2. Go to API section in settings
        3. Generate API credentials
        4. Copy Client ID and Access Token
        5. Paste them in the sidebar
        
        [Learn More →](https://api.dhan.co/)
        """)

if __name__ == "__main__":
    main()
