import json
from web3 import Web3

# --- Load ABIs ---
comptroller_abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_comptroller_abi.json"
irm_abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_irm_abi copy.json"
switcher_abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_switcher_abi copy.json"
vtoken_abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_abi.json"

with open(comptroller_abi_path, 'r') as f:
    comptroller_abi = json.load(f)
with open(irm_abi_path, 'r') as f:
    irm_abi = json.load(f)
with open(switcher_abi_path, 'r') as f:
    switcher_abi = json.load(f)
with open(vtoken_abi_path, 'r') as f:
    vtoken_abi = json.load(f)

# --- Connect to BSC Mainnet ---
rpc_url = "https://bsc-dataseed.bnbchain.org/"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# --- Helper: Get vToken Address for a Given Token ---
def get_vtoken_address(token_address: str) -> str:
    """Finds vToken address by incrementing allMarkets(i) until zero address."""
    comptroller_addr = Web3.to_checksum_address('0xfD36E2c2a6789Db23113685031d7F16329158384')
    comptroller = web3.eth.contract(comptroller_addr, abi=comptroller_abi)
    target_address = Web3.to_checksum_address(token_address).lower()
    index = 0
    while True:
        try:
            vtoken_addr = comptroller.functions.allMarkets(index).call()
            if vtoken_addr == '0x0000000000000000000000000000000000000000':
                break
            vtoken = web3.eth.contract(vtoken_addr, abi=vtoken_abi)
            try:
                underlying_addr = Web3.to_checksum_address(vtoken.functions.underlying().call()).lower()
                if underlying_addr == target_address:
                    return vtoken_addr
            except Exception:
                pass
            index += 1
        except Exception as e:
            break
    return None


# --- Main Calculation Function ---
def calculate_venus_apr(token_address: str, supply_amount: float):
    vtoken_addr = get_vtoken_address(token_address)
    if not vtoken_addr:
        raise ValueError(f"No vToken found for {token_address} in Venus Core Pool.")
    vtoken_contract = web3.eth.contract(address=vtoken_addr, abi=vtoken_abi)

    # Get market data
    cash = vtoken_contract.functions.getCash().call()
    total_borrows = vtoken_contract.functions.totalBorrows().call()
    reserve_factor = vtoken_contract.functions.reserveFactorMantissa().call()

    # Get interest rate model parameters
    irm_address = vtoken_contract.functions.interestRateModel().call()
    
    irm_contract = web3.eth.contract(address=irm_address, abi=irm_abi)

    # Fetch all required IRM parameters
    base_rate_per_block = irm_contract.functions.BASE_RATE_PER_BLOCK().call()
    multiplier_per_block = irm_contract.functions.MULTIPLIER_PER_BLOCK().call()
    kink_1 = irm_contract.functions.KINK_1().call()
    multiplier_2_per_block = irm_contract.functions.MULTIPLIER_2_PER_BLOCK().call()
    kink_2 = irm_contract.functions.KINK_2().call()
    jump_multiplier_per_block = irm_contract.functions.JUMP_MULTIPLIER_PER_BLOCK().call()
    blocks_per_year = irm_contract.functions.BLOCKS_PER_YEAR().call()
    rate_1 = irm_contract.functions.RATE_1().call()
    rate_2 = irm_contract.functions.RATE_2().call()

    # --- Venus Two Kinks Model ---
    def SV(x):
        x_wei = int(x * 1e18)
        new_cash = cash + x_wei
        new_utilization = total_borrows / (new_cash + total_borrows) if (new_cash + total_borrows) > 0 else 0
        kink_1_decimal = abs(kink_1) / 1e18
        kink_2_decimal = abs(kink_2) / 1e18

        if new_utilization <= kink_1_decimal:
            utilization_scaled = int(new_utilization * 1e18)
            borrow_rate_per_block = base_rate_per_block + ((utilization_scaled * multiplier_per_block) // int(1e18))
        elif new_utilization <= kink_2_decimal:
            excess_util_scaled = int((new_utilization - kink_1_decimal) * 1e18)
            borrow_rate_per_block = rate_1 + ((excess_util_scaled * multiplier_2_per_block) // int(1e18))
        else:
            excess_util_scaled = int((new_utilization - kink_2_decimal) * 1e18)
            borrow_rate_per_block = rate_2 + ((excess_util_scaled * jump_multiplier_per_block) // int(1e18))

        r_b = (borrow_rate_per_block / 1e18) * blocks_per_year * 100
        reserve_factor_decimal = reserve_factor / 1e18
        r_s = r_b * new_utilization * (1 - reserve_factor_decimal)
        u_new = new_utilization * 100
        return r_s, r_b, u_new

    # Current utilization for reference
    current_utilization = (total_borrows / (total_borrows + cash)) * 100 if (total_borrows + cash) > 0 else 0
    print(f"vToken Address: {vtoken_addr}")
    print(f"Current Utilization: {current_utilization:.4f}%")

    print("Case:")
    r_s, r_b, u_new = SV(0)
    print(f"Current rates -> Supply APR: {r_s:.4f}%, Borrow APR: {r_b:.4f}%, Util: {u_new:.4f}%")

    # Test with supply amount
    r_s, r_b, u_new = SV(supply_amount)
    print(f"After supplying {supply_amount:,.0f} tokens -> Supply APR: {r_s:.4f}%, Borrow APR: {r_b:.4f}%, Util: {u_new:.4f}%")

# --- Example Usage ---
if __name__ == "__main__":
    token_address = "0x55d398326f99059fF775485246999027B3197955"  # USDT
    supply_amount = 10000
    calculate_venus_apr(token_address, supply_amount)
