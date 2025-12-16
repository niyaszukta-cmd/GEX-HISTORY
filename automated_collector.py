# ============================================================================
# Automated Historical Data Collector
# Runs in background to collect data at regular intervals
# ============================================================================

import schedule
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import sys
import logging

# Import from our modules
sys.path.append('/home/claude')
from historical_data_fetcher import HistoricalRollingDataFetcher, DhanConfig, SYMBOL_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/claude/data_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class HistoricalDataDB:
    def __init__(self, db_path: str = "/home/claude/historical_gex_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Historical minute-level data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_minute_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                spot_price REAL,
                strike REAL NOT NULL,
                strike_type TEXT,
                
                call_oi INTEGER,
                call_volume INTEGER,
                call_iv REAL,
                call_open REAL,
                call_high REAL,
                call_low REAL,
                call_close REAL,
                call_oi_change INTEGER,
                
                put_oi INTEGER,
                put_volume INTEGER,
                put_iv REAL,
                put_open REAL,
                put_high REAL,
                put_low REAL,
                put_close REAL,
                put_oi_change INTEGER,
                
                call_gamma REAL,
                put_gamma REAL,
                call_delta REAL,
                put_delta REAL,
                
                call_gex REAL,
                put_gex REAL,
                net_gex REAL,
                call_dex REAL,
                put_dex REAL,
                net_dex REAL,
                
                call_flow_gex REAL,
                put_flow_gex REAL,
                net_flow_gex REAL,
                call_flow_dex REAL,
                put_flow_dex REAL,
                net_flow_dex REAL,
                
                hedging_pressure REAL,
                
                UNIQUE(symbol, timestamp, strike)
            )
        """)
        
        # Aggregated metrics per timestamp
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aggregated_minute_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                spot_price REAL,
                
                total_call_oi REAL,
                total_put_oi REAL,
                pcr REAL,
                
                net_gex_total REAL,
                net_dex_total REAL,
                flow_gex_total REAL,
                flow_dex_total REAL,
                
                atm_strike REAL,
                max_gex_strike REAL,
                min_gex_strike REAL,
                
                UNIQUE(symbol, timestamp)
            )
        """)
        
        # Collection status tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                collection_date TEXT NOT NULL,
                last_timestamp DATETIME,
                records_collected INTEGER,
                status TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_minute_data_timestamp 
            ON historical_minute_data(symbol, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_aggregated_timestamp 
            ON aggregated_minute_metrics(symbol, timestamp)
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def insert_minute_data(self, df: pd.DataFrame, symbol: str):
        """Insert minute-level data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        records_inserted = 0
        
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO historical_minute_data
                    (symbol, timestamp, date, time, spot_price, strike, strike_type,
                     call_oi, call_volume, call_iv, call_open, call_high, call_low, call_close, call_oi_change,
                     put_oi, put_volume, put_iv, put_open, put_high, put_low, put_close, put_oi_change,
                     call_gamma, put_gamma, call_delta, put_delta,
                     call_gex, put_gex, net_gex, call_dex, put_dex, net_dex,
                     call_flow_gex, put_flow_gex, net_flow_gex, call_flow_dex, put_flow_dex, net_flow_dex,
                     hedging_pressure)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    symbol, row['timestamp'], row['date'], row['time'], row['spot_price'],
                    row['strike'], row['strike_type'],
                    row['call_oi'], row['call_volume'], row['call_iv'], 
                    row['call_open'], row['call_high'], row['call_low'], row['call_close'], row['call_oi_change'],
                    row['put_oi'], row['put_volume'], row['put_iv'],
                    row['put_open'], row['put_high'], row['put_low'], row['put_close'], row['put_oi_change'],
                    row['call_gamma'], row['put_gamma'], row['call_delta'], row['put_delta'],
                    row['call_gex'], row['put_gex'], row['net_gex'],
                    row['call_dex'], row['put_dex'], row['net_dex'],
                    row['call_flow_gex'], row['put_flow_gex'], row['net_flow_gex'],
                    row['call_flow_dex'], row['put_flow_dex'], row['net_flow_dex'],
                    row['hedging_pressure']
                ))
                records_inserted += 1
            except Exception as e:
                logger.error(f"Error inserting record: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Inserted {records_inserted} records for {symbol}")
        return records_inserted
    
    def insert_aggregated_metrics(self, df: pd.DataFrame, symbol: str):
        """Insert aggregated metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Group by timestamp and aggregate
        grouped = df.groupby('timestamp').agg({
            'date': 'first',
            'time': 'first',
            'spot_price': 'first',
            'call_oi': 'sum',
            'put_oi': 'sum',
            'net_gex': 'sum',
            'net_dex': 'sum',
            'net_flow_gex': 'sum',
            'net_flow_dex': 'sum',
        }).reset_index()
        
        records_inserted = 0
        
        for _, row in grouped.iterrows():
            pcr = row['put_oi'] / row['call_oi'] if row['call_oi'] > 0 else 1
            
            # Find ATM and GEX strikes
            ts_data = df[df['timestamp'] == row['timestamp']]
            atm_strike = ts_data.iloc[(ts_data['strike'] - row['spot_price']).abs().argsort()[:1]]['strike'].values[0]
            max_gex_strike = ts_data.loc[ts_data['net_gex'].idxmax(), 'strike']
            min_gex_strike = ts_data.loc[ts_data['net_gex'].idxmin(), 'strike']
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO aggregated_minute_metrics
                    (symbol, timestamp, date, time, spot_price, total_call_oi, total_put_oi, pcr,
                     net_gex_total, net_dex_total, flow_gex_total, flow_dex_total,
                     atm_strike, max_gex_strike, min_gex_strike)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    symbol, row['timestamp'], row['date'], row['time'], row['spot_price'],
                    row['call_oi'], row['put_oi'], pcr,
                    row['net_gex'], row['net_dex'], row['net_flow_gex'], row['net_flow_dex'],
                    atm_strike, max_gex_strike, min_gex_strike
                ))
                records_inserted += 1
            except Exception as e:
                logger.error(f"Error inserting aggregated record: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Inserted {records_inserted} aggregated records for {symbol}")
        return records_inserted
    
    def update_collection_status(self, symbol: str, date: str, records: int, status: str, error: str = None):
        """Update collection status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO collection_status
            (symbol, collection_date, last_timestamp, records_collected, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (symbol, date, datetime.now(), records, status, error))
        
        conn.commit()
        conn.close()
    
    def get_last_collection_timestamp(self, symbol: str) -> datetime:
        """Get last collection timestamp for a symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT MAX(timestamp) FROM historical_minute_data WHERE symbol = ?
        """, (symbol,))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        if result:
            return datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        return None

# ============================================================================
# DATA COLLECTOR
# ============================================================================

class AutomatedDataCollector:
    def __init__(self, symbols: List[str], db_path: str = "/home/claude/historical_gex_data.db"):
        self.symbols = symbols
        self.db = HistoricalDataDB(db_path)
        self.fetcher = HistoricalRollingDataFetcher()
        self.strike_range = ["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2", "ATM+3", "ATM-3"]
    
    def collect_data_for_symbol(self, symbol: str, days_back: int = 1):
        """Collect historical data for a symbol"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting data collection for {symbol}")
            logger.info(f"{'='*60}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            from_date = start_date.strftime('%Y-%m-%d')
            to_date = end_date.strftime('%Y-%m-%d')
            
            logger.info(f"Date range: {from_date} to {to_date}")
            
            # Fetch data
            df, meta = self.fetcher.fetch_complete_chain(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                strike_range=self.strike_range,
                expiry_flag="MONTH",
                expiry_code=1,
                interval="1"  # 1-minute data
            )
            
            if df is None or len(df) == 0:
                logger.warning(f"No data fetched for {symbol}")
                self.db.update_collection_status(
                    symbol, datetime.now().strftime('%Y-%m-%d'), 0, 'FAILED', 'No data returned'
                )
                return False
            
            # Insert data into database
            logger.info("Inserting data into database...")
            
            records_minute = self.db.insert_minute_data(df, symbol)
            records_agg = self.db.insert_aggregated_metrics(df, symbol)
            
            # Update status
            self.db.update_collection_status(
                symbol, datetime.now().strftime('%Y-%m-%d'), 
                records_minute, 'SUCCESS'
            )
            
            logger.info(f"✅ Collection complete for {symbol}")
            logger.info(f"   Minute records: {records_minute}")
            logger.info(f"   Aggregated records: {records_agg}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error collecting data for {symbol}: {str(e)}")
            self.db.update_collection_status(
                symbol, datetime.now().strftime('%Y-%m-%d'), 0, 'ERROR', str(e)
            )
            return False
    
    def collect_all_symbols(self, days_back: int = 1):
        """Collect data for all configured symbols"""
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting automated collection cycle")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#'*60}\n")
        
        success_count = 0
        
        for symbol in self.symbols:
            if self.collect_data_for_symbol(symbol, days_back):
                success_count += 1
            
            # Wait between symbols to avoid rate limiting
            logger.info("Waiting 60 seconds before next symbol...\n")
            time.sleep(60)
        
        logger.info(f"\n{'#'*60}")
        logger.info(f"Collection cycle complete")
        logger.info(f"Success: {success_count}/{len(self.symbols)} symbols")
        logger.info(f"{'#'*60}\n")
    
    def incremental_collection(self, symbol: str):
        """Collect only new data since last collection"""
        last_timestamp = self.db.get_last_collection_timestamp(symbol)
        
        if last_timestamp is None:
            # No previous data, collect last 7 days
            logger.info(f"No previous data for {symbol}, collecting last 7 days")
            return self.collect_data_for_symbol(symbol, days_back=7)
        
        # Calculate how many days since last collection
        days_since = (datetime.now() - last_timestamp).days + 1
        
        if days_since > 30:
            logger.warning(f"Gap of {days_since} days detected. Limiting to 30 days.")
            days_since = 30
        
        logger.info(f"Collecting last {days_since} days for {symbol}")
        return self.collect_data_for_symbol(symbol, days_back=days_since)

