import codecs
import hashlib

import requests
from flask import *


class Transaction:

    def __init__(self, sender_address=None, recipient_address=None, amount=None):
        if not sender_address:
            raise ValueError("No sender address !")
        if not recipient_address:
            raise ValueError("No recepient address !")
        if not amount:
            raise ValueError("No amount !")
        if amount <= 0:
            raise ValueError("Amount must be > 0 !")

        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.amount = amount

    def to_dict(self):
        return dict({
                        'sender_address': self.sender_address,
                        'recipient_address': self.recipient_address,
                        'value': self.value
                    })

    def transaction_hash(self):
        tsx = self.sender_address + self.recipient_address + '%04x' % self.amount
        tsx_bytes = codecs.encode(bytes(tsx, encoding='utf-8'), 'hex')
        transaction_hash = hashlib.sha256(tsx_bytes).digest()
        return transaction_hash.hex()


class CoinbaseTransaction(Transaction):
    def __init__(self, amount=50):
        super(CoinbaseTransaction, self).__init__(
            '0000000000000000000000000000000000',
            '0000000000000000000000000000000000',
            amount)
