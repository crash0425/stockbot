# app.py
from flask import Flask, render_template_string
from screener import run_screener
from yahoo_fin.stock_info import tickers_sp500

app = Flask(__name__)

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
    tickers = tickers_sp500()[:250]
    df = run_screener(tickers)
    return render_template_string(HTML_TEMPLATE, columns=df.columns, data=df.to_dict(orient="records"))

@app.route("/test-alert")
def test_alert():
    tickers = tickers_sp500()[:100]
    df = run_screener(tickers)
    strong_buys = df[df['Signal'] == '🌟 Strong Buy']['Ticker'].tolist() if 'Signal' in df.columns else []
    return f"Strong Buy tickers: {', '.join(strong_buys) if strong_buys else 'None'}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
