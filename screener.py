# screener.py
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

# Cached results
LATEST_RESULTS = pd.DataFrame()

def run_screener(tickers):
    results = []
    for ticker in tickers:
        if not ticker.isalpha() or len(ticker) < 1:
            continue
        try:
            # Sector check
            # info = yf.Ticker(ticker).info  # Temporarily disabled to reduce memory load
            sector = 'Technology'  # Assume tech sector for testing
            if sector != 'Technology':
                continue

            # Historical price data
            df = yf.download(ticker, period='6mo', interval='1d')
            if df.empty or len(df) < 50 or df.isnull().sum().sum() > 0 or df.isna().any().any():
                print(f"Skipping {ticker}: insufficient or corrupted data")
                continue

            df['20ma'] = df['Close'].rolling(window=20).mean()
            df['50ma'] = df['Close'].rolling(window=50).mean()
            df['200ma'] = df['Close'].rolling(window=200).mean()
            df['above_20ma'] = df['Close'] > df['20ma']
            df['above_50ma'] = df['Close'] > df['50ma']
            df['above_200ma'] = df['Close'] > df['200ma']

            # Indicators
            df['RSI'] = RSIIndicator(df['Close']).rsi()
            macd = MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            bb = BollingerBands(df['Close'])
            df['BB_High'] = bb.bollinger_hband()
            df['BB_Low'] = bb.bollinger_lband()
            atr = AverageTrueRange(df['High'], df['Low'], df['Close'])
            df['ATR'] = atr.average_true_range()

            # Relative volume
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Rel_Volume'] = df['Volume'] / df['Volume_MA']

            latest = df.iloc[-1]

            # Fundamentals temporarily disabled to reduce memory load
            pe_ratio = None
            eps = None

            if (
                latest['Rel_Volume'] > 1.2 and
                20 <= latest['RSI'] <= 80 and
                latest['MACD'] > latest['MACD_Signal']
            ):
                explanation = f"RSI: {round(latest['RSI'], 2)}, MACD > Signal: {latest['MACD'] > latest['MACD_Signal']}, Price above 50MA: {latest['above_50ma']}, Volume surge: Rel Vol = {round(latest['Rel_Volume'], 2)}"
                results.append({
                    'Ticker': ticker,
                    'Close': round(latest['Close'], 2),
                    'Volume': int(latest['Volume']),
                    'Rel Vol': round(latest['Rel_Volume'], 2),
                    'RSI': round(latest['RSI'], 2),
                    'ATR': round(latest['ATR'], 2),
                    'Above 50MA': latest['above_50ma'],
                    'MACD > Signal': latest['MACD'] > latest['MACD_Signal'],
                    'Near BB High': latest['Close'] > latest['BB_High'] * 0.95,
                    'Signal': '🌟 Strong Buy',
                    'Explanation': explanation,
                    
                    
                })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    global LATEST_RESULTS
    LATEST_RESULTS = pd.DataFrame(results)
    if LATEST_RESULTS.empty:
        LATEST_RESULTS = pd.DataFrame([{"Ticker": "No matches", "Signal": "None"}])
    return LATEST_RESULTS
