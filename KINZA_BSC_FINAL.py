import json
from web3 import Web3


rpc_url = "https://bsc-dataseed.bnbchain.org/"
web3 = Web3(Web3.HTTPProvider(rpc_url))

#Input------------------------------------------------------------------------------
token_address = Web3.to_checksum_address('0x55d398326f99059fF775485246999027B3197955')
#-----------------------------------------------------------------------------------


# ABI - 1 (IRM abi)
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\kinza_IRM_abi.json"
with open(abi_path, 'r') as abi_file:
    irm_abi = json.load(abi_file)
# ABI - 2 (Pool abi)
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\kinza_abi.json"
with open(abi_path, 'r') as abi_file:
    pool_abi = json.load(abi_file)

# not an input
pool_data_contract_address = "0x09Ddc4AE826601b0F9671b9edffDf75e7E6f5D61"



pool_contract = web3.eth.contract(
    address=Web3.to_checksum_address(pool_data_contract_address),
    abi=pool_abi  
)
irm_address = pool_contract.functions.getInterestRateStrategyAddress(token_address).call()
irm_contract = web3.eth.contract(
    address=Web3.to_checksum_address(irm_address),
    abi=irm_abi
)

# Fetch parameters using CORRECT function names from your ABI
base_rate = irm_contract.functions.getBaseVariableBorrowRate().call() / 1e27  # Typically uses Ray (1e27)
slope1 = irm_contract.functions.getVariableRateSlope1().call() / 1e27
slope2 = irm_contract.functions.getVariableRateSlope2().call() / 1e27
max_rate = irm_contract.functions.getMaxVariableBorrowRate().call() / 1e27
kink = irm_contract.functions.OPTIMAL_USAGE_RATIO().call() / 1e27  # From your ABI


# Get debt/supply with token address parameter
total_debt = pool_contract.functions.getTotalDebt(token_address).call() / 1e18 # Add token_address
total_supply = pool_contract.functions.getATokenTotalSupply(token_address).call() / 1e18 # Add token_address
reserve_config = pool_contract.functions.getReserveConfigurationData(token_address).call() 
reserve_factor = reserve_config[4]/1e4


u= total_debt/total_supply

if u <= kink:
    r = base_rate + (slope1) * (u/kink)
else:
    r = base_rate + (slope1) + (slope2) * ((u - kink)/(1 - kink))
    
r_s = r * u * (1-reserve_factor)

if u>1:
    u=1


print(f"""
Interest Rate Parameters:
- Base Rate: {base_rate}
- Slope 1: {slope1}
- Slope 2: {slope2}
- Max Rate: {max_rate}
- Kink: {kink}
- debt: {total_debt}
- supply :{total_supply}
- u: {u}
- borrow apr: {r}
- supply apr: {r_s}
""")

def get_supply_apr(x):

    base_rate = irm_contract.functions.getBaseVariableBorrowRate().call() / 1e27  
    slope1 = irm_contract.functions.getVariableRateSlope1().call() / 1e27
    slope2 = irm_contract.functions.getVariableRateSlope2().call() / 1e27
    max_rate = irm_contract.functions.getMaxVariableBorrowRate().call() / 1e27
    kink = irm_contract.functions.OPTIMAL_USAGE_RATIO().call() / 1e27  

    total_debt = pool_contract.functions.getTotalDebt(token_address).call() / 1e18 
    total_supply = pool_contract.functions.getATokenTotalSupply(token_address).call() / 1e18 
    reserve_config = pool_contract.functions.getReserveConfigurationData(token_address).call() 
    reserve_factor = reserve_config[4]/1e4
    
    u= total_debt/(total_supply+x)
    
    if u <= kink:
        r = base_rate + (slope1 ) * (u / kink)
    else:
        r = base_rate + (slope1) + (slope2) * ((u - kink) / (1 - kink))


    if u>1:
        u=1

    r_s = r * u * (1-reserve_factor)
    return r_s

print(f"func output->>",get_supply_apr(0))