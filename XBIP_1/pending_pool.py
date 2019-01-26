from serializer import Deserializer
from transaction import Transaction
from tx_validator import transaction_validation


class PendingPool:
    def __init__(self):
        self.transaction_pool = []

    def add_transaction_to_pool(self, serialized_transaction):
        deserialized = Deserializer.deserialize(serialized_transaction)
        transaction = Transaction(deserialized['sender_addr'],
                                  deserialized['recepient_addr'],
                                  deserialized['num_of_coins'])
        transaction_hash = transaction.transaction_hash()
        transaction_validation(deserialized, transaction_hash)
        self.transaction_pool.append(serialized_transaction)

    def return_last_transactions(self, num_of_transactions=3):
        return self.transaction_pool[-num_of_transactions:]

    def return_all_transactions(self):
        return self.transaction_pool
