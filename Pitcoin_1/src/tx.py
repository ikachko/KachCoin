import hashlib
import base58
import ecdsa
import struct
import bech32

from wallet import Wallet

from serializer import make_varint, get_varint
input_amount = 850000
output_amount = 100000
fee = 50000
sender_address = "mv3d5P4kniPrT5owreux438yEtcFUefo71"
sender_compressed_pub = "02C3C6A89E01B4B62621233C8E0C2C26078A2449ABAA837E18F96A1F65D7B8CC8C"
sender_wif_priv = "5JrJuxQ5QhLASMpQgSCZ9Fmzt8Sit8X3h1N9LGWYdXDtBhUxCwB"
recipient_address = "n3Jqa2cyGqKDvc8QNMKYooy5yYUqoGwrvi"
prev_txid = "3e2ca1d97f66b5a2b2b376daff44c6345c5877001f01eb7797c86fdbd93282d9"


def flip_byte_order(string):
    flipped = "".join(reversed([string[i:i + 2] for i in range(0, len(string), 2)]))
    return flipped


def raw_deserialize(raw_tx):
    raw_dict = dict()

    raw_dict['txid'] = hashlib.sha256(hashlib.sha256(bytes.fromhex(raw_tx)).digest()).hexdigest()
    raw_dict['version'] = int(flip_byte_order(raw_tx[0:8]), 16)

    # Check SegWit flag
    if raw_tx[8:12] == '0001':
        raw_dict['is_sw'] = True
        i = 12
    else:
        raw_dict['is_sw'] = False
        i = 8

    plus_i, varint = get_varint(raw_tx[i:])
    raw_dict['input_count'] = varint
    i += plus_i

    raw_dict['inputs'] = []
    for _ in range(raw_dict['input_count']):
        input_transaction = dict()

        input_transaction['txid'] = flip_byte_order(raw_tx[i:i + 64])
        i += 64

        input_transaction['tx_index'] = int(flip_byte_order(raw_tx[i:i + 8]), 16)
        i += 8

        plus_i, varint = get_varint(raw_tx[i:])

        input_transaction['script_length'] = varint * 2
        i += plus_i

        input_transaction['script'] = raw_tx[i:i + input_transaction['script_length']]
        i += input_transaction['script_length']

        input_transaction['sequence'] = flip_byte_order(raw_tx[i:i + 8])
        i += 8

        raw_dict['inputs'].append(input_transaction)

    plus_i, varint = get_varint(raw_tx[i:])
    raw_dict['output_count'] = varint
    i += plus_i

    raw_dict['outputs'] = []
    for _ in range(raw_dict['output_count']):
        output_transaction = dict()

        output_transaction['value'] = int(flip_byte_order(raw_tx[i:i + 16]), 16)
        i += 16

        plus_i, pk_script_length_bytes = get_varint(raw_tx[i:])
        output_transaction['pk_script_length'] = pk_script_length_bytes * 2
        i += plus_i

        output_transaction['pk_script'] = raw_tx[i:i + (pk_script_length_bytes * 2)]
        i += (pk_script_length_bytes * 2)

        raw_dict['outputs'].append(output_transaction)
    if raw_dict['is_sw']:
        raw_dict['witness'] = []

        for _ in range(raw_dict['input_count']):
            plus_i, witness_count = get_varint(raw_tx[i:])
            i += plus_i
            witness = []

            for _ in range(witness_count):
                plus_i, varint_bytes = get_varint(raw_tx[i:])
                i += plus_i
                witness.append(raw_tx[i:i + varint_bytes * 2])
                i += varint_bytes * 2

            raw_dict['witness'].append(witness)
    raw_dict['locktime'] = int(flip_byte_order(raw_tx[-5:-1]), 16)

    return raw_dict

