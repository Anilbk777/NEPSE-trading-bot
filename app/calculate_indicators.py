import pandas as pd
import os

def calculate_indicators(file_path):
    print(f'Loading data from {file_path}...')
    df = pd.read_csv(file_path)
    df = df.sort_values(by=['symbol', 'tradedate'])
    
    print('Calculating Moving Averages...')
    df['MA20'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df['MA50'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(50, min_periods=1).mean())
    
    print('Calculating RSI...')
    delta = df.groupby('symbol')['close'].transform(lambda x: x.diff())
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14, min_periods=1).mean()
    avg_loss = loss.rolling(14, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    print('Calculating Bollinger Bands...')
    df['BB_MID'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(20, min_periods=1).mean())
    df['BB_STD'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(20, min_periods=1).std())
    df['BB_UPPER'] = df['BB_MID'] + 2 * df['BB_STD']
    df['BB_LOWER'] = df['BB_MID'] - 2 * df['BB_STD']
    
    print('Calculating MACD...')
    df['EMA12'] = df.groupby('symbol')['close'].transform(lambda x: x.ewm(span=12, adjust=False).mean())
    df['EMA26'] = df.groupby('symbol')['close'].transform(lambda x: x.ewm(span=26, adjust=False).mean())
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['MACD_Signal'] = df.groupby('symbol')['MACD'].transform(lambda x: x.ewm(span=9, adjust=False).mean())
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    output_dir = 'data/processed'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'stock_data_with_indicators.csv')
    df.to_csv(output_path, index=False)
  
    return df

if __name__ == '__main__':
    calculate_indicators('data/stock_data_ready.csv')
