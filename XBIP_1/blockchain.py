import re
import requests
import json

from pending_pool import PendingPool
from time import gmtime, strftime
from transaction import CoinbaseTransaction
from block import Block
from flask import Flask
from flask import request

node = Flask(__name__)

class Blockchain:
    def __init__(self):
        self.complexity = 2
        self.chain = [self.genesis_block()]
        self.nodes = []
        self.tx_pool = PendingPool()

    def check_hash(self, h):
        if h[0:self.complexity] == '0' * self.complexity:
            return True
        return False

    def mine(self, block):
        nonce = 0
        h = block.hash_block()
        while not self.check_hash(h):
            nonce += 1
            block.set_nonse(nonce)
            h = block.hash_block()
            time_str = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print('[' + time_str + '] nonce=' + str(block.nonce) + ', hash=' + h)
        if self.check_hash(h):
            self.chain.append(block)

    def genesis_block(self):
        prev_hash = '0'
        tsx = CoinbaseTransaction()
        signature = 'pmfvbjhumpsaolbumvynpcpuntpudpaozeafzljzdvyaovmkpzahujlybufvbyzpzaollhyaohukl' \
                    'clyfaopunaohapupahukdopjopztvylfvbsilhttfzvuceasar7'

        genesis = Block(0, prev_hash, tsx.transaction_hash())
        return genesis

    def get_new_chains(self):
        new_chains = []
        for node in self.nodes:
            blocks = requests.get(node + '/chain').content
            blocks = json.loads(blocks)

            is_valid = self.is_valid_chain(blocks)
            if is_valid:
                new_chains.append(blocks)

    def resolve_conflicts(self):
        other_chains = self.get_new_chains()
        my_chain = self.chain
        longest_chain = my_chain

        for chain in other_chains:
            if len(longest_chain) < len(chain):
                longest_chain = chain
        if longest_chain == my_chain:
            return False
        else:
            my_chain = longest_chain
            return my_chain

    def is_valid_chain(self, chain):
        for block in chain:
            block.validate_transactions()
        return True

    def add_node(self, new_node):
        regex = r'([0-9]{1,3})[.]([0-9]{1,3})[.]([0-9]{1,3})[.]([0-9]{1,3})[:]([0-9]{4,})'

        m = re.findall(regex, new_node)
        if m[0] is None:
            if (
                    int(m[0][0]) <= 255 and
                    int(m[0][1]) <= 255 and
                    int(m[0][2]) <= 255 and
                    int(m[0][3]) <= 255
            ):
                print(new_node + ' added to node pool')
                self.nodes.append(new_node)
            else:
                print("Wrong node format !")

    @node.route('/transaction/pendings', methods=['GET'])
    def get_pool_of_transaction(self):
        raw_pool = self.tx_pool.return_all_transactions()
        json_pool = json.dumps(raw_pool)
        return json_pool

    @node.route('/transaction/new', methods=['POST'])
    def push_new_transaction(self):
        new_tx_json = request.get_json()
        print(new_tx_json)

    @node.route('/nodes', methods=['GET'])
    def get_nodes(self):
        raw_nodes = self.nodes
        json_nodes = json.dumps(raw_nodes)
        return json_nodes

    @node.route('/chain/length', methods=['GET'])
    def get_chain_length(self):
        chain_len = len(self.chain)
        json_length = json.dumps(chain_len)
        return json_length

    @node.route('/chain', methods=['GET'])
    def get_chain(self):
        chain = []
        for block in self.chain:
            chain.append(block.to_dict())

        json_chain = json.dumps(chain)
        return json_chain
