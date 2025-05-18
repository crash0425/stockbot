# app.py
from flask import Flask, render_template_string
from screener import run_screener, LATEST_RESULTS
import threading
import time
import pytz
from datetime import datetime
import os
from twilio.rest import Client

app = Flask(__name__)

last_run_time = "Never"

# Twilio setup (use environment variables for security)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

def send_sms_alert(message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(
            body=message,
            from_=TWILIO_FROM,
            to=TWILIO_TO
        )
        print("✅ SMS alert sent.")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")

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
    <p><strong>Last updated:</strong> {{ last_run }}</p>
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

@app.route("/screener")
def screener():
    global last_run_time
    df = LATEST_RESULTS if not LATEST_RESULTS.empty else run_screener()
    return render_template_string(HTML_TEMPLATE, columns=df.columns, data=df.to_dict(orient="records"), last_run=last_run_time)

def scheduler():
    global last_run_time
    while True:
        now = datetime.now(pytz.timezone('US/Eastern'))
        if now.hour == 9 and now.minute == 0:
            print("Running scheduled screener...")
            df = run_screener()
            last_run_time = now.strftime("%Y-%m-%d %I:%M %p EST")

            strong_buys = df[df['Signal'] == '🌟 Strong Buy']['Ticker'].tolist()
            if strong_buys:
                alert = f"📈 Swing Trade Alert\n🌟 Strong Buy: {', '.join(strong_buys)}\nAs of {last_run_time}"
                send_sms_alert(alert)

            time.sleep(60)  # Prevent multiple runs within the same minute
        time.sleep(30)

if __name__ == "__main__":
    thread = threading.Thread(target=scheduler)
    thread.daemon = True
    thread.start()
    app.run(host="0.0.0.0", port=5000)
