import json
from web3 import Web3
import numpy as np
from scipy.optimize import minimize

# --- Connect to BSC ---
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.bnbchain.org/"))

# --- VENUS: Fetch and store parameters once ---
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_abi.json") as f:
    venus_abi = json.load(f)
venus_contract = w3.eth.contract(address="0xfD5840Cd36d94D7229439859C0112a4185BC0255", abi=venus_abi)

venus_cash = venus_contract.functions.getCash().call()
venus_borrows = venus_contract.functions.totalBorrows().call()
venus_reserves = venus_contract.functions.totalReserves().call()
venus_reserve_factor = venus_contract.functions.reserveFactorMantissa().call() / 1e18
venus_irm_addr = venus_contract.functions.interestRateModel().call()

venus_irm_abi = [ # minimal ABI for IRM
    {"inputs":[],"name":"BASE_RATE_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MULTIPLIER_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"KINK_1","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MULTIPLIER_2_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"BASE_RATE_2_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"KINK_2","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"JUMP_MULTIPLIER_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"BLOCKS_PER_YEAR","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"RATE_1","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"RATE_2","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}
]
venus_irm_contract = w3.eth.contract(address=venus_irm_addr, abi=venus_irm_abi)
venus_blocks_per_year = venus_irm_contract.functions.BLOCKS_PER_YEAR().call()
venus_base_rate = venus_irm_contract.functions.BASE_RATE_PER_BLOCK().call()
venus_multiplier = venus_irm_contract.functions.MULTIPLIER_PER_BLOCK().call()
venus_kink = abs(venus_irm_contract.functions.KINK_1().call()) / 1e18

