import json
from web3 import Web3

def calculate_aave_apr(TOKEN_ADDRESS, DECIMALS, x_supplied):
   
    # Load ABIs 
    with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_supply_abi.json") as f:
        supply_abi = json.load(f)
    with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_reserve_factor_abi.json") as f:
        reserve_abi = json.load(f)
    with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_irm_strategy_abi.json") as f:
        strategy_abi = json.load(f)

    web3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.bnbchain.org/"))
    
    data_provider = web3.eth.contract(
        address="0x1e26247502e90b4fab9D0d17e4775e90085D2A35", #just one contract address to put in
        abi=reserve_abi
    )

    config = data_provider.functions.getReserveConfigurationData(TOKEN_ADDRESS).call()
    atokens_addresses = data_provider.functions.getReserveTokensAddresses(TOKEN_ADDRESS).call()
    ATOKEN_ADDRESS = atokens_addresses[0]
    reserve_factor = config[4] / 1e4
    
    atoken_contract = web3.eth.contract(address=ATOKEN_ADDRESS, abi=supply_abi)
    total_supply = atoken_contract.functions.totalSupply().call() / 10**DECIMALS

    # 3. Get Interest Rate Strategy
    strategy_address = data_provider.functions.getInterestRateStrategyAddress(TOKEN_ADDRESS).call()
    strategy_contract = web3.eth.contract(address=strategy_address, abi=strategy_abi)
    
    RAY = 1e27
    base_rate = strategy_contract.functions.getBaseVariableBorrowRate(TOKEN_ADDRESS).call() / RAY
    slope1 = strategy_contract.functions.getVariableRateSlope1(TOKEN_ADDRESS).call() / RAY
    slope2 = strategy_contract.functions.getVariableRateSlope2(TOKEN_ADDRESS).call() / RAY
    opt_util = strategy_contract.functions.getOptimalUsageRatio(TOKEN_ADDRESS).call() / RAY

    # 4. Get Borrow Data
    reserve_data = data_provider.functions.getReserveData(TOKEN_ADDRESS).call()
    total_borrow = (reserve_data[3] + reserve_data[4]) / 10**DECIMALS  

    # 5. Calculate APR
    c_a = total_borrow * 10**DECIMALS
    d_a = total_supply * 10**DECIMALS
    x = x_supplied * 10**DECIMALS

    utilization = c_a / (d_a + x) if (d_a + x) > 0 else 0

    if utilization <= opt_util:
        borrow_rate = base_rate + (slope1 * utilization / opt_util)
    else:
        borrow_rate = base_rate + slope1 + ((utilization - opt_util) / (1 - opt_util)) * slope2

    supply_rate = borrow_rate * utilization * (1 - reserve_factor)

    return {
        'supply_apr': round(supply_rate * 100, 4),
        'borrow_apr': round(borrow_rate * 100, 4),
        'utilization': round(utilization * 100, 4)
    }

results = calculate_aave_apr(
    TOKEN_ADDRESS = "0x55d398326f99059fF775485246999027B3197955",  
    DECIMALS = 18,
    x_supplied = 100000  
)

print(f"""
Supply APR: {results['supply_apr']}%
Borrow APR: {results['borrow_apr']}%
Utilization: {results['utilization']}%
""")
