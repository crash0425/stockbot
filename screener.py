# screener.py
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from yahoo_fin.stock_info import get_quote_table, get_income_statement
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

# Cached results
LATEST_RESULTS = pd.DataFrame()

def run_screener(tickers):
    results = []
    for ticker in tickers:
        try:
            # Sector check
            info = yf.Ticker(ticker).info
            sector = info.get('sector', None)
            if sector != 'Technology':
                continue

            # Historical price data
            df = yf.download(ticker, period='6mo', interval='1d')
            if df.empty or len(df) < 50:
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

            # Fundamentals
            fundamentals = get_quote_table(ticker, dict_result=True)
            income_statement = get_income_statement(ticker, quarterly=False)
            revenue_growth = None
            earnings_growth = None
            try:
                revenue_current = income_statement.loc['totalRevenue'].iloc[0]
                revenue_prev = income_statement.loc['totalRevenue'].iloc[1]
                earnings_current = income_statement.loc['netIncome'].iloc[0]
                earnings_prev = income_statement.loc['netIncome'].iloc[1]
                revenue_growth = (revenue_current - revenue_prev) / revenue_prev
                earnings_growth = (earnings_current - earnings_prev) / abs(earnings_prev)
            except:
                pass

            pe_ratio = fundamentals.get("PE Ratio (TTM)", None)
            eps = fundamentals.get("EPS (TTM)", None)

            if (
                latest['Rel_Volume'] > 1.5 and
                30 <= latest['RSI'] <= 70 and
                latest['above_50ma'] and
                latest['Close'] > latest['BB_High'] * 0.95 and
                latest['MACD'] > latest['MACD_Signal'] and
                (pe_ratio is None or 5 < pe_ratio < 50) and
                (eps is not None and eps > 0) and
                (revenue_growth is not None and revenue_growth > 0.05) and
                (earnings_growth is not None and earnings_growth > 0.05)
            ):
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
                    'PE Ratio': pe_ratio,
                    'EPS': eps,
                    'Revenue Growth': round(revenue_growth * 100, 2) if revenue_growth else None,
                    'Earnings Growth': round(earnings_growth * 100, 2) if earnings_growth else None
                })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    global LATEST_RESULTS
    LATEST_RESULTS = pd.DataFrame(results)
    return LATEST_RESULTS
