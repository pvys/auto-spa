from web3 import Web3
import web3

from consts import *

import datetime
import time
import os


w3 = Web3(Web3.HTTPProvider("https://rpc.ftm.tools/"))

dai_contract = w3.eth.contract(
    address=dai_bond_depository_address, abi=dai_bond_depository_abi
)
lp_contract = w3.eth.contract(
    address=lp_bond_depository_address, abi=lp_bond_depository_abi
)
staking_contract = w3.eth.contract(
    address=spartacus_staking_address, abi=spartacus_staking_abi
)


my_addr = os.environ["MM_ADDR"].strip()
key = os.environ["MM_KEY"].strip()


def get_current_and_last_block():
    current_block = w3.eth.blockNumber

    epoch = staking_contract.functions.epoch().call()
    end_block = epoch[2]

    return current_block, end_block


def redeem(contract, nonce, stake=True):
    error = ValueError("error")

    for _ in range(3):
        try:
            balance = contract.functions.redeem(my_addr, False).call()
            if not balance:
                return None, None

            transaction = {
                "from": my_addr,
                "nonce": nonce,
                "gas": contract.functions.redeem(my_addr, stake).estimateGas(),
                "gasPrice": w3.eth.gas_price,
            }

            tx = contract.functions.redeem(my_addr, stake).buildTransaction(transaction)
            signed_tx = w3.eth.account.sign_transaction(tx, key)
            return tx, w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        except web3.exceptions.ContractLogicError as e:
            if "SafeMath" in str(e):
                return None, None

            print(contract.address, str(e))
            error = e
        except Exception as e:
            print("retry", str(e))
            error = e

    raise error


def run():

    last_block = 0
    while True:
        time.sleep(2)
        cur_block, end_block = get_current_and_last_block()
        if end_block - cur_block < 160 and cur_block > last_block + 3000:
            last_block = cur_block

            nonce = w3.eth.get_transaction_count(my_addr)
            tx, tx_hash = redeem(dai_contract, nonce)
            if tx_hash is not None:
                w3.eth.wait_for_transaction_receipt(tx_hash)
                print(
                    str(datetime.datetime.now()) + "DAI==============================="
                )
                print(tx)
                print(tx_hash)
                print("============================================================")
                print("\n")

            nonce = w3.eth.get_transaction_count(my_addr)
            tx, tx_hash = redeem(lp_contract, nonce)
            if tx_hash is not None:
                w3.eth.wait_for_transaction_receipt(tx_hash)
                print(
                    str(datetime.datetime.now()) + "LP================================"
                )
                print(tx)
                print(tx_hash)
                print("============================================================")
                print("\n")


if __name__ == "__main__":
    run()
