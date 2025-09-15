import json
from web3 import Web3

# Load ABI from file
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\fluid_abi.json"
with open(abi_path, 'r') as abi_file:
    abi = json.load(abi_file)

# RPC endpoint and contract address
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
contract_address = "0x46859d33E662d4bF18eEED88f74C36256E606e44"

# Connect to Arbitrum via Alchemy
web3 = Web3(Web3.HTTPProvider(rpc_url))
contract = web3.eth.contract(address=contract_address, abi=abi)

# USDT address (on Arbitrum, ensure the address is correct)
usdt_address = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"

# Fetch data specific to USDT
usdt_data = contract.functions.getOverallTokenData(usdt_address).call()

# Print the results
print("USDT Data:", usdt_data)


nested_tuple = usdt_data[-1] 
print(nested_tuple)

n2 = nested_tuple[-1]
print(n2)



# Now we can access the required values
rate_at_utilization_kink1 = n2[-3]/100  
rate_at_utilization_kink2 = n2[-2]/100  
rate_at_utilization_max = n2[-1]/100  
u2 = n2[-5]/100  
u1 = n2[-6]/100  
d = usdt_data[12]
c = usdt_data[13]

print(c,d)
print(rate_at_utilization_kink1)
print(rate_at_utilization_kink2)
print(rate_at_utilization_max)

slope1 = (rate_at_utilization_kink1-0)/(u1-0)
slope2 = (rate_at_utilization_kink2-rate_at_utilization_kink1)/(u2-u1)
slope3 = (rate_at_utilization_max-rate_at_utilization_kink2)/(100-u2)

print(slope1,slope2,slope3)


def SC(x, c, d, r0, r1, r2, r3, kink1, kink2):
    u = c / (d + x)  

    if u <= kink1:
        r = r0 + r1 * u
    elif u <= kink2:
        r = r0 + r1 * kink1 + r2 * (u - kink1)
    else:
        r = r0 + r1 * kink1 + r2 * (kink2 - kink1) + r3 * (u - kink2)

    return u, r

print(SC(0, c, d, 0, slope1, slope2, slope3, u1, u2))