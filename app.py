# ============================================================================
# NYZTrade Professional GEX/DEX Dashboard Pro - Complete Implementation
# Real-time Options Greeks Analysis with Time Machine
# Created by: Dr NIYAS | NYZTrade
# Version: 2.0.0
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
import time
import json
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="NYZTrade GEX/DEX Dashboard Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Professional Dark Theme CSS
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
        --accent-orange: #fb923c;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --border-color: #2d3748;
        --glow-green: rgba(16, 185, 129, 0.3);
        --glow-red: rgba(239, 68, 68, 0.3);
        --glow-blue: rgba(59, 130, 246, 0.3);
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 50%, var(--bg-primary) 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.15) 50%, rgba(6, 182, 212, 0.15) 100%);
        border: 2px solid var(--border-color);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 28px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        animation: gradient-shift 5s ease infinite;
        background-size: 200% 200%;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .sub-title {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin-top: 8px;
        letter-spacing: 0.05em;
    }
    
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--accent-blue), transparent);
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .metric-card:hover {
        background: var(--bg-card-hover);
        transform: translateY(-4px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.4);
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-card.positive { 
        border-left: 4px solid var(--accent-green);
        box-shadow: 0 4px 15px var(--glow-green);
    }
    .metric-card.negative { 
        border-left: 4px solid var(--accent-red);
        box-shadow: 0 4px 15px var(--glow-red);
    }
    .metric-card.neutral { 
        border-left: 4px solid var(--accent-yellow);
    }
    
    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value.positive { 
        color: var(--accent-green);
        text-shadow: 0 0 10px var(--glow-green);
    }
    .metric-value.negative { 
        color: var(--accent-red);
        text-shadow: 0 0 10px var(--glow-red);
    }
    .metric-value.neutral { color: var(--accent-yellow); }
    
    .metric-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        margin-top: 10px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 20px;
        border-radius: 24px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s;
        cursor: default;
    }
    
    .signal-badge:hover {
        transform: scale(1.05);
    }
    
    .signal-badge.bullish {
        background: rgba(16, 185, 129, 0.2);
        color: var(--accent-green);
        border: 1px solid rgba(16, 185, 129, 0.4);
        box-shadow: 0 4px 15px var(--glow-green);
    }
    
    .signal-badge.bearish {
        background: rgba(239, 68, 68, 0.2);
        color: var(--accent-red);
        border: 1px solid rgba(239, 68, 68, 0.4);
        box-shadow: 0 4px 15px var(--glow-red);
    }
    
    .signal-badge.volatile {
        background: rgba(245, 158, 11, 0.2);
        color: var(--accent-yellow);
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 18px;
        background: rgba(239, 68, 68, 0.15);
        border: 2px solid rgba(239, 68, 68, 0.4);
        border-radius: 24px;
        animation: pulse-live 2.5s infinite;
        backdrop-filter: blur(10px);
    }
    
    .live-dot {
        width: 10px;
        height: 10px;
        background: var(--accent-red);
        border-radius: 50%;
        animation: blink 1.5s infinite;
        box-shadow: 0 0 10px var(--accent-red);
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; transform: scale(1); }
        51%, 100% { opacity: 0.4; transform: scale(0.8); }
    }
    
    @keyframes pulse-live {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
            border-color: rgba(239, 68, 68, 0.4);
        }
        50% { 
            box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
            border-color: rgba(239, 68, 68, 0.8);
        }
    }
    
    .countdown-container {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(59, 130, 246, 0.05) 100%);
        border: 2px solid var(--border-color);
        border-radius: 16px;
        padding: 20px 28px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .countdown-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue), var(--accent-purple));
        animation: progress-bar 3s linear infinite;
    }
    
    @keyframes progress-bar {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .countdown-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-shadow: 0 0 15px rgba(6, 182, 212, 0.5);
        letter-spacing: 0.05em;
    }
    
    .countdown-label {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-muted);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    .strategy-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(59, 130, 246, 0.03) 100%);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 22px;
        margin: 14px 0;
        transition: all 0.3s;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
    }
    
    .strategy-card:hover {
        transform: translateX(4px);
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
    }
    
    .strategy-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--accent-cyan);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .strategy-detail {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        color: var(--text-secondary);
        line-height: 1.7;
    }
    
    .gamma-flip-zone {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.15), rgba(239, 68, 68, 0.15));
        border: 2px dashed var(--accent-yellow);
        border-radius: 14px;
        padding: 18px;
        margin: 14px 0;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2);
    }
    
    .flip-label {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--accent-yellow);
    }
    
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 24px 0 16px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--border-color);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .time-machine-control {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(139, 92, 246, 0.05) 100%);
        border: 2px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stSlider > div > div > div > div {
        background: var(--accent-purple);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: var(--bg-card);
        padding: 10px;
        border-radius: 14px;
        border: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: var(--text-secondary);
        font-family: 'Space Grotesk', sans-serif;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        color: white;
        box-shadow: 0 4px 15px var(--glow-blue);
    }
    
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
    }
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
    def calculate_vega(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            return S * norm.pdf(d1) * np.sqrt(T) / 100
        except:
            return 0
    
    @staticmethod
    def calculate_theta_call(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            term1 = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
            term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
            return (term1 + term2) / 365
        except:
            return 0
    
    @staticmethod
    def calculate_vanna(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0
        try:
            d1 = BlackScholesCalculator.calculate_d1(S, K, T, r, sigma)
            d2 = BlackScholesCalculator.calculate_d2(S, K, T, r, sigma)
            vanna = -norm.pdf(d1) * d2 / sigma
            return vanna
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
# DHAN API DATA FETCHER
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
        """Fetch expiry list from Dhan API"""
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
        except Exception as e:
            st.error(f"Error fetching expiry list: {str(e)}")
            return []
    
    def fetch_option_chain(self, symbol: str, expiry_date: str = None) -> Optional[Dict]:
        """Fetch option chain data from Dhan API"""
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
        except Exception as e:
            st.error(f"Error fetching option chain: {str(e)}")
            return None
    
    def get_futures_price(self, symbol: str, expiry_date: str) -> Optional[float]:
        """Fetch actual futures price from Dhan API - NOT using parity method"""
        try:
            # Try to get futures data from option chain first
            oc_data = self.fetch_option_chain(symbol, expiry_date)
            if oc_data and 'futures_price' in oc_data:
                return oc_data.get('futures_price')
            
            # If not available, use last_price as proxy (spot)
            if oc_data and 'last_price' in oc_data:
                return oc_data.get('last_price')
            
            return None
        except Exception as e:
            st.warning(f"Could not fetch futures price: {str(e)}")
            return None
    
    def process_option_chain(self, symbol: str, expiry_index: int = 0, strikes_range: int = 12):
        """Process option chain data with enhanced futures handling"""
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
        
        # Get actual futures price from Dhan API
        futures_price = self.get_futures_price(symbol, selected_expiry)
        
        # Fallback to spot if futures not available
        if futures_price is None or futures_price == 0:
            futures_price = spot_price
            futures_source = "Spot (Fallback)"
        else:
            futures_source = "Dhan API"
        
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
            'futures_source': futures_source,
            'expiry': selected_expiry, 'days_to_expiry': days_to_expiry,
            'atm_strike': atm_strike, 'atm_call_premium': atm_call_premium,
            'atm_put_premium': atm_put_premium, 'atm_straddle': atm_call_premium + atm_put_premium,
            'expiry_list': expiry_list, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return df, meta


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_flow_metrics(df: pd.DataFrame, futures_price: float) -> Dict:
    """Calculate comprehensive flow metrics"""
    df_unique = df.drop_duplicates(subset=['Strike']).sort_values('Strike').reset_index(drop=True)
    
    positive_gex_df = df_unique[df_unique['Net_GEX'] > 0].copy()
    positive_gex_df['Distance'] = abs(positive_gex_df['Strike'] - futures_price)
    positive_gex_df = positive_gex_df.nsmallest(5, 'Distance')
    
    negative_gex_df = df_unique[df_unique['Net_GEX'] < 0].copy()
    negative_gex_df['Distance'] = abs(negative_gex_df['Strike'] - futures_price)
    negative_gex_df = negative_gex_df.nsmallest(5, 'Distance')
    
    gex_near_positive = positive_gex_df['Net_GEX'].sum() if len(positive_gex_df) > 0 else 0
    gex_near_negative = negative_gex_df['Net_GEX'].sum() if len(negative_gex_df) > 0 else 0
    gex_near_total = gex_near_positive + gex_near_negative
    gex_total_all = df_unique['Net_GEX'].sum()
    
    above_futures = df_unique[df_unique['Strike'] > futures_price].head(5)
    below_futures = df_unique[df_unique['Strike'] < futures_price].tail(5)
    
    dex_near_above = above_futures['Net_DEX'].sum() if len(above_futures) > 0 else 0
    dex_near_below = below_futures['Net_DEX'].sum() if len(below_futures) > 0 else 0
    dex_near_total = dex_near_above + dex_near_below
    dex_total_all = df_unique['Net_DEX'].sum()
    
    vanna_total = df_unique['Net_Vanna'].sum()
    charm_total = df_unique['Net_Charm'].sum()
    flow_gex_total = df_unique['Net_Flow_GEX'].sum()
    flow_dex_total = df_unique['Net_Flow_DEX'].sum()
    
    def get_gex_bias(v):
        if v > 50: return "🟢 STRONG SUPPRESSION", "green", "Bullish - Low Vol Expected"
        elif v > 0: return "🟢 SUPPRESSION", "lightgreen", "Mild Bullish"
        elif v < -50: return "🔴 HIGH AMPLIFICATION", "red", "High Volatility Expected"
        elif v < 0: return "🔴 AMPLIFICATION", "lightcoral", "Volatile"
        return "⚖️ NEUTRAL", "orange", "Balanced"
    
    def get_dex_bias(v):
        if v > 50: return "🟢 BULLISH", "green", "Strong Upward Pressure"
        elif v < -50: return "🔴 BEARISH", "red", "Strong Downward Pressure"
        elif v > 0: return "🟢 Mild Bullish", "lightgreen", "Slight Upward Bias"
        elif v < 0: return "🔴 Mild Bearish", "lightcoral", "Slight Downward Bias"
        return "⚖️ NEUTRAL", "orange", "No Clear Direction"
    
    gex_bias, gex_color, gex_desc = get_gex_bias(gex_near_total)
    dex_bias, dex_color, dex_desc = get_dex_bias(dex_near_total)
    combined_signal = (gex_near_total + dex_near_total) / 2
    combined_bias, combined_color, combined_desc = get_gex_bias(combined_signal)
    
    return {
        'gex_near_positive': gex_near_positive, 'gex_near_negative': gex_near_negative,
        'gex_near_total': gex_near_total, 'gex_total': gex_total_all,
        'gex_bias': gex_bias, 'gex_color': gex_color, 'gex_desc': gex_desc,
        'dex_near_above': dex_near_above, 'dex_near_below': dex_near_below,
        'dex_near_total': dex_near_total, 'dex_total': dex_total_all,
        'dex_bias': dex_bias, 'dex_color': dex_color, 'dex_desc': dex_desc,
        'vanna_total': vanna_total, 'charm_total': charm_total,
        'flow_gex_total': flow_gex_total, 'flow_dex_total': flow_dex_total,
        'combined_signal': combined_signal, 'combined_bias': combined_bias,
        'combined_color': combined_color, 'combined_desc': combined_desc,
    }

def detect_gamma_flip_zones(df: pd.DataFrame) -> List[Dict]:
    """Detect gamma flip zones where GEX changes sign"""
    gamma_flip_zones = []
    df_sorted = df.sort_values('Strike').reset_index(drop=True)
    
    for i in range(len(df_sorted) - 1):
        current_gex = df_sorted.iloc[i]['Net_GEX']
        next_gex = df_sorted.iloc[i + 1]['Net_GEX']
        
        if (current_gex > 0 and next_gex < 0) or (current_gex < 0 and next_gex > 0):
            lower = df_sorted.iloc[i]['Strike']
            upper = df_sorted.iloc[i + 1]['Strike']
            weight = abs(current_gex) / (abs(current_gex) + abs(next_gex)) if (abs(current_gex) + abs(next_gex)) > 0 else 0.5
            flip_strike = lower + (upper - lower) * weight
            
            gamma_flip_zones.append({
                'flip_strike': flip_strike, 'lower_strike': lower, 'upper_strike': upper,
                'flip_type': "Positive → Negative" if current_gex > 0 else "Negative → Positive",
                'lower_gex': current_gex, 'upper_gex': next_gex,
                'impact': "Resistance" if current_gex > 0 else "Support"
            })
    
    return gamma_flip_zones

def calculate_key_levels(df: pd.DataFrame, futures_price: float) -> Dict:
    """Calculate key price levels and metrics"""
    df_sorted = df.sort_values('Strike').reset_index(drop=True)
    max_pain_strike = df_sorted.loc[df_sorted['Call_OI'].idxmax(), 'Strike']
    highest_call_oi_strike = df_sorted.loc[df_sorted['Call_OI'].idxmax(), 'Strike']
    highest_put_oi_strike = df_sorted.loc[df_sorted['Put_OI'].idxmax(), 'Strike']
    max_positive_gex_strike = df_sorted.loc[df_sorted['Net_GEX'].idxmax(), 'Strike']
    max_negative_gex_strike = df_sorted.loc[df_sorted['Net_GEX'].idxmin(), 'Strike']
    
    total_put_oi = df_sorted['Put_OI'].sum()
    total_call_oi = df_sorted['Call_OI'].sum()
    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1
    
    return {
        'max_pain': max_pain_strike, 'highest_call_oi': highest_call_oi_strike,
        'highest_put_oi': highest_put_oi_strike, 'max_positive_gex': max_positive_gex_strike,
        'max_negative_gex': max_negative_gex_strike, 'pcr': pcr,
        'total_call_oi': total_call_oi, 'total_put_oi': total_put_oi,
    }

def simulate_time_decay(df: pd.DataFrame, meta: Dict, hours_forward: float):
    """Simulate time decay effects on Greeks"""
    df_sim = df.copy()
    current_days = meta['days_to_expiry']
    new_days = max(current_days - (hours_forward / 24), 0.1)
    time_factor = new_days / current_days if current_days > 0 else 1
    gamma_decay = np.sqrt(time_factor)
    df_sim['Net_GEX'] = df_sim['Net_GEX'] * gamma_decay
    df_sim['Hedging_Pressure'] = df_sim['Hedging_Pressure'] * gamma_decay
    df_sim['Net_Vanna'] = df_sim['Net_Vanna'] * time_factor
    df_sim['Net_Charm'] = df_sim['Net_Charm'] * time_factor
    return df_sim, new_days

# ============================================================================
# ENHANCED VISUALIZATION FUNCTIONS
# ============================================================================

def create_gex_chart(df: pd.DataFrame, futures_price: float, gamma_flips: List[Dict]) -> go.Figure:
    """Enhanced GEX profile chart with volume overlay"""
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df['Net_GEX']]
    fig = go.Figure()
    
    max_gex = df['Net_GEX'].abs().max()
    max_vol = df['Total_Volume'].max()
    if max_vol > 0:
        scaled_vol = df['Total_Volume'] * (max_gex * 0.3) / max_vol
        fig.add_trace(go.Scatter(
            y=df['Strike'], x=scaled_vol, fill='tozerox',
            fillcolor='rgba(59, 130, 246, 0.15)',
            line=dict(color='#3b82f6', width=1.5), name='Volume',
            hovertemplate='Strike: %{y}<br>Volume: %{customdata:,.0f}<extra></extra>',
            customdata=df['Total_Volume']
        ))
    
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_GEX'], orientation='h',
        marker_color=colors, name='Net GEX',
        hovertemplate='<b>Strike:</b> %{y}<br><b>Net GEX:</b> %{x:.4f}B<extra></extra>'
    ))
    
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Futures: {futures_price:,.2f}", 
                  annotation_position="top right",
                  annotation=dict(font_size=11, font_color="#06b6d4", bgcolor="rgba(0,0,0,0.7)"))
    
    for zone in gamma_flips:
        fig.add_hrect(y0=zone['lower_strike'], y1=zone['upper_strike'],
                     fillcolor="rgba(245, 158, 11, 0.15)", line_width=0, layer="below")
        fig.add_annotation(y=zone['flip_strike'], x=0, 
                          text=f"🔄 Γ-Flip ({zone['impact']})",
                          showarrow=True, arrowcolor="#f59e0b", 
                          font=dict(size=10, color="#f59e0b"),
                          bgcolor="rgba(0,0,0,0.7)", bordercolor="#f59e0b")
    
    fig.update_layout(
        title=dict(text="<b>Net GEX Profile with Volume Overlay</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="GEX (₹ Billions)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=550, showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center',
                   bgcolor='rgba(26,35,50,0.8)', bordercolor='#2d3748', borderwidth=1),
        hovermode='y unified',
        xaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
        yaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
    )
    return fig

