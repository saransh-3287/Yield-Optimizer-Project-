import requests

API_URL = "https://api.venus.io/api/v1/markets"
params = {
    "underlyingSymbol": "USDC",
    "blockchainId": 56  # BNB Chain
}
headers = {
    "accept-version": "stable"
}

response = requests.get(API_URL, params=params, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"API request failed with status code: {response.status_code}")
    print(response.text)
