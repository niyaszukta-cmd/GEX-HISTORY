# ============================================================================
# NYZTrade Historical GEX/DEX Dashboard
# Time-Series Analysis with Historical Data Storage
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy.stats import norm
from datetime import datetime, timedelta
import requests
import sqlite3
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="NYZTrade Historical GEX/DEX",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #111827;
        --bg-card: #1a2332;
        --bg-card-hover: #232f42;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-yellow: #f59e0b;
        --accent-cyan: #06b6d4;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-color: #2d3748;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 50%, var(--bg-primary) 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: var(--bg-card-hover);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .metric-value.positive { color: var(--accent-green); }
    .metric-value.negative { color: var(--accent-red); }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DhanConfig:
    client_id: str = "1100480354"
    access_token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY1OTYzMzk2LCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2NTg3Njk5NiwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.K93qVFYO2XrMJ-Jn4rY2autNZ444tc-AzYtaxVUsjRfsjW7NhfQom58vzuSMVI6nRMMB_sa7fCtWE5JIvk75yw"
    expiry_time: str = "2025-12-17T14:53:17"

DHAN_SECURITY_IDS = {
    "NIFTY": 13, "BANKNIFTY": 25, "FINNIFTY": 27, "MIDCPNIFTY": 442
}

EXCHANGE_SEGMENTS = {
    "NIFTY": "NSE_FNO", "BANKNIFTY": "NSE_FNO", 
    "FINNIFTY": "NSE_FNO", "MIDCPNIFTY": "NSE_FNO"
}

