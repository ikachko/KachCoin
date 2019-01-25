from serializer import Deserializer
from merkle import merkle
from transaction import Transaction
from tx_validator import transaction_validation

import hashlib


class Block:
    def __init__(self, timestamp, previous_hash, transactions, nonce=0):
        self.timestamp = timestamp
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.merkle_root = merkle(transactions)
        self.block_hash = self.hash_block()

    def set_nonse(self, nonce):
        self.nonce = nonce

    def hash_block(self):
        s = (
                str(self.timestamp) +
                str(self.nonce) +
                str(self.previous_hash) +
                "".join(self.transactions) +
                self.merkle_root
        ).encode('utf-8')
        hash_s = hashlib.sha256(s).digest().hex()
        return hash_s

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'transactions': self.transactions,
            'merkle_root': self.merkle_root,
            'block_hash': self.block_hash
        }

    def validate_transactions(self, transactions):
        if transactions:
            for transaction in transactions:
                deserialized = Deserializer.deserialize(transaction)
                tsx = Transaction(deserialized['sender_addr'],
                                  deserialized['recepient_addr'],
                                  deserialized['num_of_coins'])
                tsx_hash = tsx.transaction_hash()
                transaction_validation(deserialized, tsx_hash)