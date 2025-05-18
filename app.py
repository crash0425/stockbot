from flask import Flask, render_template_string
from screener import run_screener, LATEST_RESULTS

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
    return "<h2>✅ Swing Trade Screener is live. Visit <a href='/screener'>/screener</a> to view signals.</h2>"

@app.route("/screener")
def screener():
    df = LATEST_RESULTS if not LATEST_RESULTS.empty else run_screener()
    return render_template_string(HTML_TEMPLATE, columns=df.columns, data=df.to_dict(orient="records"))

@app.route("/test-alert")
def test_alert():
    df = run_screener()
    strong_buys = df[df['Signal'] == '🌟 Strong Buy']['Ticker'].tolist()
    return f"Test complete. Strong Buy tickers: {', '.join(strong_buys) if strong_buys else 'None'}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