# ============================================================================
# SCHEDULER
# ============================================================================

def run_scheduled_collection():
    """Run scheduled data collection"""
    
    # Configure which symbols to collect
    SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
    
    collector = AutomatedDataCollector(SYMBOLS)
    
    # Initial collection (last 7 days)
    logger.info("Running initial collection...")
    for symbol in SYMBOLS:
        collector.collect_data_for_symbol(symbol, days_back=7)
        time.sleep(120)  # 2 minutes between symbols
    
    # Schedule regular collections
    # Collect every 15 minutes during market hours (9:15 AM - 3:30 PM)
    schedule.every(15).minutes.do(lambda: collector.collect_all_symbols(days_back=1))
    
    # Also run at market open and close
    schedule.every().day.at("09:20").do(lambda: collector.collect_all_symbols(days_back=1))
    schedule.every().day.at("15:35").do(lambda: collector.collect_all_symbols(days_back=1))
    
    logger.info("Scheduler started. Waiting for next collection...")
    logger.info("Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")

# ============================================================================
# MANUAL COLLECTION SCRIPT
# ============================================================================

def manual_collection():
    """Manual data collection for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect historical options data')
    parser.add_argument('--symbol', type=str, default='NIFTY', help='Symbol to collect')
    parser.add_argument('--days', type=int, default=7, help='Number of days to collect')
    parser.add_argument('--all', action='store_true', help='Collect all symbols')
    
    args = parser.parse_args()
    
    if args.all:
        symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        collector = AutomatedDataCollector(symbols)
        collector.collect_all_symbols(days_back=args.days)
    else:
        collector = AutomatedDataCollector([args.symbol])
        collector.collect_data_for_symbol(args.symbol, days_back=args.days)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        manual_collection()
    else:
        run_scheduled_collection()
