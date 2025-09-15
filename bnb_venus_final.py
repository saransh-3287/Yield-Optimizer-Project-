import json
from web3 import Web3

# BSC Mainnet RPC endpoint
rpc_url = "https://bsc-dataseed.bnbchain.org/"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Venus Protocol Core Pool addresses
vbnb_address = web3.to_checksum_address("0xA07c5b74C9B40447a954e1466938b865b6BBea36")

# Load your vToken ABI (same as USDT)
abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\usdt_abi.json"
with open(abi_path, 'r') as abi_file:
    vtoken_abi = json.load(abi_file)

# Direct IRM ABI (Multi-Kink Interest Rate Model) - Same parameters as USDT but direct access
direct_irm_abi = [
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

# Initialize contracts
vtoken_contract = web3.eth.contract(address=vbnb_address, abi=vtoken_abi)

# Get essential market data
cash = vtoken_contract.functions.getCash().call()
total_borrows = vtoken_contract.functions.totalBorrows().call()
total_reserves = vtoken_contract.functions.totalReserves().call()
reserve_factor = vtoken_contract.functions.reserveFactorMantissa().call()

# Get interest rate model parameters (DIRECT ACCESS - No DATA_SOURCE_1 for BNB)
ir_model_address = vtoken_contract.functions.interestRateModel().call()
print(f"BNB Interest Rate Model Address: {ir_model_address}")

# Connect directly to the IRM contract (no switcher for BNB)
irm_contract = web3.eth.contract(address=ir_model_address, abi=direct_irm_abi)

# Get all required parameters directly from IRM contract
base_rate_per_block = irm_contract.functions.BASE_RATE_PER_BLOCK().call()
multiplier_per_block = irm_contract.functions.MULTIPLIER_PER_BLOCK().call()
kink_1 = irm_contract.functions.KINK_1().call()
multiplier_2_per_block = irm_contract.functions.MULTIPLIER_2_PER_BLOCK().call()
base_rate_2_per_block = irm_contract.functions.BASE_RATE_2_PER_BLOCK().call()
kink_2 = irm_contract.functions.KINK_2().call()
jump_multiplier_per_block = irm_contract.functions.JUMP_MULTIPLIER_PER_BLOCK().call()
blocks_per_year = irm_contract.functions.BLOCKS_PER_YEAR().call()
rate_1 = irm_contract.functions.RATE_1().call()
rate_2 = irm_contract.functions.RATE_2().call()

# BNB SV function using Two Kinks Model (same logic as USDT)
def SV_BNB(x):
    """
    Calculate new supply rate, borrow rate, and utilization for BNB after supplying x BNB tokens.
    Uses Venus Two Kinks Interest Rate Model (same as USDT).
    
    Args:
        x (float): Amount of BNB to supply
    
    Returns:
        tuple: (r_s, r_b, u_new)
    """
    # Convert x to wei and calculate new cash
    x_wei = int(x * 1e18)  # BNB has 18 decimals
    new_cash = cash + x_wei
    
    # Calculate new utilization as decimal (0.0 to 1.0)
    new_utilization = total_borrows / (new_cash + total_borrows) if (new_cash + total_borrows) > 0 else 0
    
    # Convert kinks to decimal for comparison (Venus stores them as mantissa scaled by 1e18)
    kink_1_decimal = abs(kink_1) / 1e18  # Use abs() for negative values
    kink_2_decimal = abs(kink_2) / 1e18
    
    # Venus Two Kinks Interest Rate Model (work in per-block rates, scaled by 1e18)
    if new_utilization <= kink_1_decimal:
        # Segment 1: BASE_RATE_PER_BLOCK + (utilization * MULTIPLIER_PER_BLOCK)
        utilization_scaled = int(new_utilization * 1e18)
        borrow_rate_per_block = base_rate_per_block + ((utilization_scaled * multiplier_per_block) // 1e18)
        
    elif new_utilization <= kink_2_decimal:
        # Segment 2: RATE_1 + ((utilization - KINK_1) * MULTIPLIER_2_PER_BLOCK)
        excess_util_scaled = int((new_utilization - kink_1_decimal) * 1e18)
        borrow_rate_per_block = rate_1 + ((excess_util_scaled * multiplier_2_per_block) // 1e18)
        
    else:
        # Segment 3: RATE_2 + ((utilization - KINK_2) * JUMP_MULTIPLIER_PER_BLOCK)
        excess_util_scaled = int((new_utilization - kink_2_decimal) * 1e18)
        borrow_rate_per_block = rate_2 + ((excess_util_scaled * jump_multiplier_per_block) // 1e18)
    
    # Convert to annual percentage (handle negative values properly)
    if borrow_rate_per_block < 0:
        r_b = -(abs(borrow_rate_per_block) / 1e18) * blocks_per_year * 100
    else:
        r_b = (borrow_rate_per_block / 1e18) * blocks_per_year * 100
    
    # Calculate supply rate using Venus formula
    reserve_factor_decimal = reserve_factor / 1e18
    r_s = r_b * new_utilization * (1 - reserve_factor_decimal)
    
    # Return utilization as percentage for display
    u_new = new_utilization * 100
    
    return r_s, r_b, u_new

# Current utilization for reference
current_utilization = (total_borrows / (total_borrows + cash)) * 100

print(f"Current BNB Utilization: {current_utilization:.4f}%")

print("Case:")
r_s, r_b, u_new = SV_BNB(0)
print(f"Current rates -> Supply APR: {r_s:.4f}%, Borrow APR: {r_b:.4f}%, Util: {u_new:.4f}%")

# Test with supply amount
r_s, r_b, u_new = SV_BNB(10)
print(f"After supplying 10 BNB -> Supply APR: {r_s:.4f}%, Borrow APR: {r_b:.4f}%, Util: {u_new:.4f}%")

# Test with larger supply amount
r_s, r_b, u_new = SV_BNB(100)
print(f"After supplying 100 BNB -> Supply APR: {r_s:.4f}%, Borrow APR: {r_b:.4f}%, Util: {u_new:.4f}%")
