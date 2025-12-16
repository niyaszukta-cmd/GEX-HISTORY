#!/bin/bash
# ============================================================================
# NYZTrade Historical GEX/DEX Dashboard Launcher
# ============================================================================

echo "========================================="
echo "  NYZTrade Historical GEX/DEX Dashboard"
echo "========================================="
echo ""
echo "Select an option:"
echo ""
echo "  1. Launch Dashboard (Streamlit)"
echo "  2. Run Quick Start Examples"
echo "  3. Start Automated Data Collector"
echo "  4. Collect Data Manually (NIFTY - 7 days)"
echo "  5. Collect All Symbols (7 days)"
echo "  6. View Database Stats"
echo "  7. View Collection Logs"
echo ""
echo "  0. Exit"
echo ""
echo "-----------------------------------------"
read -p "Enter your choice (0-7): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Launching Streamlit Dashboard..."
        echo "   Access at: http://localhost:8501"
        echo ""
        streamlit run /home/claude/historical_gex_dashboard.py
        ;;
    2)
        echo ""
        echo "📚 Running Quick Start Examples..."
        echo ""
        python /home/claude/quick_start.py
        ;;
    3)
        echo ""
        echo "⏰ Starting Automated Collector..."
        echo "   Press Ctrl+C to stop"
        echo ""
        python /home/claude/automated_collector.py
        ;;
    4)
        echo ""
        echo "📥 Collecting NIFTY data (last 7 days)..."
        echo ""
        python /home/claude/automated_collector.py manual --symbol NIFTY --days 7
        ;;
    5)
        echo ""
        echo "📥 Collecting ALL symbols (last 7 days)..."
        echo "   This will take several minutes..."
        echo ""
        python /home/claude/automated_collector.py manual --all --days 7
        ;;
    6)
        echo ""
        echo "📊 Database Statistics:"
        echo ""
        python << EOF
import sqlite3
from datetime import datetime

db_path = '/home/claude/historical_gex_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Minute data stats
cursor.execute("SELECT symbol, COUNT(*), MIN(date), MAX(date) FROM historical_minute_data GROUP BY symbol")
minute_stats = cursor.fetchall()

# Aggregated data stats
cursor.execute("SELECT symbol, COUNT(*), MIN(date), MAX(date) FROM aggregated_minute_metrics GROUP BY symbol")
agg_stats = cursor.fetchall()

print("Minute-Level Data:")
print("-" * 60)
if minute_stats:
    for symbol, count, min_date, max_date in minute_stats:
        print(f"  {symbol:12} | Records: {count:>8,} | Range: {min_date} to {max_date}")
else:
    print("  No data available")

print("\nAggregated Data:")
print("-" * 60)
if agg_stats:
    for symbol, count, min_date, max_date in agg_stats:
        print(f"  {symbol:12} | Records: {count:>8,} | Range: {min_date} to {max_date}")
else:
    print("  No data available")

# Collection status
cursor.execute("SELECT symbol, status, COUNT(*) as runs FROM collection_status GROUP BY symbol, status")
status_stats = cursor.fetchall()

print("\nCollection Status:")
print("-" * 60)
if status_stats:
    for symbol, status, count in status_stats:
        print(f"  {symbol:12} | {status:8} | {count:>3} runs")
else:
    print("  No collection runs yet")

conn.close()
EOF
        ;;
    7)
        echo ""
        echo "📋 Recent Collection Logs (last 50 lines):"
        echo ""
        if [ -f /home/claude/data_collector.log ]; then
            tail -50 /home/claude/data_collector.log
        else
            echo "  No log file found. Run data collection first."
        fi
        ;;
    0)
        echo ""
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Please try again."
        ;;
esac

echo ""
echo "Press Enter to return to menu..."
read
exec "$0"