SYMBOL_CONFIG = {
    "NIFTY": {"contract_size": 25, "strike_interval": 50, "lot_size": 25},
    "BANKNIFTY": {"contract_size": 15, "strike_interval": 100, "lot_size": 15},
    "FINNIFTY": {"contract_size": 40, "strike_interval": 50, "lot_size": 40},
    "MIDCPNIFTY": {"contract_size": 75, "strike_interval": 25, "lot_size": 75},
}

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class HistoricalDataDB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use temp directory or current directory for Streamlit Cloud compatibility
            import tempfile
            import os
            if os.path.exists('/tmp'):
                self.db_path = "/tmp/historical_gex_data.db"
            else:
                self.db_path = os.path.join(tempfile.gettempdir(), "historical_gex_data.db")
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Main historical data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_gex_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    strike REAL NOT NULL,
                    spot_price REAL,
                    futures_price REAL,
                    call_oi INTEGER,
                    put_oi INTEGER,
                    call_oi_change INTEGER,
                    put_oi_change INTEGER,
                    call_volume INTEGER,
                    put_volume INTEGER,
                    call_iv REAL,
                    put_iv REAL,
                    call_ltp REAL,
                    put_ltp REAL,
                    call_delta REAL,
                    put_delta REAL,
                    call_gamma REAL,
                    put_gamma REAL,
                    call_vanna REAL,
                    put_vanna REAL,
                    call_charm REAL,
                    put_charm REAL,
                    net_gex REAL,
                    net_dex REAL,
                    net_vanna REAL,
                    net_charm REAL,
                    call_flow_gex REAL,
                    put_flow_gex REAL,
                    net_flow_gex REAL,
                    call_flow_dex REAL,
                    put_flow_dex REAL,
                    net_flow_dex REAL,
                    hedging_pressure REAL,
                    expiry_date TEXT,
                    days_to_expiry INTEGER,
                    UNIQUE(symbol, timestamp, strike)
                )
            """)
            
            # Aggregated metrics table for faster queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    spot_price REAL,
                    futures_price REAL,
                    total_call_oi REAL,
                    total_put_oi REAL,
                    pcr REAL,
                    net_gex_total REAL,
                    net_dex_total REAL,
                    net_vanna_total REAL,
                    net_charm_total REAL,
                    flow_gex_total REAL,
                    flow_dex_total REAL,
                    gex_near_positive REAL,
                    gex_near_negative REAL,
                    dex_near_above REAL,
                    dex_near_below REAL,
                    atm_strike REAL,
                    atm_straddle REAL,
                    max_pain REAL,
                    highest_call_oi_strike REAL,
                    highest_put_oi_strike REAL,
                    expiry_date TEXT,
                    days_to_expiry INTEGER,
                    UNIQUE(symbol, timestamp)
                )
            """)
            
            # Index for faster time-based queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_historical_timestamp 
                ON historical_gex_data(symbol, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_aggregated_timestamp 
                ON aggregated_metrics(symbol, timestamp)
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.warning(f"⚠️ Database initialization: Using temporary database. Data will not persist between sessions.")
            # Fall back to in-memory database if file system fails
            self.db_path = ":memory:"
    
    def insert_historical_data(self, df: pd.DataFrame, meta: Dict):
        """Insert complete option chain data"""
        conn = sqlite3.connect(self.db_path)
        
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        records = []
        for _, row in df.iterrows():
            record = (
                meta['symbol'], timestamp, date_str, time_str, row['Strike'],
                meta['spot_price'], meta['futures_price'],
                row['Call_OI'], row['Put_OI'], row['Call_OI_Change'], row['Put_OI_Change'],
                row['Call_Volume'], row['Put_Volume'], row['Call_IV'], row['Put_IV'],
                row['Call_LTP'], row['Put_LTP'], row['Call_Delta'], row['Put_Delta'],
                row['Call_Gamma'], row['Put_Gamma'], row['Call_Vanna'], row['Put_Vanna'],
                row['Call_Charm'], row['Put_Charm'], row['Net_GEX'], row['Net_DEX'],
                row['Net_Vanna'], row['Net_Charm'], row['Call_Flow_GEX'], row['Put_Flow_GEX'],
                row['Net_Flow_GEX'], row['Call_Flow_DEX'], row['Put_Flow_DEX'],
                row['Net_Flow_DEX'], row['Hedging_Pressure'],
                meta['expiry'], meta['days_to_expiry']
            )
            records.append(record)
        
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR REPLACE INTO historical_gex_data 
            (symbol, timestamp, date, time, strike, spot_price, futures_price,
             call_oi, put_oi, call_oi_change, put_oi_change, call_volume, put_volume,
             call_iv, put_iv, call_ltp, put_ltp, call_delta, put_delta,
             call_gamma, put_gamma, call_vanna, put_vanna, call_charm, put_charm,
             net_gex, net_dex, net_vanna, net_charm, call_flow_gex, put_flow_gex,
             net_flow_gex, call_flow_dex, put_flow_dex, net_flow_dex, hedging_pressure,
             expiry_date, days_to_expiry)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, records)
        
        conn.commit()
        conn.close()
    
    def insert_aggregated_metrics(self, metrics: Dict, meta: Dict):
        """Insert aggregated metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        cursor.execute("""
            INSERT OR REPLACE INTO aggregated_metrics
            (symbol, timestamp, date, time, spot_price, futures_price,
             total_call_oi, total_put_oi, pcr, net_gex_total, net_dex_total,
             net_vanna_total, net_charm_total, flow_gex_total, flow_dex_total,
             gex_near_positive, gex_near_negative, dex_near_above, dex_near_below,
             atm_strike, atm_straddle, max_pain, highest_call_oi_strike, 
             highest_put_oi_strike, expiry_date, days_to_expiry)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            meta['symbol'], timestamp, date_str, time_str,
            meta['spot_price'], meta['futures_price'],
            metrics.get('total_call_oi', 0), metrics.get('total_put_oi', 0),
            metrics.get('pcr', 0), metrics.get('gex_total', 0), metrics.get('dex_total', 0),
            metrics.get('vanna_total', 0), metrics.get('charm_total', 0),
            metrics.get('flow_gex_total', 0), metrics.get('flow_dex_total', 0),
            metrics.get('gex_near_positive', 0), metrics.get('gex_near_negative', 0),
            metrics.get('dex_near_above', 0), metrics.get('dex_near_below', 0),
            meta.get('atm_strike', 0), meta.get('atm_straddle', 0),
            metrics.get('max_pain', 0), metrics.get('highest_call_oi', 0),
            metrics.get('highest_put_oi', 0), meta['expiry'], meta['days_to_expiry']
        ))
        
        conn.commit()
        conn.close()
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical option chain data"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT * FROM historical_gex_data 
            WHERE symbol = ? AND date >= ? AND date <= ?
            ORDER BY timestamp, strike
        """
        df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
        conn.close()
        return df
    
    def get_aggregated_metrics(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch aggregated time-series metrics"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT * FROM aggregated_metrics 
            WHERE symbol = ? AND date >= ? AND date <= ?
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
        conn.close()
        return df
    
    def get_available_dates(self, symbol: str) -> List[str]:
        """Get list of available dates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM historical_gex_data 
            WHERE symbol = ? ORDER BY date DESC
        """, (symbol,))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dates
    
    def get_intraday_data(self, symbol: str, date: str) -> pd.DataFrame:
        """Get intraday time-series data for a specific date"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT * FROM aggregated_metrics 
            WHERE symbol = ? AND date = ?
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, conn, params=(symbol, date))
        conn.close()
        return df

