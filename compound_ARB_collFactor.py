# --------------------------- for USDC --------------------------------------

from web3 import Web3
import json

# Connect to Arbitrum
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Load Comet ABI (the ABI you posted)
with open("compound_comet_abi.json") as f:
    abi = json.load(f)

# Compound v3 USDC market contract address (Arbitrum)
comet_address = "0xAA190353CbAFa4B9f74e57276caCFb372dc8b118"
comet = web3.eth.contract(address=comet_address, abi=abi)

# ARB token address (native ARB on Arbitrum)
arb_token_address = "0x912CE59144191C1204E64559FE8253a0e49E6548" # use token contract address -> This was the problem

asset_info = comet.functions.getAssetInfoByAddress(arb_token_address).call()

print(asset_info)

coll_factor = asset_info[-4]/1e18
liq_factor = asset_info[-3]/1e18

print(f"For arb - ",coll_factor, liq_factor)



# --------------------------- for USDT ------------------------




from web3 import Web3
import json

# Connect to Arbitrum
rpc_url = "https://arb-mainnet.g.alchemy.com/v2/A74JBIQ7lj4_GjTzHMSwN8wTacre_Lq0"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Load Comet ABI (same as before)
with open("compound_usdc_abi.json") as f:
    abi = json.load(f)

# Replace this with the actual USDT market contract address for Compound v3 on Arbitrum
usdt_comet_address = "0x8D9f0d8B7C7C8375E13c1ff5D0973B5826069167"
comet = web3.eth.contract(address=usdt_comet_address, abi=abi)

# ARB token address
arb_token_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"

# Fetch asset info
asset_info = comet.functions.getAssetInfoByAddress(arb_token_address).call()

print(asset_info)

coll_factor = asset_info[-4] / 1e18
liq_factor = asset_info[-3] / 1e18

print(f"For ARB as collateral in USDT market - Collateral Factor: {coll_factor}, Liquidation Factor: {liq_factor}")



