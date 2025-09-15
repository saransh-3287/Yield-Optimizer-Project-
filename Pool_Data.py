import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Step 1: Fetch historical ETH prices for last 180 days from CoinGecko ---
url = 'https://api.coingecko.com/api/v3/coins/ethereum/market_chart'
params = {'vs_currency': 'usd', 'days': '180'}
response = requests.get(url, params=params)
data = response.json()

# Extract prices and convert to DataFrame
prices = data['prices']  # list of [timestamp, price]
df1 = pd.DataFrame(prices, columns=['timestamp', 'Price'])
df1['Date'] = pd.to_datetime(df1['timestamp'], unit='ms')
df1 = df1[['Date', 'Price']]
df1 = df1.sort_values('Date').reset_index(drop=True)

# --- Step 2: Safe LTV simulation ---
supplied_usdc = 1e5
liquidation_ltv = 0.78

def simulate_ltv_over_time(safe_ltv, price_df, supplied_usdc, liquidation_ltv):
    price_initial = price_df['Price'].iloc[0]
    borrowed_initial_eth = (safe_ltv * supplied_usdc) / price_initial
    ltv_series = price_df['Price'] * borrowed_initial_eth / supplied_usdc
    crosses_liquidation = (ltv_series > liquidation_ltv).any()
    return crosses_liquidation, borrowed_initial_eth, ltv_series

safe_ltv_values = np.arange(0.50, liquidation_ltv, 0.001)
results = []

for ltv in safe_ltv_values:
    crosses, borrowed_eth, ltv_series = simulate_ltv_over_time(
        ltv, df1, supplied_usdc, liquidation_ltv
    )
    if not crosses:
        results.append((ltv, borrowed_eth))

if results:
    max_safe_ltv, max_borrowed_eth = max(results, key=lambda x: x[0])
    print(f"Maximum safe LTV: {max_safe_ltv:.3f} ({max_safe_ltv*100:.2f}%)")
    print(f"Corresponding borrowed ETH: {max_borrowed_eth:.6f}")

    # Plot LTV over time
    _, _, ltv_series = simulate_ltv_over_time(max_safe_ltv, df1, supplied_usdc, liquidation_ltv)
    plt.figure(figsize=(14,7))
    plt.plot(df1['Date'], ltv_series, color='deepskyblue', label='LTV over time')
    plt.axhline(y=liquidation_ltv, color='red', linestyle='--', linewidth=3, label='Liquidation LTV (78%)')
    plt.axhline(y=max_safe_ltv, color='green', linestyle='--', linewidth=2, label=f'Max Safe LTV ({max_safe_ltv*100:.2f}%)')
    plt.xlabel('Date')
    plt.ylabel('LTV')
    plt.title('LTV Simulation Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
else:
    print("No safe LTV found that avoids liquidation over the price history.")
