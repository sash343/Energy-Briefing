"""
Morning Energy Briefing — Daily Auto-Texter
Fetches top energy & market headlines via NewsAPI,
then sends SMS via Twilio.
"""

import os
import requests
from twilio.rest import Client
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
NEWS_API_KEY       = os.environ["NEWS_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM_NUMBER = os.environ["TWILIO_FROM_NUMBER"]

RECIPIENT_NUMBERS = [
    os.environ.get("RECIPIENT_1", ""),
    os.environ.get("RECIPIENT_2", ""),
    os.environ.get("RECIPIENT_3", ""),
    os.environ.get("RECIPIENT_4", ""),
    os.environ.get("RECIPIENT_5", ""),
]
RECIPIENT_NUMBERS = [n for n in RECIPIENT_NUMBERS if n]

# ── Fetch headlines ───────────────────────────────────────────────────────────
def fetch_headlines() -> list[dict]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "energy OR oil OR gas OR renewables OR utilities OR electricity markets",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY,
        "domains": "wsj.com,reuters.com,bloomberg.com,cnbc.com,ft.com,nytimes.com",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    articles = response.json().get("articles", [])[:10]
    return articles


# ── Build SMS message ─────────────────────────────────────────────────────────
def build_message(articles: list[dict]) -> str:
    today = datetime.now().strftime("%A, %B %d")
    lines = "\n\n".join(
        f"{i+1}. [{a['source']['name']}] {a['title']}\n{a['url']}"
        for i, a in enumerate(articles)
    )
    return f"☀️ Energy & Market Briefing — {today}\n\n{lines}"


# ── Send SMS via Twilio ───────────────────────────────────────────────────────
def send_sms(message: str):
    twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    for number in RECIPIENT_NUMBERS:
        twilio.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=number,
        )
        print(f"  ✓ Sent to {number}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Fetching energy headlines...")
    try:
        articles = fetch_headlines()
        print(f"  ✓ Got {len(articles)} articles")
        message = build_message(articles)
        print("  ✓ Message built")
        send_sms(message)
        print("  ✓ All texts sent")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
