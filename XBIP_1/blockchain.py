import re

from time import gmtime, strftime
from transaction import CoinbaseTransaction, Transaction
from block import Block


class Blockchain:
    def __init__(self):
        self.complexity = 2
        self.chain = [self.genesis_block()]
        self.nodes = []

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
        transaction = Transaction(tsx.sender_address, tsx.recipient_address, tsx.amount)
        signature = 'pmfvbjhumpsaolbumvynpcpuntpudpaozeafzljzdvyaovmkpzahujlybufvbyzpzaollhyaohuklclyfaopunaohapupahukdopjopztvylfvbsilhttfzvuceasar7'

        genesis = Block(0, prev_hash, transaction.transaction_hash())
        return genesis

    def is_valid_chain(self):
        for block in self.chain:
            block.validate_transactions()

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
