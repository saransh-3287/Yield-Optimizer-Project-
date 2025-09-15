import json
from web3 import Web3

# BSC Mainnet RPC endpoint
rpc_url = "https://bsc-dataseed.bnbchain.org/"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Venus Protocol Core Pool addresses
vusdt_address = web3.to_checksum_address("0xfD5840Cd36d94D7229439859C0112a4185BC0255")

# Load your vToken ABI
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\usdt_abi.json"
with open(abi_path, 'r') as abi_file:
    vtoken_abi = json.load(abi_file)

# Data Source Switcher ABI
switcher_abi = [
    {"inputs":[],"name":"currentDataSource","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"DATA_SOURCE_1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"DATA_SOURCE_2","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]

# Data Source 1 ABI (Multi-Kink Interest Rate Model)
data_source_1_abi = [
    {"inputs":[],"name":"BASE_RATE_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MULTIPLIER_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"KINK_1","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MULTIPLIER_2_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"BASE_RATE_2_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"KINK_2","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"JUMP_MULTIPLIER_PER_BLOCK","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"BLOCKS_PER_YEAR","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"RATE_1","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"RATE_2","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"cash","type":"uint256"},{"internalType":"uint256","name":"borrows","type":"uint256"},{"internalType":"uint256","name":"reserves","type":"uint256"}],"name":"getBorrowRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"cash","type":"uint256"},{"internalType":"uint256","name":"borrows","type":"uint256"},{"internalType":"uint256","name":"reserves","type":"uint256"},{"internalType":"uint256","name":"reserveFactorMantissa","type":"uint256"}],"name":"getSupplyRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]

vtoken_contract = web3.eth.contract(address=vusdt_address, abi=vtoken_abi)

print("=== Venus Protocol Core Pool USDT - Multi-Kink Interest Rate Analysis ===\n")

# Get basic market data
total_supply = vtoken_contract.functions.totalSupply().call()
cash = vtoken_contract.functions.getCash().call()
total_borrows = vtoken_contract.functions.totalBorrows().call()
total_reserves = vtoken_contract.functions.totalReserves().call()
reserve_factor = vtoken_contract.functions.reserveFactorMantissa().call()

# Convert to human readable
total_supply_human = total_supply / 1e8
cash_human = cash / 1e18
total_borrows_human = total_borrows / 1e18
total_reserves_human = total_reserves / 1e18
reserve_factor_human = reserve_factor / 1e18

print(f"vUSDT Total Supply: {total_supply_human:.6f}")
print(f"Cash (Available Liquidity): {cash_human:.2f} USDT")
print(f"Total Borrowed: {total_borrows_human:.2f} USDT")
print(f"Total Reserves: {total_reserves_human:.2f} USDT")
print(f"Reserve Factor: {reserve_factor_human:.4%}")

# Calculate utilization rate using raw values from vtoken_contract
utilization_rate = total_borrows / (total_borrows + cash)
utilization_rate_pct = utilization_rate * 100

print(f"Utilization Rate: {utilization_rate_pct:.4f}%")

# Get interest rate model address (this is the switcher)
ir_model_switcher_address = vtoken_contract.functions.interestRateModel().call()
print(f"\nInterest Rate Model Switcher Address: {ir_model_switcher_address}")

# Get the actual interest rate model address
switcher_contract = web3.eth.contract(address=ir_model_switcher_address, abi=switcher_abi)
data_source_1 = switcher_contract.functions.DATA_SOURCE_1().call()
data_source_2 = switcher_contract.functions.DATA_SOURCE_2().call()
current_data_source = switcher_contract.functions.currentDataSource().call()

print(f"Data Source 1: {data_source_1}")
print(f"Data Source 2: {data_source_2}")
print(f"Current Data Source: {current_data_source}")

# Connect to Data Source 1 (Multi-Kink Model)
data_source_1_contract = web3.eth.contract(address=data_source_1, abi=data_source_1_abi)

print(f"\n=== Multi-Kink Interest Rate Model Parameters (Data Source 1) ===")

try:
    # Get all parameters
    base_rate_per_block = data_source_1_contract.functions.BASE_RATE_PER_BLOCK().call()
    multiplier_per_block = data_source_1_contract.functions.MULTIPLIER_PER_BLOCK().call()
    kink_1 = data_source_1_contract.functions.KINK_1().call()
    multiplier_2_per_block = data_source_1_contract.functions.MULTIPLIER_2_PER_BLOCK().call()
    base_rate_2_per_block = data_source_1_contract.functions.BASE_RATE_2_PER_BLOCK().call()
    kink_2 = data_source_1_contract.functions.KINK_2().call()
    jump_multiplier_per_block = data_source_1_contract.functions.JUMP_MULTIPLIER_PER_BLOCK().call()
    blocks_per_year = data_source_1_contract.functions.BLOCKS_PER_YEAR().call()
    
    # Get computed rates at kinks
    rate_1 = data_source_1_contract.functions.RATE_1().call()
    rate_2 = data_source_1_contract.functions.RATE_2().call()
    
    print("Raw Values (per block, scaled by 1e18):")
    print(f"Base Rate Per Block: {base_rate_per_block}")
    print(f"Multiplier Per Block: {multiplier_per_block}")
    print(f"Kink 1: {kink_1}")
    print(f"Multiplier 2 Per Block: {multiplier_2_per_block}")
    print(f"Base Rate 2 Per Block: {base_rate_2_per_block}")
    print(f"Kink 2: {kink_2}")
    print(f"Jump Multiplier Per Block: {jump_multiplier_per_block}")
    print(f"Blocks Per Year: {blocks_per_year}")
    print(f"Rate 1 (at Kink 1): {rate_1}")
    print(f"Rate 2 (at Kink 2): {rate_2}")
    
    print(f"\n=== Converted to Annual Percentages ===")
    
    # Convert to annual percentages
    # Note: These are signed integers, so we need to handle them carefully
    def to_percentage(value, blocks_per_year_val):
        if value < 0:
            return -(abs(value) / 1e18) * blocks_per_year_val * 100
        return (value / 1e18) * blocks_per_year_val * 100
    
    base_rate_annual = to_percentage(base_rate_per_block, blocks_per_year)
    multiplier_annual = to_percentage(multiplier_per_block, blocks_per_year) 
    kink_1_pct = (kink_1 / 1e18) * 100
    multiplier_2_annual = to_percentage(multiplier_2_per_block, blocks_per_year)
    base_rate_2_annual = to_percentage(base_rate_2_per_block, blocks_per_year)
    kink_2_pct = (kink_2 / 1e18) * 100
    jump_multiplier_annual = to_percentage(jump_multiplier_per_block, blocks_per_year)
    rate_1_annual = to_percentage(rate_1, blocks_per_year)
    rate_2_annual = to_percentage(rate_2, blocks_per_year)
    
    print(f"Base Rate: {base_rate_annual:.4f}% per year")
    print(f"Multiplier (Slope 1): {multiplier_annual:.4f}% per year")
    print(f"Kink 1: {kink_1_pct:.2f}%")
    print(f"Multiplier 2 (Slope 2): {multiplier_2_annual:.4f}% per year")
    print(f"Base Rate 2: {base_rate_2_annual:.4f}% per year")
    print(f"Kink 2: {kink_2_pct:.2f}%")
    print(f"Jump Multiplier (Slope 3): {jump_multiplier_annual:.4f}% per year")
    print(f"Blocks Per Year: {blocks_per_year:,}")
    
    print(f"\n=== Interest Rate at Key Points ===")
    print(f"Borrow Rate at Kink 1 ({kink_1_pct:.1f}%): {rate_1_annual:.4f}%")
    print(f"Borrow Rate at Kink 2 ({kink_2_pct:.1f}%): {rate_2_annual:.4f}%")
    
    # Calculate theoretical rates
    print(f"\n=== Multi-Kink Model Structure ===")
    print(f"• 0% to {kink_1_pct:.1f}%: Base Rate + (Utilization × Multiplier)")
    print(f"  Formula: {base_rate_annual:.4f}% + (util × {multiplier_annual:.4f}%)")
    print(f"• {kink_1_pct:.1f}% to {kink_2_pct:.1f}%: Base Rate 2 + (Excess Util × Multiplier 2)")
    print(f"  Formula: {base_rate_2_annual:.4f}% + (excess_util × {multiplier_2_annual:.4f}%)")
    print(f"• Above {kink_2_pct:.1f}%: Previous Rate + (Excess Util × Jump Multiplier)")
    print(f"  Formula: Rate at Kink 2 + (excess_util × {jump_multiplier_annual:.4f}%)")
    
    # Show where current utilization sits in the model
    print(f"\n=== Current Position in Model ===")
    print(f"Current Utilization: {utilization_rate_pct:.4f}%")
    if utilization_rate_pct <= kink_1_pct:
        print(f"Current position: Segment 1 (0% to {kink_1_pct:.1f}%)")
        current_rate_calc = base_rate_annual + (utilization_rate_pct * multiplier_annual / 100)
        print(f"Expected Borrow Rate: {current_rate_calc:.4f}%")
    elif utilization_rate_pct <= kink_2_pct:
        print(f"Current position: Segment 2 ({kink_1_pct:.1f}% to {kink_2_pct:.1f}%)")
        excess_util = utilization_rate_pct - kink_1_pct
        current_rate_calc = rate_1_annual + (excess_util * multiplier_2_annual / 100)
        print(f"Expected Borrow Rate: {current_rate_calc:.4f}%")
    else:
        print(f"Current position: Segment 3 (above {kink_2_pct:.1f}%)")
        excess_util = utilization_rate_pct - kink_2_pct
        current_rate_calc = rate_2_annual + (excess_util * jump_multiplier_annual / 100)
        print(f"Expected Borrow Rate: {current_rate_calc:.4f}%")
    
except Exception as e:
    print(f"Error reading Data Source 1 parameters: {e}")

# Calculate rates using contract functions
print(f"\n=== Current Borrow & Supply Rates ===")

try:
    # Get borrow rate from contract
    calculated_borrow_rate_per_block = data_source_1_contract.functions.getBorrowRate(cash, total_borrows, total_reserves).call()
    calculated_borrow_apy = ((calculated_borrow_rate_per_block / 1e18) * 10512000) * 100
    
    # Get supply rate from contract
    calculated_supply_rate_per_block = data_source_1_contract.functions.getSupplyRate(cash, total_borrows, total_reserves, reserve_factor).call()
    calculated_supply_apy = ((calculated_supply_rate_per_block / 1e18) * 10512000) * 100
    
    print(f"Contract Calculated Borrow APR: {calculated_borrow_apy:.4f}%")
    print(f"Contract Calculated Supply APR: {calculated_supply_apy:.4f}%")
    
    # Manual calculation using Venus formula: supply_rate = borrow_rate * utilization_rate * (1 - reserve_factor)
    manual_supply_rate_per_block = calculated_borrow_rate_per_block * utilization_rate * (1 - reserve_factor_human)
    manual_supply_apy = ((manual_supply_rate_per_block / 1e18) * 10512000) * 100
    
    print(f"\n=== Supply Rate Formula Verification ===")
    print(f"Venus Formula: supply_rate = borrow_rate × utilization_rate × (1 - reserve_factor)")
    print(f"Calculation: {calculated_borrow_apy:.4f}% × {utilization_rate:.6f} × {(1-reserve_factor_human):.4f}")
    print(f"Manual Calculated Supply APR: {manual_supply_apy:.4f}%")
    
    # Show the breakdown
    print(f"\n=== Supply Rate Breakdown ===")
    print(f"Borrow Rate (per block): {calculated_borrow_rate_per_block}")
    print(f"Utilization Rate: {utilization_rate:.6f}")
    print(f"Reserve Factor: {reserve_factor_human:.4f}")
    print(f"One Minus Reserve Factor: {(1-reserve_factor_human):.4f}")
    print(f"Supply Rate (per block): {calculated_supply_rate_per_block}")
    
except Exception as e:
    print(f"Error calculating rates: {e}")
