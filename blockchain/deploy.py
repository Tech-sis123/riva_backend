import json
import os
from solcx import compile_standard, install_solc
from web3 import Web3

from config import get_settings

settings = get_settings()

BASE_DIR = os.path.dirname(__file__)  #backend/blockchain
CONTRACT_PATH = os.path.join(BASE_DIR, "contracts", "ContentRegistry.sol")

print("DATABASE_URL:", settings.DATABASE_URL)
print("SECRET_KEY:", settings.SECRET_KEY)
print("DEPLOYER_PRIVATE_KEY:", settings.DEPLOYER_PRIVATE_KEY)

RPC_URL = settings.RPC_URL
CHAIN_ID = settings.CHAIN_ID
DEPLOYER_PRIVATE_KEY = settings.DEPLOYER_PRIVATE_KEY

w3 = Web3(Web3.HTTPProvider(RPC_URL))

account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)
DEPLOYER_ADDRESS = account.address

install_solc("0.8.20")
with open(CONTRACT_PATH, "r") as file:
    source_code = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"ContentRegistry.sol": {"content": source_code}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}},
    },
    solc_version="0.8.20",
)

abi = compiled_sol["contracts"]["ContentRegistry.sol"]["ContentRegistry"]["abi"]
bytecode = compiled_sol["contracts"]["ContentRegistry.sol"]["ContentRegistry"]["evm"]["bytecode"]["object"]

with open("compiled.json", "w") as f:
    json.dump(compiled_sol, f)


ContentRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(DEPLOYER_ADDRESS)

tx = ContentRegistry.constructor().build_transaction({
    "from": DEPLOYER_ADDRESS,
    "nonce": nonce,
    "gas": 3000000,
    "gasPrice": w3.to_wei("30", "gwei"),
    "chainId": CHAIN_ID
})

signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("Contract deployed at:", receipt.contractAddress)

with open("contract_data.json", "w") as f:
    json.dump({"abi": abi, "address": receipt.contractAddress}, f)
