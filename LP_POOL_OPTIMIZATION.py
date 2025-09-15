import math
import json
from web3 import Web3
from scipy.optimize import minimize

# Initialize Web3 connection
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

with open(r'C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\LP_abi.json') as f:
    V3_ABI = json.load(f)
with open(r'C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\LP_pancake_abi.json') as f:
    V3_P_ABI = json.load(f)

# Pool configurations
POOLS = {
    'uniswap_0.01': {
        'address': '0x2C3c320D49019D4f9A92352e947c7e5AcFE47D68',
        'fee_tier': 0.0001,
        'abi': V3_ABI,
        '24h_fees': 2200  
    },
    'uniswap_0.05': {
        'address': '0xcCDFcd1aaC447D5B29980f64b831c532a6a33726',
        'fee_tier': 0.0005,
        'abi': V3_ABI,
        '24h_fees': 2.14  
    },
    'pancake_0.05': {
        'address': '0x4f31Fa980a675570939B737Ebdde0471a4Be40Eb',
        'fee_tier': 0.0005,
        'abi': V3_P_ABI,
        '24h_fees': 348  
    }
}


ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')


def get_pool_data(pool_config):
    try:
        pool = w3.eth.contract(address=pool_config['address'], abi=pool_config['abi'])
        
        slot0 = pool.functions.slot0().call()
        current_tick = slot0[1]
        tick_spacing = pool.functions.tickSpacing().call()
        
        tick_lower = current_tick - tick_spacing
        tick_upper = current_tick + tick_spacing
        
        def tick_to_price(tick):
            return 1.0001 ** tick

        pa = tick_to_price(tick_lower)
        pb = tick_to_price(tick_upper)
        sqrtp_low = int(math.sqrt(pa) * (2 ** 96))
        sqrtp_upp = int(math.sqrt(pb) * (2 ** 96))

        # Calculate existing liquidity in range
        liquidity = pool.functions.liquidity.call()

        # Get token decimals
        token0 = pool.functions.token0().call()
        token1 = pool.functions.token1().call()
        decimals0 = w3.eth.contract(address=token0, abi=ERC20_ABI).functions.decimals().call()
        decimals1 = w3.eth.contract(address=token1, abi=ERC20_ABI).functions.decimals().call()

        return {
            'sqrtp_low': sqrtp_low,
            'sqrtp_upp': sqrtp_upp,
            'decimals0': decimals0,
            'decimals1': decimals1,
            'existing_liq': liquidity,
            '24h_fees': pool_config['24h_fees']
        }
    
    except Exception as e:
        print(f"Error fetching data for {pool_config['address']}: {str(e)}")
        return None

