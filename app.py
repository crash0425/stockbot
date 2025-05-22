# app.py
from flask import Flask, render_template_string
from screener import run_screener
from yahoo_fin.stock_info import tickers_sp500, tickers_nasdaq

app = Flask(__name__)

def generate_summary(df):
    if 'Signal' not in df.columns or df.empty:
        return "No data available."

    strong = df[df['Signal'] == '🌟 Strong Buy']
    weak = df[df['Signal'].str.lower().str.contains("none") | df['Signal'].str.lower().str.contains("no")]

    if len(strong) >= 5:
        top_tickers = ', '.join(strong['Ticker'].tolist()[:5])
        return f"Strong bullish momentum detected in: {top_tickers}. Check for possible swing entries."
    elif len(weak) >= len(df) * 0.8:
        return "Mostly weak or indecisive signals across the market. Consider holding or watching."
    else:
        return "Market appears mixed. A few opportunities exist, but broader confirmation is lacking."

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Swing Trade Screener</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        tr:hover { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>📈 Daily Swing Trade Screener</h1>
    <p><strong>🧠 Market Insight:</strong> {{ summary }}</p>
    <table>
        <thead>
            <tr>
                {% for col in columns %}<th>{{ col }}</th>{% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in data %}
            <tr>
                {% for col in columns %}<td>{{ row[col] }}</td>{% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route("/")
def home():
    return "✅ Swing Trade Screener is live", 200

@app.route("/screener")
def screener():
    tickers = list(set(tickers_sp500() + tickers_nasdaq()))
    df = run_screener(tickers)
    summary = generate_summary(df)
    return render_template_string(HTML_TEMPLATE, columns=df.columns, data=df.to_dict(orient="records"), summary=summary)

@app.route("/test-alert")
def test_alert():
    tickers = tickers_sp500()
    df = run_screener(tickers)
    strong_buys = df[df['Signal'] == '🌟 Strong Buy']['Ticker'].tolist() if 'Signal' in df.columns else []
    return f"Strong Buy tickers: {', '.join(strong_buys) if strong_buys else 'None'}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
