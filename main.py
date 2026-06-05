from datetime import datetime, timedelta

import requests

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

# Get resolved events
params = {
    "status": "settled",
    "limit": 5,
}
response = requests.get(f"{BASE_URL}/events", params=params)
events_data = response.json()

# print(events_data)

upsets = []
print(events_data)

for event in events_data.get("events", []):
    event_ticker = event["event_ticker"]

    # Get markets for this event
    markets_resp = requests.get(f"{BASE_URL}/markets", params={"event_ticker": event_ticker})
    markets = markets_resp.json().get("markets", [])
    if not markets:
        continue

    for market in markets:
        result = market.get("result")
        close_time = market.get("close_time")  # ISO timestamp

        if result and close_time:
            # Parse close time and get 1 hour before
            close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
            one_hour_before = close_dt - timedelta(hours=1)

            # Get candlesticks around that time
            series_ticker = market.get("series_ticker")
            print(series_ticker)
            candles_resp = requests.get(
                f"{BASE_URL}/series/{series_ticker}/markets/{market['ticker']}/candlesticks",
                params={
                    "start_ts": int(one_hour_before.timestamp()),
                    "end_ts": int(close_dt.timestamp()),
                    "period_interval": 1,  # 60-minute candles
                },
            )
            print(f"URL: {candles_resp.url}")
            print(f"Status: {candles_resp.status_code}")
            print(f"Response: {candles_resp.text[:500]}")
            candles = candles_resp.json().get("candlesticks", [])

            if candles:
                # Use the first candle's open price (price ~1 hour before close)
                price_before_close = (
                    float(candles[0]["yes_bid"]["close_dollars"])
                    + float(candles[0]["yes_ask"]["close_dollars"])
                ) / 2
            else:
                price_before_close = None

            if price_before_close is not None:
                if result == "yes" and price_before_close < 80:
                    upsets.append(
                        {
                            "title": market["title"],
                            "ticker": market["ticker"],
                            "result": result,
                            "last_price_before": price_before_close,
                            "subtitle": market.get("subtitle", ""),
                        }
                    )
                elif result == "no" and price_before_close > 20:
                    upsets.append(
                        {
                            "title": market["title"],
                            "ticker": market["ticker"],
                            "result": result,
                            "last_price_before": price_before_close,
                            "subtitle": market.get("subtitle", ""),
                        }
                    )

# Sort by how unlikely the outcome was
upsets.sort(
    key=lambda x: x["last_price_before"] if x["result"] == "yes" else 100 - x["last_price_before"]
)

print(f"Found {len(upsets)} upsets:\n")
for u in upsets[:20]:
    if u["result"] == "yes":
        prob = u["last_price_before"]
    else:
        prob = 100 - u["last_price_before"]
    print(f"  {u['title']}")
    print(f"    Result: {u['result']} | Implied probability was ~{prob}%")
    print()
