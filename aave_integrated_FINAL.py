import json
from web3 import Web3

class Aave:
    def __init__(self, token_address, atoken_address, provider_url, 
                 supply_abi_path, reserve_abi_path, strategy_abi_path, decimals=18):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.token_address = self.web3.to_checksum_address(token_address)
        self.atoken_address = self.web3.to_checksum_address(atoken_address)
        self.decimals = decimals

        # Load ABIs
        with open(supply_abi_path) as f:
            self.supply_abi = json.load(f)
        with open(reserve_abi_path) as f:
            self.reserve_abi = json.load(f)
        with open(strategy_abi_path) as f:
            self.strategy_abi = json.load(f)

        # Initialize contracts
        self.atoken_contract = self.web3.eth.contract(
            address=self.atoken_address, 
            abi=self.supply_abi
        )
        self.data_provider = self.web3.eth.contract(
            address=self.web3.to_checksum_address("0x1e26247502e90b4fab9D0d17e4775e90085D2A35"),
            abi=self.reserve_abi
        )
        
        # Initialize parameters
        self._refresh_params()

    def _refresh_params(self):
        """Refresh current market parameters from blockchain"""
        # Get total supply and reserve factor
        self.total_supply = self.atoken_contract.functions.totalSupply().call() / 10**self.decimals
        config = self.data_provider.functions.getReserveConfigurationData(self.token_address).call()
        self.reserve_factor = config[4] / 1e4  # Convert basis points to decimal
        
        # Get interest rate strategy parameters
        strategy_address = self.data_provider.functions.getInterestRateStrategyAddress(self.token_address).call()
        strategy_contract = self.web3.eth.contract(
            address=strategy_address,
            abi=self.strategy_abi
        )
        
        self.RAY = 1e27
        self.base_rate = strategy_contract.functions.getBaseVariableBorrowRate(self.token_address).call() / self.RAY
        self.slope1 = strategy_contract.functions.getVariableRateSlope1(self.token_address).call() / self.RAY
        self.slope2 = strategy_contract.functions.getVariableRateSlope2(self.token_address).call() / self.RAY
        self.opt_util = strategy_contract.functions.getOptimalUsageRatio(self.token_address).call() / self.RAY
        
        # Get current borrow data
        reserve_data = self.data_provider.functions.getReserveData(self.token_address).call()
        self.total_borrow = (reserve_data[3] + reserve_data[4]) / 10**self.decimals  # Stable + Variable

    def get_supply_apr(self, x):
        """Calculate supply APR after depositing x tokens"""
        self._refresh_params()  # Update parameters
        
        # Convert inputs to proper units
        c_a = self.total_borrow * 10**self.decimals  # Current borrows in wei
        d_a = self.total_supply * 10**self.decimals  # Current supply in wei
        x_scaled = x * 10**self.decimals  # Deposit amount in wei
        
        # Calculate new utilization
        new_supply = d_a + x_scaled
        utilization = c_a / new_supply if new_supply > 0 else 0
        
        # Calculate borrow rate
        if utilization <= self.opt_util:
            borrow_rate = self.base_rate + (self.slope1 * utilization / self.opt_util)
        else:
            borrow_rate = self.base_rate + self.slope1 + ((utilization - self.opt_util) / (1 - self.opt_util)) * self.slope2
        
        # Calculate supply rate
        supply_rate = borrow_rate * utilization * (1 - self.reserve_factor)
        
        return {
            'utilization': utilization * 100,  # as percentage
            'borrow_apr': borrow_rate * 100,   # as percentage
            'supply_apr': supply_rate * 100    # as percentage
        }

    def print_current_state(self):
        """Print current market state"""
        current = self.get_supply_apr(0)
        print("\nCurrent Aave Market State:")
        print(f"Total Supply: {self.total_supply:,.2f} USDC")
        print(f"Total Borrow: {self.total_borrow:,.2f} USDC")
        print(f"Utilization: {current['utilization']:.2f}%")
        print(f"Borrow APR: {current['borrow_apr']:.2f}%")
        print(f"Supply APR: {current['supply_apr']:.2f}%")

# Example usage
if __name__ == "__main__":
    aave = Aave(
        token_address="0x55d398326f99059fF775485246999027B3197955",  # USDT (BNB Chain)
        atoken_address="0xa9251ca9DE909CB71783723713B21E4233fbf1B1", # aUSDT (BNB Chain)
        provider_url="https://bsc-dataseed.bnbchain.org/",
        supply_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_supply_abi.json",
        reserve_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_reserve_factor_abi.json",
        strategy_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_irm_strategy_abi.json",
        decimals=18
    )
    
    # Get current state
    aave.print_current_state()
    
    # Simulate deposit
    deposit_amount = 100_000  # 100k USDC
    scenario = aave.get_supply_apr(deposit_amount)
    print(f"\nAfter depositing {deposit_amount:,} USDC:")
    print(f"New Utilization: {scenario['utilization']:.2f}%")
    print(f"New Borrow APR: {scenario['borrow_apr']:.2f}%")
    print(f"New Supply APR: {scenario['supply_apr']:.2f}%")
