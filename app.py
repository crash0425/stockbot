from flask import Flask, render_template_string
from screener import run_screener, LATEST_RESULTS
import os
from twilio.rest import Client

app = Flask(__name__)

# Twilio setup
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

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
    try:
        df = run_screener()
        if 'Signal' in df.columns and not df.empty:
            strong_buys = df[df['Signal'] == '🌟 Strong Buy']['Ticker'].tolist()
            if strong_buys:
                message = f"📈 Swing Trade Alert\n🌟 Strong Buy: {', '.join(strong_buys)}"
                try:
                    client = Client(TWILIO_SID, TWILIO_AUTH)
                    client.messages.create(body=message, from_=TWILIO_FROM, to=TWILIO_TO)
                    return f"SMS sent: {message}"
                except Exception as sms_error:
                    return f"❌ SMS failed: {sms_error}"
            else:
                return "No Strong Buy signals today."
        else:
            return "No Strong Buy signals today."
    except Exception as e:
        return f"Error during test-alert: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
