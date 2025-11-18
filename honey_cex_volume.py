import requests
import pandas as pd
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
COIN_ID = os.getenv("COIN_ID", "hivemapper")
API_KEY = os.getenv("COINGECKO_API_KEY")

# Known centralized exchanges
KNOWN_CEXS = {
    'binance', 'coinbase', 'kraken', 'gate', 'kucoin', 'mexc',
    'bybit', 'okx', 'huobi', 'bitfinex', 'crypto_com', 'gemini',
    'bitstamp', 'bithumb', 'upbit', 'bitget', 'htx', 'bitmart'
}

def get_all_exchanges(coin_id, api_key=None):
    """
    Get all exchanges where the token trades and categorize as CEX or DEX
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/tickers"
    
    headers = {}
    if api_key:
        headers["X-CG-Pro-API-Key"] = api_key
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        tickers = data.get('tickers', [])
        
        exchanges = {
            'cex': [],
            'dex': []
        }
        
        for ticker in tickers:
            exchange_name = ticker['market']['name']
            exchange_id = ticker['market']['identifier'].lower()
            
            # Check if it's a known CEX
            is_cex = any(cex in exchange_id for cex in KNOWN_CEXS)
            
            if is_cex:
                exchanges['cex'].append({
                    'name': exchange_name,
                    'id': exchange_id,
                    'pair': f"{ticker['base']}/{ticker['target']}"
                })
            else:
                exchanges['dex'].append({
                    'name': exchange_name,
                    'id': exchange_id,
                    'pair': f"{ticker['base']}/{ticker['target']}"
                })
        
        return exchanges
    
    except Exception as e:
        print(f"Error fetching exchange data: {e}")
        return None

def get_current_cex_volume(coin_id, api_key=None):
    """
    Get current 24h CEX volume breakdown
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/tickers"
    
    headers = {}
    if api_key:
        headers["X-CG-Pro-API-Key"] = api_key
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        tickers = data.get('tickers', [])
        
        cex_volumes = []
        dex_volumes = []
        
        for ticker in tickers:
            exchange_name = ticker['market']['name']
            exchange_id = ticker['market']['identifier'].lower()
            volume_usd = ticker.get('converted_volume', {}).get('usd', 0)
            pair = f"{ticker['base']}/{ticker['target']}"
            
            # Check if it's a known CEX
            is_cex = any(cex in exchange_id for cex in KNOWN_CEXS)
            
            volume_data = {
                'exchange': exchange_name,
                'pair': pair,
                'volume_24h_usd': volume_usd
            }
            
            if is_cex:
                cex_volumes.append(volume_data)
            else:
                dex_volumes.append(volume_data)
        
        return {
            'cex': cex_volumes,
            'dex': dex_volumes,
            'total_cex': sum(v['volume_24h_usd'] for v in cex_volumes),
            'total_dex': sum(v['volume_24h_usd'] for v in dex_volumes)
        }
    
    except Exception as e:
        print(f"Error fetching volume data: {e}")
        return None

