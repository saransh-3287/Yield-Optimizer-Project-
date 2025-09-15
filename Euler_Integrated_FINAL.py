import json
from web3 import Web3


# ONLY INPUT REQUIRED 
vault_address = "0xca522ECab584b5430ADb946edEE4224A63628362"
#------------------------------------------------------------------


# Load IRM ABI (1st ABI)
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\euler_usdt_abi.json"
with open(abi_path, 'r') as abi_file:
    abi = json.load(abi_file)
# Load supply vault ABI (2nd ABI)
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\euler_usdt_supply_abi.json"
with open(abi_path, 'r') as abi_file:
    abi_2 = json.load(abi_file)
#-------------------------------------------------------------------


# BSC Mainnet RPC endpoint
rpc_url = "https://bsc-dataseed.bnbchain.org/"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# IRM contract address and usdt vault address
supply_contract = web3.eth.contract(
    address=web3.to_checksum_address(vault_address),
    abi=abi_2
)
irm_address = supply_contract.functions.interestRateModel().call()
irm_contract = web3.eth.contract(
    address=web3.to_checksum_address(irm_address),
    abi=abi
)

# Fetch parameters with error handling
try:
    base_rate = irm_contract.functions.baseRate().call()
    kink = irm_contract.functions.kink().call()
    slope1 = irm_contract.functions.slope1().call()
    slope2 = irm_contract.functions.slope2().call()

    # Convert to decimals
    base_rate_dec = base_rate 
    kink_dec = kink / 4294967295
    slope1_dec = slope1 
    slope2_dec = slope2 

    print(f"Base Rate: {base_rate_dec}")
    print(f"Kink (utilization): {kink_dec:.2%}")
    print(f"Slope 1: {slope1_dec}")
    print(f"Slope 2: {slope2_dec}")

except Exception as e:
    print(f"Error fetching parameters: {e}")

try:
    totalBorrows = supply_contract.functions.totalBorrows().call() / 1e18
    print(f"totalBorrow {totalBorrows}")
except Exception as e:
    print(f"Error fetching totalBorrows: {e}")

try:
    Cash = supply_contract.functions.cash().call() / 1e18
    reserve_factor = supply_contract.functions.interestFee().call() / 1e4
    print(f"Cash {Cash}")
except Exception as e:
    print(f"Error fetching cash: {e}")

u_curr = totalBorrows / (totalBorrows + Cash)
print(f"Current utilization: {u_curr:.4%}")


# Calculate per-second rate (r)
if u_curr <= kink_dec:
    r = base_rate_dec + (slope1*0.095/743995130 ) * (u_curr / kink_dec)
else:
    r = base_rate_dec + (slope1*0.095/743995130) + (slope2*1.105/51477290240) * ((u_curr - kink_dec) / (1 - kink_dec))

print(f"borrow rate : {r}")
supply_rate = r*u_curr*(1-reserve_factor)
print(f"supply rate ", supply_rate)

def get_supply_apr(x):
    totalBorrows = supply_contract.functions.totalBorrows().call() / 1e18
    Cash = supply_contract.functions.cash().call() / 1e18
    u_curr = totalBorrows/(totalBorrows+Cash+x)

    kink = irm_contract.functions.kink().call()
    kink_dec = kink / 4294967295

    if u_curr <= kink_dec:
        borrow_APR = base_rate_dec + (slope1*0.095/743995130 ) * (u_curr / kink_dec)
    else:
        borrow_APR = base_rate_dec + (slope1*0.095/743995130) + (slope2*1.105/51477290240) * ((u_curr - kink_dec) / (1 - kink_dec))
    
    reserve_factor = supply_contract.functions.interestFee().call() / 1e4
    supply_APR = borrow_APR*u_curr*(1-reserve_factor)

    return supply_APR

print(f"supply apr on supplying ", get_supply_apr(0))