# ============================================================================
# BLACK-SCHOLES & DATA PROCESSING (Reusing from original)
# ============================================================================

class BlackScholesCalculator:
    @staticmethod
    def calculate_d1(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0:
            return 0
        return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def calculate_d2(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0:
            return 0
        d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
        return d1 - sigma * np.sqrt(T)
    
    @staticmethod
    def calculate_gamma(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            n_prime_d1 = norm.pdf(d1)
            return n_prime_d1 / (S * sigma * np.sqrt(T))
        except:
            return 0
    
    @staticmethod
    def calculate_call_delta(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return norm.cdf(d1)
        except:
            return 0
    
    @staticmethod
    def calculate_put_delta(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return norm.cdf(d1) - 1
        except:
            return 0
    
    @staticmethod
    def calculate_vanna(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            return -norm.pdf(d1) * d2 / sigma
        except:
            return 0
    
    @staticmethod
    def calculate_charm(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            charm = -norm.pdf(d1) * (2 * r * T - d2 * sigma * np.sqrt(T)) / (2 * T * sigma * np.sqrt(T))
            return charm / 365
        except:
            return 0

# ============================================================================
# HISTORICAL DATA FETCHER
# ============================================================================

class HistoricalRollingDataFetcher:
    def __init__(self, config: DhanConfig):
        self.config = config
        self.headers = {
            'access-token': config.access_token,
            'client-id': config.client_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.base_url = "https://api.dhan.co/v2"
        self.bs_calc = BlackScholesCalculator()
        self.risk_free_rate = 0.07
    
    def fetch_rolling_option_data(self, symbol: str, from_date: str, to_date: str,
                                  strike_type: str = "ATM", option_type: str = "CALL",
                                  expiry_flag: str = "MONTH", expiry_code: int = 1) -> Optional[Dict]:
        """Fetch historical rolling options data"""
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            exchange_segment = EXCHANGE_SEGMENTS.get(symbol, "NSE_FNO")
            
            payload = {
                "exchangeSegment": exchange_segment,
                "interval": "1",  # 1-minute data
                "securityId": security_id,
                "instrument": "OPTIDX",
                "expiryFlag": expiry_flag,
                "expiryCode": expiry_code,
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
                data = response.json()
                if 'data' in data:
                    return data['data']
            
            return None
        except Exception as e:
            st.error(f"Error fetching historical data: {str(e)}")
            return None
    
    def process_historical_data(self, symbol: str, from_date: str, to_date: str,
                               strikes_range: List[str] = None) -> Tuple[pd.DataFrame, Dict]:
        """Process historical data for multiple strikes"""
        
        if strikes_range is None:
            strikes_range = ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"]
        
        all_data = []
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        
        # Fetch data for all strikes
        for strike_type in strikes_range:
            # Fetch CALL data
            call_data = self.fetch_rolling_option_data(
                symbol, from_date, to_date, strike_type, "CALL"
            )
            
            # Fetch PUT data
            put_data = self.fetch_rolling_option_data(
                symbol, from_date, to_date, strike_type, "PUT"
            )
            
            if call_data and put_data:
                ce_data = call_data.get('ce', {})
                pe_data = put_data.get('pe', {})
                
                # Process timestamps
                timestamps = ce_data.get('timestamp', [])
                
                for i, ts in enumerate(timestamps):
                    try:
                        dt = datetime.fromtimestamp(ts)
                        
                        # Extract all data points
                        spot_price = ce_data.get('spot', [0])[i] if i < len(ce_data.get('spot', [])) else 0
                        strike_price = ce_data.get('strike', [0])[i] if i < len(ce_data.get('strike', [])) else 0
                        
                        call_oi = ce_data.get('oi', [0])[i] if i < len(ce_data.get('oi', [])) else 0
                        put_oi = pe_data.get('oi', [0])[i] if i < len(pe_data.get('oi', [])) else 0
                        
                        call_volume = ce_data.get('volume', [0])[i] if i < len(ce_data.get('volume', [])) else 0
                        put_volume = pe_data.get('volume', [0])[i] if i < len(pe_data.get('volume', [])) else 0
                        
                        call_iv = ce_data.get('iv', [0])[i] if i < len(ce_data.get('iv', [])) else 15
                        put_iv = pe_data.get('iv', [0])[i] if i < len(pe_data.get('iv', [])) else 15
                        
                        call_ltp = ce_data.get('close', [0])[i] if i < len(ce_data.get('close', [])) else 0
                        put_ltp = pe_data.get('close', [0])[i] if i < len(pe_data.get('close', [])) else 0
                        
                        # Calculate Greeks (simplified - assume 7 days to expiry for historical)
                        time_to_expiry = 7 / 365
                        call_iv_dec = call_iv / 100 if call_iv > 1 else call_iv
                        put_iv_dec = put_iv / 100 if put_iv > 1 else put_iv
                        
                        call_gamma = self.bs_calc.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                        put_gamma = self.bs_calc.calculate_gamma(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                        call_delta = self.bs_calc.calculate_call_delta(spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec)
                        put_delta = self.bs_calc.calculate_put_delta(spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec)
                        
                        # Calculate exposures
                        call_gex = (call_oi * call_gamma * spot_price**2 * contract_size) / 1e9
                        put_gex = -(put_oi * put_gamma * spot_price**2 * contract_size) / 1e9
                        call_dex = (call_oi * call_delta * spot_price * contract_size) / 1e9
                        put_dex = (put_oi * put_delta * spot_price * contract_size) / 1e9
                        
                        record = {
                            'timestamp': dt,
                            'date': dt.strftime('%Y-%m-%d'),
                            'time': dt.strftime('%H:%M:%S'),
                            'spot_price': spot_price,
                            'strike': strike_price,
                            'strike_type': strike_type,
                            'call_oi': call_oi,
                            'put_oi': put_oi,
                            'call_volume': call_volume,
                            'put_volume': put_volume,
                            'call_iv': call_iv,
                            'put_iv': put_iv,
                            'call_ltp': call_ltp,
                            'put_ltp': put_ltp,
                            'call_gamma': call_gamma,
                            'put_gamma': put_gamma,
                            'call_delta': call_delta,
                            'put_delta': put_delta,
                            'call_gex': call_gex,
                            'put_gex': put_gex,
                            'net_gex': call_gex + put_gex,
                            'call_dex': call_dex,
                            'put_dex': put_dex,
                            'net_dex': call_dex + put_dex
                        }
                        
                        all_data.append(record)
                    except Exception as e:
                        continue
        
        if not all_data:
            return None, None
        
        df = pd.DataFrame(all_data)
        meta = {
            'symbol': symbol,
            'from_date': from_date,
            'to_date': to_date,
            'records': len(df)
        }
        
        return df, meta

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_timeseries_chart(df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """Create time-series chart for any metric"""
    fig = go.Figure()
    
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df[metric]]
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[metric],
        mode='lines+markers',
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=4, color=colors),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.2)',
        name=metric,
        hovertemplate='%{x}<br>Value: %{y:.4f}<extra></extra>'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=16, color='white')),
        xaxis_title="Time",
        yaxis_title=metric,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_heatmap_chart(df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """Create heatmap for strike vs time"""
    pivot_df = df.pivot_table(
        index='strike',
        columns='time',
        values=metric,
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='RdYlGn',
        zmid=0,
        text=pivot_df.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 8},
        colorbar=dict(title=metric)
    ))
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=16, color='white')),
        xaxis_title="Time",
        yaxis_title="Strike Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=500
    )
    
    return fig

def create_intraday_flow_chart(df: pd.DataFrame) -> go.Figure:
    """Create intraday flow analysis chart"""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Net GEX Flow", "Net DEX Flow"),
        vertical_spacing=0.15
    )
    
    # GEX Flow
    colors_gex = ['#10b981' if x > 0 else '#ef4444' for x in df['net_gex_total']]
    fig.add_trace(
        go.Bar(x=df['timestamp'], y=df['net_gex_total'], marker_color=colors_gex, name='GEX Flow'),
        row=1, col=1
    )
    
    # DEX Flow
    colors_dex = ['#10b981' if x > 0 else '#ef4444' for x in df['net_dex_total']]
    fig.add_trace(
        go.Bar(x=df['timestamp'], y=df['net_dex_total'], marker_color=colors_dex, name='DEX Flow'),
        row=2, col=1
    )
    
    fig.update_layout(
        title=dict(text="<b>Intraday Flow Analysis</b>", font=dict(size=16, color='white')),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=600,
        showlegend=False
    )
    
    return fig

def create_pcr_chart(df: pd.DataFrame) -> go.Figure:
    """Create Put-Call Ratio chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['pcr'],
        mode='lines+markers',
        line=dict(color='#8b5cf6', width=2),
        marker=dict(size=6),
        name='PCR',
        fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)'
    ))
    
    fig.add_hline(y=1.0, line_dash="dash", line_color="#06b6d4", line_width=2,
                  annotation_text="Neutral (1.0)")
    fig.add_hline(y=1.2, line_dash="dot", line_color="#ef4444", line_width=1,
                  annotation_text="Bearish Zone")
    fig.add_hline(y=0.8, line_dash="dot", line_color="#10b981", line_width=1,
                  annotation_text="Bullish Zone")
    
    fig.update_layout(
        title=dict(text="<b>Put-Call Ratio Trend</b>", font=dict(size=16, color='white')),
        xaxis_title="Time",
        yaxis_title="PCR",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=350
    )
    
    return fig

def create_spot_futures_chart(df: pd.DataFrame) -> go.Figure:
    """Create spot vs futures price chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['spot_price'],
        mode='lines',
        line=dict(color='#10b981', width=2),
        name='Spot Price'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['futures_price'],
        mode='lines',
        line=dict(color='#ef4444', width=2, dash='dash'),
        name='Futures Price'
    ))
    
    fig.update_layout(
        title=dict(text="<b>Spot vs Futures Price</b>", font=dict(size=16, color='white')),
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)',
        height=350,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    return fig

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_flow_metrics(df: pd.DataFrame, futures_price: float) -> Dict:
    """Calculate aggregated flow metrics"""
    df_unique = df.drop_duplicates(subset=['Strike']).sort_values('Strike').reset_index(drop=True)
    
    gex_total = df_unique['Net_GEX'].sum()
    dex_total = df_unique['Net_DEX'].sum()
    vanna_total = df_unique.get('Net_Vanna', pd.Series([0])).sum()
    charm_total = df_unique.get('Net_Charm', pd.Series([0])).sum()
    
    total_call_oi = df_unique['Call_OI'].sum()
    total_put_oi = df_unique['Put_OI'].sum()
    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
    
    max_pain = df_unique.loc[df_unique['Call_OI'].idxmax(), 'Strike']
    highest_call_oi = df_unique.loc[df_unique['Call_OI'].idxmax(), 'Strike']
    highest_put_oi = df_unique.loc[df_unique['Put_OI'].idxmax(), 'Strike']
    
    return {
        'gex_total': gex_total,
        'dex_total': dex_total,
        'vanna_total': vanna_total,
        'charm_total': charm_total,
        'total_call_oi': total_call_oi,
        'total_put_oi': total_put_oi,
        'pcr': pcr,
        'max_pain': max_pain,
        'highest_call_oi': highest_call_oi,
        'highest_put_oi': highest_put_oi,
    }

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    st.markdown("""
    <div class="main-header">
        <div>
            <h1 class="main-title">📈 NYZTrade Historical GEX/DEX Dashboard</h1>
            <p style="color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
                Time-Series Analysis | Historical Options Flow | Intraday Patterns
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    db = HistoricalDataDB()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        mode = st.radio("📊 Mode", ["Live Capture", "Historical Analysis"])
        
        symbol = st.selectbox("📈 Select Index", 
                             options=list(DHAN_SECURITY_IDS.keys()), 
                             index=0)
        
        if mode == "Historical Analysis":
            st.markdown("---")
            st.markdown("### 📅 Date Range")
            
            available_dates = db.get_available_dates(symbol)
            
            if available_dates:
                st.success(f"✅ {len(available_dates)} days of data available")
                
                # Date range selection
                max_date = datetime.strptime(available_dates[0], '%Y-%m-%d')
                min_date = datetime.strptime(available_dates[-1], '%Y-%m-%d')
                
                selected_date = st.date_input(
                    "Select Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
                
                analysis_type = st.selectbox(
                    "Analysis Type",
                    ["Intraday Analysis", "Multi-Day Comparison", "Custom Range"]
                )
            else:
                st.warning("⚠️ No historical data available. Use Live Capture mode first.")
                return
        
        st.markdown("---")
        st.markdown("### 🔑 API Status")
        config = DhanConfig()
        try:
            expiry_time = datetime.strptime(config.expiry_time, "%Y-%m-%dT%H:%M:%S")
            remaining = expiry_time - datetime.now()
            if remaining.total_seconds() > 0:
                st.success(f"✅ Token Valid: {remaining.days}d {remaining.seconds//3600}h")
            else:
                st.error("❌ Token Expired")
        except:
            st.warning("⚠️ Token status unknown")
    
    # Main content based on mode
    if mode == "Live Capture":
        st.markdown("### 📊 Live Data Capture")
        st.info("This mode will fetch current data and store it in the database for historical analysis.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            capture_interval = st.number_input("Capture Interval (minutes)", 
                                              min_value=1, max_value=60, value=5)
        with col2:
            auto_capture = st.checkbox("Auto Capture", value=False)
        with col3:
            if st.button("📸 Capture Now", use_container_width=True):
                with st.spinner("Capturing data..."):
                    # Use the fetcher from historical_data_fetcher
                    from historical_data_fetcher import HistoricalRollingDataFetcher
                    
                    # Get yesterday's date for historical data
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    fetcher = HistoricalRollingDataFetcher(DhanConfig())
                    df, meta = fetcher.fetch_complete_chain(
                        symbol=symbol,
                        from_date=yesterday,
                        to_date=today,
                        strike_range=["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"],
                        interval="5"
                    )
                    
                    if df is not None and meta is not None:
                        metrics = calculate_flow_metrics(df, meta['futures_price'])
                        db.insert_historical_data(df, meta)
                        db.insert_aggregated_metrics(metrics, meta)
                        st.success(f"✅ Data captured at {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        st.error("❌ Failed to capture data")
        
        if auto_capture:
            st.warning("⚠️ Auto-capture will run in the background. Keep this window open.")
    
    else:  # Historical Analysis mode
        date_str = selected_date.strftime('%Y-%m-%d')
        
        if analysis_type == "Intraday Analysis":
            st.markdown(f"### 📊 Intraday Analysis - {date_str}")
            
            # Fetch intraday data
            intraday_df = db.get_intraday_data(symbol, date_str)
            
            if intraday_df.empty:
                st.warning(f"⚠️ No data available for {date_str}")
                return
            
            # Convert timestamp strings to datetime
            intraday_df['timestamp'] = pd.to_datetime(intraday_df['timestamp'])
            
            # Display metrics overview
            st.markdown("### 📊 Daily Metrics Overview")
            cols = st.columns(6)
            
            latest = intraday_df.iloc[-1]
            first = intraday_df.iloc[0]
            
            with cols[0]:
                change = latest['spot_price'] - first['spot_price']
                change_pct = (change / first['spot_price']) * 100
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Spot Price</div>
                    <div class="metric-value">₹{latest['spot_price']:,.2f}</div>
                    <div style="color: {'#10b981' if change > 0 else '#ef4444'}; font-size: 0.8rem;">
                    {'+' if change > 0 else ''}{change:.2f} ({change_pct:+.2f}%)
                    </div></div>""", unsafe_allow_html=True)
            
            with cols[1]:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Net GEX</div>
                    <div class="metric-value {'positive' if latest['net_gex_total'] > 0 else 'negative'}">
                    {latest['net_gex_total']:.4f}B</div></div>""", unsafe_allow_html=True)
            
            with cols[2]:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Net DEX</div>
                    <div class="metric-value {'positive' if latest['net_dex_total'] > 0 else 'negative'}">
                    {latest['net_dex_total']:.4f}B</div></div>""", unsafe_allow_html=True)
            
            with cols[3]:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">PCR</div>
                    <div class="metric-value {'positive' if latest['pcr'] > 1 else 'negative'}">
                    {latest['pcr']:.2f}</div></div>""", unsafe_allow_html=True)
            
            with cols[4]:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Flow GEX</div>
                    <div class="metric-value {'positive' if latest['flow_gex_total'] > 0 else 'negative'}">
                    {latest['flow_gex_total']:.4f}B</div></div>""", unsafe_allow_html=True)
            
            with cols[5]:
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">Flow DEX</div>
                    <div class="metric-value {'positive' if latest['flow_dex_total'] > 0 else 'negative'}">
                    {latest['flow_dex_total']:.4f}B</div></div>""", unsafe_allow_html=True)
            
            # Time-series charts
            st.markdown("---")
            tabs = st.tabs(["📊 GEX/DEX Flow", "📈 Price Movement", "🎯 PCR & OI", "📋 Raw Data"])
            
            with tabs[0]:
                st.plotly_chart(create_intraday_flow_chart(intraday_df), use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(create_timeseries_chart(
                        intraday_df, 'net_gex_total', 'Net GEX Time Series'
                    ), use_container_width=True)
                
                with col2:
                    st.plotly_chart(create_timeseries_chart(
                        intraday_df, 'net_dex_total', 'Net DEX Time Series'
                    ), use_container_width=True)
            
            with tabs[1]:
                st.plotly_chart(create_spot_futures_chart(intraday_df), use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(create_timeseries_chart(
                        intraday_df, 'flow_gex_total', 'GEX Flow (Intraday)'
                    ), use_container_width=True)
                
                with col2:
                    st.plotly_chart(create_timeseries_chart(
                        intraday_df, 'flow_dex_total', 'DEX Flow (Intraday)'
                    ), use_container_width=True)
            
            with tabs[2]:
                st.plotly_chart(create_pcr_chart(intraday_df), use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_call_oi = create_timeseries_chart(
                        intraday_df, 'total_call_oi', 'Call OI Trend'
                    )
                    st.plotly_chart(fig_call_oi, use_container_width=True)
                
                with col2:
                    fig_put_oi = create_timeseries_chart(
                        intraday_df, 'total_put_oi', 'Put OI Trend'
                    )
                    st.plotly_chart(fig_put_oi, use_container_width=True)
            
            with tabs[3]:
                st.markdown("### 📋 Complete Intraday Data")
                display_cols = ['time', 'spot_price', 'futures_price', 'net_gex_total', 
                              'net_dex_total', 'pcr', 'flow_gex_total', 'flow_dex_total',
                              'total_call_oi', 'total_put_oi']
                
                display_df = intraday_df[display_cols].copy()
                st.dataframe(display_df, use_container_width=True, height=600)
                
                csv = display_df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name=f"intraday_analysis_{symbol}_{date_str}.csv",
                    mime="text/csv"
                )
        
        elif analysis_type == "Multi-Day Comparison":
            st.markdown("### 📊 Multi-Day Comparison")
            
            num_days = st.slider("Number of Days", min_value=2, max_value=30, value=7)
            
            end_date = selected_date
            start_date = end_date - timedelta(days=num_days)
            
            # Fetch multi-day data
            multi_day_df = db.get_aggregated_metrics(
                symbol, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if multi_day_df.empty:
                st.warning("⚠️ No data available for the selected range")
                return
            
            multi_day_df['timestamp'] = pd.to_datetime(multi_day_df['timestamp'])
            
            # Create comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(create_timeseries_chart(
                    multi_day_df, 'net_gex_total', f'Net GEX - Last {num_days} Days'
                ), use_container_width=True)
            
            with col2:
                st.plotly_chart(create_timeseries_chart(
                    multi_day_df, 'net_dex_total', f'Net DEX - Last {num_days} Days'
                ), use_container_width=True)
            
            st.plotly_chart(create_spot_futures_chart(multi_day_df), use_container_width=True)
            st.plotly_chart(create_pcr_chart(multi_day_df), use_container_width=True)
        
        elif analysis_type == "Custom Range":
            st.markdown("### 📊 Custom Date Range Analysis")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=selected_date - timedelta(days=7))
            with col2:
                end_date = st.date_input("End Date", value=selected_date)
            
            if st.button("📊 Analyze Range", use_container_width=True):
                custom_df = db.get_aggregated_metrics(
                    symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if custom_df.empty:
                    st.warning("⚠️ No data available for the selected range")
                else:
                    custom_df['timestamp'] = pd.to_datetime(custom_df['timestamp'])
                    
                    # Display comprehensive analysis
                    st.plotly_chart(create_timeseries_chart(
                        custom_df, 'net_gex_total', 'Net GEX - Custom Range'
                    ), use_container_width=True)
                    
                    st.plotly_chart(create_timeseries_chart(
                        custom_df, 'net_dex_total', 'Net DEX - Custom Range'
                    ), use_container_width=True)
                    
                    # Download button
                    csv = custom_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Analysis",
                        data=csv,
                        file_name=f"custom_analysis_{symbol}_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
    
    # Footer
    st.markdown("---")
    st.markdown(f"""<div style="text-align: center; padding: 20px; color: #64748b;">
        <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
        NYZTrade Historical GEX/DEX Dashboard | Database Storage | Time-Series Analysis<br>
        Symbol: {symbol} | Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p style="font-size: 0.75rem;">⚠️ Historical analysis for research purposes only.</p>
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
