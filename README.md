# HONEY Token CEX Volume Analysis

A Python script to analyze centralized exchange (CEX) volume for the HONEY token using the CoinGecko API.

## Features

- Identifies all exchanges (CEX and DEX) where the token trades
- Calculates current 24h CEX volume breakdown
- Estimates historical CEX volume for specified date ranges
- Exports results to CSV

## Setup

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your CoinGecko API key:
     ```
     COINGECKO_API_KEY=your_api_key_here
     COIN_ID=hivemapper
     ```
   
   **Note:** The API key is optional for basic usage, but recommended for higher rate limits. Get your API key from [CoinGecko API Pricing](https://www.coingecko.com/en/api/pricing).

## Usage

Run the script:
```bash
python honey_cex_volume.py
```

The script will:
1. Identify all exchanges where HONEY trades
2. Calculate current 24h CEX volume breakdown
3. Fetch historical volume data for May - October 2025
4. Generate a CSV file with monthly CEX volume estimates

## Output

The script generates `honey_cex_volume_may_oct_2025.csv` with the following columns:
- Month
- Days with Data
- Total Volume (USD)
- Estimated CEX Volume (USD)
- CEX % of Total
- Avg Daily Total Volume (USD)
- Avg Daily CEX Volume (USD)

## Configuration

You can modify the following in the `.env` file:
- `COINGECKO_API_KEY`: Your CoinGecko API key (optional)
- `COIN_ID`: The CoinGecko coin ID to analyze (default: "hivemapper")

## Requirements

- Python 3.7+
- requests
- pandas
- python-dotenv

## License

MIT

