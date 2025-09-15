import json
from web3 import Web3
import numpy as np
from scipy.optimize import minimize

SECONDS_PER_YEAR = 365 * 24 * 60 * 60
TOTAL_TOKEN_ALLOCATION = 1e6 # Total tokens 

RPC_URL = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

USDT_ADDRESS = web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9")

# ------------------- Compound Setup -------------------
COMPOUND_ABI_PATH = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\compound_abi.json"
with open(COMPOUND_ABI_PATH, 'r') as abi_file:
    compound_abi = json.load(abi_file)

COMPOUND_CONTRACT_ADDRESS = "0xd98Be00b5D27fc98112BdE293e487f8D4cA57d07"
compound_contract = web3.eth.contract(address=COMPOUND_CONTRACT_ADDRESS, abi=compound_abi)
COMPOUND_RESERVE_FACTOR = 0.2

def get_compound_rate(param_name):
    try:
        raw = int(getattr(compound_contract.functions, param_name)().call())
        return raw * SECONDS_PER_YEAR / 1e18
    except Exception as e:
        print(f"Error fetching {param_name}: {e}")
        return 0


compound_base_rate = get_compound_rate("borrowPerSecondInterestRateBase")
compound_slope1 = get_compound_rate("borrowPerSecondInterestRateSlopeLow")
compound_slope2 = get_compound_rate("borrowPerSecondInterestRateSlopeHigh")
compound_kink = int(compound_contract.functions.borrowKink().call()) / 1e18
compound_total_borrow = int(compound_contract.functions.totalBorrow().call())
compound_total_supply = int(compound_contract.functions.totalSupply().call())


def compound_supply_side_apy(x, total_borrow, total_supply, base, slope1, slope2, kink, reserve_factor):
    utilization = total_borrow / (total_supply + x)
    if utilization <= kink:
        borrow_rate = base + slope1 * utilization
    else:
        borrow_rate = base + slope1 * kink + slope2 * (utilization - kink)
    supply_apy = borrow_rate * utilization * (1 - reserve_factor)
    return utilization, borrow_rate, supply_apy



# ------------------- Fluid Setup -------------------
FLUID_ABI_PATH = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\fluid_abi.json"
with open(FLUID_ABI_PATH, 'r') as abi_file:
    fluid_abi = json.load(abi_file)

FLUID_CONTRACT_ADDRESS = "0x46859d33E662d4bF18eEED88f74C36256E606e44"
fluid_contract = web3.eth.contract(address=FLUID_CONTRACT_ADDRESS, abi=fluid_abi)
FLUID_RESERVE_FACTOR = 0.1

fluid_token_data = fluid_contract.functions.getOverallTokenData(USDT_ADDRESS).call()
fluid_nested = fluid_token_data[-1][-1]
fluid_rate_kink1 = fluid_nested[-3] / 100
fluid_rate_kink2 = fluid_nested[-2] / 100
fluid_rate_max = fluid_nested[-1] / 100
fluid_util_kink2 = fluid_nested[-5] / 100
fluid_util_kink1 = fluid_nested[-6] / 100
fluid_total_supply = fluid_token_data[12]
fluid_total_borrow = fluid_token_data[13]

fluid_slope1 = (fluid_rate_kink1 - 0) / (fluid_util_kink1 - 0)
fluid_slope2 = (fluid_rate_kink2 - fluid_rate_kink1) / (fluid_util_kink2 - fluid_util_kink1)
fluid_slope3 = (fluid_rate_max - fluid_rate_kink2) / (100 - fluid_util_kink2)

def fluid_supply_side_apy(x, total_borrow, total_supply, r0, slope1, slope2, slope3, kink1, kink2, reserve_factor):
    utilization = total_borrow / (total_supply + x)
    if utilization <= kink1:
        borrow_rate = r0 + slope1 * utilization
    elif utilization <= kink2:
        borrow_rate = r0 + slope1 * kink1 + slope2 * (utilization - kink1)
    else:
        borrow_rate = r0 + slope1 * kink1 + slope2 * (kink2 - kink1) + slope3 * (utilization - kink2)
    supply_apy = borrow_rate * utilization * (1 - reserve_factor)
    return utilization, borrow_rate, supply_apy





# ------------------- Aave Setup -------------------
# Get Aave Reserve Factor
AAVE_CONFIG_ABI_PATH = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_interestRateParam_abi.json"
with open(AAVE_CONFIG_ABI_PATH, 'r') as abi_file:
    aave_config_abi = json.load(abi_file)

AAVE_DATA_PROVIDER_ADDRESS = web3.to_checksum_address("0x14496b405D62c24F91f04Cda1c69Dc526D56fDE5")
aave_data_provider = web3.eth.contract(address=AAVE_DATA_PROVIDER_ADDRESS, abi=aave_config_abi)
aave_config = aave_data_provider.functions.getReserveConfigurationData(USDT_ADDRESS).call()
aave_reserve_factor = aave_config[4] / 1e4  # basis points to fraction

