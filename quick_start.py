#!/usr/bin/env python3
# ============================================================================
# Quick Start & Example Usage Script
# Demonstrates all key features of Historical GEX/DEX Dashboard
# ============================================================================

import sys
sys.path.append('/home/claude')

from historical_data_fetcher import HistoricalRollingDataFetcher, DhanConfig
from automated_collector import HistoricalDataDB, AutomatedDataCollector
from datetime import datetime, timedelta
import pandas as pd

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def example_1_fetch_single_day():
    """Example 1: Fetch single day of data"""
    print_header("EXAMPLE 1: Fetch Single Day Historical Data")
    
    fetcher = HistoricalRollingDataFetcher()
    
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Fetching NIFTY data for {yesterday}")
    print("Strike range: ATM ±2")
    print("Interval: 5 minutes\n")
    
    df, meta = fetcher.fetch_complete_chain(
        symbol="NIFTY",
        from_date=yesterday,
        to_date=today,
        strike_range=["ATM", "ATM+1", "ATM-1", "ATM+2", "ATM-2"],
        interval="5"  # 5-minute intervals
    )
    
    if df is not None:
        print("\n✅ Data fetched successfully!")
        print(f"\nData Summary:")
        print(f"  Total records: {len(df):,}")
        print(f"  Unique timestamps: {df['timestamp'].nunique()}")
        print(f"  Unique strikes: {df['strike'].nunique()}")
        print(f"  Time range: {df['time'].min()} to {df['time'].max()}")
        
        print("\n📊 Sample Data (First 5 rows):")
        print(df[['timestamp', 'strike', 'spot_price', 'net_gex', 'net_dex']].head())
        
        # Save to CSV
        filename = f"example_1_{yesterday}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Data saved to: {filename}")
    else:
        print("❌ Failed to fetch data")

def example_2_analyze_gex_patterns():
    """Example 2: Analyze GEX patterns from database"""
    print_header("EXAMPLE 2: Analyze Historical GEX Patterns")
    
    db = HistoricalDataDB()
    
    # Get last 7 days of aggregated data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"Analyzing NIFTY from {start_date} to {end_date}\n")
    
    df = db.get_aggregated_metrics("NIFTY", start_date, end_date)
    
    if not df.empty:
        print(f"✅ Retrieved {len(df)} records\n")
        
        # Calculate statistics
        print("📈 GEX Statistics:")
        print(f"  Average Net GEX: {df['net_gex_total'].mean():.4f}B")
        print(f"  Max Net GEX: {df['net_gex_total'].max():.4f}B")
        print(f"  Min Net GEX: {df['net_gex_total'].min():.4f}B")
        print(f"  Std Dev: {df['net_gex_total'].std():.4f}B")
        
        print("\n📊 DEX Statistics:")
        print(f"  Average Net DEX: {df['net_dex_total'].mean():.4f}B")
        print(f"  Max Net DEX: {df['net_dex_total'].max():.4f}B")
        print(f"  Min Net DEX: {df['net_dex_total'].min():.4f}B")
        
        print("\n🎯 PCR Statistics:")
        print(f"  Average PCR: {df['pcr'].mean():.2f}")
        print(f"  Max PCR: {df['pcr'].max():.2f}")
        print(f"  Min PCR: {df['pcr'].min():.2f}")
        
        # Identify regime changes
        print("\n🔍 Market Regime Analysis:")
        positive_gex_pct = (df['net_gex_total'] > 0).sum() / len(df) * 100
        print(f"  Positive GEX periods: {positive_gex_pct:.1f}%")
        print(f"  Negative GEX periods: {100-positive_gex_pct:.1f}%")
        
        if positive_gex_pct > 60:
            print("  → Predominantly LOW VOLATILITY regime")
        elif positive_gex_pct < 40:
            print("  → Predominantly HIGH VOLATILITY regime")
        else:
            print("  → MIXED/TRANSITIONAL regime")
    else:
        print("❌ No data available. Run data collection first!")

