# screener.py
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

# Tickers to scan
TICKERS = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMZN', 'GOOGL', 'JPM', 'UNH', 'HD']

# Shared models
rf = RandomForestClassifier(n_estimators=100, random_state=42)
xgb = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
logreg = LogisticRegression()

# Cached results
LATEST_RESULTS = pd.DataFrame()

def engineer_features(df):
    df['Return_1d'] = df['Close'].pct_change()
    df['Target'] = (df['Close'].shift(-5) > df['Close'] * 1.02).astype(int)
    df['RSI'] = RSIIndicator(df['Close']).rsi()
    macd = MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    bb = BollingerBands(df['Close'])
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    return df.dropna()

def backtest_model(df, features):
    X = df[features]
    y = df['Target']
    preds = []
    for i in range(200, len(df) - 5):
        X_train = X[:i]
        y_train = y[:i]
        X_pred = X[i:i+1]

        rf.fit(X_train, y_train)
        xgb.fit(X_train, y_train)
        logreg.fit(X_train, y_train)

        avg_prob = (rf.predict_proba(X_pred)[:, 1][0] +
                    xgb.predict_proba(X_pred)[:, 1][0] +
                    logreg.predict_proba(X_pred)[:, 1][0]) / 3
        pred = 1 if avg_prob > 0.6 else 0
        actual = y[i]
        preds.append((pred, actual))

    correct = sum(1 for p, a in preds if p == a and p == 1)
    total = sum(1 for p, _ in preds if p == 1)
    return round((correct / total) * 100, 1) if total else 0, total

def run_screener():
    global LATEST_RESULTS
    results = []
    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period='1y', interval='1d')
            if df.empty:
                print(f"No data for {ticker}")
                continue

            df = engineer_features(df)
            if df.empty:
                print(f"No engineered data for {ticker}")
                continue

            features = ['RSI', 'MACD', 'MACD_Signal', 'BB_High', 'BB_Low', 'Return_1d']
            X = df[features]
            y = df['Target']
            X_train, X_test = X[:-1], X[-1:]
            y_train = y[:-1]

            rf.fit(X_train, y_train)
            xgb.fit(X_train, y_train)
            logreg.fit(X_train, y_train)

            avg_prob = (rf.predict_proba(X_test)[:, 1][0] +
                        xgb.predict_proba(X_test)[:, 1][0] +
                        logreg.predict_proba(X_test)[:, 1][0]) / 3

            if avg_prob > 0.6:
                win_rate, past_signals = backtest_model(df, features)
                signal_label = '🌟 Strong Buy' if avg_prob > 0.7 and win_rate > 65 else '✅ Buy'
                results.append({
                    'Ticker': ticker,
                    'Date': df.index[-1].date(),
                    'RSI': round(X_test['RSI'].values[0], 2),
                    'MACD': round(X_test['MACD'].values[0], 2),
                    'Confidence': f"{avg_prob * 100:.1f}%",
                    'Backtest Win Rate': f"{win_rate}%",
                    'Past Signals': past_signals,
                    'Signal': signal_label
                })
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    LATEST_RESULTS = pd.DataFrame(results)
    return LATEST_RESULTS if not LATEST_RESULTS.empty else pd.DataFrame([{"Message": "No strong signals today."}])
