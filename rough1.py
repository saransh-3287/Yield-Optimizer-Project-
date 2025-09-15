from web3 import Web3

# Connect to BNB Chain mainnet
web3 = Web3(Web3.HTTPProvider('https://bsc-dataseed.binance.org/'))

# PoolRegistry contract address and ABI snippet for getVTokenForAsset
pool_registry_address = '0x9F7b01A536aFA00EF10310A162877fd792cD0666'
pool_registry_abi = [
    {
        "inputs": [
            {"internalType": "address", "name": "comptroller", "type": "address"},
            {"internalType": "address", "name": "asset", "type": "address"}
        ],
        "name": "getVTokenForAsset",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Instantiate contract
pool_registry = web3.eth.contract(address=pool_registry_address, abi=pool_registry_abi)

# Known Comptroller and USDT addresses for BNB Chain Mainnet Core Pool
comptroller_address = '0xfD36E2c2a6789Db23113685031d7F16329158384'
usdt_address = '0x55d398326f99059fF775485246999027B3197955'

# Call getVTokenForAsset
vtoken_address = pool_registry.functions.getVTokenForAsset(comptroller_address, usdt_address).call()

print("vUSDT address:", vtoken_address)
