import codecs
import hashlib

# TODO : Rewrite Transaction class for new raw bitcoin transaction form


class Input:
    def __init__(self, prev_output, prev_output_idx, sign_script, sequence):
        self.prev_output_hash = self.__reverse_hash(prev_output)
        self.prev_output_idx = prev_output_idx
        self.script_length = len(sign_script)
        self.sign_script = sign_script
        self.sequence = sequence

    def __reverse_hash(self, prev_output):
        output_hash_bytes = codecs.decode(prev_output, 'hex')
        output_hash = hashlib.sha256(hashlib.sha256(output_hash_bytes).digest()).hexdigest()
        return output_hash[::-1]


class Output:
    def __init__(self, value, pubkey_script):
        self.value = value
        self.script_length = len(pubkey_script)
        self.pubkey_script = pubkey_script


class Transaction:
    def __init__(self, version, inputs, outputs, locktime):
        self.version = version
        self.inputs_count = '%02i' % len(inputs)
        self.inputs = inputs
        self.outputs_count = '%02i' % len(outputs)
        self.locktime = locktime

#
# class Transaction:
#
#     def __init__(self, sender_address=None, recipient_address=None, amount=None):
#         if not sender_address:
#             raise ValueError("No sender address !")
#         if not recipient_address:
#             raise ValueError("No recepient address !")
#         if not amount:
#             raise ValueError("No amount !")
#         if amount <= 0:
#             raise ValueError("Amount must be > 0 !")
#
#         self.sender_address = sender_address
#         self.recipient_address = recipient_address
#         self.amount = amount
#
#     def to_dict(self):
#         return dict({
#                         'sender_address': self.sender_address,
#                         'recipient_address': self.recipient_address,
#                         'value': self.value
#                     })
#
#     def transaction_hash(self):
#         tsx = self.sender_address + self.recipient_address + '%04x' % self.amount
#         tsx_bytes = codecs.encode(bytes(tsx, encoding='utf-8'), 'hex')
#         transaction_hash = hashlib.sha256(tsx_bytes).digest()
#         return transaction_hash.hex()
#
#
# class CoinbaseTransaction(Transaction):
#     def __init__(self, amount=50):
#         super(CoinbaseTransaction, self).__init__(
#             '0000000000000000000000000000000000',
#             '0000000000000000000000000000000000',
#             amount)
