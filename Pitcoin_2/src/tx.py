import base58
import hashlib
import ecdsa
import struct
import codecs
import binascii
from serializer import *
from colored_print import prRed
from wallet import Wallet
outpoint = "9844f4682eae5bb14297a94124d09f7fd635dbb2241490c99ca2e2ec3dc821db"

Alice_adress 		= "1NWzVg38ggPoVGAG2VWt6ktdWMaV6S1pJK"
Alice_hashed_pubkey = base58.b58decode_check(Alice_adress)[1:].hex()

Bob_adress	 		= "1ANRQ9bEJZcwXiw7YZ6uE5egrE7t9gCyip"
Bob_hashed_pubkey	= base58.b58decode_check(Bob_adress)[1:].hex()


Alice_private_key	= "73356839c2883cdf723b44f329928d5acd51e0b3b9d88ea3e1639e34e1dc6958"
my_privkey          = 'cQxh5qHbpebWiaEgQsN4jFs6a8KHjk1uvRno2tDVceQEo2KuN2ZB'
class Transaction:
    def __init__(self, sender_addr, recepient_addr, inputs, value, locktime):
        self.version = struct.pack("<L", 1)
        self.tx_in_count = struct.pack("<B", 1)

        self.tx_in = dict()
        self.tx_in['outpoint_hash'] = codecs.decode(self.flip_byte_order(inputs), 'hex')
        self.tx_in['outpoint_index'] = struct.pack("<L", 0)
        self.tx_in['script'] = codecs.decode(("76a914%s88ac" % Wallet.publkey_hash_from_addr(sender_addr)), 'hex')
        self.tx_in['script_bytes'] = struct.pack("<B", (len(self.tx_in['script'])))
        self.tx_in['sequence'] = codecs.decode("ffffffff", 'hex')

        self.tx_out_count = struct.pack("<B", 2)
        self.tx_out1 = dict()
        self.tx_out1['value'] = struct.pack("<Q", value)
        self.tx_out1['pk_script'] = codecs.decode(("76a914%s88ac" % Wallet.publkey_hash_from_addr(recepient_addr)), 'hex')
        self.tx_out1['pk_script_bytes'] = struct.pack("<B", (len(self.tx_out1['pk_script'])))

        self.tx_out2 = dict()
        self.tx_out2['value'] = struct.pack("<Q", value)
        self.tx_out2['pk_script'] = codecs.decode(("76a914%s88ac" % Wallet.publkey_hash_from_addr(sender_addr)), 'hex')
        self.tx_out2['pk_script_bytes'] = struct.pack("<B", (len(self.tx_out2['pk_script'])))
        self.lock_time = struct.pack("<L", locktime)

        self.sign = None
        self.sig_script = None

    def flip_byte_order(self, string):
        flipped = "".join(reversed([string[i:i + 2] for i in range(0, len(string), 2)]))
        return flipped

    def serialize_to_sign(self):
        s = (
            self.version +
            self.tx_in_count +
            self.tx_in['outpoint_hash'] +
            self.tx_in['outpoint_index'] +
            self.tx_in['script_bytes'] +
            self.tx_in['sequence'] +
            self.tx_out_count +
            self.tx_out1["value"] +
            self.tx_out1["pk_script_bytes"] +
            self.tx_out1["pk_script"] +
            self.tx_out2["value"] +
            self.tx_out2["pk_script_bytes"] +
            self.tx_out2["pk_script"] +
            self.lock_time +
            struct.pack("<L", 1)
        )
        return s

    def sign_transaction(self, prkey):
        raw_tx_string = self.serialize_to_sign()
        hashed_tx_to_sign = hashlib.sha256(hashlib.sha256(raw_tx_string.hex().encode()).digest()).digest()

        prRed(prkey)
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(prkey), curve=ecdsa.SECP256k1)
        vk = sk.verifying_key
        public_key = (b"04" + binascii.hexlify(vk.to_string()))
        self.sign = sk.sign_digest(hashed_tx_to_sign, sigencode=ecdsa.util.sigencode_der)

        self.sig_script = (
                self.sign
                + b"01"
                + struct.pack("<B", len(binascii.unhexlify(public_key).hex()))
                + public_key
        )

    def raw_transaction(self, prkey):
        prRed(prkey)
        self.sign_transaction(prkey)
        inputs = (
                self.tx_in['outpoint_hash']
                + self.tx_in['outpoint_index']
                + struct.pack("<B", (len(self.sig_script) + 1))
                + struct.pack("<B", (len(self.sign) + 1))
                + self.sig_script
                + self.tx_in['sequence']
        )
        raw_tx = (
                self.version
                + self.tx_in_count
                + inputs
                + self.tx_out_count
                + self.tx_out1["value"]
                + self.tx_out1["pk_script_bytes"]
                + self.tx_out1["pk_script"]
                + self.tx_out2["value"]
                + self.tx_out2["pk_script_bytes"]
                + self.tx_out2["pk_script"]
                + self.lock_time
        )
        return raw_tx

out_txid = '746f07af15f9fca472c993cd343ab3207072020b0fd3797def150473e88cbdf6'
my_address = '2NEBZ1E7FqWCQsC3aETLepmADibZ7Mgnz3D'
taras_address = '2NEHZANaV4s48mzmnuRanzW4nF9vLnB2you'

tx = Transaction(my_address, taras_address, out_txid, 20, 10)
# print(tx.raw_transaction(Alice_private_key))
privkey = Wallet.WIF_to_priv(my_privkey)
prk = swap_bits_in_str(privkey)
print(prk)
abcde = Wallet.WIF_to_priv('Qqj2j371SdysJ9ru9WaTnfimX2tsQKr1snvJRrNg4X6jwYnZnUoKgUhDgppodgFbQY6dB4V')
prRed(abcde)
raw = tx.raw_transaction('')

raw_dict = deserialize(raw.hex())

print('--------')
print(raw.hex())
print('--------')
# print(raw_dict)

