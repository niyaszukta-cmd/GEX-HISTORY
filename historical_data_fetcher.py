# ============================================================================
# Historical Rolling Options Data Fetcher
# Fetches expired options data using Dhan Rolling API
# ============================================================================

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from scipy.stats import norm
import time

class DhanConfig:
    client_id: str = "1100480354"
    access_token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY1OTYzMzk2LCJhcHBfaWQiOiJjOTNkM2UwOSIsImlhdCI6MTc2NTg3Njk5NiwidG9rZW5Db25zdW1lclR5cGUiOiJBUFAiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDQ4MDM1NCJ9.K93qVFYO2XrMJ-Jn4rY2autNZ444tc-AzYtaxVUsjRfsjW7NhfQom58vzuSMVI6nRMMB_sa7fCtWE5JIvk75yw"

DHAN_SECURITY_IDS = {
    "NIFTY": 13,
    "BANKNIFTY": 25,
    "FINNIFTY": 27,
    "MIDCPNIFTY": 442
}

EXCHANGE_SEGMENTS = {
    "NIFTY": "NSE_FNO",
    "BANKNIFTY": "NSE_FNO",
    "FINNIFTY": "NSE_FNO",
    "MIDCPNIFTY": "NSE_FNO"
}

SYMBOL_CONFIG = {
    "NIFTY": {"contract_size": 25, "strike_interval": 50},
    "BANKNIFTY": {"contract_size": 15, "strike_interval": 100},
    "FINNIFTY": {"contract_size": 40, "strike_interval": 50},
    "MIDCPNIFTY": {"contract_size": 75, "strike_interval": 25},
}

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

