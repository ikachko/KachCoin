from serializer import Deserializer
from merkle import merkle
from transaction import Transaction
from tx_validator import transaction_validation
from serializer import make_varint, get_varint
import hashlib
import struct


class Block:
    def __init__(self, bits, previous_hash, transactions, version=1, timestamp=0, nonce=0):
        self.version = version
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.merkle_root = merkle(transactions)
        self.block_hash = self.hash_block()

    @staticmethod
    def block_from_dict(block_dict):
        return Block(version=block_dict["version"],
                     previous_hash=block_dict["previous_hash"],
                     timestamp=block_dict["timestamp"],
                     bits=block_dict["bits"],
                     nonce=block_dict["nonce"],
                     transactions=block_dict["transactions"])

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

    def block_header(self):
        h = (
            struct.pack("<L", self.version)
            + bytes.fromhex(self.previous_hash)
            + bytes.fromhex(self.merkle_root)
            + struct.pack("<L", self.timestamp)
            + struct.pack("<L", self.nonce)
        )

        return h

    def serialized_block(self):
        serialized = b''

        serialized += self.block_header()  # Header

        serialized += bytes.fromhex(make_varint(len(self.transactions)))
        for tx in self.transactions:
            serialized += bytes.fromhex(tx)  # Transactions

        return serialized

    def to_dict(self):
        return {
            "version": self.version,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "bits": self.bits,
            "nonce": self.nonce,
            "tx_count": len(self.transactions),
            "transactions": self.transactions,
            "block_hash": self.block_hash
        }

    def validate_transactions(self):
        if self.transactions:
            for transaction in self.transactions:

                deserialized = Deserializer.deserialize(transaction)
                tsx = Transaction(deserialized['sender_addr'],
                                  deserialized['recepient_addr'],
                                  deserialized['num_of_coins'])
                tsx_hash = tsx.transaction_hash()
                transaction_validation(transaction, tsx_hash)
