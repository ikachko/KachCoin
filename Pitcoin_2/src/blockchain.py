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

from globals import (
    PENDING_POOL_FILE,
    BLOCKS_LENGTH_FILE,
    BLOCKS_DIRECTORY,
    MINER_PRIVKEY_FILE,
    MINER_NODES
)


# TODO: Remove global variables and store all in files


class Blockchain:
    def __init__(self):
        self.complexity = 2
        self.chain = Blockchain.recover_blockchain_from_fileblock()
        if not self.chain:
            self.chain = [self.genesis_block()]
        self.nodes = Blockchain.recover_nodes_from_file()
        self.tx_pool = PendingPool()

    @staticmethod
    def get_chain():
        chain = Blockchain.recover_blockchain_from_fileblock()
        if not chain:
            return [Blockchain.genesis_block()]
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

    @staticmethod
    def check_hash(h, complexity):
        if h[0:complexity] == '0' * complexity:
            return True
        return False

    def mine(self, block):
        nonce = 0
        h = block.hash_block()
        while not Blockchain.check_hash(h, self.complexity):
            nonce += 1
            block.set_nonse(nonce)
            h = block.hash_block()
            if nonce % 100 == 0:
                time_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                prCyan('[' + time_str + '] nonce=' + str(block.nonce) + ', hash=' + h)
        if self.check_hash(h, self.complexity):
            time_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            prGreen('[' + time_str + '] nonce=' + str(block.nonce) + ', hash=' + h)
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

            return h, block

    @staticmethod
    def genesis_block():
        prev_hash = '0'
        tsx = CoinbaseTransaction()
        signature = 'pmfvbjhumpsaolbumvynpcpuntpudpaozeafzljzdvyaovmkpzahujlybufvbyzpzaollhyaohukl' \
                    'clyfaopunaohapupahukdopjopztvylfvbsilhttfzvuceasar7'

        f = open(MINER_PRIVKEY_FILE, 'r')
        miner_privkey_wif = f.read()
        f.close()
        miner_privkey = Wallet.WIF_to_priv(miner_privkey_wif)
        sign, publkey = Wallet.sign_message(signature, miner_privkey)
        serialized_tx = Serializer.serialize(tsx.amount, tsx.sender_address, tsx.recipient_address, publkey, signature)
        genesis = Block(timestamp=0, previous_hash=prev_hash, transactions=[serialized_tx, serialized_tx])
        f = open(BLOCKS_DIRECTORY + '00000000.block', 'w')
        json.dump(genesis.to_dict(), f)
        f.close()
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
        # for block in chain:
        #     # print(block.to_dict())
        #     block.validate_transactions()
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
