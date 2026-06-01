import requests

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

event_ticker = "KXRAMBO-35"
markets_resp = requests.get(f"{BASE_URL}/markets", params={"event_ticker": event_ticker})
print(markets_resp.url)