def get_supply_apr_venus(x):
    x_wei = int(x * 1e18)
    new_cash = venus_cash + x_wei
    borrows = venus_borrows
    util = borrows / (new_cash + borrows) if (new_cash + borrows) else 0
    if util <= venus_kink:
        util_scaled = int(util * 1e18)
        brpb = venus_base_rate + ((util_scaled * venus_multiplier) // 1e18)
    else:
        # For simplicity, use linear extension after kink
        brpb = venus_base_rate + venus_multiplier
    borrow_apy = (brpb / 1e18) * venus_blocks_per_year * 100
    supply_apy = borrow_apy * util * (1 - venus_reserve_factor)
    return {'supply_apr': supply_apy}

# --- AAVE: Fetch and store parameters once ---
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_supply_abi.json") as f:
    aave_supply_abi = json.load(f)
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_reserve_factor_abi.json") as f:
    aave_reserve_abi = json.load(f)
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_irm_strategy_abi.json") as f:
    aave_strategy_abi = json.load(f)

aave_atoken_contract = w3.eth.contract(
    address="0xa9251ca9DE909CB71783723713B21E4233fbf1B1",
    abi=aave_supply_abi
)
aave_data_provider = w3.eth.contract(
    address=w3.to_checksum_address("0x1e26247502e90b4fab9D0d17e4775e90085D2A35"),
    abi=aave_reserve_abi
)
aave_total_supply = aave_atoken_contract.functions.totalSupply().call() / 1e18
aave_config = aave_data_provider.functions.getReserveConfigurationData("0x55d398326f99059fF775485246999027B3197955").call()
aave_reserve_factor = aave_config[4] / 1e4
aave_strategy_address = aave_data_provider.functions.getInterestRateStrategyAddress("0x55d398326f99059fF775485246999027B3197955").call()
aave_strategy_contract = w3.eth.contract(address=aave_strategy_address, abi=aave_strategy_abi)
aave_base_rate = aave_strategy_contract.functions.getBaseVariableBorrowRate("0x55d398326f99059fF775485246999027B3197955").call() / 1e27
aave_slope1 = aave_strategy_contract.functions.getVariableRateSlope1("0x55d398326f99059fF775485246999027B3197955").call() / 1e27
aave_slope2 = aave_strategy_contract.functions.getVariableRateSlope2("0x55d398326f99059fF775485246999027B3197955").call() / 1e27
aave_opt_util = aave_strategy_contract.functions.getOptimalUsageRatio("0x55d398326f99059fF775485246999027B3197955").call() / 1e27
aave_reserve_data = aave_data_provider.functions.getReserveData("0x55d398326f99059fF775485246999027B3197955").call()
aave_total_borrow = (aave_reserve_data[3] + aave_reserve_data[4]) / 1e18

def get_supply_apr_aave(x):
    new_supply = aave_total_supply + x
    utilization = aave_total_borrow / new_supply if new_supply > 0 else 0
    if utilization <= aave_opt_util:
        borrow_rate = aave_base_rate + (aave_slope1 * utilization / aave_opt_util)
    else:
        borrow_rate = aave_base_rate + aave_slope1 + ((utilization - aave_opt_util) / (1 - aave_opt_util)) * aave_slope2
    supply_rate = borrow_rate * utilization * (1 - aave_reserve_factor)
    return {'supply_apr': supply_rate * 100}

# --- KINZA: Fetch and store parameters once -----
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\kinza_abi.json") as f:
    kinza_pool_abi = json.load(f)
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\kinza_IRM_abi.json") as f:
    kinza_irm_abi = json.load(f)
kinza_pool_contract = w3.eth.contract(
    address=w3.to_checksum_address("0x09Ddc4AE826601b0F9671b9edffDf75e7E6f5D61"),
    abi=kinza_pool_abi
)

kinza_irm_address = kinza_pool_contract.functions.getInterestRateStrategyAddress("0x55d398326f99059fF775485246999027B3197955").call()
kinza_irm_contract = w3.eth.contract(address=kinza_irm_address, abi=kinza_irm_abi)
kinza_base_rate = kinza_irm_contract.functions.getBaseVariableBorrowRate().call() / 1e27
kinza_slope1 = kinza_irm_contract.functions.getVariableRateSlope1().call() / 1e27
kinza_slope2 = kinza_irm_contract.functions.getVariableRateSlope2().call() / 1e27
kinza_kink = kinza_irm_contract.functions.OPTIMAL_USAGE_RATIO().call() / 1e27
kinza_total_debt = kinza_pool_contract.functions.getTotalDebt("0x55d398326f99059fF775485246999027B3197955").call() / 1e18
kinza_total_supply = kinza_pool_contract.functions.getATokenTotalSupply("0x55d398326f99059fF775485246999027B3197955").call() / 1e18
kinza_reserve_config = kinza_pool_contract.functions.getReserveConfigurationData("0x55d398326f99059fF775485246999027B3197955").call()
kinza_reserve_factor = kinza_reserve_config[4] / 1e4

def get_supply_apr_kinza(x):
    new_supply = kinza_total_supply + x
    utilization = kinza_total_debt / new_supply if new_supply > 0 else 0
    utilization = min(utilization, 1.0)
    if utilization <= kinza_kink:
        borrow_rate = kinza_base_rate + (kinza_slope1 * utilization / kinza_kink)
    else:
        borrow_rate = kinza_base_rate + kinza_slope1 + (kinza_slope2 * (utilization - kinza_kink) / (1 - kinza_kink))
    supply_rate = borrow_rate * utilization * (1 - kinza_reserve_factor)
    return {'supply_apr': supply_rate * 100}

# --- EULER: Fetch and store parameters once -----
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\euler_usdt_supply_abi.json") as f:
    euler_supply_abi = json.load(f)
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\euler_usdt_abi.json") as f:
    euler_irm_abi = json.load(f)
euler_supply_contract = w3.eth.contract(
    address=w3.to_checksum_address("0xca522ECab584b5430ADb946edEE4224A63628362"),
    abi=euler_supply_abi
)
euler_irm_address = euler_supply_contract.functions.interestRateModel().call()
euler_irm_contract = w3.eth.contract(address=euler_irm_address, abi=euler_irm_abi)
euler_base_rate = euler_irm_contract.functions.baseRate().call()
euler_kink = euler_irm_contract.functions.kink().call() / 4294967295
euler_slope1 = euler_irm_contract.functions.slope1().call()
euler_slope2 = euler_irm_contract.functions.slope2().call()
euler_total_borrows = euler_supply_contract.functions.totalBorrows().call() / 1e18
euler_cash = euler_supply_contract.functions.cash().call() / 1e18
euler_reserve_factor = euler_supply_contract.functions.interestFee().call() / 1e4

def get_supply_apr_euler(x):
    new_cash = euler_cash + x
    total_liquidity = euler_total_borrows + new_cash
    utilization = euler_total_borrows / total_liquidity if total_liquidity > 0 else 0
    if utilization <= euler_kink:
        borrow_rate = euler_base_rate + (euler_slope1 * 0.095 / 743995130) * (utilization / euler_kink)
    else:
        excess_util = utilization - euler_kink
        borrow_rate = euler_base_rate + (euler_slope1 * 0.095 / 743995130) + (euler_slope2 * 1.105 / 51477290240) * (excess_util / (1 - euler_kink))
    supply_rate = borrow_rate * utilization * (1 - euler_reserve_factor)
    return {'supply_apr': supply_rate * 100}

# --- Objective Function ---
def objective(vars):
    x, y, z = vars
    k = T - x - y - z
    return -(
        x * get_supply_apr_venus(x)['supply_apr'] / 100 +
        y * get_supply_apr_aave(y)['supply_apr'] / 100 +
        z * get_supply_apr_kinza(z)['supply_apr'] / 100 +
        k * get_supply_apr_euler(k)['supply_apr'] / 100
    )

# --- Print Current State Parameters ---
print("Current Protocol Parameters:")
print("-" * 45)
print("Venus:")
print(f"  Current Supply APR: {get_supply_apr_venus(0)['supply_apr']:.2f}%")

print("\nAave:")
print(f"  Current Supply APR: {get_supply_apr_aave(0)['supply_apr']:.2f}%")

print("\nKinza:")
print(f"  Current Supply APR: {get_supply_apr_kinza(0)['supply_apr']:.2f}%")

print("\nEuler:")
print(f"  Current Supply APR: {get_supply_apr_euler(0)['supply_apr']:.2f}%")
print("-" * 45)



#---------------------------------------------------------------------
#-------------Optimization heree--------------------------------------------


T = 1e8

def optimize_allocations(T):

    aprs = [
        get_supply_apr_venus(0)['supply_apr'],
        get_supply_apr_aave(0)['supply_apr'],
        get_supply_apr_kinza(0)['supply_apr'],
        get_supply_apr_euler(0)['supply_apr']
    ]
    main_idx = np.argmax(aprs)
    
    x0 = [0.0, 0.0, 0.0]  

    bounds = [(0, T) for _ in range(3)]
    constraints = {'type': 'ineq', 'fun': lambda x: T - np.sum(x)}

    result = minimize(
    objective, x0=x0,
    method='trust-constr',
    bounds=bounds,
    constraints=constraints,
    options={
        'maxiter': 2000,
        'xtol': 1e-4,
        'gtol': 1e-4,
        'disp': True,
        'initial_tr_radius': 10.0
    }
)

    if result.success:
        allocations = list(result.x) + [T - sum(result.x)]
        allocations = [max(a, 0) for a in allocations]
        
        # Normalize to handle floating point errors
        total_alloc = sum(allocations)
        if abs(total_alloc - T) > 1e-4:
            allocations = [a * T / total_alloc for a in allocations]
        
        return {
            'allocations': allocations,
            'total_apr': -result.fun / T
        }
    
    raise RuntimeError(f"Optimization failed: {result.message}")


# ----Optimization-----------------------------------------------------


try:
    result = optimize_allocations(T)
    print("-" * 45)

    print("Optimal Allocations For T:", T)
    for name, alloc in zip(["Venus", "Aave", "Kinza", "Euler"], result['allocations']):
        print(f"{name}: {alloc*100/T} %")
    print("-" * 45)
    print(f"Projected Total APR (%): {result['total_apr']*100}")
except Exception as e:
    print(f"\nOptimization Error: {str(e)}")


print("-" * 45)
print(f"Full alloc on Venus (%)",get_supply_apr_venus(T)['supply_apr'])
print(f"Full alloc on aave (%)",get_supply_apr_aave(T)['supply_apr'])
print(f"Full alloc on kinza (%)",get_supply_apr_kinza(T)['supply_apr'])
print(f"Full alloc on euler (%)",get_supply_apr_euler(T)['supply_apr'])
print("-" * 45)



# -------------------Checking the optimization Results---------------------------



import numpy as np
import matplotlib.pyplot as plt

def plot_strategy_slice(T, fixed_protocol, fixed_value, optimizer_result=None):
    
    protocol_map = {'venus':0, 'aave':1, 'kinza':2, 'euler':3}
    fixed_idx = protocol_map[fixed_protocol]
    
    n = 50
    x = np.linspace(0, T, n)
    y = np.linspace(0, T, n)
    X, Y = np.meshgrid(x, y)
    Z = np.full_like(X, np.nan)
    
    for i in range(n):
        for j in range(n):
            allocations = [0]*4
            allocations[fixed_idx] = fixed_value
            
            # Determine varying protocols based on fixed index
            if fixed_idx == 0:  # Venus fixed
                allocations[1] = X[i,j]  # Aave
                allocations[2] = Y[i,j]  # Kinza
            elif fixed_idx == 1:  # Aave fixed
                allocations[0] = X[i,j]  # Venus
                allocations[2] = Y[i,j]  # Kinza
            elif fixed_idx == 2:  # Kinza fixed
                allocations[0] = X[i,j]  # Venus  
                allocations[1] = Y[i,j]  # Aave
            else:  # Euler fixed
                allocations[0] = X[i,j]  # Venus
                allocations[1] = Y[i,j]  # Aave
            
            # Calculate residual
            residual = T - sum(allocations)
            if residual < 0: continue
            
            # Set residual protocol
            residual_idx = 3 if fixed_idx !=3 else 2  # Handle Kinza/Euler
            allocations[residual_idx] = residual
            
            # Calculate APR
            try:
                total = sum(
                    alloc * globals()[f'get_supply_apr_{proto}'](alloc)['supply_apr']/100 
                    for proto, alloc in zip(['venus','aave','kinza','euler'], allocations)
                )
                Z[i,j] = total / T * 100  # Convert to percentage
            except:
                Z[i,j] = np.nan

    # Plotting
    plt.figure(figsize=(10,7))
    cp = plt.contourf(X, Y, Z, levels=30, cmap='viridis')
    plt.colorbar(label='Strategy APR (%)')
    
    # Dynamic labels
    if fixed_idx == 0:
        xlabel, ylabel = 'Aave Allocation', 'Kinza Allocation'
    elif fixed_idx == 1:
        xlabel, ylabel = 'Venus Allocation', 'Kinza Allocation'  
    elif fixed_idx == 2:
        xlabel, ylabel = 'Venus Allocation', 'Aave Allocation'
    else:
        xlabel, ylabel = 'Venus Allocation', 'Aave Allocation'
        
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(f"Fixed {fixed_protocol.capitalize()} at {fixed_value} USDT | Max APR: {np.nanmax(Z):.2f}%")

    # Mark optimizer solution
    if optimizer_result:
        allocs = optimizer_result['allocations']
        if fixed_idx == 0:
            plt.scatter(allocs[1], allocs[2], color='red', s=80, label='Optimizer')
        elif fixed_idx == 1:
            plt.scatter(allocs[0], allocs[2], color='red', s=80, label='Optimizer')
        elif fixed_idx == 2:
            plt.scatter(allocs[0], allocs[1], color='red', s=80, label='Optimizer')  
        else:
            plt.scatter(allocs[0], allocs[1], color='red', s=80, label='Optimizer')
        plt.legend()

    plt.show()


# Check all fixed protocol slices
plot_strategy_slice(T, 'venus', 0, result)
plot_strategy_slice(T, 'aave', 0, result) 
plot_strategy_slice(T, 'kinza', 0, result)
plot_strategy_slice(T, 'euler', 0, result)
