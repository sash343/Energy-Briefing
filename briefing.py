"""
Morning Energy Briefing — Daily Auto-Texter
Runs every day at 7:00 AM, fetches top 10 energy & market headlines
via Anthropic API (with web search), then sends SMS via Twilio.

Setup: see README.md
"""

import os
import json
import anthropic
from twilio.rest import Client
from datetime import datetime

# ── Config (set these as environment variables) ──────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM_NUMBER = os.environ["TWILIO_FROM_NUMBER"]   # e.g. +12015550100

# Add every recipient's number here
RECIPIENT_NUMBERS = [
    os.environ.get("RECIPIENT_1", ""),
    os.environ.get("RECIPIENT_2", ""),
    os.environ.get("RECIPIENT_3", ""),
    os.environ.get("RECIPIENT_4", ""),
    os.environ.get("RECIPIENT_5", ""),
]
RECIPIENT_NUMBERS = [n for n in RECIPIENT_NUMBERS if n]   # drop blanks

# ── Fetch headlines ───────────────────────────────────────────────────────────
def fetch_headlines() -> list[dict]:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today is {today}. Search the web and find the 10 most important
news articles from TODAY about the energy sector (oil, gas, renewables,
utilities, energy policy) and financial markets broadly.

Prioritize: WSJ, NYT, Bloomberg, Reuters, FT, CNBC.
Include a mix of energy-specific and broader market stories
relevant to energy investors.

Respond ONLY with a JSON array of exactly 10 objects — no preamble,
no markdown, no backticks. Each object must have:
  "title"  : headline text
  "url"    : full article URL
  "source" : publication (e.g. "WSJ", "Bloomberg")
  "summary": one sentence (max 15 words) on why it matters

Return only the raw JSON array."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )

    text_block = next((b for b in response.content if b.type == "text"), None)
    if not text_block:
        raise ValueError("No text in API response")

    raw = text_block.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)[:10]


# ── Build SMS message ─────────────────────────────────────────────────────────
def build_message(articles: list[dict]) -> str:
    today = datetime.now().strftime("%A, %B %d")
    lines = "\n\n".join(
        f"{i+1}. [{a['source']}] {a['title']}\n{a['url']}"
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