class SwRawTransactionMultInputs:
    def __init__(self,
                 version: int,
                 sender_priv_wif: str,
                 sender_addr: str,
                 recipient_addr: str,
                 inputs,
                 out_value: int,
                 miner_fee: int,
                 locktime: int
                 ):
        raw_privkey = Wallet.WIF_to_priv(sender_priv_wif)
        sender_pubkey_compressed = Wallet.compressed_publkey_from_publkey(Wallet.private_to_public(raw_privkey))

        self.version = struct.pack("<L", version)
        self.marker = struct.pack("<B", 0)
        self.flag = struct.pack("<B", 1)
        self.tx_in_count = struct.pack("<B", len(inputs))
        self.tx_in = {}  # TEMP
        self.tx_out_count = struct.pack("<B", 2)
        self.tx_out1 = {}  # TEMP
        self.tx_out2 = {}  # TEMP
        self.lock_time = struct.pack("<L", locktime)
        self.tx_to_sign = None
        self.raw_tx = self.make_raw_transaction(sender_priv_wif,
                                                sender_pubkey_compressed,
                                                sender_addr,
                                                recipient_addr,
                                                inputs,
                                                out_value,
                                                miner_fee)

    def make_raw_transaction(self,
                             sender_priv_wif,
                             sender_pubkey_compressed,
                             sender_addr,
                             recipient_addr,
                             inputs,
                             out_value,
                             miner_fee):

        my_address = sender_addr
        my_hashed_pubkey = Wallet.get_hashed_pbk_from_addr(my_address)

        my_private_key = sender_priv_wif
        my_private_key_hex = base58.b58decode_check(my_private_key)[1:33].hex()

        recipient = recipient_addr
        recipient_hashed_pubkey = Wallet.get_hashed_pbk_from_addr(recipient)

        # form tx_out
        self.tx_out1["value"] = struct.pack("<Q", out_value)
        self.tx_out1["pk_script"] = bytes.fromhex("76a914%s88ac" % recipient_hashed_pubkey)
        self.tx_out1["pk_script_bytes"] = struct.pack("<B", len(self.tx_out1["pk_script"]))

        input_value = 0
        for i in inputs:
            input_value += i['value']

        return_value = input_value - output_amount - miner_fee  # 1000 left as fee
        self.tx_out2["value"] = struct.pack("<Q", return_value)
        self.tx_out2["pk_script"] = bytes.fromhex("76a914%s88ac" % my_hashed_pubkey)
        self.tx_out2["pk_script_bytes"] = struct.pack("<B", len(self.tx_out2["pk_script"]))

        pk_bytes = bytes.fromhex(my_private_key_hex)

        witnesses = []
        for i in range(len(inputs)):
            msg_for_sign = b''
            for j in range(len(inputs)):
                msg_for_sign += self.version
                msg_for_sign += self.marker
                msg_for_sign += self.flag
                msg_for_sign += self.tx_in_count
                msg_for_sign += bytes.fromhex(flip_byte_order(inputs[i]['txid']))
                msg_for_sign += struct.pack("<L", i)
                if i == j:
                    script = bytes.fromhex("76a914%s88ac" % my_hashed_pubkey)
                    msg_for_sign += struct.pack("<B", len(script))
                    msg_for_sign += script
                else:
                    msg_for_sign += struct.pack("<B", 0)
            msg_for_sign += self.tx_out_count
            msg_for_sign += self.tx_out1["value"]
            msg_for_sign += self.tx_out1["pk_script_bytes"]
            msg_for_sign += self.tx_out1["pk_script"]
            msg_for_sign += self.tx_out2["value"]
            msg_for_sign += self.tx_out2["pk_script_bytes"]
            msg_for_sign += self.tx_out2["pk_script"]
            msg_for_sign += self.lock_time
            msg_for_sign += struct.pack("<L", 1)

            hashed_tx_to_sign = hashlib.sha256(hashlib.sha256(msg_for_sign).digest()).digest()
            sk = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1)
            signature = sk.sign_digest(hashed_tx_to_sign, sigencode=ecdsa.util.sigencode_der_canonize())

            pk_bytes_hex = sender_pubkey_compressed

            witness = (
                struct.pack("<B", len(signature) + 1)
                + signature
                + b'\01'
                + struct.pack("<B", len(bytes.fromhex(pk_bytes_hex)))
                + bytes.fromhex(pk_bytes_hex)
            )
            witnesses.append(witness)

        bytes_witnesses = b''
        for w in witnesses:
            bytes_witnesses += w

        real_tx = (
                self.version
                + self.marker
                + self.flag
                + self.tx_in_count
                + self.tx_in["tx_out_hash"]
                + self.tx_in["tx_out_index"]
                + struct.pack("<B", 0)
                # + struct.pack("<B", 0)
                + self.tx_in["sequence"]
                + self.tx_out_count
                + self.tx_out1["value"]
                + self.tx_out1["pk_script_bytes"]
                + self.tx_out1["pk_script"]
                + self.tx_out2["value"]
                + self.tx_out2["pk_script_bytes"]
                + self.tx_out2["pk_script"]
                + struct.pack("<B", len(inputs) + 1)  # Num of inputs
                + struct.pack("<B", len(witnesses) + 1)
                + bytes_witnesses
                + self.lock_time
        )
        return real_tx

    def unlock_utxo(self, public_key, utxo):
        pass

    def get_raw_transaction(self, hex=False):
        if self.raw_tx:
            if hex:
                return self.raw_tx.hex()
            else:
                return self.raw_tx



