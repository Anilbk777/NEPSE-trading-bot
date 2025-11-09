import pandas as pd
from langchain_core.documents import Document

def stock_to_text_chunks(file_path, last_n_days=60, chunk_size=5):
    """
    Convert stock data with indicators into text chunks for RAG.
    Creates chunks of N days per stock for better semantic search.

    Args:
        file_path: Path to the CSV file with stock data and indicators
        last_n_days: Number of recent days to include per stock (default: 60)
        chunk_size: Number of days per chunk (default: 5 for weekly patterns)

    Returns:
        List of Document objects containing stock information
    """
    df = pd.read_csv(file_path)

    # Sort by symbol and date
    df = df.sort_values(by=['symbol', 'tradedate'])

    docs = []
    symbols = df['symbol'].unique()


    for symbol in symbols:
        # Get last N days for each symbol
        stock_df = df[df['symbol'] == symbol].tail(last_n_days)

        if stock_df.empty:
            continue

        # Split into chunks of chunk_size days
        for i in range(0, len(stock_df), chunk_size):
            chunk_df = stock_df.iloc[i:i+chunk_size]

            if chunk_df.empty:
                continue

            # Get first and last date in chunk
            start_date = chunk_df.iloc[0]['tradedate']
            end_date = chunk_df.iloc[-1]['tradedate']
            latest = chunk_df.iloc[-1]

            # Calculate chunk statistics
            avg_volume = chunk_df['vol'].mean()
            price_change = ((latest['close'] - chunk_df.iloc[0]['close']) / chunk_df.iloc[0]['close']) * 100

            # Build chunk document
            doc_text = f"""Stock: {symbol}
Period: {start_date} to {end_date} ({len(chunk_df)} days)

=== LATEST IN PERIOD ===
Date: {latest['tradedate']}
Close: {latest['close']:.2f} | Open: {latest['open']:.2f} | High: {latest['high']:.2f} | Low: {latest['low']:.2f}
Volume: {latest['vol']} | VWAP: {latest['vwap']:.2f}

Technical Indicators:
- MA20: {latest['MA20']:.2f} | MA50: {latest['MA50']:.2f}
- RSI: {latest['RSI']:.2f}
- Bollinger Bands: Upper={latest['BB_UPPER']:.2f}, Mid={latest['BB_MID']:.2f}, Lower={latest['BB_LOWER']:.2f}
- MACD: {latest['MACD']:.2f} | Signal: {latest['MACD_Signal']:.2f} | Histogram: {latest['MACD_Hist']:.2f}

Price Analysis:
- Period Change: {price_change:.2f}%
- 52W High: {latest['52 weeks high']:.2f} | 52W Low: {latest['52 weeks low']:.2f}
- Avg Volume: {avg_volume:.0f}

=== DAILY DATA ==="""

            # Add each day's data
            for _, row in chunk_df.iterrows():
                doc_text += f"""
{row['tradedate']}: Close={row['close']:.2f}, Vol={row['vol']}, RSI={row['RSI']:.2f}, MA20={row['MA20']:.2f}, Change={row['diff %']:.2f}%"""

            # Add metadata for filtering
            metadata = {
                "symbol": symbol,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "latest_close": float(latest['close']),
                "latest_rsi": float(latest['RSI']),
                "period_change": float(price_change)
            }

            docs.append(Document(page_content=doc_text.strip(), metadata=metadata))

    return docs

if __name__ == "__main__":
    docs = stock_to_text_chunks("data/processed/stock_data_with_indicators.csv")

