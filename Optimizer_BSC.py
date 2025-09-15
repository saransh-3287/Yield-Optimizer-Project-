import json
from web3 import Web3


# Class Venus ------------------------------------------------------------
#-----------------------------------------------------------------------

class Venus:
    def __init__(self, VTOKEN_ADDRESS, PROVIDER_URL, ABI_PATH):
        self.web3 = Web3(Web3.HTTPProvider(PROVIDER_URL))
        self.vtoken_address = self.web3.to_checksum_address(VTOKEN_ADDRESS)
        self.abi_path = ABI_PATH

        with open(self.abi_path, 'r') as abi_file:
            self.vtoken_abi = json.load(abi_file)
        self.vtoken_contract = self.web3.eth.contract(address=self.vtoken_address, abi=self.vtoken_abi)

        self.irm_abi = [
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
        self.switcher_abi = [
            {"inputs":[],"name":"DATA_SOURCE_1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
        ]

        self.params = self.get_params() 

    def get_params(self):
        cash = self.vtoken_contract.functions.getCash().call()
        total_borrows = self.vtoken_contract.functions.totalBorrows().call()
        total_reserves = self.vtoken_contract.functions.totalReserves().call()
        reserve_factor = self.vtoken_contract.functions.reserveFactorMantissa().call()

        
        irm_address = self.vtoken_contract.functions.interestRateModel().call()
        try:
            
            switcher_contract = self.web3.eth.contract(address=irm_address, abi=self.switcher_abi)
            data_source_1 = switcher_contract.functions.DATA_SOURCE_1().call()
            irm_contract = self.web3.eth.contract(address=data_source_1, abi=self.irm_abi)
        except Exception:
            
            irm_contract = self.web3.eth.contract(address=irm_address, abi=self.irm_abi)

        # IRM parameters
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

        # calculating utilization
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

        # Annualizing rates
        borrow_apy = (brpb / 1e18) * blocks_per_year * 100
        supply_apy = borrow_apy * util * (1 - reserve_factor)
        return {
            'supply_apr': supply_apy,
            'borrow_apr': borrow_apy,
            'utilization': util * 100
        }

#--------------------------------------------------------------------------------
# AAVE class now ----------------------------------------------------------------------

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
        
        
        self._refresh_params()

    def _refresh_params(self):
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

        self._refresh_params()  
        
        # Convert inputs to proper units
        c_a = self.total_borrow * 10**self.decimals 
        d_a = self.total_supply * 10**self.decimals  
        x_scaled = x * 10**self.decimals  
        
        new_supply = d_a + x_scaled
        utilization = c_a / new_supply if new_supply > 0 else 0
        
        if utilization <= self.opt_util:
            borrow_rate = self.base_rate + (self.slope1 * utilization / self.opt_util)
        else:
            borrow_rate = self.base_rate + self.slope1 + ((utilization - self.opt_util) / (1 - self.opt_util)) * self.slope2
        
        supply_rate = borrow_rate * utilization * (1 - self.reserve_factor)
        
        return {
            'supply_apr': supply_rate*100,
            'borrow_apr': borrow_rate*100,
            'utilization': utilization
        }

#----------------------------------------------------------------------------
# Kinza class now ----------------------------------------------------------------

import json
from web3 import Web3

class Kinza:
    def __init__(self, token_address, provider_url, pool_abi_path, irm_abi_path):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.token_address = self.web3.to_checksum_address(token_address)
        self.pool_address = self.web3.to_checksum_address("0x09Ddc4AE826601b0F9671b9edffDf75e7E6f5D61")

        # Load ABIs
        with open(pool_abi_path) as f:
            self.pool_abi = json.load(f)
        with open(irm_abi_path) as f:
            self.irm_abi = json.load(f)

        # Initialize contracts
        self.pool_contract = self.web3.eth.contract(
            address=self.pool_address,
            abi=self.pool_abi
        )
        self._refresh_params()

    def _refresh_params(self):

        # Get IRM contract
        irm_address = self.pool_contract.functions.getInterestRateStrategyAddress(self.token_address).call()
        self.irm_contract = self.web3.eth.contract(
            address=irm_address,
            abi=self.irm_abi
        )

        # Get rate parameters
        self.base_rate = self.irm_contract.functions.getBaseVariableBorrowRate().call() / 1e27
        self.slope1 = self.irm_contract.functions.getVariableRateSlope1().call() / 1e27
        self.slope2 = self.irm_contract.functions.getVariableRateSlope2().call() / 1e27
        self.kink = self.irm_contract.functions.OPTIMAL_USAGE_RATIO().call() / 1e27

        # Get market state
        self.total_debt = self.pool_contract.functions.getTotalDebt(self.token_address).call() / 1e18
        self.total_supply = self.pool_contract.functions.getATokenTotalSupply(self.token_address).call() / 1e18
        reserve_config = self.pool_contract.functions.getReserveConfigurationData(self.token_address).call()
        self.reserve_factor = reserve_config[4] / 1e4

    def get_supply_apr(self, x):
        self._refresh_params()
        
        new_supply = self.total_supply + x
        utilization = self.total_debt / new_supply if new_supply > 0 else 0
        utilization = min(utilization, 1.0)  

        # Calculate borrow rate
        if utilization <= self.kink:
            borrow_rate = self.base_rate + (self.slope1 * utilization / self.kink)
        else:
            borrow_rate = self.base_rate + self.slope1 + (self.slope2 * (utilization - self.kink) / (1 - self.kink))

        # Calculate supply rate
        supply_rate = borrow_rate * utilization * (1 - self.reserve_factor)
        
        return {
            'supply_apr': supply_rate*100,
            'borrow_apr': borrow_rate*100,
            'utilization': utilization
        }

#----------------------------------------------------------------------------------
#-------Euler class Now------------------------------------------------------------------

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
        
        self._refresh_params()

    def _refresh_params(self):
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
        self._refresh_params()
        
        new_cash = self.cash + x
        total_liquidity = self.total_borrows + new_cash
        utilization = self.total_borrows / total_liquidity if total_liquidity > 0 else 0
        
        if utilization <= self.kink:
            borrow_rate = self.base_rate + (self.slope1 * 0.095 / 743995130) * (utilization / self.kink)
        else:
            excess_util = utilization - self.kink
            borrow_rate = self.base_rate + (self.slope1 * 0.095 / 743995130) + \
                          (self.slope2 * 1.105 / 51477290240) * (excess_util / (1 - self.kink))
        
        supply_rate = borrow_rate * utilization * (1 - self.reserve_factor)
        
        return {
            'supply_apr': supply_rate*100,
            'borrow_apr': borrow_rate*100,
            'utilization': utilization
        }


#-------------------------------------------------------------------------------




#-------------------------------------------------------------


# ====================== OPTIMIZATION ========================
import numpy as np
from scipy.optimize import minimize

def objective(vars, T, protocols):
    x, y, z = vars
    k = T - x - y - z
    
    try:
        return -(
            x * protocols[0].get_supply_apr(x)['supply_apr']/100 +
            y * protocols[1].get_supply_apr(y)['supply_apr']/100 +
            z * protocols[2].get_supply_apr(z)['supply_apr']/100 +
            k * protocols[3].get_supply_apr(k)['supply_apr']/100
        )
    except Exception as e:
        print(f"Error in objective calculation: {str(e)}")
        return 1e12

def optimize_allocations(T, protocols):
    # Get initial APRs to bias initial guess
    initial_aprs = [proto.get_supply_apr(0)['supply_apr'] for proto in protocols]
    main_idx = np.argmax(initial_aprs)
    
    # Initialize biased towards highest APR protocol
    x0 = [0.0]*3
    if main_idx < 3:  # First 3 protocols in variables
        x0[main_idx] = T * 0.9

    bounds = [(0, T) for _ in range(3)]
    constraints = {'type': 'ineq', 'fun': lambda x: T - sum(x)}
    
    result = minimize(
        objective,
        x0=x0,
        args=(T, protocols),
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

# ====================== MAIN EXECUTION ========================
if __name__ == "__main__":
    T = 1e8 
    
    # Initialization part---------------------------------------------------------- 

    # 1. Venus USDT
    venus = Venus(
        VTOKEN_ADDRESS="0xfD5840Cd36d94D7229439859C0112a4185BC0255",
        PROVIDER_URL="https://bsc-dataseed.bnbchain.org/",
        ABI_PATH=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\venus_abi.json"
    )

    # 2. Aave USDT
    aave = Aave(
        token_address="0x55d398326f99059fF775485246999027B3197955",  # USDT (BNB Chain)
        atoken_address="0xa9251ca9DE909CB71783723713B21E4233fbf1B1", # aUSDT (BNB Chain)
        provider_url="https://bsc-dataseed.bnbchain.org/",
        supply_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_supply_abi.json",
        reserve_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_reserve_factor_abi.json",
        strategy_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\aave_irm_strategy_abi.json",
        decimals=18
    )

    # 3. Kinza USDT
    kinza = Kinza(
        token_address="0x55d398326f99059fF775485246999027B3197955",
        provider_url="https://bsc-dataseed.bnbchain.org/",
        pool_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\kinza_abi.json",
        irm_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\kinza_IRM_abi.json"
    )

    # 4. Euler USDT
    euler = Euler(
        vault_address="0xca522ECab584b5430ADb946edEE4224A63628362",
        provider_url="https://bsc-dataseed.bnbchain.org/",
        irm_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\euler_usdt_abi.json",
        supply_abi_path=r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\euler_usdt_supply_abi.json"
    )
    protocols = [venus, aave, kinza, euler]

    try:
        result = optimize_allocations(T, protocols)
        print("\nOptimal Allocations:")
        for name, alloc in zip(["Venus", "Aave", "Kinza", "Euler"], result['allocations']):
            print(f"{name}: {alloc:,.2f} USDT ({alloc/T:.1%})")
        print(f"\nProjected APR: {result['total_apr']:.2%}")
        
        # Verification
        print("\nFull Allocation APRs:")
        for proto, name in zip(protocols, ["Venus", "Aave", "Kinza", "Euler"]):
            full_apr = proto.get_supply_apr(T)['supply_apr']
            print(f"{name}: {full_apr:.2f}%")
            
    except Exception as e:
        print(f"\nOptimization error: {str(e)}")