def calculate_liquidity(amount0, amount1, sqrt_a, sqrt_b):

    q96 = 2 ** 96
    if sqrt_b <= sqrt_a or (sqrt_b - sqrt_a) == 0:
        return 0
    liq0 = (amount0 * (sqrt_a * sqrt_b) // q96) // (sqrt_b - sqrt_a)
    liq1 = (amount1 * q96) // (sqrt_b - sqrt_a)
    return min(liq0, liq1)


def optimize_allocation(T_usdc, T_usdt):
    pool_params = {}
    for pool_name, config in POOLS.items():
        data = get_pool_data(config)
        if data:
            pool_params[pool_name] = data

    scale = 10

    # Objective function
    def objective(x):
        total_fees = 0
        for i, (pool_name, params) in enumerate(pool_params.items()):
            usdc_alloc = x[i*2]
            usdt_alloc = x[i*2+1]
            
            # Convert to raw units
            amount0 = int(usdc_alloc * 10**params['decimals0'])
            amount1 = int(usdt_alloc * 10**params['decimals1'])
            
            # Calculate added liquidity
            added_liq = calculate_liquidity(amount0, amount1, 
                                          params['sqrtp_low'], 
                                          params['sqrtp_upp'])
            
            # Calculate fee share
            total_liq = params['existing_liq'] + added_liq
            if total_liq == 0:
                continue
            fee_share = added_liq / total_liq
            total_fees += fee_share * params['24h_fees']*scale
            
        return -total_fees  


    # Constraints
    constraints = [
        {'type': 'ineq', 'fun': lambda x: T_usdc - sum(x[::2])},  # USDC total
        {'type': 'ineq', 'fun': lambda x: T_usdt - sum(x[1::2])}, # USDT total
    ]

    # Bounds (non-negative allocations)
    num_pools = len(pool_params)
    bounds = [(0, T_usdc) if i%2==0 else (0, T_usdt) for i in range(num_pools*2)]

    # Initial guess (equal distribution)
    x0 = [T_usdc/num_pools if i%2==0 else T_usdt/num_pools for i in range(num_pools*2)]

    # Run optimization
    result = minimize(
    objective, x0, method='trust-constr',
    bounds=bounds, constraints=constraints,
    options={
        'maxiter': 10000,
        'xtol': 1e-4,
        'gtol': 1e-4,
        'disp': True,
        'initial_tr_radius': 10.0
    })
    
    return result, pool_params
def compute_fee_for_allocation(usdc_alloc, usdt_alloc, pool_params):
    """Compute total fees for a given allocation to all pools"""
    total_fees = 0
    for i, (pool_name, params) in enumerate(pool_params.items()):
        # Convert to raw units
        amount0 = int(usdc_alloc[i] * 10**params['decimals0'])
        amount1 = int(usdt_alloc[i] * 10**params['decimals1'])
        
        # Calculate added liquidity
        added_liq = calculate_liquidity(amount0, amount1, 
                                      params['sqrtp_low'], 
                                      params['sqrtp_upp'])
        
        # Calculate fee share
        total_liq = params['existing_liq'] + added_liq
        if total_liq == 0:
            continue
        fee_share = added_liq / (total_liq + 1e-9)
        total_fees += fee_share * params['24h_fees']
        
    return total_fees/10

import math
import json
import random
import numpy as np
from web3 import Web3
from scipy.optimize import minimize
import time


def brute_force_validation(T_usdc, T_usdt, pool_params, num_samples=10000):
    """Validate optimizer results with random sampling"""
    print("\nRunning brute-force validation with", num_samples, "samples...")
    start_time = time.time()
    
    # Get optimizer's solution fee
    optimizer_fee = compute_fee_for_allocation(
        [result.x[0], result.x[2], result.x[4]],
        [result.x[1], result.x[3], result.x[5]],
        pool_params
    )
    
    # Initialize best found allocation
    best_fee = -1
    best_usdc_alloc = [0, 0, 0]
    best_usdt_alloc = [0, 0, 0]
    
    # Generate random allocations
    for _ in range(num_samples):
        # Generate random allocation percentages
        weights = np.random.dirichlet(np.ones(3), size=1)[0]
        
        # Allocate USDC
        usdc_alloc = [T_usdc * w for w in weights]
        
        # Allocate USDT (can be different distribution)
        weights_usdt = np.random.dirichlet(np.ones(3), size=1)[0]
        usdt_alloc = [T_usdt * w for w in weights_usdt]
        
        # Compute fees for this allocation
        fee = compute_fee_for_allocation(usdc_alloc, usdt_alloc, pool_params)
        
        # Track best found
        if fee > best_fee:
            best_fee = fee
            best_usdc_alloc = usdc_alloc
            best_usdt_alloc = usdt_alloc
    
    # Print results
    print(f"Brute-force completed in {time.time()-start_time:.2f} seconds")
    print(f"Best random fee: {best_fee:.6f}")
    print(f"Optimizer's fee: {optimizer_fee:.6f}")
    print(f"Difference: {optimizer_fee - best_fee:.6f}")
    
    return best_usdc_alloc, best_usdt_alloc, best_fee   


# User inputs---------------------------------------------------------------
T_usdc = 1e5
T_usdt = 1e5


# Run optimization
result, pool_params = optimize_allocation(T_usdc, T_usdt)


# Display results
if result.success:
    print("-" * 45)
    print("Optimized Allocation for T:", T_usdc)
    print("-" * 45)

    total_alloc_usdc = sum(result.x[::2])  # Sum all USDC allocations
    total_alloc_usdt = sum(result.x[1::2])  # Sum all USDT allocations
    
    for i, (pool_name, params) in enumerate(pool_params.items()):
        usdc = result.x[i*2]
        usdt = result.x[i*2+1]
        
        # Calculate percentages
        usdc_pct = (usdc / total_alloc_usdc * 100) if total_alloc_usdc > 0 else 0
        usdt_pct = (usdt / total_alloc_usdt * 100) if total_alloc_usdt > 0 else 0
        
        print(f"\n{pool_name} ({POOLS[pool_name]['address']}):")
        print(f"  USDC allocated: {usdc:.2f} ({usdc_pct:.2f}%)")
        print(f"  USDT allocated: {usdt:.2f} ({usdt_pct:.2f}%)")
        
        # Calculate position liquidity 
        raw_usdc = int(usdc * 10**params['decimals0'])
        raw_usdt = int(usdt * 10**params['decimals1'])
        liq = calculate_liquidity(raw_usdc, raw_usdt, 
                                params['sqrtp_low'], 
                                params['sqrtp_upp'])
        print(f"  Liquidity provided: {liq}")
        print(f"  Existing pool liquidity: {params['existing_liq']}")
        print(f"  fraction : {liq/(liq+params['existing_liq'])}")
        print(f"  Projected daily fees: ${(liq/(params['existing_liq'] + liq)) * params['24h_fees']:.2f}")
        print("-" * 45)

    print(f"\nTotal projected daily fees: ${-result.fun:.2f}")
    print("\nComparison: Fees if all tokens are allocated to a single pool")
    for pool_name, params in pool_params.items():
        raw_usdc = int(T_usdc * 10**params['decimals0'])
        raw_usdt = int(T_usdt * 10**params['decimals1'])
        liq = calculate_liquidity(raw_usdc, raw_usdt, params['sqrtp_low'], params['sqrtp_upp'])
        fee_share = liq / (liq + params['existing_liq'] + 1e-9)
        fees = fee_share * params['24h_fees']
        print(f"{pool_name}: ${fees:.2f} (Fraction: {fee_share:.6f})")
    best_usdc, best_usdt, best_fee = brute_force_validation(T_usdc, T_usdt, pool_params)
    
    # Print comparison
    print("\nBrute-force validation results:")
    print(f"Best fee found: {best_fee:.6f}")
    print(f"Optimizer's fee: {-result.fun:.6f}")
    print(f"Difference: {-result.fun - best_fee:.6f}")
    
    # Print all-in-one comparisons
    print("\nAll-in-one comparisons:")
    for i, (pool_name, params) in enumerate(pool_params.items()):
        # All-in for this pool
        usdc_alloc = [0, 0, 0]
        usdt_alloc = [0, 0, 0]
        usdc_alloc[i] = T_usdc
        usdt_alloc[i] = T_usdt
        
        fee = compute_fee_for_allocation(usdc_alloc, usdt_alloc, pool_params)
        print(f"{pool_name}: ${fee:.6f}")   
else:
    print("Optimization failed:", result.message)

