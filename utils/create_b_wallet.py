from web3 import Web3, Account
import secrets

def create_b_wallet():
    account = Account.create(secrets.token_hex(32))
    wallet_address = account.address
    private_key = account._private_key.hex()

    return wallet_address, private_key