# TODO: Implement for saving and accessing unspent transactions

import base58

from globals import UTXO_POOL_FILE
from colored_print import *
from tx import raw_deserialize

class Utxo:
    def __init__(self):
        pass

    @staticmethod
    def serialize_utxo(utxo_dict):
        pass

    @staticmethod
    def deserialize_utxo(utxo):
        pass

    @staticmethod
    def extract_outputs_from_tx(tx):
        try:
            dict_tx = raw_deserialize(tx)
            utxos = []

            for out in dict_tx['outputs']:
                to_out = out
                to_out['txid'] = dict_tx['txid']
                utxos.append(to_out)
            return utxos
        except Exception as e:
            prRed("extract_output_from_tx:")
            prRed(e)

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
    def get_txs_from_utxo_file():
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
        try:
            txs = Utxo.get_txs_from_utxo_file()
            hashed_pubkey = base58.b58decode_check(addr)[1:].hex()
            if not txs:
                prRed("Something wrong with utxo pool or it is empty")
            else:
                utxo = []
                deserialized_txs = [raw_deserialize(tx) for tx in txs]
                for i in range(len(deserialized_txs)):
                    for out in deserialized_txs[i]['outputs']:
                        if out['pk_script'][6:-4] == hashed_pubkey:
                            to_out = out
                            to_out['txid'] = deserialized_txs[i]['txid']
                            utxo.append(to_out)
                return utxo
            return None
        except Exception as e:
            prRed("get_utxo_of_addr:")
            prRed(e)
            return None

    @staticmethod
    def remove_tx_from_utxo(txid):
        try:
            txs = Utxo.get_txs_from_utxo_file()
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
        except Exception as e:
            prRed("remove_tx_from_utxo:")
            prRed(e)

    @staticmethod
    def check_balance_of_addr(addr):
        balance = 0
        outputs = Utxo.get_utxo_of_addr(addr)
        if outputs:
            for out in outputs:
                balance += out['value']
            return balance
        else:
            prRed("No utxo of addr")
            return None

    @staticmethod
    def get_inputs(addr, value):

        outputs = Utxo.get_utxo_of_addr(addr)

        if outputs == [] or not outputs:
            prRed(addr + " has no/not enough unspent outputs!")
            return

        inputs = []
        while outputs is not []:
            min_diff = 1234567890987654321
            for out in outputs:
                if abs(value - out['value']) <= min_diff:
                    best = out
                    min_diff = abs(value - out['value'])
            inputs.append(best)
            current_sum = 0

            for i in inputs:
                current_sum += i['value']

            if current_sum >= value:
                return inputs
            else:
                outputs.remove(best)
        if not inputs:
            prRed("Error: get_inputs:")
            prRed(addr + " has no/not enough unspent outputs!")
        sum = 0
        for i in inputs:
            sum += i['value']
        if sum < value:
            prRed("Error: get_inputs:")
            prRed(addr + " has no/not enough unspent outputs!")


import wallet
miner_addr = '5KWkjDCpMQYasUykLvKpCuZXThd9VQHunRitAA1U8iXQtwohc2H'

# print('miner addr from wallet: ', miner_addr)
addr = '5KWkjDCpMQYasUykLvKpCuZXThd9VQHunRitAA1U8iXQtwohc2H'
hashed_key = 'df95714eeeabaf42dd0338d4ff694b87d4697b1ce8bbc7294bbddd980e7bdc83'
# print(Utxo.get_inputs(miner_addr, 50))

from wallet import *
uncompressed_pbk = Wallet.private_to_public('a8abac3ca5a30557b92752251cedf86119fb99b7d60620afaf95ec72eefdb4de')
print(uncompressed_pbk)
compressed_pbk = Wallet.compressed_publkey_from_publkey(uncompressed_pbk)
print(compressed_pbk)
uncompressed_again = Wallet.uncompress_publkey(compressed_pbk)
print(uncompressed_again)