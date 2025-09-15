import json
from web3 import Web3

# Load ABI from file
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_reservefactor_abi.json"
with open(abi_path, 'r') as abi_file:
    abi = json.load(abi_file)

# RPC endpoint and contract address
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
contract_address = "0x6ab707Aca953eDAeFBc4fD23bA73294241490620"

web3 = Web3(Web3.HTTPProvider(rpc_url))
contract = web3.eth.contract(address=contract_address, abi=abi)

try:
    kink = int(contract.functions.totalSupply().call()) / 1e12
    print(f"total supply: {kink:.6f}")
except Exception as e:
    print(f"Error fetching : {e}")



from web3 import Web3
import json

# Load ABI
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_interestRateParam_abi.json"
with open(abi_path, 'r') as abi_file:
    abi = json.load(abi_file)

# RPC and contract
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
contract_address = "0x14496b405D62c24F91f04Cda1c69Dc526D56fDE5"

web3 = Web3(Web3.HTTPProvider(rpc_url))
contract = web3.eth.contract(address=contract_address, abi=abi)

# Choose asset (e.g., USDC on Arbitrum)
usdc_address = Web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9")  # USDC

try:
    config = contract.functions.getReserveConfigurationData(usdc_address).call()
    reserve_factor = config[4] / 1e4  # Aave V3 uses basis points (e.g., 1000 = 10%)
    print(f"Reserve Factor for USDT: {reserve_factor:.2f}")
except Exception as e:
    print(f"Error fetching reserve factor: {e}")



import json
from web3 import Web3


# USDT asset address on Arbitrum
usdt_address = web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9")

# AaveProtocolDataProvider address on Arbitrum V3
data_provider_address = web3.to_checksum_address("0x14496b405D62c24F91f04Cda1c69Dc526D56fDE5")

# Minimal ABI for getInterestRateStrategyAddress
data_provider_abi = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getInterestRateStrategyAddress",
        "outputs": [{"internalType": "address", "name": "irStrategyAddress", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

data_provider_contract = web3.eth.contract(address=data_provider_address, abi=data_provider_abi)

# Fetch strategy contract address
strategy_address = data_provider_contract.functions.getInterestRateStrategyAddress(usdt_address).call()
print("Strategy Contract Address:", strategy_address)


# Minimal ABI for interest rate strategy
strategy_abi = [
    {
        "inputs": [{"internalType": "address", "name": "reserve", "type": "address"}],
        "name": "getBaseVariableBorrowRate",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "reserve", "type": "address"}],
        "name": "getVariableRateSlope1",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "reserve", "type": "address"}],
        "name": "getVariableRateSlope2",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "reserve", "type": "address"}],
        "name": "getOptimalUsageRatio",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Load contract
strategy_contract = web3.eth.contract(address=strategy_address, abi=strategy_abi)

# Call all interest rate model parameters
base_rate = strategy_contract.functions.getBaseVariableBorrowRate(usdt_address).call()
slope1 = strategy_contract.functions.getVariableRateSlope1(usdt_address).call()
slope2 = strategy_contract.functions.getVariableRateSlope2(usdt_address).call()
opt_util = strategy_contract.functions.getOptimalUsageRatio(usdt_address).call()

RAY = 1e27
print("\n Aave Interest Rate Model Parameters for USDT:")
print(f"Base Borrow Rate:           {base_rate / RAY:.6%}")
print(f"Variable Rate Slope1:       {slope1 / RAY:.6%}")
print(f"Variable Rate Slope2:       {slope2 / RAY:.6%}")
print(f" Utilization at kink:  {opt_util / RAY:.6%}")


import json
from web3 import Web3

from web3 import Web3

# RPC and addresses
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# USDT asset address on Arbitrum
usdt_address = web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9")

# AaveProtocolDataProvider address on Arbitrum V3
data_provider_address = web3.to_checksum_address("0x14496b405D62c24F91f04Cda1c69Dc526D56fDE5")

# Minimal ABI for getReserveData
abi = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveData",
        "outputs": [
            {"internalType": "uint256", "name": "unbacked", "type": "uint256"},
            {"internalType": "uint256", "name": "accruedToTreasuryScaled", "type": "uint256"},
            {"internalType": "uint256", "name": "totalAToken", "type": "uint256"},
            {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},
            {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},
            {"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},
            {"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},
            {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Create contract instance
contract = web3.eth.contract(address=data_provider_address, abi=abi)

# Call getReserveData for USDT
reserve_data = contract.functions.getReserveData(usdt_address).call()

# Extract total borrow (stable + variable debt)
total_stable_debt = reserve_data[3]
total_variable_debt = reserve_data[4]
total_borrow = total_stable_debt + total_variable_debt


human_total_borrow = total_borrow / 1e12
print(f"Total USDT borrowed on Aave V3 Arbitrum: {human_total_borrow:.2f} USDT")



c_a = human_total_borrow*1e6
d_a = kink*1e6
base = base_rate
slope1 = slope1/1e25
slope2 = slope2/1e25
u_o = opt_util/1e27
rf = reserve_factor




def SA(x,c_a,d_a,u_o, base, slope1, slope2, rf):
    u = c_a/(d_a + x)
    

    if u<=u_o:
        r_b = base + slope1*u/u_o
    else:
        r_b = base + slope1 + ((u - u_o)/(1-u_o)) * slope2
    
    r_s = r_b * u * (1-rf)
    return u, r_b, r_s


print(SA(0,c_a,d_a,u_o, base, slope1, slope2, rf))
print(f"supplied amount ->>>",d_a)
print(f"borrowed amt.->>>", c_a)