def get_historical_total_volume(coin_id, start_date, end_date, api_key=None):
    """
    Get historical total volume (CEX + DEX combined)
    This is what we'll use to estimate historical CEX volume
    """
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    
    params = {
        'vs_currency': 'usd',
        'from': start_timestamp,
        'to': end_timestamp
    }
    
    headers = {}
    if api_key:
        headers["X-CG-Pro-API-Key"] = api_key
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        volumes = data.get('total_volumes', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(volumes, columns=['timestamp', 'volume_usd'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Extract just the date (no time) for proper grouping
        df['date_only'] = df['date'].dt.date
        
        # Group by actual calendar day and sum volumes
        daily_df = df.groupby('date_only').agg({
            'volume_usd': 'sum'
        }).reset_index()
        
        return daily_df
    
    except Exception as e:
        print(f"Error fetching historical volume: {e}")
        return None

def main():
    print("="*70)
    print("HONEY Token CEX Volume Analysis")
    print("="*70)
    print()
    
    # Step 1: Get current exchange breakdown
    print("Step 1: Identifying where HONEY trades...")
    print("-"*70)
    
    exchanges = get_all_exchanges(COIN_ID, API_KEY)
    
    if exchanges:
        print(f"\nCentralized Exchanges ({len(exchanges['cex'])}):")
        for ex in exchanges['cex']:
            print(f"  • {ex['name']} - {ex['pair']}")
        
        print(f"\nDecentralized Exchanges ({len(exchanges['dex'])}):")
        for ex in exchanges['dex']:
            print(f"  • {ex['name']} - {ex['pair']}")
    
    print()
    
    # Step 2: Get current volume breakdown
    print("\nStep 2: Getting current 24h volume breakdown...")
    print("-"*70)
    
    current_volumes = get_current_cex_volume(COIN_ID, API_KEY)
    
    cex_ratio = 0  # Initialize
    cex_percentage = 0  # Initialize
    
    if current_volumes:
        print(f"\nCEX Volume (24h):")
        for vol in sorted(current_volumes['cex'], key=lambda x: x['volume_24h_usd'], reverse=True):
            print(f"  {vol['exchange']:<20} {vol['pair']:<15} ${vol['volume_24h_usd']:>15,.2f}")
        
        print(f"\n  TOTAL CEX: ${current_volumes['total_cex']:,.2f}")
        print(f"  TOTAL DEX: ${current_volumes['total_dex']:,.2f}")
        
        total = current_volumes['total_cex'] + current_volumes['total_dex']
        if total > 0:
            cex_percentage = (current_volumes['total_cex'] / total) * 100
            print(f"\n  CEX represents {cex_percentage:.1f}% of total volume")
            
            # Store this ratio for historical estimation
            cex_ratio = current_volumes['total_cex'] / total if total > 0 else 0
    
    print()
    
    # Step 3: Get historical data for May-October 2025
    print("\nStep 3: Fetching historical volume data (May - October 2025)...")
    print("-"*70)
    
    months = [
        ('May', datetime(2025, 5, 1), datetime(2025, 5, 31, 23, 59, 59)),
        ('June', datetime(2025, 6, 1), datetime(2025, 6, 30, 23, 59, 59)),
        ('July', datetime(2025, 7, 1), datetime(2025, 7, 31, 23, 59, 59)),
        ('August', datetime(2025, 8, 1), datetime(2025, 8, 31, 23, 59, 59)),
        ('September', datetime(2025, 9, 1), datetime(2025, 9, 30, 23, 59, 59)),
        ('October', datetime(2025, 10, 1), datetime(2025, 10, 31, 23, 59, 59))
    ]
    
    monthly_results = []
    
    for month_name, start_date, end_date in months:
        print(f"\nFetching {month_name} 2025...")
        
        df = get_historical_total_volume(COIN_ID, start_date, end_date, API_KEY)
        
        if df is not None and len(df) > 0:
            total_volume = df['volume_usd'].sum()
            avg_daily_volume = df['volume_usd'].mean()
            actual_days = len(df)  # Now this is actual unique days
            
            # Estimate CEX volume using current ratio
            estimated_cex_volume = total_volume * cex_ratio
            estimated_cex_daily_avg = avg_daily_volume * cex_ratio
            
            monthly_results.append({
                'Month': month_name,
                'Days with Data': actual_days,
                'Total Volume (USD)': total_volume,
                'Estimated CEX Volume (USD)': estimated_cex_volume,
                'CEX % of Total': cex_percentage,
                'Avg Daily Total Volume (USD)': avg_daily_volume,
                'Avg Daily CEX Volume (USD)': estimated_cex_daily_avg
            })
            
            print(f"  ✓ Days: {actual_days}")
            print(f"  ✓ Total Volume: ${total_volume:,.2f}")
            print(f"  ✓ Estimated CEX Volume: ${estimated_cex_volume:,.2f}")
        
        # Rate limiting
        time.sleep(1.5)
    
    # Step 4: Display summary
    print("\n" + "="*70)
    print("SUMMARY: HONEY CEX Volume Estimates (May - October 2025)")
    print("="*70)
    print()
    
    summary_df = pd.DataFrame(monthly_results)
    
    # Format for display
    pd.options.display.float_format = '{:,.2f}'.format
    print(summary_df.to_string(index=False))
    
    print(f"\nNote: CEX volume estimated at {cex_percentage:.1f}% of total volume")
    print(f"based on current 24h CEX/Total ratio")
    
    # Save to CSV
    filename = 'honey_cex_volume_may_oct_2025.csv'
    summary_df.to_csv(filename, index=False)
    print(f"\n✓ Data saved to {filename}")

if __name__ == "__main__":
    main()