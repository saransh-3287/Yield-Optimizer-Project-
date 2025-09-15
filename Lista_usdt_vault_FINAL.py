from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
import math

# --- Initialize Web3 with POA middleware ---
w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware(), layer=0)

# --- Constants ---
SECONDS_PER_YEAR = 31536000
CURVE_STEEPNESS = 4 * 10**18  # Verify with protocol docs
TARGET_UTILIZATION = 0.9 * 10**18  # 90% in WAD

# --- Load ABIs ---
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\Lista_abi.json") as f:
    irm_abi = json.load(f)
with open(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\moolah_abi.json") as f:
    moolah_abi = json.load(f)

# Minimal ERC-20 ABI for decimals
ERC20_ABI = [{
    "constant": True,
    "inputs": [],
    "name": "decimals",
    "outputs": [{"name": "", "type": "uint8"}],
    "type": "function"
}]

# --- Contract Setup ---
irm_contract_address = Web3.to_checksum_address("0xFe7dAe87Ebb11a7BEB9F534BB23267992d9cDe7c")
irm = w3.eth.contract(address=irm_contract_address, abi=irm_abi)
moolah_address = Web3.to_checksum_address(irm.functions.MOOLAH().call())
moolah = w3.eth.contract(address=moolah_address, abi=moolah_abi)

# --- All Market IDs ---
market_ids = [
    bytes.fromhex("975f4cf3db16812d995f60e19bec91a96108d47429237acc8d208bc0519c5b19"),
    bytes.fromhex("417eef8a15b54c61c64026d13ff067611579d95d392c969cac919115b5a379a2"),
    bytes.fromhex("ed20ae46f7f909622225cdf9f301854bd46d74f639ab07bba723e5431ab27653"),
    bytes.fromhex("8a1fffce64f5b29d59e7ebfd7a927e29acdb932cc73508c9861157eeef9b8e1a"),
    bytes.fromhex("7024975b01054a099391a7335367b04ca419592dc0f5b94ef93d5da8d1fe570a"),
    bytes.fromhex("2b87aedf2672376147a71cf09d3b7c776f92e6c52d22a12fe1322bb205892961"),
    bytes.fromhex("6350ccd3fe864c1c750f2b5d99b81d1fd712250a650808d2f6e17651b1047e37"),
    bytes.fromhex("98736236a21390ea3697d1776974c4adcd7d8fe2961c9296cb744c3627b8b349"),
    bytes.fromhex("e2fac994ce98526fbc986a2f3877efddd114a09f790d679eb1cd978c3e050e55"),
    bytes.fromhex("169a54980294ed1343d1d2bac1f279924a572ab0f2097214672565f06a275d19"),
    bytes.fromhex("8bf69f18eb2ad0ca4defa8e8ae8d5c1516118561e543a448dcdcdc860ed1fa47"),
    bytes.fromhex("df6046e4442d873576d16313f634a44a3a621ddc69fdf973ba5025ca427a5e5b")
]

def get_token_decimals(token_address):
    """Fetch decimals for an ERC-20 token"""
    token = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    return token.functions.decimals().call()

def calculate_current_borrow_rate(market_id):
    try:
        # Get market state
        market = moolah.functions.market(market_id).call()
        total_supply = market[0]  # totalSupplyAssets
        total_borrow = market[2]  # totalBorrowAssets

        # Utilization rate calculation
        utilization = (total_borrow * 10**18) // total_supply if total_supply else 0

        # Get current rate at target
        rate_at_target = irm.functions.rateAtTarget(market_id).call()

        # Error term calculation
        if utilization > TARGET_UTILIZATION:
            err_norm_factor = 10**18 - TARGET_UTILIZATION
        else:
            err_norm_factor = TARGET_UTILIZATION
        err = (utilization - TARGET_UTILIZATION) * 10**18 // err_norm_factor

        # Curve calculation
        if err < 0:
            coeff = (10**18 - (10**18 // CURVE_STEEPNESS)) * err // 10**18 + 10**18
        else:
            coeff = (CURVE_STEEPNESS - 10**18) * err // 10**18 + 10**18

        # Final borrow rate calculation
        borrow_rate = (coeff * rate_at_target) // 10**18
        borrow_rate_apr = borrow_rate * SECONDS_PER_YEAR / 10**18

        return {
            'total_supply': total_supply,
            'utilization': utilization / 10**18,
            'current_borrow_rate_apr': borrow_rate_apr
        }

    except Exception as e:
        print(f"Calculation error: {str(e)}")
        return None

def get_borrow_apr(market_id, x):
    """Calculate borrow APR after depositing x tokens"""
    try:
        # Get market parameters
        market_params = moolah.functions.idToMarketParams(market_id).call()
        loan_token_address = market_params[1]  # loanAsset address

        # Get token decimals
        decimals = get_token_decimals(loan_token_address)
        x_scaled = int(x * 10**decimals)  # Correct scaling

        # Get market state
        market = moolah.functions.market(market_id).call()
        total_supply = market[0]
        total_borrow = market[2]

        # Simulate new supply
        new_total_supply = total_supply + x_scaled
        if new_total_supply == 0:
            new_utilization = 0
        else:
            new_utilization = (total_borrow * 10**18) // new_total_supply

        # Get current rate at target
        rate_at_target = irm.functions.rateAtTarget(market_id).call()

        # Error term calculation
        if new_utilization > TARGET_UTILIZATION:
            err_norm_factor = 10**18 - TARGET_UTILIZATION
        else:
            err_norm_factor = TARGET_UTILIZATION
        err = (new_utilization - TARGET_UTILIZATION) * 10**18 // err_norm_factor

        # Curve calculation
        if err < 0:
            coeff = (10**18 - (10**18 // CURVE_STEEPNESS)) * err // 10**18 + 10**18
        else:
            coeff = (CURVE_STEEPNESS - 10**18) * err // 10**18 + 10**18

        borrow_rate = (coeff * rate_at_target) // 10**18
        borrow_rate_apr = borrow_rate * SECONDS_PER_YEAR / 10**18

        return {
            'new_utilization': new_utilization / 10**18,
            'new_borrow_rate_apr': borrow_rate_apr
        }

    except Exception as e:
        print(f"Simulation error: {str(e)}")
        return None

if __name__ == "__main__":
    deposit_amount = 100000  # 100,000 tokens
    market_data = []
    
    for idx, market_id in enumerate(market_ids, 1):
        print(f"\n{'='*40}")
        print(f"Market {idx} (ID: {market_id.hex()})")
        
        # Get current state
        current = calculate_current_borrow_rate(market_id)
        if current:
            print(f"\nCurrent Utilization: {current['utilization']:.2%}")
            print(f"Current Borrow Rate: {current['current_borrow_rate_apr']:.2%} APR")
            
            # Store data for weighted average
            market_data.append({
                'borrow_apr': current['current_borrow_rate_apr'],
                'total_supply': current['total_supply']
            })
        
        # Simulate deposit
        simulation = get_borrow_apr(market_id, deposit_amount)
        if simulation:
            print(f"\nAfter depositing {deposit_amount} tokens:")
            print(f"New Utilization: {simulation['new_utilization']:.2%}")
            print(f"New Borrow Rate: {simulation['new_borrow_rate_apr']:.2%} APR")
        
        print(f"{'='*40}\n")
    
    # Calculate weighted average borrow APR
    if market_data:
        total_weight = sum(item['total_supply'] for item in market_data)
        if total_weight > 0:
            weighted_sum = sum(item['borrow_apr'] * item['total_supply'] for item in market_data)
            weighted_avg_apr = weighted_sum / total_weight
            
            print(f"\n{'='*40}")
            print(f"VAULT-LEVEL WEIGHTED AVERAGE BORROW APR")
            print(f"Total Supply Across Markets: {total_weight / 1e6:,.2f} USDT")  # Assuming USDT decimals=6
            print(f"Weighted Average APR: {weighted_avg_apr:.2%}")
            print(f"{'='*40}")
        else:
            print("Error: Total supply across markets is zero")

if __name__ == "__main__":
    deposit_amount = 100000  # 100,000 tokens
    market_data = []
    supply_data = []
    
    for idx, market_id in enumerate(market_ids, 1):
        print(f"\n{'='*40}")
        print(f"Market {idx} (ID: {market_id.hex()})")
        
        # Get current state
        current = calculate_current_borrow_rate(market_id)
        if current:
            print(f"\nCurrent Utilization: {current['utilization']:.2%}")
            print(f"Current Borrow Rate: {current['current_borrow_rate_apr']:.2%} APR")
            
            # Store data for weighted averages
            market_data.append({
                'borrow_apr': current['current_borrow_rate_apr'],
                'total_supply': current['total_supply']
            })
            
            # Calculate supply APR with assumed 5% reserve factor (0.95)
            supply_apr = current['current_borrow_rate_apr'] * current['utilization'] * 0.95
            supply_data.append({
                'supply_apr': supply_apr,
                'total_supply': current['total_supply']
            })
            print(f"Current Supply APR: {supply_apr:.2%}")
        
        # Simulate deposit
        simulation = get_borrow_apr(market_id, deposit_amount)
        if simulation:
            print(f"\nAfter depositing {deposit_amount} tokens:")
            print(f"New Utilization: {simulation['new_utilization']:.2%}")
            print(f"New Borrow Rate: {simulation['new_borrow_rate_apr']:.2%} APR")
        
        print(f"{'='*40}\n")
    
    # Calculate weighted average borrow APR
    if market_data:
        total_weight = sum(item['total_supply'] for item in market_data)
        if total_weight > 0:
            weighted_sum = sum(item['borrow_apr'] * item['total_supply'] for item in market_data)
            weighted_avg_apr = weighted_sum / total_weight
            
            print(f"\n{'='*40}")
            print(f"VAULT-LEVEL WEIGHTED AVERAGE BORROW APR")
            print(f"Total Supply Across Markets: {total_weight / 1e6:,.2f} USDT")
            print(f"Weighted Average Borrow APR: {weighted_avg_apr:.2%}")
            print(f"{'='*40}")
        else:
            print("Error: Total supply across markets is zero")
    
    # Calculate weighted average supply APR
    if supply_data:
        total_supply_weight = sum(item['total_supply'] for item in supply_data)
        if total_supply_weight > 0:
            weighted_supply_sum = sum(item['supply_apr'] * item['total_supply'] for item in supply_data)
            weighted_avg_supply_apr = weighted_supply_sum / total_supply_weight
            
            print(f"\n{'='*40}")
            print(f"VAULT-LEVEL WEIGHTED AVERAGE SUPPLY APR")
            print(f"Total Supply Across Markets: {total_supply_weight / 1e6:,.2f} USDT")
            print(f"Weighted Average Supply APR: {weighted_avg_supply_apr:.2%}")
            print(f"{'='*40}")
        else:
            print("Error: Total supply across markets is zero for supply APR")