def example_3_intraday_flow_analysis():
    """Example 3: Intraday flow analysis"""
    print_header("EXAMPLE 3: Intraday Flow Analysis")
    
    db = HistoricalDataDB()
    
    # Get yesterday's intraday data
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Analyzing intraday flows for {yesterday}\n")
    
    df = db.get_intraday_data("NIFTY", yesterday)
    
    if not df.empty:
        print(f"✅ Retrieved {len(df)} intraday records\n")
        
        # Find key moments
        print("🔥 Key Intraday Moments:")
        
        # Largest GEX flow
        max_flow_idx = df['flow_gex_total'].abs().idxmax()
        max_flow = df.loc[max_flow_idx]
        print(f"\n  Largest GEX Flow:")
        print(f"    Time: {max_flow['time']}")
        print(f"    Flow GEX: {max_flow['flow_gex_total']:.4f}B")
        print(f"    Spot: {max_flow['spot_price']:.2f}")
        
        # PCR extremes
        max_pcr_idx = df['pcr'].idxmax()
        min_pcr_idx = df['pcr'].idxmin()
        
        print(f"\n  Highest PCR (Most Bearish):")
        print(f"    Time: {df.loc[max_pcr_idx, 'time']}")
        print(f"    PCR: {df.loc[max_pcr_idx, 'pcr']:.2f}")
        print(f"    Spot: {df.loc[max_pcr_idx, 'spot_price']:.2f}")
        
        print(f"\n  Lowest PCR (Most Bullish):")
        print(f"    Time: {df.loc[min_pcr_idx, 'time']}")
        print(f"    PCR: {df.loc[min_pcr_idx, 'pcr']:.2f}")
        print(f"    Spot: {df.loc[min_pcr_idx, 'spot_price']:.2f}")
        
        # Price movement
        price_change = df.iloc[-1]['spot_price'] - df.iloc[0]['spot_price']
        price_change_pct = (price_change / df.iloc[0]['spot_price']) * 100
        
        print(f"\n📊 Daily Summary:")
        print(f"  Opening Spot: {df.iloc[0]['spot_price']:.2f}")
        print(f"  Closing Spot: {df.iloc[-1]['spot_price']:.2f}")
        print(f"  Change: {price_change:+.2f} ({price_change_pct:+.2f}%)")
        
    else:
        print("❌ No intraday data available for this date")

def example_4_multi_symbol_comparison():
    """Example 4: Compare multiple symbols"""
    print_header("EXAMPLE 4: Multi-Symbol Comparison")
    
    db = HistoricalDataDB()
    symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
    
    date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Comparing symbols for {date}\n")
    
    comparison_data = []
    
    for symbol in symbols:
        df = db.get_intraday_data(symbol, date)
        
        if not df.empty:
            summary = {
                'Symbol': symbol,
                'Avg_GEX': df['net_gex_total'].mean(),
                'Avg_DEX': df['net_dex_total'].mean(),
                'Avg_PCR': df['pcr'].mean(),
                'Spot_Change_%': ((df.iloc[-1]['spot_price'] - df.iloc[0]['spot_price']) / 
                                  df.iloc[0]['spot_price'] * 100),
                'Records': len(df)
            }
            comparison_data.append(summary)
    
    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        print("📊 Comparison Summary:\n")
        print(comp_df.to_string(index=False))
        
        print("\n💡 Insights:")
        
        # Most volatile
        most_volatile = comp_df.loc[comp_df['Avg_GEX'].abs().idxmin()]
        print(f"  Most Volatile: {most_volatile['Symbol']} (GEX: {most_volatile['Avg_GEX']:.4f}B)")
        
        # Most bullish positioning
        most_bullish = comp_df.loc[comp_df['Avg_DEX'].idxmax()]
        print(f"  Most Bullish DEX: {most_bullish['Symbol']} (DEX: {most_bullish['Avg_DEX']:.4f}B)")
        
        # Best performer
        best_performer = comp_df.loc[comp_df['Spot_Change_%'].idxmax()]
        print(f"  Best Performer: {best_performer['Symbol']} ({best_performer['Spot_Change_%']:+.2f}%)")
    else:
        print("❌ No data available for comparison")

def example_5_collect_new_data():
    """Example 5: Collect new historical data"""
    print_header("EXAMPLE 5: Collect New Historical Data")
    
    print("This example will fetch and store data in the database.\n")
    
    response = input("Proceed with data collection? (y/n): ")
    
    if response.lower() != 'y':
        print("Skipped.")
        return
    
    collector = AutomatedDataCollector(["NIFTY"])
    
    print("\nCollecting last 2 days of NIFTY data...")
    success = collector.collect_data_for_symbol("NIFTY", days_back=2)
    
    if success:
        print("\n✅ Collection successful!")
        print("You can now analyze this data in the dashboard.")
    else:
        print("\n❌ Collection failed. Check logs for details.")

def show_menu():
    """Show interactive menu"""
    print("\n" + "="*70)
    print("  NYZTrade Historical GEX/DEX Dashboard - Examples")
    print("="*70)
    print("\nSelect an example to run:")
    print("\n  1. Fetch Single Day Historical Data")
    print("  2. Analyze Historical GEX Patterns")
    print("  3. Intraday Flow Analysis")
    print("  4. Multi-Symbol Comparison")
    print("  5. Collect New Historical Data")
    print("\n  0. Exit")
    print("\n" + "-"*70)
    
    choice = input("\nEnter your choice (0-5): ")
    return choice

def main():
    """Main function"""
    print("\n")
    print("🚀 " + "="*66 + " 🚀")
    print("   NYZTrade Historical GEX/DEX Dashboard - Quick Start Examples")
    print("🚀 " + "="*66 + " 🚀")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            example_1_fetch_single_day()
        elif choice == '2':
            example_2_analyze_gex_patterns()
        elif choice == '3':
            example_3_intraday_flow_analysis()
        elif choice == '4':
            example_4_multi_symbol_comparison()
        elif choice == '5':
            example_5_collect_new_data()
        elif choice == '0':
            print("\n👋 Thanks for using NYZTrade Dashboard!")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
