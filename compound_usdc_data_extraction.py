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
    kink = int(contract.functions.supplyKink().call()) / 1e18
    print(f"supplyKink (utilization threshold): {kink:.6f}")
except Exception as e:
    print(f"Error fetching supplyKink: {e}")

# Fetch supply kink (this is a utilization ratio between 0–1)
try:
    kink = int(contract.functions.borrowKink().call()) / 1e18
    print(f"borrowKink (utilization threshold): {kink:.6f}")
except Exception as e:
    print(f"Error fetching borrowKink: {e}")


try:
    totalBorrow = int(contract.functions.totalBorrow().call())
    print(f"totalBorrow: {totalBorrow:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")


try:
    totalSupply = int(contract.functions.totalSupply().call())
    print(f"totalSupply: {totalSupply:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")



# Fetch rates
s2 = get_rate("supplyPerSecondInterestRateSlopeHigh")
s1 = get_rate("supplyPerSecondInterestRateSlopeLow")
s0 = get_rate("supplyPerSecondInterestRateBase")
r2 = get_rate("borrowPerSecondInterestRateSlopeHigh")
r1 = get_rate("borrowPerSecondInterestRateSlopeLow")
r0 = get_rate("borrowPerSecondInterestRateBase")
c = totalBorrow
d = totalSupply
u_old = c/d

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


print(f"utilization_old: {u_old:.6f}")
print(f"b_rate_old for USDC: {SC(0, c, d, r0, r1, r2, s0, s1, s2, kink)[1]}")
print(f"s_rate_old for USDC: {SC(0, c, d, r0, r1, r2, s0, s1, s2, kink)[2]}")


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

coll_factor = asset_info[-4]/1e18
liq_factor = asset_info[-3]/1e18

print(f"For arb - ", coll_factor, liq_factor)