class SwRawTransaction:
    def __init__(self,
                 version: int,
                 sender_priv_wif: str,
                 sender_addr: str,
                 recipient_addr: str,
                 prevtxid: str,
                 in_value: int,
                 out_value: int,
                 miner_fee: int,
                 locktime: int
                 ):
        raw_privkey = Wallet.WIF_to_priv(sender_priv_wif)
        sender_pubkey_compressed = Wallet.compressed_publkey_from_publkey(Wallet.private_to_public(raw_privkey))

        self.version = struct.pack("<L", version)
        self.marker = struct.pack("<B", 0)
        self.flag = struct.pack("<B", 1)
        self.tx_in_count = struct.pack("<B", 1)
        self.tx_in = {}  # TEMP
        self.tx_out_count = struct.pack("<B", 2)
        self.tx_out1 = {}  # TEMP
        self.tx_out2 = {}  # TEMP
        self.lock_time = struct.pack("<L", locktime)
        self.tx_to_sign = None
        self.raw_tx = self.make_raw_transaction(sender_priv_wif,
                                                sender_pubkey_compressed,
                                                sender_addr,
                                                recipient_addr,
                                                prevtxid,
                                                in_value,
                                                out_value,
                                                miner_fee)

    def make_raw_transaction(self,
                             sender_priv_wif,
                             sender_pubkey_compressed,
                             sender_addr,
                             recipient_addr,
                             prevtxid,
                             in_value,
                             out_value,
                             miner_fee):
        my_address = sender_addr
        my_hashed_pubkey = base58.b58decode_check(my_address)[1:].hex()

        my_private_key = sender_priv_wif
        my_private_key_hex = base58.b58decode_check(my_private_key)[1:33].hex()

        recipient = recipient_addr
        recipient_hashed_pubkey = base58.b58decode_check(recipient)[1:].hex()

        my_output_tx = prevtxid
        input_value = in_value

        # form tx_in
        self.tx_in["tx_out_hash"] = bytes.fromhex(flip_byte_order(my_output_tx))
        self.tx_in["tx_out_index"] = struct.pack("<L", 1)
        self.tx_in["script"] = bytes.fromhex("76a914%s88ac" % my_hashed_pubkey)
        self.tx_in["scrip_bytes"] = struct.pack("<B", len(self.tx_in["script"]))
        self.tx_in["sequence"] = bytes.fromhex("ffffffff")

        # form tx_out
        self.tx_out1["value"] = struct.pack("<Q", out_value)
        self.tx_out1["pk_script"] = bytes.fromhex("76a914%s88ac" % recipient_hashed_pubkey)
        self.tx_out1["pk_script_bytes"] = struct.pack("<B", len(self.tx_out1["pk_script"]))

        return_value = input_value - output_amount - miner_fee  # 1000 left as fee
        self.tx_out2["value"] = struct.pack("<Q", return_value)
        self.tx_out2["pk_script"] = bytes.fromhex("76a914%s88ac" % my_hashed_pubkey)
        self.tx_out2["pk_script_bytes"] = struct.pack("<B", len(self.tx_out2["pk_script"]))

        # =========================================
        # form raw_tx
        self.tx_to_sign = (
                self.version
                + self.marker
                + self.flag
                + self.tx_in_count
                + self.tx_in["tx_out_hash"]
                + self.tx_in["tx_out_index"]
                + self.tx_in["scrip_bytes"]
                + self.tx_in["script"]
                + self.tx_in["sequence"]
                + self.tx_out_count
                + self.tx_out1["value"]
                + self.tx_out1["pk_script_bytes"]
                + self.tx_out1["pk_script"]
                + self.tx_out2["value"]
                + self.tx_out2["pk_script_bytes"]
                + self.tx_out2["pk_script"]
                + self.lock_time
                + struct.pack("<L", 1)
        )

        hashed_tx_to_sign = hashlib.sha256(hashlib.sha256(self.tx_to_sign).digest()).digest()
        pk_bytes = bytes.fromhex(my_private_key_hex)
        sk = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1)

        public_key_bytes_hex = sender_pubkey_compressed

        signature = sk.sign_digest(hashed_tx_to_sign, sigencode=ecdsa.util.sigencode_der_canonize)

        witness = (
            signature
            + b'\01'
            + struct.pack("<B", len(bytes.fromhex(public_key_bytes_hex)))
            + bytes.fromhex(public_key_bytes_hex)
        )

        real_tx = (
                self.version
                + self.marker
                + self.flag
                + self.tx_in_count
                + self.tx_in["tx_out_hash"]
                + self.tx_in["tx_out_index"]
                + struct.pack("<B", 0)
                # + struct.pack("<B", 0)
                + self.tx_in["sequence"]
                + self.tx_out_count
                + self.tx_out1["value"]
                + self.tx_out1["pk_script_bytes"]
                + self.tx_out1["pk_script"]
                + self.tx_out2["value"]
                + self.tx_out2["pk_script_bytes"]
                + self.tx_out2["pk_script"]
                + struct.pack("<B", (1) + 1) # Num of inputs
                + struct.pack("<B", len(signature) + 1)
                + witness
                + self.lock_time

        )
        return real_tx

    def get_raw_transaction(self, hex=False):
        if self.raw_tx:
            if hex:
                return self.raw_tx.hex()
            else:
                return self.raw_tx


