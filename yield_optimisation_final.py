import json
from web3 import Web3
import numpy as np
from scipy.optimize import minimize_scalar

SECONDS_PER_YEAR = 365 * 24 * 60 * 60
compound_reserve_factor = 0.2
fluid_reserve_factor = 0.1

import json
from web3 import Web3

# Load ABI from file
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\compound_abi.json"
with open(abi_path, 'r') as abi_file:
    abi = json.load(abi_file)

# RPC endpoint and contract address
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
contract_address = "0xd98Be00b5D27fc98112BdE293e487f8D4cA57d07"

# Connect to Arbitrum via Alchemy
web3 = Web3(Web3.HTTPProvider(rpc_url))
contract = web3.eth.contract(address=contract_address, abi=abi)

SECONDS_PER_YEAR = 365 * 24 * 60 * 60

# Function to fetch, convert, and print per-second interest rates
def get_rate(name):
    try:
        raw = int(getattr(contract.functions, name)().call())
        rate = raw * SECONDS_PER_YEAR / 1e18  # Convert to annual rate
        print(f"{name} (per-year calculated): {rate:.6f}")
        return rate

    except Exception as e:
        print(f"Error fetching {name}: {e}")

# Fetch supply kink (this is a utilization ratio between 0–1)
try:
    kink_c = int(contract.functions.supplyKink().call()) / 1e18
    print(f"supplyKink (utilization threshold): {kink_c:.6f}")
except Exception as e:
    print(f"Error fetching supplyKink: {e}")

# Fetch supply kink (this is a utilization ratio between 0–1)
try:
    kink_c = int(contract.functions.borrowKink().call()) / 1e18
    print(f"borrowKink (utilization threshold): {kink_c:.6f}")
except Exception as e:
    print(f"Error fetching borrowKink: {e}")


try:
    totalBorrow_usdt = int(contract.functions.totalBorrow().call())
    print(f"totalBorrow: {totalBorrow_usdt:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")


try:
    totalSupply_usdt = int(contract.functions.totalSupply().call())
    print(f"totalSupply: {totalSupply_usdt:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")



# Fetch rates
s2_c = get_rate("supplyPerSecondInterestRateSlopeHigh")
s1_c = get_rate("supplyPerSecondInterestRateSlopeLow")
s0_c = get_rate("supplyPerSecondInterestRateBase")
r2_c = get_rate("borrowPerSecondInterestRateSlopeHigh")
r1_c = get_rate("borrowPerSecondInterestRateSlopeLow")
r0_c = get_rate("borrowPerSecondInterestRateBase")
c_c = totalBorrow_usdt
d_c = totalSupply_usdt
u_old_c = c_c/d_c


def SC(x, c, d, r0, r1, r2, s0, s1, s2, kink):

    u = c / (d + x)  

    # multi-function below
    if u <= kink:
        r_b = r0 + r1 * u
    else:
        r_b = r0 + r1 * kink + r2 * (u - kink)

    if u <= kink:
        r_s = s0 + s1 * u
    else:
        r_s = s0 + s1 * kink + s2 * (u - kink)

    return u, r_b, r_s


# --------------------- Fluid Setup ---------------------
fluid_abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\fluid_abi.json"
with open(fluid_abi_path, 'r') as abi_file:
    fluid_abi = json.load(abi_file)

fluid_contract_address = "0x46859d33E662d4bF18eEED88f74C36256E606e44"
fluid_contract = web3.eth.contract(address=fluid_contract_address, abi=fluid_abi)
usdt_address = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"

usdt_data = fluid_contract.functions.getOverallTokenData(usdt_address).call()
nested = usdt_data[-1][-1]
rate_at_utilization_kink1 = nested[-3] / 100
rate_at_utilization_kink2 = nested[-2] / 100
rate_at_utilization_max = nested[-1] / 100
u2 = nested[-5] / 100
u1 = nested[-6] / 100
d_f = usdt_data[12]
c_f = usdt_data[13]

print("Fluid Inputs:")
print(f"Rate at Kink1: {rate_at_utilization_kink1:.4f}")
print(f"Rate at Kink2: {rate_at_utilization_kink2:.4f}")
print(f"Rate at Max:   {rate_at_utilization_max:.4f}")
print(f"Utilization Kink1 (u1): {u1:.2f}%")
print(f"Utilization Kink2 (u2): {u2:.2f}%")
print(f"Total Borrowed (c_f): {c_f}")
print(f"Total Supplied (d_f): {d_f}")
print(f"Reserve Factor: {fluid_reserve_factor}\n")

