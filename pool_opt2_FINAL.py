import math
import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

with open(r'C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\LP_pancake_abi.json') as f:
    V3_ABI = json.load(f)

POOL_ADDRESS = '0x4f31Fa980a675570939B737Ebdde0471a4Be40Eb'
pool = w3.eth.contract(address=POOL_ADDRESS, abi=V3_ABI)

# --- FETCH POOL METADATA ---
slot0 = pool.functions.slot0().call()
sqrtPriceX96 = slot0[0]
current_tick = slot0[1]
tick_spacing = pool.functions.tickSpacing().call()
token0 = pool.functions.token0().call()
token1 = pool.functions.token1().call()

# Fetch decimals
erc20_abi = '[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
token0_contract = w3.eth.contract(address=token0, abi=json.loads(erc20_abi))
token1_contract = w3.eth.contract(address=token1, abi=json.loads(erc20_abi))
decimals0 = 18
decimals1 = 18

# --- Specify tick range ---
tick_lower = current_tick
tick_upper = current_tick + tick_spacing

# --- CALCULATE NET LIQUIDITY IN RANGE ---
liquidity = 0
for tick in range(tick_lower, tick_upper + 1, tick_spacing):
    tick_data = pool.functions.ticks(tick).call()
    liquidity_gross = tick_data[0]  
    liquidity += liquidity_gross

# --- CALCULATE PRICES ---
def tick_to_price(tick):
    return 1.0001 ** tick

def price_to_sqrtp(p):
    q96 = 2 ** 96
    return int(math.sqrt(p) * q96)

pa = tick_to_price(tick_lower)
pb = tick_to_price(tick_upper)
sqrtp_low = price_to_sqrtp(pa)
sqrtp_upp = price_to_sqrtp(pb)
sqrtP = sqrtPriceX96  # Already in Q64.96 format

#------------------------------------------------------------------------
# --- USER'S LIQUIDITY Provision CALCULATION ---

def calculate_liquidity(amount0, amount1, sqrt_a, sqrt_b):
    q96 = 2 ** 96
    liq0 = (amount0 * (sqrt_a * sqrt_b) // q96) // (sqrt_b - sqrt_a) if sqrt_b != sqrt_a else 0
    liq1 = (amount1 * q96) // (sqrt_b - sqrt_a) if sqrt_b != sqrt_a else 0
    return min(liq0, liq1)

# Get user input
user_usdc = float(input("\nEnter USDC amount to deposit: "))
user_usdt = float(input("Enter USDT amount to deposit: "))

# Convert to raw units
amount0_raw = int(user_usdc * 10**decimals0)
amount1_raw = int(user_usdt * 10**decimals1)

# Calculate liquidity
user_liq = calculate_liquidity(amount0_raw, amount1_raw, sqrtp_low, sqrtp_upp)

print(f"\nYour liquidity contribution: {user_liq}")
print(f"\n Grossliquidity there: {liquidity}")

print(f"\n Ratio: {user_liq/liquidity}")
