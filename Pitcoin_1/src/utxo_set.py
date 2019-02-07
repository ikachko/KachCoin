# TODO: Implement for saving and accessing unspent transactions

import base58

from globals import UTXO_POOL_FILE
from colored_print import *
from tx import raw_deserialize

class Utxo:
    def __init__(self):
        pass

    @staticmethod
    def add_txs_to_utxo(transactions):
        try:
            f = open(UTXO_POOL_FILE, 'a+')
            for tx in transactions:
                f.write(tx + '\n')
            f.close()
        except Exception as e:
            prRed("add_block_tx_to_utxo:")
            prRed(e)

    @staticmethod
    def get_txs_from_utxo():
        txs = None
        try:
            f = open(UTXO_POOL_FILE, 'r')
            txs = f.readlines()
            f.close()
            txs = [tx[:-1] for tx in txs]
        except Exception as e:
            prRed("get_txs_from_utxo:")
            prRed(e)
        return txs

    @staticmethod
    def get_utxo_of_addr(addr):
        txs = Utxo.get_txs_from_utxo()
        hashed_pubkey = base58.b58decode_check(addr)[1:].hex()
        if not txs:
            prRed("Something wrong with utxo pool or it is empty")
        else:
            utxo = []
            deserialized_txs = [raw_deserialize(tx) for tx in txs]
            for tx in deserialized_txs:
                for out in tx['outputs']:
                    if out['pk_script'][6:-4] == hashed_pubkey:
                        utxo.append(tx)
            return utxo
        return None

    @staticmethod
    def remove_tx_from_utxo(txid):
        txs = Utxo.get_txs_from_utxo()
        if not txs:
            prRed("Something wrong with utxo pool or it is empty")
        else:
            deserialized_txs = [raw_deserialize(tx) for tx in txs]
            i = 0
            while i < len(deserialized_txs):
                if deserialized_txs[i]['txid'] == txid:
                    txs.remove(txs[i])
                    break
            f = open(UTXO_POOL_FILE, 'w')
            f.writelines(txs)
            f.close()

    @staticmethod
    def get_inputs(addr, value):
        sum = 0
        txs = Utxo.get_txs_from_utxo()
        inputs = []

        min_diff = 12345678
        for tx in txs:
            if tx['output```````']



import wallet
miner_addr = '5KWkjDCpMQYasUykLvKpCuZXThd9VQHunRitAA1U8iXQtwohc2H'

print('miner addr from waller: ', miner_addr)
addr = '5KWkjDCpMQYasUykLvKpCuZXThd9VQHunRitAA1U8iXQtwohc2H'
hashed_key = 'df95714eeeabaf42dd0338d4ff694b87d4697b1ce8bbc7294bbddd980e7bdc83'
print('original addr: ', addr)
print('original hashed_key: ', hashed_key)
print(Utxo.get_utxo_of_addr(miner_addr))