# Get Aave Interest Rate Model Parameters
AAVE_STRATEGY_ABI = [
    {"inputs": [{"internalType": "address", "name": "reserve", "type": "address"}], "name": "getBaseVariableBorrowRate", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "reserve", "type": "address"}], "name": "getVariableRateSlope1", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "reserve", "type": "address"}], "name": "getVariableRateSlope2", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "reserve", "type": "address"}], "name": "getOptimalUsageRatio", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

AAVE_STRATEGY_ADDRESS = aave_data_provider.functions.getInterestRateStrategyAddress(USDT_ADDRESS).call()
aave_strategy_contract = web3.eth.contract(address=AAVE_STRATEGY_ADDRESS, abi=AAVE_STRATEGY_ABI)

aave_base_rate = aave_strategy_contract.functions.getBaseVariableBorrowRate(USDT_ADDRESS).call() / 1e27
aave_slope1 = aave_strategy_contract.functions.getVariableRateSlope1(USDT_ADDRESS).call() / 1e27
aave_slope2 = aave_strategy_contract.functions.getVariableRateSlope2(USDT_ADDRESS).call() / 1e27
aave_optimal_util = aave_strategy_contract.functions.getOptimalUsageRatio(USDT_ADDRESS).call() / 1e27

# Get Aave total borrow and supply
AAVE_RESERVE_DATA_ABI = [
    {"inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
     "name": "getReserveData",
     "outputs": [
         {"internalType": "uint256", "name": "unbacked", "type": "uint256"},
         {"internalType": "uint256", "name": "accruedToTreasuryScaled", "type": "uint256"},
         {"internalType": "uint256", "name": "totalAToken", "type": "uint256"},
         {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},
         {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},
         # ... (rest omitted for brevity)
     ],
     "stateMutability": "view",
     "type": "function"
    }
]
aave_reserve_data_contract = web3.eth.contract(address=AAVE_DATA_PROVIDER_ADDRESS, abi=AAVE_RESERVE_DATA_ABI)
aave_reserve_data = aave_reserve_data_contract.functions.getReserveData(USDT_ADDRESS).call()
aave_total_stable_debt = aave_reserve_data[3]
aave_total_variable_debt = aave_reserve_data[4]
aave_total_borrow = aave_total_stable_debt + aave_total_variable_debt
aave_total_borrow_human = aave_total_borrow / 1e6  # USDT is 6 decimals
aave_total_supply = aave_reserve_data[2]  # totalAToken

def aave_supply_side_apy(x, total_borrow, total_supply, optimal_util, base, slope1, slope2, reserve_factor):
    utilization = total_borrow / (total_supply + x)
    if utilization <= optimal_util:
        borrow_rate = base + slope1 * utilization / optimal_util
    else:
        borrow_rate = base + slope1 + ((utilization - optimal_util) / (1 - optimal_util)) * slope2
    supply_apy = borrow_rate * utilization * (1 - reserve_factor)
    return utilization, borrow_rate, supply_apy













# ------------------- Optimization Function -------------------
def negative_total_yield(allocation_vars):
    compound_alloc, fluid_alloc = allocation_vars
    aave_alloc = TOTAL_TOKEN_ALLOCATION - compound_alloc - fluid_alloc

    _, _, compound_apy = compound_supply_side_apy(
        compound_alloc, compound_total_borrow, compound_total_supply,
        compound_base_rate, compound_slope1, compound_slope2, compound_kink, COMPOUND_RESERVE_FACTOR
    )
    _, _, fluid_apy = fluid_supply_side_apy(
        fluid_alloc, fluid_total_borrow, fluid_total_supply,
        0, fluid_slope1, fluid_slope2, fluid_slope3, fluid_util_kink1/100, fluid_util_kink2/100, FLUID_RESERVE_FACTOR
    )
    _, _, aave_apy = aave_supply_side_apy(
        aave_alloc, aave_total_borrow, aave_total_supply,
        aave_optimal_util, aave_base_rate, aave_slope1, aave_slope2, aave_reserve_factor
    )

    total_yield = (
        compound_apy * compound_alloc +
        fluid_apy * fluid_alloc +
        aave_apy * aave_alloc
    )
    return -total_yield  # We minimize, so negate







# ------------------- Run Optimization -------------------

INITIAL_GUESSES = [
    [0.0 * TOTAL_TOKEN_ALLOCATION, 0.0 * TOTAL_TOKEN_ALLOCATION],  # Aave-centric
    [TOTAL_TOKEN_ALLOCATION/3, TOTAL_TOKEN_ALLOCATION/3],            # Balanced
    [0.9 * TOTAL_TOKEN_ALLOCATION, 0.05 * TOTAL_TOKEN_ALLOCATION]    # Compound-heavy
]
bounds = [(0, TOTAL_TOKEN_ALLOCATION), (0, TOTAL_TOKEN_ALLOCATION)]
constraints = {'type': 'ineq', 'fun': lambda x: TOTAL_TOKEN_ALLOCATION - x[0] - x[1]}

