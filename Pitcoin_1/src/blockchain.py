import re
import requests
import json

from time import gmtime, strftime

from pending_pool import PendingPool
from transaction import CoinbaseTransaction
from block import Block
from serializer import Serializer
from wallet import Wallet
from colored_print import *
from utxo_set import Utxo

from tx import SwCoinbaseTransaction, SwRawTransaction

from utils import clamp

from globals import (
    PENDING_POOL_FILE,
    BLOCKS_LENGTH_FILE,
    BLOCKS_DIRECTORY,
    MINER_PRIVKEY_FILE,
    MINER_NODES,
    NETWORKS,
    DIFFICULTY_FILE
)

# TODO: Remove global variables and store all in files

class Blockchain:
    def __init__(self):
        self.complexity = 2
        self.chain = Blockchain.recover_blockchain_from_fileblock()
        self.nodes = Blockchain.recover_nodes_from_file()
        self.tx_pool = PendingPool()
        self.target = 0x000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
        self.coinbase = 50000000
        if not self.chain:
            self.chain = [self.genesis_block()]

    @staticmethod
    def get_chain():
        chain = Blockchain.recover_blockchain_from_fileblock()
        return chain

    @staticmethod
    def get_pool_of_transactions():
        try:
            f = open(PENDING_POOL_FILE, 'r')
            tx = f.readline()
            txs = []
            while True:
                txs.append(tx[:-1])
                tx = f.readline()
                if not tx:
                    break
            f.close()
            return txs
        except Exception as e:
            prRed(e)

    @staticmethod
    def get_transactions_to_block():
        try:
            f = open(PENDING_POOL_FILE, 'r')
            tx = f.readline()
            txs = []
            while True:
                txs.append(tx[:-1])
                tx = f.readline()
                if not tx:
                    break
            f.close()
            to_block = txs[:3]
            f = open(PENDING_POOL_FILE, 'w')
            to_write = txs[3:]
            for tx in to_write:
                f.write(tx)
            f.close()
            # print(to_block)
            return to_block
        except Exception as e:
            prRed(e)

    @staticmethod
    def recover_chain_length_from_file():
        try:
            f = open(BLOCKS_LENGTH_FILE, 'r')
            length = int(f.read())
            f.close()
            return length
        except Exception as e:
            prRed(e)

    @staticmethod
    def recover_blockchain_from_fileblock():
        idx = 0
        recovered_chain = []
        while True:
            try:
                f = open(BLOCKS_DIRECTORY + ('%08i' % idx) + '.block', 'r')
                block = json.load(f)
                block_dict = dict(block)
                recovered_block = Block(
                    bits=block_dict['bits'],
                    timestamp=block_dict['timestamp'],
                    previous_hash=block_dict['previous_hash'],
                    transactions=list(block_dict['transactions']),
                    nonce=block_dict['nonce'])
                recovered_chain.append(recovered_block)
            except FileNotFoundError:
                break
            idx += 1
        return recovered_chain

    @staticmethod
    def recover_nodes_from_file():
        nodes = []
        try:
            f = open(MINER_NODES, 'r')
            node = f.readline()[:-1]
            while node:
                if Blockchain.validate_node(node):
                    nodes.append(node)
                node = f.readline()[:-1]
            return nodes
        except Exception as e:
            prRed(e)

    def check_hash(self, h: str) -> bool:
        if int(h, 16) <= self.target:
            return True
        return False

    @staticmethod
    def get_n_block(height=0, last=False):
        i = 0
        b_f = None
        if last:
            while True:
                try:
                    b_f = open(BLOCKS_DIRECTORY + ('%08i' % i) + '.block', 'r')
                    i += 1
                except FileNotFoundError:
                    break
        else:
            while i <= height:
                try:
                    b_f = open(BLOCKS_DIRECTORY + ('%08i' % i) + '.block', 'r')
                    i += 1
                except FileNotFoundError:
                    break
        if not b_f:
            prRed("No blocks were found")
            return
        try:
            if b_f.readable():
                block = json.load(b_f)
                block_dict = dict(block)
                last_block = Block(
                                    bits=block_dict['bits'],
                                    timestamp=block_dict['timestamp'],
                                    previous_hash=block_dict['previous_hash'],
                                    transactions=list(block_dict['transactions']),
                                    nonce=block_dict['nonce']
                )
                return last_block
        except Exception as e:
            prRed(e)

    def recalculate_difficulty(self):

        timestamps_diff = []
        if len(self.chain) > 5:
            low_threshold = len(self.chain) - 5
        else:
            low_threshold = 1

        for i in range(len(self.chain), low_threshold):
            timestamps_diff.append(self.chain[i].timestamp - self.chain[i - 1].timestamp)

        sum_timestamp_diff = sum(timestamps_diff)
        if sum_timestamp_diff not in range(55, 65):
            coeff = clamp(float(sum_timestamp_diff)/20.0, 0.85, 1.25)
            if coeff != 0:
                self.target *= coeff
                prPurple("CHANGING DIFFICULTY, COEF -> " + str(coeff))
                prLightPurple("self.target -> " + str(self.target))

                difficulty_str = '0x' + ('%066x' % self.target)[2:]
                f = open(DIFFICULTY_FILE, 'w')
                f.write(difficulty_str)
                f.close()


    def mine(self, block):
        nonce = 0
        h = block.hash_block()
        while not self.check_hash(h):
            nonce += 1
            block.set_nonse(nonce)
            h = block.hash_block()
        if self.check_hash(h):
            time_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            prGreen('[' + time_str + '] nonce=' + str(block.nonce) + ', hash=' + h)
            block.block_hash = h
            self.chain.append(block)
            block_height = len(self.chain) - 1

            # Write block dict to file
            f = open(BLOCKS_DIRECTORY + ('%08i' % block_height) + '.block', 'w+')
            json.dump(block.to_dict(), f)
            f.close()

            # Write chain length to file
            f = open(BLOCKS_LENGTH_FILE, 'w')
            f.write(str(block_height + 1))
            f.close()
            Utxo.add_txs_to_utxo(block.transactions)
            if len(self.chain) % 5 == 0:
                self.recalculate_difficulty()
                self.coinbase = self.coinbase * 0.5
            return h, block

    def genesis_block(self):
        prev_hash = '0000000000000000000000000000000000000000000000000000000000000000'

        f = open(MINER_PRIVKEY_FILE, 'r')
        miner_prkey = f.read().replace('\n', '')
        f.close()

        hashed_pbk = Wallet.get_hashed_pbk_from_addr(Wallet.bech32_addr_from_privkey(miner_prkey, NETWORKS.BITCOIN))
        coin_tsx = SwCoinbaseTransaction(1, hashed_pbk, 0, out_value=self.coinbase)

        serialized_tx = coin_tsx.get_raw_transaction(hex=True)
        genesis = Block(
                        bits=self.complexity,
                        timestamp=0,
                        previous_hash=prev_hash,
                        transactions=[serialized_tx]
        )

        self.mine(genesis)
        return genesis

    @staticmethod
    def get_new_chains():
        new_chains = []
        nodes = Blockchain.recover_nodes_from_file()
        for node in nodes:
            try:
                raw_blocks = requests.get("http://" + node + '/chain').content
                blocks = json.loads(raw_blocks)
                chain = []
                for i in range(len(blocks)):
                    new_block = Block.block_from_dict(blocks[i])
                    chain.append(new_block)

                is_valid = Blockchain.is_valid_chain(chain)
                if is_valid:
                    new_chains.append(chain)
            except Exception as e:
                prRed(e)
        return new_chains

    @staticmethod
    def resolve_conflicts(my_chain, other_chains):
        my_chain = my_chain
        longest_chain = my_chain
        for chain in other_chains:
            if len(longest_chain) < len(chain):
                longest_chain = chain
        if longest_chain == my_chain:
            return False
        else:
            my_chain = longest_chain
            return my_chain

    @staticmethod
    def is_valid_chain(chain):
        for i in range(1, len(chain)):
            chain[i].validate_transactions()
        return True

    @staticmethod
    def validate_node(node):
        regex = r'([0-9]{1,3})[.]([0-9]{1,3})[.]([0-9]{1,3})[.]([0-9]{1,3})[:]([0-9]{4,})'

        m = re.findall(regex, node)

        if m:
            if (
                    int(m[0][0]) <= 255 and
                    int(m[0][1]) <= 255 and
                    int(m[0][2]) <= 255 and
                    int(m[0][3]) <= 255
            ):
                return True
        return False