def create_dex_chart(df: pd.DataFrame, futures_price: float) -> go.Figure:
    """Enhanced DEX profile chart"""
    colors = ['#10b981' if x > 0 else '#ef4444' for x in df['Net_DEX']]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_DEX'], orientation='h',
        marker_color=colors, name='Net DEX',
        hovertemplate='<b>Strike:</b> %{y}<br><b>Net DEX:</b> %{x:.4f}B<extra></extra>'
    ))
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Futures: {futures_price:,.2f}", 
                  annotation_position="top right",
                  annotation=dict(font_size=11, font_color="#06b6d4", bgcolor="rgba(0,0,0,0.7)"))
    fig.update_layout(
        title=dict(text="<b>Net DEX Profile</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="DEX (₹ Billions)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=550,
        hovermode='y unified',
        xaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
        yaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
    )
    return fig

def create_hedging_pressure_chart(df: pd.DataFrame, futures_price: float) -> go.Figure:
    """Enhanced hedging pressure distribution chart"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Hedging_Pressure'], orientation='h',
        marker=dict(
            color=df['Hedging_Pressure'], 
            colorscale='RdYlGn', 
            showscale=True,
            colorbar=dict(
                title='Pressure %',
                titleside='right',
                tickmode='linear',
                tick0=-100,
                dtick=25,
                bgcolor='rgba(26,35,50,0.8)',
                bordercolor='#2d3748',
                borderwidth=1
            )
        ),
        hovertemplate='<b>Strike:</b> %{y}<br><b>Pressure:</b> %{x:.1f}%<extra></extra>'
    ))
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Futures: {futures_price:,.2f}",
                  annotation=dict(font_size=11, font_color="#06b6d4", bgcolor="rgba(0,0,0,0.7)"))
    fig.update_layout(
        title=dict(text="<b>Hedging Pressure Distribution</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="Hedging Pressure (%)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=550,
        hovermode='y unified',
        xaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
        yaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
    )
    return fig

def create_vanna_charm_chart(df: pd.DataFrame, futures_price: float) -> go.Figure:
    """Enhanced Vanna & Charm exposure chart"""
    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=("<b>Vanna Exposure</b>", "<b>Charm Exposure</b>"),
        horizontal_spacing=0.12
    )
    
    vanna_colors = ['#8b5cf6' if x > 0 else '#f59e0b' for x in df['Net_Vanna']]
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_Vanna'], orientation='h',
        marker_color=vanna_colors, name='Net Vanna',
        hovertemplate='<b>Strike:</b> %{y}<br><b>Vanna:</b> %{x:.4f}B<extra></extra>'
    ), row=1, col=1)
    
    charm_colors = ['#06b6d4' if x > 0 else '#ec4899' for x in df['Net_Charm']]
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_Charm'], orientation='h',
        marker_color=charm_colors, name='Net Charm',
        hovertemplate='<b>Strike:</b> %{y}<br><b>Charm:</b> %{x:.6f}B<extra></extra>'
    ), row=1, col=2)
    
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=2, row=1, col=1)
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=2, row=1, col=2)
    
    fig.update_layout(
        title=dict(text="<b>Vanna & Charm Exposure Analysis</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=500, showlegend=False,
        hovermode='y unified'
    )
    
    fig.update_xaxes(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True)
    
    return fig

def create_flow_chart(df: pd.DataFrame, futures_price: float) -> go.Figure:
    """Enhanced flow analysis chart"""
    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=("<b>GEX Flow (OI Change)</b>", "<b>DEX Flow (OI Change)</b>"),
        horizontal_spacing=0.12
    )
    
    gex_flow_colors = ['#10b981' if x > 0 else '#ef4444' for x in df['Net_Flow_GEX']]
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_Flow_GEX'], orientation='h',
        marker_color=gex_flow_colors, name='GEX Flow',
        hovertemplate='<b>Strike:</b> %{y}<br><b>GEX Flow:</b> %{x:.4f}B<extra></extra>'
    ), row=1, col=1)
    
    dex_flow_colors = ['#10b981' if x > 0 else '#ef4444' for x in df['Net_Flow_DEX']]
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Net_Flow_DEX'], orientation='h',
        marker_color=dex_flow_colors, name='DEX Flow',
        hovertemplate='<b>Strike:</b> %{y}<br><b>DEX Flow:</b> %{x:.4f}B<extra></extra>'
    ), row=1, col=2)
    
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=2, row=1, col=1)
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=2, row=1, col=2)
    
    fig.update_layout(
        title=dict(text="<b>Today's Flow Analysis (OI Change Impact)</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=500, showlegend=False,
        hovermode='y unified'
    )
    
    fig.update_xaxes(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True)
    fig.update_yaxes(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True)
    
    return fig

def create_straddle_payoff_chart(meta: Dict) -> go.Figure:
    """Enhanced ATM Straddle payoff chart"""
    atm_strike = meta['atm_strike']
    call_premium = meta['atm_call_premium']
    put_premium = meta['atm_put_premium']
    straddle_premium = meta['atm_straddle']
    futures = meta['futures_price']
    
    strike_range = np.linspace(atm_strike * 0.9, atm_strike * 1.1, 100)
    call_payoff = np.maximum(strike_range - atm_strike, 0) - call_premium
    put_payoff = np.maximum(atm_strike - strike_range, 0) - put_premium
    straddle_payoff = call_payoff + put_payoff
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=strike_range, y=straddle_payoff, name='Straddle P&L',
        line=dict(color='#8b5cf6', width=4), fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)',
        hovertemplate='<b>Price:</b> %{x:,.2f}<br><b>P&L:</b> ₹%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=strike_range, y=call_payoff, name='Call P&L',
        line=dict(color='#10b981', width=2, dash='dot'),
        hovertemplate='<b>Price:</b> %{x:,.2f}<br><b>Call P&L:</b> ₹%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=strike_range, y=put_payoff, name='Put P&L',
        line=dict(color='#ef4444', width=2, dash='dot'),
        hovertemplate='<b>Price:</b> %{x:,.2f}<br><b>Put P&L:</b> ₹%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1.5)
    fig.add_vline(x=atm_strike, line_color="#3b82f6", line_width=3, 
                  annotation_text=f"ATM: {atm_strike:,.0f}",
                  annotation=dict(font_color="#3b82f6", bgcolor="rgba(0,0,0,0.7)"))
    fig.add_vline(x=atm_strike + straddle_premium, line_dash="dash", line_color="#f59e0b",
                  annotation_text=f"Upper BE: {atm_strike + straddle_premium:,.0f}",
                  annotation=dict(font_color="#f59e0b", bgcolor="rgba(0,0,0,0.7)"))
    fig.add_vline(x=atm_strike - straddle_premium, line_dash="dash", line_color="#f59e0b",
                  annotation_text=f"Lower BE: {atm_strike - straddle_premium:,.0f}",
                  annotation=dict(font_color="#f59e0b", bgcolor="rgba(0,0,0,0.7)"))
    fig.add_vline(x=futures, line_color="#ef4444", line_width=2.5, 
                  annotation_text=f"Current: {futures:,.0f}",
                  annotation=dict(font_color="#ef4444", bgcolor="rgba(0,0,0,0.7)"))
    
    fig.update_layout(
        title=dict(text=f"<b>ATM Straddle Payoff | Premium: ₹{straddle_premium:,.2f}</b>",
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="Underlying Price", yaxis_title="Profit/Loss (₹)",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center',
                   bgcolor='rgba(26,35,50,0.8)', bordercolor='#2d3748', borderwidth=1),
        hovermode='x unified',
        xaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
        yaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True, zeroline=True),
    )
    return fig

def create_oi_distribution_chart(df: pd.DataFrame, futures_price: float) -> go.Figure:
    """Enhanced OI distribution chart"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['Strike'], x=df['Call_OI'], orientation='h',
        name='Call OI', marker_color='#10b981', opacity=0.75,
        hovertemplate='<b>Strike:</b> %{y}<br><b>Call OI:</b> %{x:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        y=df['Strike'], x=-df['Put_OI'], orientation='h',
        name='Put OI', marker_color='#ef4444', opacity=0.75,
        hovertemplate='<b>Strike:</b> %{y}<br><b>Put OI:</b> %{customdata:,.0f}<extra></extra>',
        customdata=df['Put_OI']
    ))
    fig.add_hline(y=futures_price, line_dash="dash", line_color="#06b6d4", line_width=3,
                  annotation_text=f"Futures: {futures_price:,.2f}",
                  annotation=dict(font_color="#06b6d4", bgcolor="rgba(0,0,0,0.7)"))
    fig.update_layout(
        title=dict(text="<b>Open Interest Distribution</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="Open Interest (Calls +ve | Puts -ve)", yaxis_title="Strike Price",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=500, barmode='overlay',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center',
                   bgcolor='rgba(26,35,50,0.8)', bordercolor='#2d3748', borderwidth=1),
        hovermode='y unified',
        xaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
        yaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
    )
    return fig