class HistoricalRollingDataFetcher:
    def __init__(self, config: DhanConfig = None):
        if config is None:
            config = DhanConfig()
        
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
    
    def fetch_rolling_option_data(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        strike_type: str = "ATM",
        option_type: str = "CALL",
        expiry_flag: str = "MONTH",
        expiry_code: int = 1,
        interval: str = "1"
    ) -> Optional[Dict]:
        """
        Fetch historical rolling options data
        
        Parameters:
        -----------
        symbol : str
            Index symbol (NIFTY, BANKNIFTY, etc.)
        from_date : str
            Start date in YYYY-MM-DD format
        to_date : str
            End date in YYYY-MM-DD format
        strike_type : str
            ATM, ATM+1, ATM-1, etc. (up to ATM+10/ATM-10 for indices)
        option_type : str
            CALL or PUT
        expiry_flag : str
            WEEK or MONTH
        expiry_code : int
            Expiry code (1 for current, 2 for next, etc.)
        interval : str
            Time interval: "1" (1min), "5", "15", "25", "60"
        
        Returns:
        --------
        dict : API response data
        """
        try:
            security_id = DHAN_SECURITY_IDS.get(symbol, 13)
            exchange_segment = EXCHANGE_SEGMENTS.get(symbol, "NSE_FNO")
            
            payload = {
                "exchangeSegment": exchange_segment,
                "interval": interval,
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
            
            print(f"Fetching {option_type} data for {strike_type}...")
            
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
                else:
                    print(f"No data in response for {strike_type} {option_type}")
            else:
                print(f"API Error {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return None
    
    def process_strike_data(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        strike_type: str,
        expiry_flag: str = "MONTH",
        expiry_code: int = 1,
        interval: str = "1"
    ) -> List[Dict]:
        """Process both CALL and PUT data for a specific strike"""
        
        # Fetch CALL data
        call_data = self.fetch_rolling_option_data(
            symbol, from_date, to_date, strike_type, "CALL", expiry_flag, expiry_code, interval
        )
        
        # Small delay between requests
        time.sleep(0.5)
        
        # Fetch PUT data
        put_data = self.fetch_rolling_option_data(
            symbol, from_date, to_date, strike_type, "PUT", expiry_flag, expiry_code, interval
        )
        
        if not call_data or not put_data:
            return []
        
        ce_data = call_data.get('ce', {})
        pe_data = put_data.get('pe', {})
        
        if not ce_data:
            return []
        
        config = SYMBOL_CONFIG.get(symbol, SYMBOL_CONFIG["NIFTY"])
        contract_size = config["contract_size"]
        
        records = []
        timestamps = ce_data.get('timestamp', [])
        
        for i, ts in enumerate(timestamps):
            try:
                dt = datetime.fromtimestamp(ts)
                
                # Extract data points
                spot_price = ce_data.get('spot', [0])[i] if i < len(ce_data.get('spot', [])) else 0
                strike_price = ce_data.get('strike', [0])[i] if i < len(ce_data.get('strike', [])) else 0
                
                # Skip if no valid data
                if spot_price == 0 or strike_price == 0:
                    continue
                
                # Call data
                call_oi = ce_data.get('oi', [0])[i] if i < len(ce_data.get('oi', [])) else 0
                call_volume = ce_data.get('volume', [0])[i] if i < len(ce_data.get('volume', [])) else 0
                call_iv = ce_data.get('iv', [15])[i] if i < len(ce_data.get('iv', [])) else 15
                call_open = ce_data.get('open', [0])[i] if i < len(ce_data.get('open', [])) else 0
                call_high = ce_data.get('high', [0])[i] if i < len(ce_data.get('high', [])) else 0
                call_low = ce_data.get('low', [0])[i] if i < len(ce_data.get('low', [])) else 0
                call_close = ce_data.get('close', [0])[i] if i < len(ce_data.get('close', [])) else 0
                
                # Put data
                put_oi = pe_data.get('oi', [0])[i] if i < len(pe_data.get('oi', [])) else 0
                put_volume = pe_data.get('volume', [0])[i] if i < len(pe_data.get('volume', [])) else 0
                put_iv = pe_data.get('iv', [15])[i] if i < len(pe_data.get('iv', [])) else 15
                put_open = pe_data.get('open', [0])[i] if i < len(pe_data.get('open', [])) else 0
                put_high = pe_data.get('high', [0])[i] if i < len(pe_data.get('high', [])) else 0
                put_low = pe_data.get('low', [0])[i] if i < len(pe_data.get('low', [])) else 0
                put_close = pe_data.get('close', [0])[i] if i < len(pe_data.get('close', [])) else 0
                
                # Calculate OI changes (compare with previous record)
                call_oi_change = 0
                put_oi_change = 0
                if len(records) > 0 and records[-1]['strike'] == strike_price:
                    call_oi_change = call_oi - records[-1]['call_oi']
                    put_oi_change = put_oi - records[-1]['put_oi']
                
                # Greeks calculation (assume some time to expiry)
                time_to_expiry = 7 / 365  # Approximate
                
                call_iv_dec = call_iv / 100 if call_iv > 1 else (call_iv if call_iv > 0 else 0.15)
                put_iv_dec = put_iv / 100 if put_iv > 1 else (put_iv if put_iv > 0 else 0.15)
                
                call_gamma = self.bs_calc.calculate_gamma(
                    spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec
                )
                put_gamma = self.bs_calc.calculate_gamma(
                    spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec
                )
                call_delta = self.bs_calc.calculate_call_delta(
                    spot_price, strike_price, time_to_expiry, self.risk_free_rate, call_iv_dec
                )
                put_delta = self.bs_calc.calculate_put_delta(
                    spot_price, strike_price, time_to_expiry, self.risk_free_rate, put_iv_dec
                )
                
                # Calculate exposures (in billions)
                call_gex = (call_oi * call_gamma * spot_price**2 * contract_size) / 1e9
                put_gex = -(put_oi * put_gamma * spot_price**2 * contract_size) / 1e9
                call_dex = (call_oi * call_delta * spot_price * contract_size) / 1e9
                put_dex = (put_oi * put_delta * spot_price * contract_size) / 1e9
                
                # Flow exposures
                call_flow_gex = (call_oi_change * call_gamma * spot_price**2 * contract_size) / 1e9
                put_flow_gex = -(put_oi_change * put_gamma * spot_price**2 * contract_size) / 1e9
                call_flow_dex = (call_oi_change * call_delta * spot_price * contract_size) / 1e9
                put_flow_dex = (put_oi_change * put_delta * spot_price * contract_size) / 1e9
                
                record = {
                    'timestamp': dt,
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'spot_price': spot_price,
                    'strike': strike_price,
                    'strike_type': strike_type,
                    
                    # Call data
                    'call_oi': call_oi,
                    'call_volume': call_volume,
                    'call_iv': call_iv,
                    'call_open': call_open,
                    'call_high': call_high,
                    'call_low': call_low,
                    'call_close': call_close,
                    'call_oi_change': call_oi_change,
                    
                    # Put data
                    'put_oi': put_oi,
                    'put_volume': put_volume,
                    'put_iv': put_iv,
                    'put_open': put_open,
                    'put_high': put_high,
                    'put_low': put_low,
                    'put_close': put_close,
                    'put_oi_change': put_oi_change,
                    
                    # Greeks
                    'call_gamma': call_gamma,
                    'put_gamma': put_gamma,
                    'call_delta': call_delta,
                    'put_delta': put_delta,
                    
                    # Exposures
                    'call_gex': call_gex,
                    'put_gex': put_gex,
                    'net_gex': call_gex + put_gex,
                    'call_dex': call_dex,
                    'put_dex': put_dex,
                    'net_dex': call_dex + put_dex,
                    
                    # Flow exposures
                    'call_flow_gex': call_flow_gex,
                    'put_flow_gex': put_flow_gex,
                    'net_flow_gex': call_flow_gex + put_flow_gex,
                    'call_flow_dex': call_flow_dex,
                    'put_flow_dex': put_flow_dex,
                    'net_flow_dex': call_flow_dex + put_flow_dex,
                }
                
                records.append(record)
                
            except Exception as e:
                print(f"Error processing record {i}: {str(e)}")
                continue
        
        return records
    
    def fetch_complete_chain(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        strike_range: List[str] = None,
        expiry_flag: str = "MONTH",
        expiry_code: int = 1,
        interval: str = "1"
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Fetch complete option chain for multiple strikes
        
        Parameters:
        -----------
        strike_range : list
            List of strikes to fetch (e.g., ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"])
        """
        
        if strike_range is None:
            # Default range for index options
            strike_range = ["ATM"]
            for i in range(1, 6):
                strike_range.extend([f"ATM+{i}", f"ATM-{i}"])
        
        print(f"\nFetching historical data for {symbol}")
        print(f"Date range: {from_date} to {to_date}")
        print(f"Strikes: {', '.join(strike_range)}")
        print(f"Interval: {interval} minute(s)")
        print("-" * 60)
        
        all_records = []
        
        for strike_type in strike_range:
            print(f"\nProcessing {strike_type}...")
            
            strike_records = self.process_strike_data(
                symbol, from_date, to_date, strike_type, expiry_flag, expiry_code, interval
            )
            
            if strike_records:
                all_records.extend(strike_records)
                print(f"✓ {len(strike_records)} records fetched for {strike_type}")
            else:
                print(f"✗ No data for {strike_type}")
            
            # Rate limiting
            time.sleep(1)
        
        if not all_records:
            print("\n❌ No data fetched!")
            return None, None
        
        df = pd.DataFrame(all_records)
        df = df.sort_values(['timestamp', 'strike']).reset_index(drop=True)
        
        # Calculate hedging pressure
        max_gex = df['net_gex'].abs().max()
        df['hedging_pressure'] = (df['net_gex'] / max_gex * 100) if max_gex > 0 else 0
        
        meta = {
            'symbol': symbol,
            'from_date': from_date,
            'to_date': to_date,
            'interval': interval,
            'expiry_flag': expiry_flag,
            'expiry_code': expiry_code,
            'total_records': len(df),
            'unique_timestamps': df['timestamp'].nunique(),
            'unique_strikes': df['strike'].nunique(),
            'date_range': f"{df['date'].min()} to {df['date'].max()}"
        }
        
        print("\n" + "=" * 60)
        print("✅ Data fetch complete!")
        print(f"Total records: {meta['total_records']:,}")
        print(f"Unique timestamps: {meta['unique_timestamps']:,}")
        print(f"Unique strikes: {meta['unique_strikes']}")
        print("=" * 60)
        
        return df, meta

def main():
    """Example usage"""
    
    fetcher = HistoricalRollingDataFetcher()
    
    # Fetch last 7 days of NIFTY data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    
    # Fetch data
    df, meta = fetcher.fetch_complete_chain(
        symbol="NIFTY",
        from_date=from_date,
        to_date=to_date,
        strike_range=["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"],
        expiry_flag="MONTH",
        expiry_code=1,
        interval="5"  # 5-minute intervals
    )
    
    if df is not None:
        print("\nSample data:")
        print(df.head(10))
        
        # Save to CSV
        filename = f"historical_data_{meta['symbol']}_{from_date}_{to_date}.csv"
        df.to_csv(filename, index=False)
        print(f"\n📥 Data saved to {filename}")

if __name__ == "__main__":
    main()