class SwCoinbaseTransaction(SwRawTransaction):
    def __init__(self,
                 version: int,
                 recipient_hashed_pbk: str,
                 locktime: int,
                 out_value=50):
        self.version = struct.pack("<L", version)
        self.marker = struct.pack("<B", 0)
        self.flag = struct.pack("<B", 1)
        self.tx_in_count = struct.pack("<B", 1)
        self.tx_in = {}
        self.tx_out_count = struct.pack("<B", 1)
        self.tx_out = {}
        self.lock_time = struct.pack("<L", locktime)

        self.raw_tx = self.make_transaction(recipient_hashed_pbk, out_value)

    def make_transaction(self, recipient_hashed_pbk, out_value):
        my_output_tx = "0000000000000000000000000000000000000000000000000000000000000000"

        # form tx_in
        self.tx_in["tx_out_hash"] = bytes.fromhex(flip_byte_order(my_output_tx))
        self.tx_in["tx_out_index"] = struct.pack("<L", 1)
        self.tx_in["sequence"] = bytes.fromhex("ffffffff")

        # form tx_out
        self.tx_out["value"] = struct.pack("<Q", out_value)
        self.tx_out["pk_script"] = bytes.fromhex("76a914%s88ac" % recipient_hashed_pbk)
        self.tx_out["pk_script_bytes"] = struct.pack("<B", len(self.tx_out["pk_script"]))

        public_key_bytes_hex = "492077616e7420746f2074616c6b20746f20796f7520616761696e"

        signature = bytes.fromhex("48656c6c6f206461726b6e657373206d79206f6c6420667269656e64")

        sigscript = (
                signature
                + b'\01'
                + struct.pack("<B", len(bytes.fromhex(public_key_bytes_hex)))
                + bytes.fromhex(public_key_bytes_hex)

        )

        real_tx = (
                self.version
                + self.tx_in_count
                + self.tx_in["tx_out_hash"]
                + self.tx_in["tx_out_index"]
                + struct.pack("<B", len(sigscript) + 1)
                + struct.pack("<B", len(signature) + 1)
                + sigscript
                + self.tx_in["sequence"]
                + self.tx_out_count
                + self.tx_out["value"]
                + self.tx_out["pk_script_bytes"]
                + self.tx_out["pk_script"]
                + self.lock_time
        )
        return real_tx

