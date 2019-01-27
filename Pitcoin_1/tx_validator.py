import hashlib

from wallet import Wallet
from serializer import Deserializer

def address_check(addr):
    def decode_base58(bc, length):
        digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        n = 0
        for char in bc:
            n = n * 58 + digits58.index(char)
        return n.to_bytes(length, 'big')
    bcbytes = decode_base58(addr, 25)
    return bcbytes[-4:] == hashlib.sha256(hashlib.sha256(bcbytes[:-4]).digest()).digest()[:4]


def transaction_validation(transaction, transaction_hash):
    tx = Deserializer.deserialize(transaction)
    if (
            # not address_check(tx['sender_addr']) or
            # not address_check(tx['recepient_addr']) or
            Wallet.public_key_to_addr(tx['public_key']) != tx['sender_addr'] or
            not Wallet.verify_message(
                                        transaction_hash,
                                        tx['public_key'],
                                        tx['signature'])
            ):
        return False
    return True
