import requests

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

# Get resolved events
params = {
    "status": "settled",
    "limit": 200,
}
response = requests.get(f"{BASE_URL}/events", params=params)
events_data = response.json()

# print(events_data)

upsets = []

for event in events_data.get("events", []):
    event_ticker = event["event_ticker"]

    # Get markets for this event
    markets_resp = requests.get(f"{BASE_URL}/markets", params={"event_ticker": event_ticker})
    markets = markets_resp.json().get("markets", [])
    print(markets)

    for market in markets:
        # result = "yes" or "no", yes_price was the probability of yes happening
        result = market.get("result")
        last_price = market.get("last_price")  # last traded price (0-100 cents)

        if result and last_price is not None:
            # If "yes" won but yes_price was low, or "no" won but yes_price was high
            if result == "yes" and last_price < 50:
                upsets.append(
                    {
                        "title": market["title"],
                        "ticker": market["ticker"],
                        "result": result,
                        "last_price_before": last_price,
                        "subtitle": market.get("subtitle", ""),
                    }
                )
            elif result == "no" and last_price > 50:
                upsets.append(
                    {
                        "title": market["title"],
                        "ticker": market["ticker"],
                        "result": result,
                        "last_price_before": last_price,
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