slope1 = (rate_at_utilization_kink1 - 0) / (u1 - 0)
slope2 = (rate_at_utilization_kink2 - rate_at_utilization_kink1) / (u2 - u1)
slope3 = (rate_at_utilization_max - rate_at_utilization_kink2) / (100 - u2)

print("Fluid Slopes:")
print(f"Slope1: {slope1:.6f}")
print(f"Slope2: {slope2:.6f}")
print(f"Slope3: {slope3:.6f}\n")

def SF(x, c, d, r0, r1, r2, r3, kink1, kink2, rf):
    u = c / (d + x)
    if u <= kink1:
        r_b = r0 + r1 * u
    elif u <= kink2:
        r_b = r0 + r1 * kink1 + r2 * (u - kink1)
    else:
        r_b = r0 + r1 * kink1 + r2 * (kink2 - kink1) + r3 * (u - kink2)
    r_s = r_b * u * (1 - rf)
    return u, r_b, r_s



# --------------------- Optimization ---------------------

T = 1e13  
compound_params = (r0_c, r1_c, r2_c, s0_c, s1_c, s2_c, kink_c)
fluid_params = (0, slope1, slope2, slope3, u1 / 100, u2 / 100, fluid_reserve_factor)

def objective(x):
    u_c, r_b_c, r_s_c = SC(x, c_c, d_c, *compound_params)
    u_f, r_b_f, r_s_f = SF(T - x, c_f, d_f, *fluid_params)
    total_yield = r_s_c * x + r_s_f * (T - x)
    return -total_yield  

result = minimize_scalar(objective, bounds=(0, T), method='bounded')

if result.success:
    x_opt = result.x
    u_c, r_b_c, r_s_c = SC(x_opt, c_c, d_c, *compound_params)
    u_f, r_b_f, r_s_f = SF(T - x_opt, c_f, d_f, *fluid_params)

    total_yield = r_s_c * x_opt + r_s_f * (T - x_opt)
    strategy_apr = (total_yield / T) * 100


u_c, r_b_c, rsc_if = SC(T, c_c, d_c, *compound_params)
u_f, r_b_f, rsf_if = SF(T, c_f, d_f, *fluid_params)

_,_, curr_c = SC(0,c_c, d_c, *compound_params)
_,_, curr_f = SF(0,c_f, d_f, *fluid_params)


print(f"\n Optimal allocation to Compound (x): {x_opt:,.2f}")
print(f" Optimal allocation to Fluid (T - x): {T - x_opt:,.2f}")

print(f"\n Current supply apr on Compound -> APR: {curr_c * 100:.4f}%")
print(f"Current supply apr on Fluid -> APR: {curr_f * 100:.4f}%")

print(f"\n If only on Compound -> APR: {rsc_if * 100:.4f}%")
print(f"If only on Fluid -> APR: {rsf_if * 100:.4f}%")
print(f"Strategy APR -> {strategy_apr:.4f}%\n")

import matplotlib.pyplot as plt

# Generate a range of allocation values (x) between 0 and T
allocations = np.linspace(0, T, 100)

# Calculate APRs and yields for each allocation
compound_aprs = []
fluid_aprs = []
total_yields = []

for x in allocations:
    # Get the APR for Compound and Fluid for each allocation
    u_c, r_b_c, r_s_c = SC(x, c_c, d_c, *compound_params)
    u_f, r_b_f, r_s_f = SF(T - x, c_f, d_f, *fluid_params)
    
    total_yield = r_s_c * x + r_s_f * (T - x)
    compound_apr = r_s_c * 100  # Compound APR
    fluid_apr = r_s_f * 100     # Fluid APR
    
    compound_aprs.append(compound_apr)
    fluid_aprs.append(fluid_apr)
    total_yields.append(total_yield)


# Plot 1: APR vs Allocation
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.plot(allocations, compound_aprs, label="Compound APR", color='b')
plt.plot(allocations, fluid_aprs, label="Fluid APR", color='g')
plt.xlabel('Allocation to Compound (x)')
plt.ylabel('APR (%)')
plt.title('APR vs Allocation')
plt.legend()

# Plot 2: Total Yield vs Allocation
plt.subplot(1, 2, 2)
plt.plot(allocations, total_yields, label="Total Yield", color='r')
plt.xlabel('Allocation to Compound (x)')
plt.ylabel('Total Yield')
plt.title('Total Yield vs Allocation')
plt.legend()

# Show the plots
plt.tight_layout()
plt.show()











