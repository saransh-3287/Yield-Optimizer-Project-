# DATA FOR USDC 




import json
from web3 import Web3

# Load ABI from file
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\compound_abi.json"
with open(abi_path, 'r') as abi_file:
    abi = json.load(abi_file)

# RPC endpoint and contract address
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
contract_address = "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf"

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
    kink_usdc = int(contract.functions.supplyKink().call()) / 1e18
    print(f"supplyKink (utilization threshold): {kink_usdc:.6f}")
except Exception as e:
    print(f"Error fetching supplyKink: {e}")

# Fetch supply kink (this is a utilization ratio between 0–1)
try:
    kink_usdc = int(contract.functions.borrowKink().call()) / 1e18
    print(f"borrowKink (utilization threshold): {kink_usdc:.6f}")
except Exception as e:
    print(f"Error fetching borrowKink: {e}")


try:
    totalBorrow_usdc = int(contract.functions.totalBorrow().call())
    print(f"totalBorrow: {totalBorrow_usdc:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")


try:
    totalSupply_usdc = int(contract.functions.totalSupply().call())
    print(f"totalSupply: {totalSupply_usdc:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")



# Fetch rates
s2_usdc = get_rate("supplyPerSecondInterestRateSlopeHigh")
s1_usdc = get_rate("supplyPerSecondInterestRateSlopeLow")
s0_usdc = get_rate("supplyPerSecondInterestRateBase")
r2_usdc = get_rate("borrowPerSecondInterestRateSlopeHigh")
r1_usdc = get_rate("borrowPerSecondInterestRateSlopeLow")
r0_usdc = get_rate("borrowPerSecondInterestRateBase")
c_usdc = totalBorrow_usdc
d_usdc = totalSupply_usdc
u_old_usdc = c_usdc/d_usdc

def SC(x, c, d, r0, r1, r2, s0, s1, s2, kink):

    u = c/(d + x)  

    # multi-function below
    if u <= kink:
        r_b = r0 + r1 * u
    else:
        r_b = r0 + r1 * kink + r2 * (u - kink)
    
    if u <= kink:
        r_s = s0 + s1 * u
    else:
        r_b = s0 + s1 * kink + s2 * (u - kink)

    return u, r_b, r_s


print(f"utilization_old: {u_old_usdc:.6f}")
print(f"borrow_rate_old for USDC: {SC(0, c_usdc, d_usdc, r0_usdc, r1_usdc, r2_usdc, s0_usdc, s1_usdc, s2_usdc, kink_usdc)[1]}")
print(f"supply_rate_old for USDC: {SC(0, c_usdc, d_usdc, r0_usdc, r1_usdc, r2_usdc, s0_usdc, s1_usdc, s2_usdc, kink_usdc)[2]}")


from web3 import Web3
import json

# Connect to Arbitrum
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Load Comet ABI (the ABI you posted)
with open("compound_comet_abi.json") as f:
    abi = json.load(f)

# Compound v3 USDC market contract address (Arbitrum)
comet_address = "0xAA190353CbAFa4B9f74e57276caCFb372dc8b118"
comet = web3.eth.contract(address=comet_address, abi=abi)

# ARB token address (native ARB on Arbitrum)
arb_token_address = "0x912CE59144191C1204E64559FE8253a0e49E6548" # use token contract address -> This was the problem

asset_info = comet.functions.getAssetInfoByAddress(arb_token_address).call()




print(asset_info)

coll_factor_ARB_USDC = asset_info[-4]/1e18
liq_factor_ARB_USDC = asset_info[-3]/1e18

print(f"For arb coll for USDC - ", coll_factor_ARB_USDC, liq_factor_ARB_USDC)

#  ----------------------------------------------------------------------------

# For USDT --------------------------------------------------------------------


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
    kink_usdt = int(contract.functions.supplyKink().call()) / 1e18
    print(f"supplyKink (utilization threshold): {kink_usdt:.6f}")
except Exception as e:
    print(f"Error fetching supplyKink: {e}")

# Fetch supply kink (this is a utilization ratio between 0–1)
try:
    kink_usdt = int(contract.functions.borrowKink().call()) / 1e18
    print(f"borrowKink (utilization threshold): {kink_usdt:.6f}")
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
s2_usdt = get_rate("supplyPerSecondInterestRateSlopeHigh")
s1_usdt = get_rate("supplyPerSecondInterestRateSlopeLow")
s0_usdt = get_rate("supplyPerSecondInterestRateBase")
r2_usdt = get_rate("borrowPerSecondInterestRateSlopeHigh")
r1_usdt = get_rate("borrowPerSecondInterestRateSlopeLow")
r0_usdt = get_rate("borrowPerSecondInterestRateBase")
c_usdt = totalBorrow_usdt
d_usdt = totalSupply_usdt
u_old_usdt = c_usdt/d_usdt


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



print(f"utilization_old for USDT: {u_old_usdt:.6f}")
print(f"borrow rate_old for USDT: {SC(0,c_usdt,d_usdt,r0_usdt,r1_usdt,r2_usdt,s0_usdt,s1_usdt,s2_usdt,kink_usdt)[1]}")
print(f"supply rate_old for USDT: {SC(0,c_usdt,d_usdt,r0_usdt,r1_usdt,r2_usdt,s0_usdt,s1_usdt,s2_usdt,kink_usdt)[2]}")


# fetching collateral factor for ARB as coll to borrow USDT
from web3 import Web3
import json

# Connect to Arbitrum
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Load Comet ABI (same as before)
with open("compound_comet_abi.json") as f:
    abi = json.load(f)

# Replace this with the actual USDT market contract address for Compound v3 on Arbitrum
usdt_comet_address = "0x8D9f0d8B7C7C8375E13c1ff5D0973B5826069167"
comet = web3.eth.contract(address=usdt_comet_address, abi=abi)

# ARB token address
arb_token_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"

# Fetch asset info
asset_info = comet.functions.getAssetInfoByAddress(arb_token_address).call()

print(asset_info)

coll_factor_ARB_USDT = asset_info[-4] / 1e18
liq_factor_ARB_USDT = asset_info[-3] / 1e18

print(f"For ARB as collateral in USDT market - Collateral Factor: {coll_factor_ARB_USDT}, Liquidation Factor: {liq_factor_ARB_USDT}")


#-----------------------Price of ARB------------

#taken from tuple returned by comet while finding collFactor
price_feed_address = web3.to_checksum_address("0xb2A824043730FE05F3DA2efaFa1CBbe83fa548D6")

# Calling getPrice
price = comet.functions.getPrice(price_feed_address).call()

# Chainlink price feeds usually have 8 decimals
price_in_usd = price / 1e8

print(f"ARB Price (USD): {price_in_usd}")

#-----------------------------------------------

# From here we get ARB collateral factor and liquidation factor for USDT and USDC, now
# we will borrow at safe LTV by depositing T tokens of ARB