def create_iv_smile_chart(df: pd.DataFrame, futures_price: float) -> go.Figure:
    """Enhanced IV smile chart"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Strike'], y=df['Call_IV'], name='Call IV',
        mode='lines+markers', 
        line=dict(color='#10b981', width=3), 
        marker=dict(size=7, symbol='circle'),
        hovertemplate='<b>Strike:</b> %{x}<br><b>Call IV:</b> %{y:.2f}%<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=df['Strike'], y=df['Put_IV'], name='Put IV',
        mode='lines+markers', 
        line=dict(color='#ef4444', width=3), 
        marker=dict(size=7, symbol='circle'),
        hovertemplate='<b>Strike:</b> %{x}<br><b>Put IV:</b> %{y:.2f}%<extra></extra>'
    ))
    fig.add_vline(x=futures_price, line_dash="dash", line_color="#06b6d4", line_width=2.5, 
                  annotation_text="ATM",
                  annotation=dict(font_color="#06b6d4", bgcolor="rgba(0,0,0,0.7)"))
    fig.update_layout(
        title=dict(text="<b>Implied Volatility Smile</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="Strike Price", yaxis_title="Implied Volatility (%)",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0.5, xanchor='center',
                   bgcolor='rgba(26,35,50,0.8)', bordercolor='#2d3748', borderwidth=1),
        hovermode='x unified',
        xaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
        yaxis=dict(gridcolor='rgba(45, 55, 72, 0.4)', showgrid=True),
    )
    return fig

def create_combined_gauge(metrics: Dict) -> go.Figure:
    """Enhanced combined signal gauge"""
    combined_signal = metrics['combined_signal']
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=combined_signal,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Combined GEX+DEX Signal</b>", 
               'font': {'size': 18, 'color': 'white', 'family': 'Space Grotesk'}},
        delta={'reference': 0, 
               'increasing': {'color': "#10b981"}, 
               'decreasing': {'color': "#ef4444"},
               'font': {'size': 16}},
        number={'font': {'size': 32, 'family': 'JetBrains Mono'}},
        gauge={
            'axis': {'range': [-100, 100], 'tickcolor': 'white', 'tickwidth': 2},
            'bar': {'color': "#3b82f6", 'thickness': 0.75},
            'bgcolor': "rgba(26,35,50,0.8)",
            'borderwidth': 3, 'bordercolor': "#2d3748",
            'steps': [
                {'range': [-100, -50], 'color': 'rgba(239, 68, 68, 0.4)'},
                {'range': [-50, 0], 'color': 'rgba(245, 158, 11, 0.4)'},
                {'range': [0, 50], 'color': 'rgba(16, 185, 129, 0.4)'},
                {'range': [50, 100], 'color': 'rgba(16, 185, 129, 0.6)'}
            ],
            'threshold': {'line': {'color': "white", 'width': 5}, 'thickness': 0.8, 'value': combined_signal}
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        font={'color': "white", 'family': 'Space Grotesk'}, 
        height=350,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig

def create_greeks_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create interactive Greeks heatmap"""
    greeks_data = df[['Strike', 'Call_Gamma', 'Put_Gamma', 'Call_Delta', 'Put_Delta', 'Call_Vanna', 'Put_Vanna']].copy()
    greeks_data = greeks_data.set_index('Strike')
    
    fig = go.Figure(data=go.Heatmap(
        z=greeks_data.T.values,
        x=greeks_data.index,
        y=['Call Gamma', 'Put Gamma', 'Call Delta', 'Put Delta', 'Call Vanna', 'Put Vanna'],
        colorscale='RdYlGn',
        hovertemplate='<b>Strike:</b> %{x}<br><b>Greek:</b> %{y}<br><b>Value:</b> %{z:.4f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text="<b>Greeks Heatmap Across Strikes</b>", 
                  font=dict(size=17, color='white', family='Space Grotesk')),
        xaxis_title="Strike Price", yaxis_title="Greek",
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,35,50,0.6)', height=400,
    )
    return fig


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize session state
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 180
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    if 'time_machine_active' not in st.session_state:
        st.session_state.time_machine_active = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="main-title">📊 NYZTrade GEX/DEX Dashboard Pro</h1>
                <p class="sub-title">Professional Options Greeks Analysis | Real-time Market Intelligence with Time Machine</p>
            </div>
            <div class="live-indicator">
                <div class="live-dot"></div>
                <span style="color: #ef4444; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600;">LIVE</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        symbol = st.selectbox("📈 Select Index", options=list(DHAN_SECURITY_IDS.keys()), index=0)
        strikes_range = st.slider("📏 Strikes Range", min_value=5, max_value=25, value=15)
        expiry_index = st.number_input("📅 Expiry Index", min_value=0, max_value=5, value=0, 
                                       help="0 = Current expiry, 1 = Next expiry, etc.")
        
        st.markdown("---")
        st.markdown("### 🔄 Auto Refresh")
        auto_refresh = st.checkbox("Enable Auto Refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
        refresh_interval = st.slider("Refresh Interval (sec)", min_value=60, max_value=600, value=180, step=30)
        st.session_state.refresh_interval = refresh_interval
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.last_refresh = datetime.now()
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("Cache cleared!")
        
        st.markdown("---")
        st.markdown("### 🔑 API Status")
        config = DhanConfig()
        try:
            expiry_time = datetime.strptime(config.expiry_time, "%Y-%m-%dT%H:%M:%S")
            remaining = expiry_time - datetime.now()
            if remaining.total_seconds() > 0:
                st.success(f"✅ Token Valid: {remaining.days}d {remaining.seconds//3600}h")
            else:
                st.error("❌ Token Expired - Please update")
        except:
            st.warning("⚠️ Token status unknown")
        
        st.markdown("---")
        st.markdown("### ⏰ Time Machine")
        st.markdown("**Simulate Time Forward**")
        time_machine_enabled = st.checkbox("Enable Time Machine", value=st.session_state.time_machine_active)
        st.session_state.time_machine_active = time_machine_enabled
        
        if time_machine_enabled:
            time_offset = st.slider("⏰ Hours Forward", min_value=0.0, max_value=48.0, value=0.0, step=0.5,
                                   help="Simulate Greeks decay over time")
            st.info(f"🔮 Simulating {time_offset}h ahead")
        else:
            time_offset = 0.0
        
        st.markdown("---")
        st.markdown("### 📊 Display Options")
        show_volume = st.checkbox("Show Volume Overlay", value=True)
        show_greeks_heatmap = st.checkbox("Show Greeks Heatmap", value=False)
    
    # Auto-refresh countdown
    if st.session_state.auto_refresh:
        elapsed = (datetime.now() - st.session_state.last_refresh).total_seconds()
        remaining = max(0, st.session_state.refresh_interval - elapsed)
        progress = 1 - (remaining / st.session_state.refresh_interval)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div class="countdown-container">
                <div class="countdown-label">Next Refresh In</div>
                <div class="countdown-value">{int(remaining // 60):02d}:{int(remaining % 60):02d}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress)
        
        if remaining <= 0:
            st.session_state.last_refresh = datetime.now()
            st.cache_data.clear()
            st.rerun()
    
    # Data fetching with caching
    @st.cache_data(ttl=180)
    def fetch_data(symbol, strikes_range, expiry_index):
        fetcher = DhanAPIFetcher(DhanConfig())
        return fetcher.process_option_chain(symbol, expiry_index, strikes_range)
    
    # Fetch data
    with st.spinner(f"🔄 Fetching {symbol} data from Dhan API..."):
        df, meta = fetch_data(symbol, strikes_range, expiry_index)
    
    if df is None or meta is None:
        st.error("❌ Failed to fetch data. Please check API credentials or try again.")
        st.info("💡 Tip: Ensure your Dhan API token is valid and not expired.")
        return
    
    # Apply time machine if enabled
    original_days = meta['days_to_expiry']
    if time_offset > 0 and st.session_state.time_machine_active:
        df, sim_days = simulate_time_decay(df, meta, time_offset)
        st.warning(f"⏰ **Time Machine Active:** Simulating {time_offset}h forward | Days to expiry: {sim_days:.2f} (Original: {original_days})")
    
    # Calculate metrics
    metrics = calculate_flow_metrics(df, meta['futures_price'])
    gamma_flips = detect_gamma_flip_zones(df)
    key_levels = calculate_key_levels(df, meta['futures_price'])
    
    # Market Overview Section
    st.markdown('<div class="section-header">📊 Market Overview</div>', unsafe_allow_html=True)
    
    cols = st.columns(6)
    
    with cols[0]:
        st.markdown(f"""<div class="metric-card neutral">
            <div class="metric-label">💰 Spot Price</div>
            <div class="metric-value">₹{meta['spot_price']:,.2f}</div>
            <div class="metric-delta">{symbol}</div>
        </div>""", unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""<div class="metric-card neutral">
            <div class="metric-label">📈 Futures</div>
            <div class="metric-value">₹{meta['futures_price']:,.2f}</div>
            <div class="metric-delta">{meta.get('futures_source', 'API')}</div>
        </div>""", unsafe_allow_html=True)
    
    with cols[2]:
        gex_class = "positive" if metrics['gex_near_total'] > 0 else "negative"
        st.markdown(f"""<div class="metric-card {gex_class}">
            <div class="metric-label">🎯 Net GEX (Near)</div>
            <div class="metric-value {gex_class}">{metrics['gex_near_total']:.4f}B</div>
            <div class="metric-delta">{metrics['gex_desc']}</div>
        </div>""", unsafe_allow_html=True)
    
    with cols[3]:
        dex_class = "positive" if metrics['dex_near_total'] > 0 else "negative"
        st.markdown(f"""<div class="metric-card {dex_class}">
            <div class="metric-label">📊 Net DEX (Near)</div>
            <div class="metric-value {dex_class}">{metrics['dex_near_total']:.4f}B</div>
            <div class="metric-delta">{metrics['dex_desc']}</div>
        </div>""", unsafe_allow_html=True)
    
    with cols[4]:
        pcr_class = "positive" if key_levels['pcr'] > 1 else "negative"
        pcr_sentiment = 'Bearish' if key_levels['pcr'] > 1.2 else 'Bullish' if key_levels['pcr'] < 0.8 else 'Neutral'
        st.markdown(f"""<div class="metric-card {pcr_class}">
            <div class="metric-label">📉 Put/Call Ratio</div>
            <div class="metric-value {pcr_class}">{key_levels['pcr']:.2f}</div>
            <div class="metric-delta">{pcr_sentiment}</div>
        </div>""", unsafe_allow_html=True)
    
    with cols[5]:
        st.markdown(f"""<div class="metric-card neutral">
            <div class="metric-label">🎲 ATM Straddle</div>
            <div class="metric-value">₹{meta['atm_straddle']:.2f}</div>
            <div class="metric-delta">Strike: {meta['atm_strike']:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Signal Badges
    cols = st.columns(4)
    with cols[0]:
        badge_class = "bullish" if "SUPPRESSION" in metrics['gex_bias'] else "bearish" if "HIGH" in metrics['gex_bias'] else "volatile"
        st.markdown(f'<div class="signal-badge {badge_class}">{metrics["gex_bias"]}</div>', unsafe_allow_html=True)
    with cols[1]:
        badge_class = "bullish" if "BULLISH" in metrics['dex_bias'] else "bearish" if "BEARISH" in metrics['dex_bias'] else "volatile"
        st.markdown(f'<div class="signal-badge {badge_class}">{metrics["dex_bias"]}</div>', unsafe_allow_html=True)
    with cols[2]:
        badge_class = "bullish" if metrics['combined_signal'] > 0 else "bearish"
        st.markdown(f'<div class="signal-badge {badge_class}">{metrics["combined_bias"]}</div>', unsafe_allow_html=True)
    with cols[3]:
        flip_badge = f"🔄 {len(gamma_flips)} Gamma Flip Zone(s)" if gamma_flips else "✅ No Gamma Flips"
        flip_class = "volatile" if gamma_flips else "bullish"
        st.markdown(f'<div class="signal-badge {flip_class}">{flip_badge}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs for different views
    tabs = st.tabs(["📊 GEX/DEX", "🎯 Hedging", "📈 Vanna & Charm", "🔄 Flow", "📋 Data", "💡 Strategies", "🔬 Advanced"])
    
    # Tab 1: GEX/DEX Analysis
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_gex_chart(df, meta['futures_price'], gamma_flips), use_container_width=True)
        with col2:
            st.plotly_chart(create_dex_chart(df, meta['futures_price']), use_container_width=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.plotly_chart(create_combined_gauge(metrics), use_container_width=True)
        
        st.plotly_chart(create_straddle_payoff_chart(meta), use_container_width=True)
    
    # Tab 2: Hedging Pressure
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_hedging_pressure_chart(df, meta['futures_price']), use_container_width=True)
        with col2:
            st.plotly_chart(create_oi_distribution_chart(df, meta['futures_price']), use_container_width=True)
        
        st.markdown('<div class="section-header">🎯 Key Price Levels</div>', unsafe_allow_html=True)
        cols = st.columns(5)
        levels = [
            ("Max Pain", key_levels['max_pain'], "#f59e0b", "💀"),
            ("Highest Call OI", key_levels['highest_call_oi'], "#10b981", "📞"),
            ("Highest Put OI", key_levels['highest_put_oi'], "#ef4444", "📉"),
            ("Max +GEX", key_levels['max_positive_gex'], "#8b5cf6", "🟢"),
            ("Max -GEX", key_levels['max_negative_gex'], "#ec4899", "🔴")
        ]
        for col, (label, value, color, icon) in zip(cols, levels):
            with col:
                st.markdown(f"""<div class="metric-card" style="border-left-color: {color};">
                    <div class="metric-label">{icon} {label}</div>
                    <div class="metric-value" style="color: {color};">{value:,.0f}</div>
                </div>""", unsafe_allow_html=True)
        
        if gamma_flips:
            st.markdown('<div class="section-header">🔄 Gamma Flip Zones</div>', unsafe_allow_html=True)
            for i, zone in enumerate(gamma_flips, 1):
                st.markdown(f"""<div class="gamma-flip-zone">
                    <div class="flip-label">🔄 Zone #{i}: {zone['flip_type']}</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 12px; flex-wrap: wrap; gap: 10px;">
                        <div><span style="color: #64748b;">Flip Strike:</span> 
                            <span style="font-weight: 600; color: #f59e0b;"> {zone['flip_strike']:,.2f}</span></div>
                        <div><span style="color: #64748b;">Range:</span> 
                            <span style="font-weight: 600;"> {zone['lower_strike']:,.0f} - {zone['upper_strike']:,.0f}</span></div>
                        <div><span style="color: #64748b;">Impact:</span> 
                            <span style="font-weight: 600; color: {'#10b981' if zone['impact'] == 'Support' else '#ef4444'};"> 
                            {zone['impact']}</span></div>
                    </div>
                </div>""", unsafe_allow_html=True)
    
    # Tab 3: Vanna & Charm
    with tabs[2]:
        st.plotly_chart(create_vanna_charm_chart(df, meta['futures_price']), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📊 Top Vanna Exposure")
            vanna_df = df[['Strike', 'Net_Vanna', 'Call_Vanna', 'Put_Vanna']].sort_values('Net_Vanna', key=abs, ascending=False).head(10)
            st.dataframe(vanna_df.style.format({
                'Net_Vanna': '{:.6f}B',
                'Call_Vanna': '{:.6f}',
                'Put_Vanna': '{:.6f}'
            }), use_container_width=True, hide_index=True)
            st.markdown(f"**Total Vanna:** {metrics['vanna_total']:.6f}B")
        
        with col2:
            st.markdown("### 📊 Top Charm Exposure")
            charm_df = df[['Strike', 'Net_Charm', 'Call_Charm', 'Put_Charm']].sort_values('Net_Charm', key=abs, ascending=False).head(10)
            st.dataframe(charm_df.style.format({
                'Net_Charm': '{:.8f}B',
                'Call_Charm': '{:.8f}',
                'Put_Charm': '{:.8f}'
            }), use_container_width=True, hide_index=True)
            st.markdown(f"**Total Charm:** {metrics['charm_total']:.8f}B/day")
        
        st.plotly_chart(create_iv_smile_chart(df, meta['futures_price']), use_container_width=True)
    
    # Tab 4: Flow Analysis
    with tabs[3]:
        st.plotly_chart(create_flow_chart(df, meta['futures_price']), use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 📊 GEX Flow")
            gex_class = 'positive' if metrics['flow_gex_total'] > 0 else 'negative'
            st.markdown(f"""<div class="metric-card {gex_class}">
                <div class="metric-label">Total GEX Flow (Today)</div>
                <div class="metric-value">{'+'if metrics['flow_gex_total'] > 0 else ''}{metrics['flow_gex_total']:.4f}B</div>
                <div class="metric-delta">Based on OI Changes</div>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📊 DEX Flow")
            dex_class = 'positive' if metrics['flow_dex_total'] > 0 else 'negative'
            st.markdown(f"""<div class="metric-card {dex_class}">
                <div class="metric-label">Total DEX Flow (Today)</div>
                <div class="metric-value">{'+'if metrics['flow_dex_total'] > 0 else ''}{metrics['flow_dex_total']:.4f}B</div>
                <div class="metric-delta">Based on OI Changes</div>
            </div>""", unsafe_allow_html=True)
        
        with col3:
            flow_ratio = metrics['flow_gex_total'] / metrics['flow_dex_total'] if metrics['flow_dex_total'] != 0 else 0
            st.markdown("### 📊 Flow Ratio")
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">GEX/DEX Flow Ratio</div>
                <div class="metric-value">{flow_ratio:.2f}</div>
                <div class="metric-delta">Flow Balance</div>
            </div>""", unsafe_allow_html=True)
    
    # Tab 5: Data Table
    with tabs[4]:
        st.markdown("### 📋 Complete Option Chain Data")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            data_filter = st.selectbox("Filter by:", ["All Strikes", "ITM Calls", "OTM Calls", "ITM Puts", "OTM Puts", "Near ATM"])
        with col2:
            sort_column = st.selectbox("Sort by:", ["Strike", "Net_GEX", "Net_DEX", "Total_Volume", "Call_OI", "Put_OI"])
        with col3:
            sort_order = st.radio("Order:", ["Ascending", "Descending"], horizontal=True)
        
        df_filtered = df.copy()
        futures = meta['futures_price']
        
        if data_filter == "ITM Calls":
            df_filtered = df_filtered[df_filtered['Strike'] < futures]
        elif data_filter == "OTM Calls":
            df_filtered = df_filtered[df_filtered['Strike'] >= futures]
        elif data_filter == "ITM Puts":
            df_filtered = df_filtered[df_filtered['Strike'] > futures]
        elif data_filter == "OTM Puts":
            df_filtered = df_filtered[df_filtered['Strike'] <= futures]
        elif data_filter == "Near ATM":
            atm = meta['atm_strike']
            df_filtered = df_filtered[abs(df_filtered['Strike'] - atm) <= meta['atm_strike'] * 0.03]
        
        ascending = (sort_order == "Ascending")
        df_filtered = df_filtered.sort_values(sort_column, ascending=ascending)
        
        display_cols = ['Strike', 'Call_OI', 'Put_OI', 'Call_OI_Change', 'Put_OI_Change',
                       'Call_Volume', 'Put_Volume', 'Call_IV', 'Put_IV', 'Call_LTP', 'Put_LTP', 
                       'Net_GEX', 'Net_DEX', 'Net_Vanna', 'Net_Charm', 'Hedging_Pressure']
        
        st.dataframe(df_filtered[display_cols].style.format({
            'Net_GEX': '{:.4f}B',
            'Net_DEX': '{:.4f}B',
            'Net_Vanna': '{:.6f}B',
            'Net_Charm': '{:.8f}B',
            'Hedging_Pressure': '{:.1f}%',
            'Call_IV': '{:.2f}',
            'Put_IV': '{:.2f}'
        }), use_container_width=True, hide_index=True, height=600)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Full Data (CSV)", 
                data=csv,
                file_name=f"NYZTrade_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            filtered_csv = df_filtered.to_csv(index=False)
            st.download_button(
                "📥 Download Filtered Data", 
                data=filtered_csv,
                file_name=f"NYZTrade_{symbol}_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                mime="text/csv",
                use_container_width=True
            )
        with col3:
            st.metric("Total Strikes", len(df_filtered))
    
    # Tab 6: Strategies
    with tabs[5]:
        st.markdown("### 💼 Trading Strategy Recommendations")
        
        gex_bias = metrics['gex_near_total']
        dex_bias = metrics['dex_near_total']
        atm_strike = meta['atm_strike']
        straddle = meta['atm_straddle']
        pcr = key_levels['pcr']
        
        if gex_bias > 50:
            regime, regime_color, regime_icon = "Low Volatility / Mean Reversion", "#10b981", "🟢"
        elif gex_bias < -50:
            regime, regime_color, regime_icon = "High Volatility / Trending", "#ef4444", "🔴"
        else:
            regime, regime_color, regime_icon = "Transitional / Mixed", "#f59e0b", "🟡"
        
        st.markdown(f"""<div class="strategy-card" style="border-left: 4px solid {regime_color};">
            <div class="strategy-title">{regime_icon} Market Regime: {regime}</div>
            <div class="strategy-detail">
            <b>GEX:</b> {gex_bias:.2f} | <b>DEX:</b> {dex_bias:.2f} | <b>PCR:</b> {pcr:.2f} | 
            <b>ATM:</b> {atm_strike:,.0f} | <b>Straddle:</b> ₹{straddle:.2f}
            </div>
        </div>""", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Recommended Strategies")
            
            if gex_bias > 50:
                st.markdown("""<div class="strategy-card" style="border-left: 4px solid #10b981;">
                    <div class="strategy-title">🎯 Iron Condor / Short Straddle</div>
                    <div class="strategy-detail">
                    <b>Setup:</b> Sell ATM straddle or OTM iron condor<br>
                    <b>Rationale:</b> Strong positive GEX suppresses moves<br>
                    <b>Target:</b> Collect premium as market stays range-bound<br>
                    <b>Risk:</b> Unlimited if GEX flips negative suddenly<br>
                    <b>Stop Loss:</b> 2x premium collected
                    </div>
                </div>""", unsafe_allow_html=True)
            
            elif gex_bias < -50:
                st.markdown("""<div class="strategy-card" style="border-left: 4px solid #ef4444;">
                    <div class="strategy-title">🎯 Long Straddle / Strangle</div>
                    <div class="strategy-detail">
                    <b>Setup:</b> Buy ATM straddle or OTM strangle<br>
                    <b>Rationale:</b> Negative GEX amplifies volatility<br>
                    <b>Target:</b> Profit from large directional moves<br>
                    <b>Risk:</b> Premium paid if no move occurs<br>
                    <b>Stop Loss:</b> Exit if volatility drops sharply
                    </div>
                </div>""", unsafe_allow_html=True)
                
                if dex_bias > 20:
                    st.markdown("""<div class="strategy-card" style="border-left: 4px solid #10b981;">
                        <div class="strategy-title">📈 Bull Call Spread</div>
                        <div class="strategy-detail">
                        <b>Setup:</b> Buy ATM call, sell OTM call<br>
                        <b>Rationale:</b> DEX bullish + high volatility = upside momentum<br>
                        <b>Target:</b> Upper strike of spread<br>
                        <b>Risk:</b> Limited to debit paid
                        </div>
                    </div>""", unsafe_allow_html=True)
                elif dex_bias < -20:
                    st.markdown("""<div class="strategy-card" style="border-left: 4px solid #ef4444;">
                        <div class="strategy-title">📉 Bear Put Spread</div>
                        <div class="strategy-detail">
                        <b>Setup:</b> Buy ATM put, sell OTM put<br>
                        <b>Rationale:</b> DEX bearish + high volatility = downside momentum<br>
                        <b>Target:</b> Lower strike of spread<br>
                        <b>Risk:</b> Limited to debit paid
                        </div>
                    </div>""", unsafe_allow_html=True)
            
            else:
                st.markdown("""<div class="strategy-card" style="border-left: 4px solid #f59e0b;">
                    <div class="strategy-title">⏳ Wait for Clarity</div>
                    <div class="strategy-detail">
                    <b>Situation:</b> Mixed GEX/DEX signals<br>
                    <b>Action:</b> Stay on sidelines or use small positions<br>
                    <b>Watch For:</b> Clear trend in GEX or DEX<br>
                    <b>Alternative:</b> Trade gamma flips or key levels
                    </div>
                </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### ⚠️ Risk Management")
            
            st.markdown(f"""<div class="strategy-card" style="border-left: 4px solid #ef4444;">
                <div class="strategy-title">🛡️ Position Sizing</div>
                <div class="strategy-detail">
                • <b>Max Single Position:</b> 2% of capital<br>
                • <b>Max Daily Loss:</b> 5% of capital<br>
                • <b>Scale Into Positions:</b> 3 entries (33% each)<br>
                • <b>Correlation Risk:</b> Max 3 positions same direction
                </div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown(f"""<div class="strategy-card" style="border-left: 4px solid #f59e0b;">
                <div class="strategy-title">⏰ Time-Based Rules</div>
                <div class="strategy-detail">
                • <b>Avoid:</b> 9:15-9:30 AM (volatile opening)<br>
                • <b>Best Time:</b> 10:00-11:30 AM & 2:00-3:00 PM<br>
                • <b>Days to Expiry:</b> {meta['days_to_expiry']} days<br>
                • <b>Theta Decay:</b> {'High' if meta['days_to_expiry'] < 7 else 'Moderate' if meta['days_to_expiry'] < 15 else 'Low'}
                </div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown(f"""<div class="strategy-card" style="border-left: 4px solid #8b5cf6;">
                <div class="strategy-title">🎯 Key Levels to Watch</div>
                <div class="strategy-detail">
                • <b>ATM Strike:</b> {atm_strike:,.0f}<br>
                • <b>Upper Breakeven:</b> {atm_strike + straddle:,.0f}<br>
                • <b>Lower Breakeven:</b> {atm_strike - straddle:,.0f}<br>
                • <b>Max Pain:</b> {key_levels['max_pain']:,.0f}<br>
                • <b>Support (High Put OI):</b> {key_levels['highest_put_oi']:,.0f}<br>
                • <b>Resistance (High Call OI):</b> {key_levels['highest_call_oi']:,.0f}
                </div>
            </div>""", unsafe_allow_html=True)
    
    # Tab 7: Advanced
    with tabs[6]:
        st.markdown("### 🔬 Advanced Analytics")
        
        if show_greeks_heatmap:
            st.plotly_chart(create_greeks_heatmap(df), use_container_width=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_gamma = df['Call_Gamma'].sum() + df['Put_Gamma'].sum()
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">Σ Gamma</div>
                <div class="metric-value">{total_gamma:.6f}</div>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            total_delta = df['Call_Delta'].sum() + df['Put_Delta'].sum()
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">Σ Delta</div>
                <div class="metric-value">{total_delta:.2f}</div>
            </div>""", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">Σ Vanna</div>
                <div class="metric-value">{metrics['vanna_total']:.6f}B</div>
            </div>""", unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""<div class="metric-card neutral">
                <div class="metric-label">Σ Charm</div>
                <div class="metric-value">{metrics['charm_total']:.8f}B</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("### 📊 Statistical Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**GEX Statistics**")
            gex_stats = df['Net_GEX'].describe()
            stats_data = {
                'Metric': ['Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Value': [f"{gex_stats['mean']:.4f}B", f"{gex_stats['std']:.4f}B", 
                         f"{gex_stats['min']:.4f}B", f"{gex_stats['25%']:.4f}B",
                         f"{gex_stats['50%']:.4f}B", f"{gex_stats['75%']:.4f}B",
                         f"{gex_stats['max']:.4f}B"]
            }
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**DEX Statistics**")
            dex_stats = df['Net_DEX'].describe()
            stats_data = {
                'Metric': ['Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Value': [f"{dex_stats['mean']:.4f}B", f"{dex_stats['std']:.4f}B", 
                         f"{dex_stats['min']:.4f}B", f"{dex_stats['25%']:.4f}B",
                         f"{dex_stats['50%']:.4f}B", f"{dex_stats['75%']:.4f}B",
                         f"{dex_stats['max']:.4f}B"]
            }
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""<div style="text-align: center; padding: 24px; color: #64748b;">
        <p style="font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; font-weight: 500;">
        📊 NYZTrade GEX/DEX Dashboard Pro | Powered by Dhan API</p>
        <p style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
        Last Update: {meta['timestamp']} | Expiry: {meta['expiry']} | Symbol: {symbol} | Strikes: {len(df)}</p>
        <p style="font-size: 0.8rem; color: #475569;">
        ⚠️ <b>Disclaimer:</b> This dashboard is for educational and informational purposes only. 
        Options trading involves substantial risk of loss. Past performance does not guarantee future results. 
        Always consult with a financial advisor before making trading decisions.</p>
        <p style="font-size: 0.75rem; margin-top: 12px;">
        Created by <b>NIYAS</b> | <a href="https://youtube.com/@NYZTrade" style="color: #3b82f6; text-decoration: none;">YouTube: NYZTrade</a></p>
    </div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
