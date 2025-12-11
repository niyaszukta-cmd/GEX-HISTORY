# ============================================================================
# NYZTrade Historical Time Machine Dashboard
# Past Data Analysis with Draggable Timeline
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import norm
from datetime import datetime, timedelta, time as dt_time
import requests
import time
import json
import os
import pickle
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="NYZTrade Time Machine",
    page_icon="⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# PROFESSIONAL STYLING
# ============================================================================

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
        --accent-pink: #ec4899;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-color: #2d3748;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 50%, #1a1a2e 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 28px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #8b5cf6, #06b6d4, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .sub-title {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin-top: 10px;
    }
    
    .time-machine-container {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(236, 72, 153, 0.1));
        border: 2px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 28px;
        margin: 24px 0;
        position: relative;
        overflow: hidden;
    }
    
    .time-machine-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #10b981, #f59e0b, #ec4899);
        animation: rainbow-slide 3s linear infinite;
    }
    
    @keyframes rainbow-slide {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    
    .time-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 3rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-align: center;
        text-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
        margin: 16px 0;
    }
    
    .date-display {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.4rem;
        color: var(--text-primary);
        text-align: center;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 20px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        background: var(--bg-card-hover);
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
    }
    
    .metric-card.positive { border-left: 4px solid var(--accent-green); }
    .metric-card.negative { border-left: 4px solid var(--accent-red); }
    .metric-card.neutral { border-left: 4px solid var(--accent-yellow); }
    .metric-card.info { border-left: 4px solid var(--accent-cyan); }
    
    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }
    
    .metric-value.positive { color: var(--accent-green); }
    .metric-value.negative { color: var(--accent-red); }
    .metric-value.neutral { color: var(--accent-yellow); }
    
    .metric-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        margin-top: 8px;
        color: var(--text-secondary);
    }
    
    .timeline-marker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: var(--accent-purple);
    }
    
    .snapshot-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(26, 35, 50, 0.8) 100%);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .snapshot-card:hover {
        border-color: var(--accent-purple);
        transform: scale(1.02);
    }
    
    .snapshot-card.active {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
    }
    
    .change-indicator {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 12px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .change-indicator.up {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
    }
    
    .change-indicator.down {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
    }
    
    .history-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: rgba(236, 72, 153, 0.15);
        border: 1px solid rgba(236, 72, 153, 0.3);
        border-radius: 20px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--accent-pink);
    }
    
    .playback-controls {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin: 20px 0;
    }
    
    .playback-btn {
        padding: 12px 24px;
        border-radius: 12px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--bg-card);
        padding: 10px;
        border-radius: 14px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: var(--text-secondary);
        font-family: 'Space Grotesk', sans-serif;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
        color: white;
    }
    
    .comparison-arrow {
        font-size: 2rem;
        color: var(--accent-purple);
        text-align: center;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DhanConfig:
    client_id: str = "1100480354"
    access_token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY1NDgzNzg3LCJhcHBfaWQiOiI4NjFmZjMyMSIsImlhdCI6MTc2NTM5NzM4NywidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.XDHIi24skiRDG3Uc6CFA-eZVadHfuPIounKW0eFiFpJrRoAplaGS2sXzpI5c0ndrmL-Ee72NnBqqyEG2UPqjKg"
    expiry_time: str = "2025-12-12T01:39:47"

DHAN_SECURITY_IDS = {
    "NIFTY": 13, "BANKNIFTY": 25, "FINNIFTY": 27, "MIDCPNIFTY": 442, "SENSEX": 51
}

EXCHANGE_SEGMENTS = {
    "NIFTY": "IDX_I", "BANKNIFTY": "IDX_I", "FINNIFTY": "IDX_I",
    "MIDCPNIFTY": "IDX_I", "SENSEX": "BSE_IDX"
}

SYMBOL_CONFIG = {
    "NIFTY": {"contract_size": 25, "strike_interval": 50, "lot_size": 25},
    "BANKNIFTY": {"contract_size": 15, "strike_interval": 100, "lot_size": 15},
    "FINNIFTY": {"contract_size": 40, "strike_interval": 50, "lot_size": 40},
    "MIDCPNIFTY": {"contract_size": 75, "strike_interval": 25, "lot_size": 75},
}

# Market hours
MARKET_OPEN = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)

# Data storage path
DATA_DIR = "historical_data"

# ============================================================================
# BLACK-SCHOLES CALCULATOR
# ============================================================================