class RawTransaction:
    def __init__(self,
                 version: int,
                 sender_priv_wif: str,
                 sender_addr: str,
                 recipient_addr: str,
                 prevtxid: str,
                 in_value: int,
                 out_value: int,
                 miner_fee: int,
                 locktime: int):
        raw_privkey = Wallet.WIF_to_priv(sender_priv_wif)
        sender_pubkey_compressed = Wallet.compressed_publkey_from_publkey(Wallet.private_to_public(raw_privkey))
        self.version = struct.pack("<L", version)
        self.tx_in_count = struct.pack("<B", 1)
        self.tx_in = {}  # TEMP
        self.tx_out_count = struct.pack("<B", 2)
        self.tx_out1 = {}  # TEMP
        self.tx_out2 = {}  # TEMP
        self.lock_time = struct.pack("<L", locktime)
        self.raw_tx = self.make_raw_transaction(sender_priv_wif,
                                                sender_pubkey_compressed,
                                                sender_addr,
                                                recipient_addr,
                                                prevtxid,
                                                in_value,
                                                out_value,
                                                miner_fee)

    def flip_byte_order(self, string):
        flipped = "".join(reversed([string[i:i + 2] for i in range(0, len(string), 2)]))
        return flipped

    def get_raw_transaction(self, hex=False):
        if self.raw_tx:
            if hex:
                return self.raw_tx.hex()
            else:
                return self.raw_tx

    def make_raw_transaction(self,
                             sender_priv_wif,
                             sender_pubkey_compressed,
                             sender_addr,
                             recipient_addr,
                             prevtxid,
                             in_value,
                             out_value,
                             miner_fee):
        my_address = sender_addr
        my_hashed_pubkey = base58.b58decode_check(my_address)[1:].hex()

        my_private_key = sender_priv_wif
        my_private_key_hex = base58.b58decode_check(my_private_key)[1:33].hex()

        recipient = recipient_addr
        recipient_hashed_pubkey = base58.b58decode_check(recipient)[1:].hex()

        my_output_tx = prevtxid
        input_value = in_value

        # form tx_in
        self.tx_in["tx_out_hash"] = bytes.fromhex(self.flip_byte_order(my_output_tx))
        self.tx_in["tx_out_index"] = struct.pack("<L", 1)
        self.tx_in["script"] = bytes.fromhex("76a914%s88ac" % my_hashed_pubkey)
        self.tx_in["scrip_bytes"] = struct.pack("<B", len(self.tx_in["script"]))
        self.tx_in["sequence"] = bytes.fromhex("ffffffff")

        # form tx_out
        self.tx_out1["value"] = struct.pack("<Q", out_value)
        self.tx_out1["pk_script"] = bytes.fromhex("76a914%s88ac" % recipient_hashed_pubkey)
        self.tx_out1["pk_script_bytes"] = struct.pack("<B", len(self.tx_out1["pk_script"]))

        return_value = input_value - output_amount - miner_fee  # 1000 left as fee
        self.tx_out2["value"] = struct.pack("<Q", return_value)
        self.tx_out2["pk_script"] = bytes.fromhex("76a914%s88ac" % my_hashed_pubkey)
        self.tx_out2["pk_script_bytes"] = struct.pack("<B", len(self.tx_out2["pk_script"]))

        # =========================================
        # form raw_tx
        raw_tx_string = (
                self.version
                + self.tx_in_count
                + self.tx_in["tx_out_hash"]
                + self.tx_in["tx_out_index"]
                + self.tx_in["scrip_bytes"]
                + self.tx_in["script"]
                + self.tx_in["sequence"]
                + self.tx_out_count
                + self.tx_out1["value"]
                + self.tx_out1["pk_script_bytes"]
                + self.tx_out1["pk_script"]
                + self.tx_out2["value"]
                + self.tx_out2["pk_script_bytes"]
                + self.tx_out2["pk_script"]
                + self.lock_time
                + struct.pack("<L", 1)
        )

        hashed_tx_to_sign = hashlib.sha256(hashlib.sha256(raw_tx_string).digest()).digest()
        pk_bytes = bytes.fromhex(my_private_key_hex)
        sk = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1)

        public_key_bytes_hex = sender_pubkey_compressed

        signature = sk.sign_digest(hashed_tx_to_sign, sigencode=ecdsa.util.sigencode_der_canonize)

        sigscript = (

                signature
                + b'\01'
                + struct.pack("<B", len(bytes.fromhex(public_key_bytes_hex)))
                + bytes.fromhex(public_key_bytes_hex)

        )

        real_tx = (
                self.version
                + self.tx_in_count
                + self.tx_in["tx_out_hash"]
                + self.tx_in["tx_out_index"]
                + struct.pack("<B", len(sigscript) + 1)
                + struct.pack("<B", len(signature) + 1)
                + sigscript
                + self.tx_in["sequence"]
                + self.tx_out_count
                + self.tx_out1["value"]
                + self.tx_out1["pk_script_bytes"]
                + self.tx_out1["pk_script"]
                + self.tx_out2["value"]
                + self.tx_out2["pk_script_bytes"]
                + self.tx_out2["pk_script"]
                + self.lock_time

        )
        return real_tx