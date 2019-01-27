import re
import requests
import json
from flask import (Flask,
                   request)
from time import gmtime, strftime

from pending_pool import PendingPool
from transaction import CoinbaseTransaction
from block import Block
from serializer import Serializer
from wallet import Wallet

node = Flask(__name__)


BLOCKCHAIN = []



NODES = []
WAITING_TRANSACTIONS = []


@node.route("/")
def index():
    return "HELLO WORLD"


class Blockchain:
    def __init__(self):
        self.complexity = 2
        self.chain = [self.genesis_block()]
        BLOCKCHAIN.append(Blockchain.genesis_block())
        self.nodes = Blockchain.recover_nodes_from_file()
        self.tx_pool = PendingPool()

    @staticmethod
    def get_pool_of_transactions():
        try:
            f = open('pending_pool', 'r')
            tx = f.readline()
            txs = []
            while True:
                txs.append(tx)
                tx = f.readline()
                if not tx:
                    break
            f.close()
            return txs
        except Exception as e:
            print(e)

    @staticmethod
    def get_transactions_to_block():
        try:
            f = open('pending_pool', 'r')
            tx = f.readline()
            txs = []
            while True:
                txs.append(tx)
                tx = f.readline()
                if not tx:
                    break
            f.close()
            to_block = txs[:3]
            f = open('pending_pool', 'w')
            to_write = txs[3:]
            for tx in to_write:
                f.write(tx)
            f.close()
            return to_block
        except Exception as e:
            print(e)

    @staticmethod
    def recover_blockchain_from_fileblock():
        idx = 0
        recovered_chain = []
        while True:
            try:
                f = open('./blocks/' + ('%04x' % idx) + '.block', 'r')
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
            f = open('./miner_data/nodes', 'r')
            node = f.readline()[:-1]
            while node:
                if Blockchain.validate_node(node):
                    nodes.append(node)
                node = f.readline()[:-1]
            return nodes
        except Exception as e:
            print(e)

    @staticmethod
    def check_hash(h, complexity):
        if h[0:complexity] == '0' * complexity:
            return True
        return False

    @staticmethod
    def get_my_blockchain():
        return BLOCKCHAIN

    def mine(self, block):
        nonce = 0
        h = block.hash_block()
        while not Blockchain.check_hash(h, self.complexity):
            nonce += 1
            block.set_nonse(nonce)
            h = block.hash_block()
            if nonce % 100 == 0:
                time_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                print('[' + time_str + '] nonce=' + str(block.nonce) + ', hash=' + h)
        if self.check_hash(h, self.complexity):
            time_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print('[' + time_str + '] nonce=' + str(block.nonce) + ', hash=' + h)
            BLOCKCHAIN.append(block)
            block_height = len(BLOCKCHAIN) - 1
            f = open('./blocks/' + ('%04x' % block_height) + '.block', 'w+')
            json.dump(block.to_dict(), f)

            f.close()
            return h, block

    @staticmethod
    def genesis_block():
        prev_hash = '0'
        tsx = CoinbaseTransaction()
        signature = 'pmfvbjhumpsaolbumvynpcpuntpudpaozeafzljzdvyaovmkpzahujlybufvbyzpzaollhyaohukl' \
                    'clyfaopunaohapupahukdopjopztvylfvbsilhttfzvuceasar7'

        f = open('./miner_data/privkey.wif', 'r')
        miner_privkey_wif = f.read()
        f.close()
        miner_privkey = Wallet.WIF_to_priv(miner_privkey_wif)
        sign, publkey = Wallet.sign_message(signature, miner_privkey)
        serialized_tx = Serializer.serialize(tsx.amount, tsx.sender_address, tsx.recipient_address, publkey, signature)

        genesis = Block(timestamp=0, previous_hash=prev_hash, transactions=[serialized_tx, serialized_tx])
        f = open('./blocks/0000.block', 'w')
        json.dump(genesis.to_dict(), f)
        f.close()
        return genesis

    @staticmethod
    def get_new_chains():
        new_chains = []
        nodes = Blockchain.recover_nodes_from_file()
        for node in nodes:
            raw_blocks = requests.get("http://" + node + '/chain').content
            blocks = json.loads(raw_blocks)
            chain = []
            for i in range(len(blocks)):
                new_block = Block.block_from_dict(blocks[i])
                chain.append(new_block)

            is_valid = Blockchain.is_valid_chain(chain)
            if is_valid:
                new_chains.append(chain)
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

    def add_node(self, new_node):
        if Blockchain.validate_node(new_node):
            NODES.append(new_node)

            f = open('nodes', 'a+')
            f.write(new_node + '\n')
            f.close()

            print(new_node + ' added to node pool')
        else:
            print("Wrong node format !")


@node.route('/transaction/pendings', methods=['GET'])
def get_pool_of_transaction():
    raw_pool = Blockchain.get_pool_of_transactions()
    json_pool = json.dumps(raw_pool)
    return json_pool


@node.route('/transaction/new', methods=['GET', 'POST'])
def submit_tx():
    if request.method == 'POST':
        new_tx_json = request.get_json()
        my_pool = Blockchain.get_pool_of_transactions()
        for transaction in new_tx_json['transactions']:
            my_pool.append(transaction[-1])
        my_pool = list(set(my_pool))
        f = open('pending_pool', 'w')
        for tx in my_pool:
            f.write(tx)
        f.close()
        return "Transaction added"
    elif request.method == 'GET':
        json_txs = json.dumps(PENDING_TRANSACTIONS)
        return json_txs


@node.route('/nodes/new', methods=['POST'])
def add_node():
    new_node = request.get_json()
    if Blockchain.validate_node(new_node):
        NODES.append(new_node)

        f = open('nodes', 'a+')
        f.write(new_node + '\n')
        f.close()

        print(new_node + ' added to node pool')
    else:
        print("Wrong node format !")


@node.route('/nodes', methods=['GET'])
def get_nodes():
    raw_nodes = NODES
    json_nodes = json.dumps(raw_nodes)
    return json_nodes


@node.route('/chain', methods=['GET'])
def get_chain():
    chain = Blockchain.recover_blockchain_from_fileblock()
    dict_chain = []
    for block in chain:
        dict_chain.append(block.to_dict())
    json_chain = json.dumps(dict_chain)
    return json_chain


@node.route('/chain/length', methods=['GET'])
def get_chain_length():
    chain_len = len(BLOCKCHAIN)
    json_length = json.dumps(chain_len)
    return json_length


def get_miner_ip_and_port():
    try:
        f = open('./miner_data/network_data')
        json_data = json.load(f)
        read_ip = json_data["ip"]
        read_port = json_data["port"]
        return read_ip, read_port
    except Exception as e:
        print(e)


if __name__ == "__main__":
    ip, port = get_miner_ip_and_port()
    node.run(host=ip, port=port, debug=True)