class BlackScholesCalculator:
    @staticmethod
    def calculate_d1(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0:
            return 0
        return (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def calculate_gamma(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return norm.pdf(d1) / (S * sigma * np.sqrt(T))
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
            d2 = d1 - sigma * np.sqrt(T)
            return -norm.pdf(d1) * d2 / sigma
        except:
            return 0
    
    @staticmethod
    def calculate_charm(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = d1 - sigma * np.sqrt(T)
            charm = -norm.pdf(d1) * (2 * 0.07 * T - d2 * sigma * np.sqrt(T)) / (2 * T * sigma * np.sqrt(T))
            return charm / 365
        except:
            return 0

# ============================================================================
# HISTORICAL DATA MANAGER
# ============================================================================

class HistoricalDataManager:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def get_snapshot_filename(self, symbol: str, timestamp: datetime) -> str:
        date_str = timestamp.strftime("%Y%m%d")
        time_str = timestamp.strftime("%H%M%S")
        return os.path.join(self.data_dir, f"{symbol}_{date_str}_{time_str}.pkl")
    
    def save_snapshot(self, symbol: str, df: pd.DataFrame, meta: Dict, timestamp: datetime = None):
        if timestamp is None:
            timestamp = datetime.now()
        
        filename = self.get_snapshot_filename(symbol, timestamp)
        data = {
            'df': df,
            'meta': meta,
            'timestamp': timestamp
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        
        return filename
    
    def load_snapshot(self, filename: str) -> Tuple[pd.DataFrame, Dict, datetime]:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        return data['df'], data['meta'], data['timestamp']
    
    def get_available_snapshots(self, symbol: str, date: datetime = None) -> List[Dict]:
        snapshots = []
        
        for filename in os.listdir(self.data_dir):
            if filename.startswith(symbol) and filename.endswith('.pkl'):
                parts = filename.replace('.pkl', '').split('_')
                if len(parts) >= 3:
                    try:
                        date_str = parts[1]
                        time_str = parts[2]
                        snap_datetime = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                        
                        if date is None or snap_datetime.date() == date.date():
                            snapshots.append({
                                'filename': os.path.join(self.data_dir, filename),
                                'datetime': snap_datetime,
                                'time_str': snap_datetime.strftime("%H:%M:%S"),
                                'date_str': snap_datetime.strftime("%Y-%m-%d")
                            })
                    except:
                        continue
        
        return sorted(snapshots, key=lambda x: x['datetime'])
    
    def get_available_dates(self, symbol: str) -> List[datetime]:
        dates = set()
        
        for filename in os.listdir(self.data_dir):
            if filename.startswith(symbol) and filename.endswith('.pkl'):
                parts = filename.replace('.pkl', '').split('_')
                if len(parts) >= 2:
                    try:
                        date_str = parts[1]
                        date = datetime.strptime(date_str, "%Y%m%d")
                        dates.add(date.date())
                    except:
                        continue
        
        return sorted(list(dates), reverse=True)
    
    def get_day_summary(self, symbol: str, date: datetime) -> Dict:
        snapshots = self.get_available_snapshots(symbol, date)
        
        if not snapshots:
            return None
        
        summary = {
            'date': date.date(),
            'num_snapshots': len(snapshots),
            'first_snapshot': snapshots[0]['datetime'],
            'last_snapshot': snapshots[-1]['datetime'],
            'snapshots': snapshots
        }
        
        # Load first and last for comparison
        if len(snapshots) >= 2:
            df_first, meta_first, _ = self.load_snapshot(snapshots[0]['filename'])
            df_last, meta_last, _ = self.load_snapshot(snapshots[-1]['filename'])
            
            summary['open_price'] = meta_first.get('futures_price', 0)
            summary['close_price'] = meta_last.get('futures_price', 0)
            summary['price_change'] = summary['close_price'] - summary['open_price']
            summary['price_change_pct'] = (summary['price_change'] / summary['open_price'] * 100) if summary['open_price'] > 0 else 0
        
        return summary

# ============================================================================
# DHAN API FETCHER
# ============================================================================

class DhanAPIFetcher:
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
    
    def get_expiry_list(self, symbol: str) -> List[str]:
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            segment = EXCHANGE_SEGMENTS.get(symbol, "IDX_I")
            payload = {"UnderlyingScrip": security_id, "UnderlyingSeg": segment}
            response = requests.post(
                f"{self.base_url}/optionchain/expirylist",
                headers=self.headers, json=payload, timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('data', [])
            return []
        except:
            return []
    
    def fetch_option_chain(self, symbol: str, expiry_date: str = None) -> Optional[Dict]:
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            segment = EXCHANGE_SEGMENTS.get(symbol, "IDX_I")
            payload = {"UnderlyingScrip": security_id, "UnderlyingSeg": segment}
            if expiry_date:
                payload["Expiry"] = expiry_date
            response = requests.post(
                f"{self.base_url}/optionchain",
                headers=self.headers, json=payload, timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
            return None
        except:
            return None
    
    def process_option_chain(self, symbol: str, expiry_index: int = 0, strikes_range: int = 12):
        expiry_list = self.get_expiry_list(symbol)
        if not expiry_list:
            return None, None
        
        selected_expiry = expiry_list[min(expiry_index, len(expiry_list) - 1)]
        
        try:
            expiry_date = datetime.strptime(selected_expiry, "%Y-%m-%d")
            days_to_expiry = max((expiry_date - datetime.now()).days, 1)
            time_to_expiry = days_to_expiry / 365
        except:
            days_to_expiry = 7
            time_to_expiry = 7 / 365
        
        oc_data = self.fetch_option_chain(symbol, selected_expiry)
        if not oc_data:
            return None, None
        
        spot_price = oc_data.get('last_price', 0)
        option_chain = oc_data.get('oc', {})
        futures_price = spot_price * np.exp(self.risk_free_rate * time_to_expiry)
        
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        strike_interval = config["strike_interval"]
        
        all_strikes = []
        atm_strike = None
        min_atm_diff = float('inf')
        atm_call_premium = 0
        atm_put_premium = 0
        
        for strike_str, strike_data in option_chain.items():
            try:
                strike = float(strike_str)
            except:
                continue
            
            if strike == 0 or abs(strike - futures_price) / strike_interval > strikes_range:
                continue
            
            ce = strike_data.get('ce', {})
            pe = strike_data.get('pe', {})
            
            call_oi = ce.get('oi', 0) or 0
            put_oi = pe.get('oi', 0) or 0
            call_oi_change = (ce.get('oi', 0) or 0) - (ce.get('previous_oi', 0) or 0)
            put_oi_change = (pe.get('oi', 0) or 0) - (pe.get('previous_oi', 0) or 0)
            call_volume = ce.get('volume', 0) or 0
            put_volume = pe.get('volume', 0) or 0
            call_iv = ce.get('implied_volatility', 0) or 0
            put_iv = pe.get('implied_volatility', 0) or 0
            call_ltp = ce.get('last_price', 0) or 0
            put_ltp = pe.get('last_price', 0) or 0
            
            strike_diff = abs(strike - futures_price)
            if strike_diff < min_atm_diff:
                min_atm_diff = strike_diff
                atm_strike = strike
                atm_call_premium = call_ltp
                atm_put_premium = put_ltp
            
            call_iv_dec = call_iv / 100 if call_iv > 1 else (call_iv if call_iv > 0 else 0.15)
            put_iv_dec = put_iv / 100 if put_iv > 1 else (put_iv if put_iv > 0 else 0.15)
            
            call_gamma = self.bs_calc.calculate_gamma(futures_price, strike, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_gamma = self.bs_calc.calculate_gamma(futures_price, strike, time_to_expiry, self.risk_free_rate, put_iv_dec)
            call_delta = self.bs_calc.calculate_call_delta(futures_price, strike, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_delta = self.bs_calc.calculate_put_delta(futures_price, strike, time_to_expiry, self.risk_free_rate, put_iv_dec)
            call_vanna = self.bs_calc.calculate_vanna(futures_price, strike, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_vanna = self.bs_calc.calculate_vanna(futures_price, strike, time_to_expiry, self.risk_free_rate, put_iv_dec)
            call_charm = self.bs_calc.calculate_charm(futures_price, strike, time_to_expiry, self.risk_free_rate, call_iv_dec)
            put_charm = self.bs_calc.calculate_charm(futures_price, strike, time_to_expiry, self.risk_free_rate, put_iv_dec)
            
            call_gex = (call_oi * call_gamma * futures_price**2 * contract_size) / 1e9
            put_gex = -(put_oi * put_gamma * futures_price**2 * contract_size) / 1e9
            call_dex = (call_oi * call_delta * futures_price * contract_size) / 1e9
            put_dex = (put_oi * put_delta * futures_price * contract_size) / 1e9
            call_vanna_exp = (call_oi * call_vanna * futures_price * contract_size) / 1e9
            put_vanna_exp = (put_oi * put_vanna * futures_price * contract_size) / 1e9
            call_charm_exp = (call_oi * call_charm * futures_price * contract_size) / 1e9
            put_charm_exp = (put_oi * put_charm * futures_price * contract_size) / 1e9
            call_flow_gex = (call_oi_change * call_gamma * futures_price**2 * contract_size) / 1e9
            put_flow_gex = -(put_oi_change * put_gamma * futures_price**2 * contract_size) / 1e9
            call_flow_dex = (call_oi_change * call_delta * futures_price * contract_size) / 1e9
            put_flow_dex = (put_oi_change * put_delta * futures_price * contract_size) / 1e9
            
            all_strikes.append({
                'Strike': strike, 'Call_OI': call_oi, 'Put_OI': put_oi,
                'Call_OI_Change': call_oi_change, 'Put_OI_Change': put_oi_change,
                'Call_Volume': call_volume, 'Put_Volume': put_volume,
                'Total_Volume': call_volume + put_volume,
                'Call_IV': call_iv, 'Put_IV': put_iv,
                'Call_LTP': call_ltp, 'Put_LTP': put_ltp,
                'Call_Delta': call_delta, 'Put_Delta': put_delta,
                'Call_Gamma': call_gamma, 'Put_Gamma': put_gamma,
                'Call_Vanna': call_vanna, 'Put_Vanna': put_vanna,
                'Call_Charm': call_charm, 'Put_Charm': put_charm,
                'Call_GEX': call_gex, 'Put_GEX': put_gex, 'Net_GEX': call_gex + put_gex,
                'Call_DEX': call_dex, 'Put_DEX': put_dex, 'Net_DEX': call_dex + put_dex,
                'Call_Vanna_Exp': call_vanna_exp, 'Put_Vanna_Exp': put_vanna_exp,
                'Net_Vanna': call_vanna_exp + put_vanna_exp,
                'Call_Charm_Exp': call_charm_exp, 'Put_Charm_Exp': put_charm_exp,
                'Net_Charm': call_charm_exp + put_charm_exp,
                'Call_Flow_GEX': call_flow_gex, 'Put_Flow_GEX': put_flow_gex,
                'Net_Flow_GEX': call_flow_gex + put_flow_gex,
                'Call_Flow_DEX': call_flow_dex, 'Put_Flow_DEX': put_flow_dex,
                'Net_Flow_DEX': call_flow_dex + put_flow_dex,
            })
        
        if not all_strikes:
            return None, None
        
        df = pd.DataFrame(all_strikes).sort_values('Strike').reset_index(drop=True)
        max_gex = df['Net_GEX'].abs().max()
        df['Hedging_Pressure'] = (df['Net_GEX'] / max_gex * 100) if max_gex > 0 else 0
        
        meta = {
            'symbol': symbol, 'spot_price': spot_price, 'futures_price': futures_price,
            'expiry': selected_expiry, 'days_to_expiry': days_to_expiry,
            'atm_strike': atm_strike, 'atm_call_premium': atm_call_premium,
            'atm_put_premium': atm_put_premium, 'atm_straddle': atm_call_premium + atm_put_premium,
            'expiry_list': expiry_list, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return df, meta

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_metrics(df: pd.DataFrame, futures_price: float) -> Dict:
    df_unique = df.drop_duplicates(subset=['Strike']).sort_values('Strike').reset_index(drop=True)
    
    positive_gex_df = df_unique[df_unique['Net_GEX'] > 0].copy()
    if len(positive_gex_df) > 0:
        positive_gex_df['Distance'] = abs(positive_gex_df['Strike'] - futures_price)
        positive_gex_df = positive_gex_df.nsmallest(5, 'Distance')
    
    negative_gex_df = df_unique[df_unique['Net_GEX'] < 0].copy()
    if len(negative_gex_df) > 0:
        negative_gex_df['Distance'] = abs(negative_gex_df['Strike'] - futures_price)
        negative_gex_df = negative_gex_df.nsmallest(5, 'Distance')
    
    gex_near_total = (positive_gex_df['Net_GEX'].sum() if len(positive_gex_df) > 0 else 0) + \
                     (negative_gex_df['Net_GEX'].sum() if len(negative_gex_df) > 0 else 0)
    gex_total = df_unique['Net_GEX'].sum()
    
    above_futures = df_unique[df_unique['Strike'] > futures_price].head(5)
    below_futures = df_unique[df_unique['Strike'] < futures_price].tail(5)
    dex_near_total = (above_futures['Net_DEX'].sum() if len(above_futures) > 0 else 0) + \
                     (below_futures['Net_DEX'].sum() if len(below_futures) > 0 else 0)
    dex_total = df_unique['Net_DEX'].sum()
    
    vanna_total = df_unique['Net_Vanna'].sum()
    charm_total = df_unique['Net_Charm'].sum()
    flow_gex_total = df_unique['Net_Flow_GEX'].sum()
    flow_dex_total = df_unique['Net_Flow_DEX'].sum()
    
    total_put_oi = df_unique['Put_OI'].sum()
    total_call_oi = df_unique['Call_OI'].sum()
    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
    
    max_call_oi_strike = df_unique.loc[df_unique['Call_OI'].idxmax(), 'Strike']
    max_put_oi_strike = df_unique.loc[df_unique['Put_OI'].idxmax(), 'Strike']
    max_gex_strike = df_unique.loc[df_unique['Net_GEX'].idxmax(), 'Strike']
    min_gex_strike = df_unique.loc[df_unique['Net_GEX'].idxmin(), 'Strike']
    
    def get_gex_bias(v):
        if v > 50: return "🟢 STRONG SUPPRESSION", "green"
        elif v > 0: return "🟢 SUPPRESSION", "lightgreen"
        elif v < -50: return "🔴 HIGH AMPLIFICATION", "red"
        elif v < 0: return "🔴 AMPLIFICATION", "lightcoral"
        return "⚖️ NEUTRAL", "orange"
    
    def get_dex_bias(v):
        if v > 50: return "🟢 BULLISH", "green"
        elif v < -50: return "🔴 BEARISH", "red"
        elif v > 0: return "🟢 Mild Bullish", "lightgreen"
        elif v < 0: return "🔴 Mild Bearish", "lightcoral"
        return "⚖️ NEUTRAL", "orange"
    
    gex_bias, gex_color = get_gex_bias(gex_near_total)
    dex_bias, dex_color = get_dex_bias(dex_near_total)
    combined_signal = (gex_near_total + dex_near_total) / 2
    combined_bias, combined_color = get_gex_bias(combined_signal)
    
    return {
        'gex_near_total': gex_near_total, 'gex_total': gex_total,
        'gex_bias': gex_bias, 'gex_color': gex_color,
        'dex_near_total': dex_near_total, 'dex_total': dex_total,
        'dex_bias': dex_bias, 'dex_color': dex_color,
        'vanna_total': vanna_total, 'charm_total': charm_total,
        'flow_gex_total': flow_gex_total, 'flow_dex_total': flow_dex_total,
        'pcr': pcr, 'total_call_oi': total_call_oi, 'total_put_oi': total_put_oi,
        'max_call_oi_strike': max_call_oi_strike, 'max_put_oi_strike': max_put_oi_strike,
        'max_gex_strike': max_gex_strike, 'min_gex_strike': min_gex_strike,
        'combined_signal': combined_signal, 'combined_bias': combined_bias, 'combined_color': combined_color,
    }

def detect_gamma_flips(df: pd.DataFrame) -> List[Dict]:
    gamma_flips = []
    df_sorted = df.sort_values('Strike').reset_index(drop=True)
    
    for i in range(len(df_sorted) - 1):
        current_gex = df_sorted.iloc[i]['Net_GEX']
        next_gex = df_sorted.iloc[i + 1]['Net_GEX']
        
        if (current_gex > 0 and next_gex < 0) or (current_gex < 0 and next_gex > 0):
            lower = df_sorted.iloc[i]['Strike']
            upper = df_sorted.iloc[i + 1]['Strike']
            weight = abs(current_gex) / (abs(current_gex) + abs(next_gex)) if (abs(current_gex) + abs(next_gex)) > 0 else 0.5
            flip_strike = lower + (upper - lower) * weight
            
            gamma_flips.append({
                'flip_strike': flip_strike, 'lower_strike': lower, 'upper_strike': upper,
                'flip_type': "Positive → Negative" if current_gex > 0 else "Negative → Positive",
                'impact': "Resistance" if current_gex > 0 else "Support"
            })
    
    return gamma_flips

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_gex_chart(df: pd.DataFrame, futures_price: float, title_suffix: str = "") -> go.Figure:
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df['Net_GEX']]
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_GEX'], orientation='h',
        marker_color=colors, name='Net GEX',
        hovertemplate='Strike: %{y}<br>Net GEX: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Futures: {futures_price:,.2f}")
    
    fig.update_layout(
        title=dict(text=f"<b>Net GEX Profile {title_suffix}</b>", font=dict(size=14, color='white')),
        xaxis_title="GEX (₹ Billions)", yaxis_title="Strike",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=450, margin=dict(l=60, r=20, t=50, b=40)
    )
    return fig

def create_dex_chart(df: pd.DataFrame, futures_price: float, title_suffix: str = "") -> go.Figure:
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df['Net_DEX']]
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_DEX'], orientation='h',
        marker_color=colors, name='Net DEX',
        hovertemplate='Strike: %{y}<br>Net DEX: %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=3)
    
    fig.update_layout(
        title=dict(text=f"<b>Net DEX Profile {title_suffix}</b>", font=dict(size=14, color='white')),
        xaxis_title="DEX (₹ Billions)", yaxis_title="Strike",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=450, margin=dict(l=60, r=20, t=50, b=40)
    )
    return fig

def create_timeline_chart(snapshots_data: List[Dict]) -> go.Figure:
    if not snapshots_data:
        return go.Figure()
    
    times = [s['time'] for s in snapshots_data]
    gex_values = [s['gex'] for s in snapshots_data]
    dex_values = [s['dex'] for s in snapshots_data]
    prices = [s['price'] for s in snapshots_data]
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                       subplot_titles=("GEX & DEX Evolution", "Price Movement"))
    
    fig.add_trace(go.Scatter(
        x=times, y=gex_values, name='Net GEX',
        line=dict(color='#8b5cf6', width=3),
        fill='tozeroy', fillcolor='rgba(139, 92, 246, 0.2)'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=times, y=dex_values, name='Net DEX',
        line=dict(color='#06b6d4', width=3),
        fill='tozeroy', fillcolor='rgba(6, 182, 212, 0.2)'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=times, y=prices, name='Futures Price',
        line=dict(color='#f59e0b', width=3),
        fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.2)'
    ), row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=60, r=20, t=80, b=40)
    )
    
    return fig

def create_comparison_chart(df1: pd.DataFrame, df2: pd.DataFrame, 
                           meta1: Dict, meta2: Dict, metric: str = 'Net_GEX') -> go.Figure:
    fig = go.Figure()
    
    # First snapshot
    colors1 = ['rgba(139, 92, 246, 0.7)' if x > 0 else 'rgba(239, 68, 68, 0.7)' for x in df1[metric]]
    fig.add_trace(go.Bar(
        y=df1['Strike'], x=df1[metric], orientation='h',
        marker_color=colors1, name=f"T1: {meta1.get('timestamp', '')[:16]}",
        opacity=0.7
    ))
    
    # Second snapshot
    colors2 = ['rgba(16, 185, 129, 0.9)' if x > 0 else 'rgba(236, 72, 153, 0.9)' for x in df2[metric]]
    fig.add_trace(go.Bar(
        y=df2['Strike'], x=df2[metric], orientation='h',
        marker_color=colors2, name=f"T2: {meta2.get('timestamp', '')[:16]}",
        opacity=0.9
    ))
    
    fig.add_hline(y=meta1['futures_price'], line_dash="dash", line_color="#8b5cf6", 
                  line_width=2, annotation_text=f"T1: {meta1['futures_price']:,.0f}")
    fig.add_hline(y=meta2['futures_price'], line_dash="dot", line_color="#10b981",
                  line_width=2, annotation_text=f"T2: {meta2['futures_price']:,.0f}")
    
    fig.update_layout(
        title=dict(text=f"<b>{metric} Comparison</b>", font=dict(size=16, color='white')),
        xaxis_title=f"{metric} (₹ Billions)", yaxis_title="Strike",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=550,
        barmode='group', legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    return fig

def create_heatmap_evolution(snapshots_data: List[Tuple[pd.DataFrame, Dict, datetime]], 
                            metric: str = 'Net_GEX') -> go.Figure:
    if len(snapshots_data) < 2:
        return go.Figure()
    
    # Get common strikes
    all_strikes = set()
    for df, _, _ in snapshots_data:
        all_strikes.update(df['Strike'].tolist())
    strikes = sorted(list(all_strikes))
    
    # Build matrix
    times = []
    matrix = []
    
    for df, meta, ts in snapshots_data:
        times.append(ts.strftime('%H:%M'))
        row = []
        df_indexed = df.set_index('Strike')
        for strike in strikes:
            if strike in df_indexed.index:
                row.append(df_indexed.loc[strike, metric])
            else:
                row.append(0)
        matrix.append(row)
    
    matrix = np.array(matrix).T  # Transpose for strikes on y-axis
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=times,
        y=strikes,
        colorscale='RdYlGn',
        zmid=0,
        colorbar=dict(title=metric)
    ))
    
    fig.update_layout(
        title=dict(text=f"<b>{metric} Evolution Heatmap</b>", font=dict(size=16, color='white')),
        xaxis_title="Time", yaxis_title="Strike",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.8)', height=500
    )
    
    return fig

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize
    if 'history_manager' not in st.session_state:
        st.session_state.history_manager = HistoricalDataManager()
    if 'current_snapshot_idx' not in st.session_state:
        st.session_state.current_snapshot_idx = 0
    if 'playback_running' not in st.session_state:
        st.session_state.playback_running = False
    if 'selected_snapshots' not in st.session_state:
        st.session_state.selected_snapshots = []
    
    history_manager = st.session_state.history_manager
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="main-title">⏰ NYZTrade Time Machine</h1>
                <p class="sub-title">Historical GEX/DEX Analysis | Travel Through Market Data</p>
            </div>
            <div class="history-badge">
                <span>📚 Historical Mode</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        symbol = st.selectbox("📈 Select Index", options=list(DHAN_SECURITY_IDS.keys()), index=0)
        strikes_range = st.slider("📏 Strikes Range", min_value=5, max_value=20, value=12)
        expiry_index = st.number_input("📅 Expiry Index", min_value=0, max_value=5, value=0)
        
        st.markdown("---")
        st.markdown("### 📸 Snapshot Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📷 Capture Now", use_container_width=True):
                with st.spinner("Capturing snapshot..."):
                    fetcher = DhanAPIFetcher(DhanConfig())
                    df, meta = fetcher.process_option_chain(symbol, expiry_index, strikes_range)
                    if df is not None:
                        filename = history_manager.save_snapshot(symbol, df, meta)
                        st.success(f"✅ Saved!")
                    else:
                        st.error("❌ Failed to capture")
        
        with col2:
            auto_capture = st.checkbox("🔄 Auto", value=False)
        
        if auto_capture:
            capture_interval = st.slider("Interval (min)", 1, 30, 5)
            st.info(f"Auto-capture every {capture_interval} min")
        
        st.markdown("---")
        st.markdown("### 📅 Select Date")
        
        available_dates = history_manager.get_available_dates(symbol)
        
        if available_dates:
            # Add today's date option
            today = datetime.now().date()
            date_options = [today] + [d for d in available_dates if d != today]
            date_labels = ["Today" if d == today else d.strftime("%Y-%m-%d") for d in date_options]
            
            selected_date_idx = st.selectbox(
                "Choose Date",
                range(len(date_options)),
                format_func=lambda x: date_labels[x]
            )
            selected_date = datetime.combine(date_options[selected_date_idx], dt_time())
        else:
            selected_date = datetime.now()
            st.info("No historical data yet. Capture some snapshots!")
        
        st.markdown("---")
        st.markdown("### 🔑 API Status")
        config = DhanConfig()
        try:
            expiry_time = datetime.strptime(config.expiry_time, "%Y-%m-%dT%H:%M:%S")
            remaining = expiry_time - datetime.now()
            if remaining.total_seconds() > 0:
                st.success(f"✅ Valid: {remaining.days}d {remaining.seconds//3600}h")
            else:
                st.error("❌ Token Expired")
        except:
            st.warning("⚠️ Unknown")
    
    # Get snapshots for selected date
    snapshots = history_manager.get_available_snapshots(symbol, selected_date)
    
    # Main Time Machine Interface
    st.markdown("""
    <div class="time-machine-container">
        <h3 style="text-align: center; color: #8b5cf6; font-family: 'Space Grotesk', sans-serif; margin-bottom: 10px;">
            🕰️ TIME MACHINE CONTROLS
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if snapshots:
        # Time slider
        st.markdown(f"**📊 {len(snapshots)} snapshots available for {selected_date.strftime('%Y-%m-%d')}**")
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.markdown(f"**Start:** {snapshots[0]['time_str']}")
        
        with col2:
            snapshot_idx = st.slider(
                "🎚️ Drag to travel through time",
                min_value=0,
                max_value=len(snapshots) - 1,
                value=st.session_state.current_snapshot_idx,
                format="",
                key="time_slider"
            )
            st.session_state.current_snapshot_idx = snapshot_idx
        
        with col3:
            st.markdown(f"**End:** {snapshots[-1]['time_str']}")
        
        # Current time display
        current_snapshot = snapshots[snapshot_idx]
        
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <div class="date-display">{current_snapshot['date_str']}</div>
            <div class="time-display">{current_snapshot['time_str']}</div>
            <div class="timeline-marker">Snapshot {snapshot_idx + 1} of {len(snapshots)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Playback controls
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⏮️ First", use_container_width=True):
                st.session_state.current_snapshot_idx = 0
                st.rerun()
        
        with col2:
            if st.button("◀️ Prev", use_container_width=True):
                if st.session_state.current_snapshot_idx > 0:
                    st.session_state.current_snapshot_idx -= 1
                    st.rerun()
        
        with col3:
            if st.button("▶️ Play" if not st.session_state.playback_running else "⏸️ Pause", use_container_width=True):
                st.session_state.playback_running = not st.session_state.playback_running
        
        with col4:
            if st.button("▶️ Next", use_container_width=True):
                if st.session_state.current_snapshot_idx < len(snapshots) - 1:
                    st.session_state.current_snapshot_idx += 1
                    st.rerun()
        
        with col5:
            if st.button("⏭️ Last", use_container_width=True):
                st.session_state.current_snapshot_idx = len(snapshots) - 1
                st.rerun()
        
        # Load current snapshot data
        df, meta, timestamp = history_manager.load_snapshot(current_snapshot['filename'])
        metrics = calculate_metrics(df, meta['futures_price'])
        gamma_flips = detect_gamma_flips(df)
        
        # Display metrics
        st.markdown("---")
        st.markdown("### 📊 Snapshot Data")
        
        cols = st.columns(6)
        
        with cols[0]:
            st.markdown(f"""<div class="metric-card info"><div class="metric-label">Spot Price</div>
                <div class="metric-value">₹{meta['spot_price']:,.2f}</div></div>""", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"""<div class="metric-card info"><div class="metric-label">Futures</div>
                <div class="metric-value">₹{meta['futures_price']:,.2f}</div></div>""", unsafe_allow_html=True)
        with cols[2]:
            gex_class = "positive" if metrics['gex_near_total'] > 0 else "negative"
            st.markdown(f"""<div class="metric-card {gex_class}"><div class="metric-label">Net GEX</div>
                <div class="metric-value {gex_class}">{metrics['gex_near_total']:.4f}B</div></div>""", unsafe_allow_html=True)
        with cols[3]:
            dex_class = "positive" if metrics['dex_near_total'] > 0 else "negative"
            st.markdown(f"""<div class="metric-card {dex_class}"><div class="metric-label">Net DEX</div>
                <div class="metric-value {dex_class}">{metrics['dex_near_total']:.4f}B</div></div>""", unsafe_allow_html=True)
        with cols[4]:
            pcr_class = "positive" if metrics['pcr'] > 1 else "negative"
            st.markdown(f"""<div class="metric-card {pcr_class}"><div class="metric-label">PCR</div>
                <div class="metric-value {pcr_class}">{metrics['pcr']:.2f}</div></div>""", unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f"""<div class="metric-card neutral"><div class="metric-label">ATM Straddle</div>
                <div class="metric-value">₹{meta['atm_straddle']:.2f}</div></div>""", unsafe_allow_html=True)
        
        # Tabs for different views
        tabs = st.tabs(["📊 GEX/DEX Charts", "🔄 Compare Snapshots", "📈 Timeline Evolution", "🗺️ Heatmap", "📋 Data"])
        
        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_gex_chart(df, meta['futures_price'], f"@ {current_snapshot['time_str']}"), 
                               use_container_width=True)
            with col2:
                st.plotly_chart(create_dex_chart(df, meta['futures_price'], f"@ {current_snapshot['time_str']}"), 
                               use_container_width=True)
            
            # Gamma flips
            if gamma_flips:
                st.markdown("### 🔄 Gamma Flip Zones")
                for i, flip in enumerate(gamma_flips, 1):
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.1); border: 1px dashed #f59e0b; 
                                border-radius: 10px; padding: 12px; margin: 8px 0;">
                        <span style="color: #f59e0b; font-weight: 600;">Zone #{i}:</span> 
                        {flip['flip_strike']:,.2f} ({flip['flip_type']}) - {flip['impact']}
                    </div>
                    """, unsafe_allow_html=True)
        
        with tabs[1]:
            st.markdown("### 🔄 Compare Two Points in Time")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📍 First Point (T1)**")
                t1_idx = st.selectbox(
                    "Select T1",
                    range(len(snapshots)),
                    format_func=lambda x: snapshots[x]['time_str'],
                    key="t1_select"
                )
            
            with col2:
                st.markdown("**📍 Second Point (T2)**")
                t2_idx = st.selectbox(
                    "Select T2",
                    range(len(snapshots)),
                    index=min(len(snapshots)-1, t1_idx + 1),
                    format_func=lambda x: snapshots[x]['time_str'],
                    key="t2_select"
                )
            
            if t1_idx != t2_idx:
                df1, meta1, ts1 = history_manager.load_snapshot(snapshots[t1_idx]['filename'])
                df2, meta2, ts2 = history_manager.load_snapshot(snapshots[t2_idx]['filename'])
                
                metrics1 = calculate_metrics(df1, meta1['futures_price'])
                metrics2 = calculate_metrics(df2, meta2['futures_price'])
                
                # Change summary
                st.markdown("### 📊 Changes Summary")
                
                cols = st.columns(4)
                changes = [
                    ("Price", meta2['futures_price'] - meta1['futures_price'], meta1['futures_price']),
                    ("GEX", metrics2['gex_near_total'] - metrics1['gex_near_total'], metrics1['gex_near_total']),
                    ("DEX", metrics2['dex_near_total'] - metrics1['dex_near_total'], metrics1['dex_near_total']),
                    ("PCR", metrics2['pcr'] - metrics1['pcr'], metrics1['pcr']),
                ]
                
                for col, (name, change, base) in zip(cols, changes):
                    with col:
                        pct = (change / base * 100) if base != 0 else 0
                        indicator_class = "up" if change > 0 else "down"
                        arrow = "↑" if change > 0 else "↓"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{name} Change</div>
                            <div class="metric-value">{change:+.4f}</div>
                            <div class="change-indicator {indicator_class}">{arrow} {abs(pct):.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Comparison charts
                metric_to_compare = st.selectbox("Select metric to compare", 
                                                ["Net_GEX", "Net_DEX", "Net_Vanna", "Hedging_Pressure"])
                
                st.plotly_chart(create_comparison_chart(df1, df2, meta1, meta2, metric_to_compare), 
                               use_container_width=True)
        
        with tabs[2]:
            st.markdown("### 📈 Timeline Evolution")
            
            # Load all snapshots for timeline
            timeline_data = []
            for snap in snapshots:
                try:
                    df_snap, meta_snap, ts_snap = history_manager.load_snapshot(snap['filename'])
                    metrics_snap = calculate_metrics(df_snap, meta_snap['futures_price'])
                    timeline_data.append({
                        'time': ts_snap,
                        'gex': metrics_snap['gex_near_total'],
                        'dex': metrics_snap['dex_near_total'],
                        'price': meta_snap['futures_price'],
                        'pcr': metrics_snap['pcr']
                    })
                except:
                    continue
            
            if timeline_data:
                st.plotly_chart(create_timeline_chart(timeline_data), use_container_width=True)
                
                # Additional timeline metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### GEX Range")
                    gex_values = [d['gex'] for d in timeline_data]
                    st.markdown(f"**Max:** {max(gex_values):.4f}B")
                    st.markdown(f"**Min:** {min(gex_values):.4f}B")
                    st.markdown(f"**Range:** {max(gex_values) - min(gex_values):.4f}B")
                
                with col2:
                    st.markdown("#### Price Range")
                    price_values = [d['price'] for d in timeline_data]
                    st.markdown(f"**High:** ₹{max(price_values):,.2f}")
                    st.markdown(f"**Low:** ₹{min(price_values):,.2f}")
                    st.markdown(f"**Range:** ₹{max(price_values) - min(price_values):,.2f}")
        
        with tabs[3]:
            st.markdown("### 🗺️ GEX Evolution Heatmap")
            
            # Load snapshots for heatmap
            heatmap_data = []
            for snap in snapshots[::max(1, len(snapshots)//20)]:  # Sample max 20 points
                try:
                    df_snap, meta_snap, ts_snap = history_manager.load_snapshot(snap['filename'])
                    heatmap_data.append((df_snap, meta_snap, ts_snap))
                except:
                    continue
            
            if len(heatmap_data) >= 2:
                metric_for_heatmap = st.selectbox("Select metric", 
                                                 ["Net_GEX", "Net_DEX", "Hedging_Pressure"],
                                                 key="heatmap_metric")
                st.plotly_chart(create_heatmap_evolution(heatmap_data, metric_for_heatmap), 
                               use_container_width=True)
            else:
                st.info("Need at least 2 snapshots for heatmap")
        
        with tabs[4]:
            st.markdown("### 📋 Snapshot Data")
            
            display_cols = ['Strike', 'Call_OI', 'Put_OI', 'Call_IV', 'Put_IV', 
                           'Net_GEX', 'Net_DEX', 'Net_Vanna', 'Hedging_Pressure']
            display_df = df[display_cols].copy()
            display_df['Net_GEX'] = display_df['Net_GEX'].apply(lambda x: f"{x:.4f}B")
            display_df['Net_DEX'] = display_df['Net_DEX'].apply(lambda x: f"{x:.4f}B")
            display_df['Net_Vanna'] = display_df['Net_Vanna'].apply(lambda x: f"{x:.4f}B")
            display_df['Hedging_Pressure'] = display_df['Hedging_Pressure'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
            
            # Export
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Snapshot Data",
                data=csv,
                file_name=f"NYZTrade_{symbol}_{current_snapshot['datetime'].strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px; background: rgba(139, 92, 246, 0.1); 
                    border-radius: 20px; margin: 40px 0;">
            <h2 style="color: #8b5cf6;">📸 No Snapshots Yet</h2>
            <p style="color: #94a3b8;">Start capturing snapshots to build your historical database.</p>
            <p style="color: #64748b;">Use the "Capture Now" button in the sidebar to save the current market state.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Offer to capture current data
        if st.button("📷 Capture Current Snapshot", use_container_width=True):
            with st.spinner("Fetching and saving data..."):
                fetcher = DhanAPIFetcher(DhanConfig())
                df, meta = fetcher.process_option_chain(symbol, expiry_index, strikes_range)
                if df is not None:
                    filename = history_manager.save_snapshot(symbol, df, meta)
                    st.success("✅ Snapshot captured! Refresh to see the data.")
                    st.rerun()
                else:
                    st.error("❌ Failed to fetch data")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; color: #64748b;">
        <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
        NYZTrade Time Machine | Historical GEX/DEX Analysis<br>
        Symbol: {symbol} | Data Directory: {DATA_DIR}
        </p>
        <p style="font-size: 0.75rem;">⚠️ Educational purposes only. Past performance doesn't indicate future results.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh for playback
    if st.session_state.playback_running and snapshots:
        time.sleep(1)
        if st.session_state.current_snapshot_idx < len(snapshots) - 1:
            st.session_state.current_snapshot_idx += 1
        else:
            st.session_state.playback_running = False
        st.rerun()

if __name__ == "__main__":
    main()
