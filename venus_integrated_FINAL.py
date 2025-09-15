import json
from web3 import Web3

class Venus:
    def __init__(self, VTOKEN_ADDRESS, PROVIDER_URL, ABI_PATH):
        self.web3 = Web3(Web3.HTTPProvider(PROVIDER_URL))
        self.vtoken_address = self.web3.to_checksum_address(VTOKEN_ADDRESS)
        self.abi_path = ABI_PATH

        with open(self.abi_path, 'r') as abi_file:
            self.vtoken_abi = json.load(abi_file)
        self.vtoken_contract = self.web3.eth.contract(address=self.vtoken_address, abi=self.vtoken_abi)

        # Remove self.irm_abi!
        self.irm_abi_path = r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_IRM_abi.json"
        self.switcher_abi = [
            {"inputs":[],"name":"DATA_SOURCE_1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
        ]

        self.params = self.get_params()  

    def get_params(self):
        cash = self.vtoken_contract.functions.getCash().call()
        total_borrows = self.vtoken_contract.functions.totalBorrows().call()
        total_reserves = self.vtoken_contract.functions.totalReserves().call()
        reserve_factor = self.vtoken_contract.functions.reserveFactorMantissa().call()

        # IRM contract detection
        irm_address = self.vtoken_contract.functions.interestRateModel().call()
        with open(self.irm_abi_path, 'r') as f:
            irm_abi = json.load(f)
        try:
            # Try switcher
            switcher_contract = self.web3.eth.contract(address=irm_address, abi=self.switcher_abi)
            data_source_1 = switcher_contract.functions.DATA_SOURCE_1().call()
            irm_contract = self.web3.eth.contract(address=data_source_1, abi=irm_abi)
        except Exception:
            # Direct IRM
            irm_contract = self.web3.eth.contract(address=irm_address, abi=irm_abi)

        # IRM params
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

        return {
            "cash": cash,
            "total_borrows": total_borrows,
            "total_reserves": total_reserves,
            "reserve_factor": reserve_factor,
            "base_rate_per_block": base_rate_per_block,
            "multiplier_per_block": multiplier_per_block,
            "kink_1": kink_1,
            "multiplier_2_per_block": multiplier_2_per_block,
            "base_rate_2_per_block": base_rate_2_per_block,
            "kink_2": kink_2,
            "jump_multiplier_per_block": jump_multiplier_per_block,
            "blocks_per_year": blocks_per_year,
            "rate_1": rate_1,
            "rate_2": rate_2
        }


    def get_supply_apr(self, x):
        p = self.params
        x_wei = int(x * 1e18)
        new_cash = p["cash"] + x_wei
        borrows = p["total_borrows"]
        reserve_factor = p["reserve_factor"] / 1e18
        blocks_per_year = p["blocks_per_year"]

        util = borrows / (new_cash + borrows) if (new_cash + borrows) else 0

        # Kinks as decimals
        k1 = abs(p["kink_1"]) / 1e18
        k2 = abs(p["kink_2"]) / 1e18

        # Borrow rate per block
        if util <= k1:
            util_scaled = int(util * 1e18)
            brpb = p["base_rate_per_block"] + ((util_scaled * p["multiplier_per_block"]) // 1e18)
        elif util <= k2:
            excess_util_scaled = int((util - k1) * 1e18)
            brpb = p["rate_1"] + ((excess_util_scaled * p["multiplier_2_per_block"]) // 1e18)
        else:
            excess_util_scaled = int((util - k2) * 1e18)
            brpb = p["rate_2"] + ((excess_util_scaled * p["jump_multiplier_per_block"]) // 1e18)

        # Annualize
        borrow_apy = (brpb / 1e18) * blocks_per_year * 100
        supply_apy = borrow_apy * util * (1 - reserve_factor)
        return supply_apy

    def get_borrow_apr(self, x):
        p = self.params
        x_wei = int(x * 1e18)
        new_cash = p["cash"] + x_wei
        borrows = p["total_borrows"]
        blocks_per_year = p["blocks_per_year"]

        util = borrows / (new_cash + borrows) if (new_cash + borrows) else 0

        # Kinks as decimals
        k1 = abs(p["kink_1"]) / 1e18
        k2 = abs(p["kink_2"]) / 1e18

        # Borrow rate per block
        if util <= k1:
            util_scaled = int(util * 1e18)
            brpb = p["base_rate_per_block"] + ((util_scaled * p["multiplier_per_block"]) // 1e18)
        elif util <= k2:
            excess_util_scaled = int((util - k1) * 1e18)
            brpb = p["rate_1"] + ((excess_util_scaled * p["multiplier_2_per_block"]) // 1e18)
        else:
            excess_util_scaled = int((util - k2) * 1e18)
            brpb = p["rate_2"] + ((excess_util_scaled * p["jump_multiplier_per_block"]) // 1e18)

        borrow_apy = (brpb / 1e18) * blocks_per_year * 100
        return borrow_apy

    def get_utilization(self, x):
        p = self.params
        x_wei = int(x * 1e18)
        new_cash = p["cash"] + x_wei
        borrows = p["total_borrows"]
        return borrows / (new_cash + borrows) * 100 if (new_cash + borrows) else 0




#=======================================================================


# usage:
if __name__ == "__main__":
    # USDT
    venus_usdt = Venus(
        VTOKEN_ADDRESS="0xfD5840Cd36d94D7229439859C0112a4185BC0255",
        PROVIDER_URL="https://bsc-dataseed.bnbchain.org/",
        ABI_PATH=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_abi.json"
    )
    print("USDT supply APR current :", venus_usdt.get_supply_apr(0))
    print("USDT borrow APR current :", venus_usdt.get_borrow_apr(0))
    print("USDT utilization current:", venus_usdt.get_utilization(0))
    print('\n')

    # BNB
    venus_bnb = Venus(
        VTOKEN_ADDRESS="0xA07c5b74C9B40447a954e1466938b865b6BBea36",
        PROVIDER_URL="https://bsc-dataseed.bnbchain.org/",
        ABI_PATH=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_abi.json"
    )
    print("BNB supply APR current :", venus_bnb.get_supply_apr(0))
    print("BNB borrow current :", venus_bnb.get_borrow_apr(0))
    print("BNB utilization current :", venus_bnb.get_utilization(0))

    print('\n')

    # USDC
    venus_usdc = Venus(
        VTOKEN_ADDRESS="0xecA88125a5ADbe82614ffC12D0DB554E2e2867C8",
        PROVIDER_URL="https://bsc-dataseed.bnbchain.org/",
        ABI_PATH=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_abi.json"
    )
    print("USDT supply APR current :", venus_usdc.get_supply_apr(0))
    print("USDT borrow APR current :", venus_usdc.get_borrow_apr(0))
    print("USDT utilization current:", venus_usdc.get_utilization(0))
    print('\n')
