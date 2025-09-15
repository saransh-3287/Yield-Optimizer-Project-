import json
from web3 import Web3

class Euler:
    def __init__(self, vault_address, provider_url, irm_abi_path, supply_abi_path):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Load ABIs
        with open(irm_abi_path) as f:
            irm_abi = json.load(f)
        with open(supply_abi_path) as f:
            supply_abi = json.load(f)
            
        # Initialize contracts
        self.vault_address = self.web3.to_checksum_address(vault_address)
        self.supply_contract = self.web3.eth.contract(
            address=self.vault_address,
            abi=supply_abi
        )
        irm_address = self.supply_contract.functions.interestRateModel().call()
        self.irm_contract = self.web3.eth.contract(
            address=irm_address,
            abi=irm_abi
        )
        
        # Initialize parameters
        self._refresh_params()

    def _refresh_params(self):
        """Refresh current market parameters from blockchain"""
        # IRM parameters
        self.base_rate = self.irm_contract.functions.baseRate().call()
        self.kink = self.irm_contract.functions.kink().call() / 4294967295  # Convert Q32.32 to decimal
        self.slope1 = self.irm_contract.functions.slope1().call()
        self.slope2 = self.irm_contract.functions.slope2().call()
        
        # Market state
        self.total_borrows = self.supply_contract.functions.totalBorrows().call() / 1e18
        self.cash = self.supply_contract.functions.cash().call() / 1e18
        self.reserve_factor = self.supply_contract.functions.interestFee().call() / 1e4

    def get_supply_apr(self, x):
        """Calculate supply APR after depositing x USDT"""
        self._refresh_params()
        
        # Calculate utilization
        new_cash = self.cash + x
        total_liquidity = self.total_borrows + new_cash
        utilization = self.total_borrows / total_liquidity if total_liquidity > 0 else 0
        
        # Euler-specific rate calculation (convert rates from contract's fixed-point format)
        if utilization <= self.kink:
            borrow_rate = self.base_rate + (self.slope1 * 0.095 / 743995130) * (utilization / self.kink)
        else:
            excess_util = utilization - self.kink
            borrow_rate = self.base_rate + (self.slope1 * 0.095 / 743995130) + \
                          (self.slope2 * 1.105 / 51477290240) * (excess_util / (1 - self.kink))
        
        # Calculate supply rate
        supply_rate = borrow_rate * utilization * (1 - self.reserve_factor)
        
        return {
            'utilization': utilization * 100,
            'borrow_apr': borrow_rate * 100,
            'supply_apr': supply_rate * 100
        }

    def print_current_state(self):
        """Print current market state"""
        current = self.get_supply_apr(0)
        print("\nCurrent Euler Market State:")
        print(f"Total Borrows: {self.total_borrows:,.2f} USDT")
        print(f"Available Cash: {self.cash:,.2f} USDT")
        print(f"Utilization: {current['utilization']:.2f}%")
        print(f"Borrow APR: {current['borrow_apr']:.2f}%")
        print(f"Supply APR: {current['supply_apr']:.2f}%")