from scipy.optimize import basinhopping

optimizer_config = {
    'niter': 10,
    'stepsize': 1e9,  # Token allocation step size
    'T': 1.0,         # Temperature parameter
    'minimizer_kwargs': {
        'method': 'SLSQP',
        'bounds': bounds,
        'constraints': constraints,
        'options': {'maxiter': 5000, 'ftol': 1e-12}
    }
}

best_result = basinhopping(
    func=negative_total_yield,
    x0=[TOTAL_TOKEN_ALLOCATION/3, TOTAL_TOKEN_ALLOCATION/3],
    **optimizer_config
)

result = best_result


if result.success:
    compound_opt, fluid_opt = result.x
    aave_opt = TOTAL_TOKEN_ALLOCATION - compound_opt - fluid_opt

    _, _, compound_apy = compound_supply_side_apy(
        compound_opt, compound_total_borrow, compound_total_supply,
        compound_base_rate, compound_slope1, compound_slope2, compound_kink, COMPOUND_RESERVE_FACTOR
    )
    _, _, fluid_apy = fluid_supply_side_apy(
        fluid_opt, fluid_total_borrow, fluid_total_supply,
        0, fluid_slope1, fluid_slope2, fluid_slope3, fluid_util_kink1/100, fluid_util_kink2/100, FLUID_RESERVE_FACTOR
    )
    _, _, aave_apy = aave_supply_side_apy(
        aave_opt, aave_total_borrow, aave_total_supply,
        aave_optimal_util, aave_base_rate, aave_slope1, aave_slope2, aave_reserve_factor
    )

    total_yield = (
        compound_apy * compound_opt +
        fluid_apy * fluid_opt +
        aave_apy * aave_opt
    )
    strategy_apr = (total_yield / TOTAL_TOKEN_ALLOCATION) * 100








_, _, r_only_c = compound_supply_side_apy(
        TOTAL_TOKEN_ALLOCATION, compound_total_borrow, compound_total_supply,
        compound_base_rate, compound_slope1, compound_slope2, compound_kink, COMPOUND_RESERVE_FACTOR
    )

_, _, r_only_f = fluid_supply_side_apy(
        TOTAL_TOKEN_ALLOCATION, fluid_total_borrow, fluid_total_supply,
        0, fluid_slope1, fluid_slope2, fluid_slope3, fluid_util_kink1/100, fluid_util_kink2/100, FLUID_RESERVE_FACTOR
    )
_, _, r_only_a = aave_supply_side_apy(
        TOTAL_TOKEN_ALLOCATION, aave_total_borrow, aave_total_supply,
        aave_optimal_util, aave_base_rate, aave_slope1, aave_slope2, aave_reserve_factor
    )

#at time step 1 
curr_comp = 1395102009940.27
curr_fluid = 491278046205.69
curr_aave = 8113619943854.03

opt_comp = compound_opt
opt_fluid = fluid_opt
opt_aave = aave_opt

    
change_c =  opt_comp - curr_comp
change_f = opt_fluid - curr_fluid
change_a = opt_aave - curr_aave





print(f"CURRENT->>> Compound: ${curr_comp:,.2f}, Fluid: ${curr_fluid:,.2f}, Aave: ${curr_aave:,.2f}")
print(f"OPTIMAL ->>> Compound: ${opt_comp:,.2f}, Fluid: ${opt_fluid:,.2f}, Aave: ${opt_aave:,.2f}")

change_c = opt_comp - curr_comp
change_f = opt_fluid - curr_fluid
change_a = opt_aave - curr_aave

print(f"\nRequired Changes:")
print(f"Compound needs {'+' if change_c > 0 else ''}{change_c:,.2f}")
print(f"Fluid needs {'+' if change_f > 0 else ''}{change_f:,.2f}")
print(f"Aave needs {'+' if change_a > 0 else ''}{change_a:,.2f}")

deficits = {
    'Compound': max(change_c, 0),
    'Fluid': max(change_f, 0),
    'Aave': max(change_a, 0)
}

surpluses = {
    'Compound': max(-change_c, 0),
    'Fluid': max(-change_f, 0),
    'Aave': max(-change_a, 0)
}





















# Calculate transfers
transfers = []
print("\n")

for sender in ['Compound', 'Fluid', 'Aave']:
    if surpluses[sender] <= 0:
        continue
        
    for receiver in ['Compound', 'Fluid', 'Aave']:
        if deficits[receiver] <= 0:
            continue
            
        transfer_amount = min(surpluses[sender], deficits[receiver])
        if transfer_amount > 0:
            transfers.append({
                'from': sender,
                'to': receiver,
                'amount': transfer_amount
            })
            surpluses[sender] -= transfer_amount
            deficits[receiver] -= transfer_amount
            print(f"Transfer {transfer_amount:,.2f} from {sender} to {receiver}")

print("\n")