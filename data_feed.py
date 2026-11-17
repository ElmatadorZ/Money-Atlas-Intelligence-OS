import requests

def get_btc_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    return float(requests.get(url, timeout=10).json()["price"])

def get_macro_news():
    url = "https://newsapi.org/v2/top-headlines?category=business&apiKey=YOUR_API_KEY"
    return requests.get(url, timeout=10).json()
