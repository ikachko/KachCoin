import hashlib
import ecdsa
import codecs
import binascii
import base58
import math
import struct

from enum import Enum

from key_generator import KeyGenerator
from globals import WALLET_PRIVKEY_FILE, NETWORKS
from colored_print import prRed

import bech32

class Wallet:
    def __init__(self, seed=None, key_to_file=False):
        self.__create_priv_key(seed, key_to_file)
        self.public_keys = []

    def __create_priv_key(self, seed=None, key_to_file=False):
        keygen = KeyGenerator()
        if seed:
            keygen.seed_input(seed)
        key = keygen.generate_key()
        while len(key) != 64:
            key = KeyGenerator().generate_key()
        if key_to_file:
            f = open(WALLET_PRIVKEY_FILE, "w+")
            f.write(key)
            f.close()
        else:
            print(key)
        del key
        del keygen

    @staticmethod
    def base58(address_hex):
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        b58_string = ''
        leading_zeros = len(address_hex) - len(address_hex.lstrip('0'))
        address_int = int(address_hex, 16)
        while address_int > 0:
            digit = address_int % 58
            digit_char = alphabet[digit]
            b58_string = digit_char + b58_string
            address_int //= 58
        ones = leading_zeros // 2
        for one in range(ones):
            b58_string = '1' + b58_string
        return b58_string

    @staticmethod
    def private_to_public(private_key, is_print=False):
        pk_bytes = codecs.decode(private_key, 'hex')

        key = ecdsa.SigningKey.from_string(pk_bytes, curve=ecdsa.SECP256k1).verifying_key
        key_bytes = key.to_string()
        key_hex = codecs.encode(key_bytes, 'hex')
        btc_byte = b'04'
        public_key = btc_byte + key_hex

        if is_print:
            print(public_key.decode('utf-8'))

        return public_key.decode('utf-8')

    @staticmethod
    def public_key_to_addr(key):
        public_key_bytes = codecs.decode(key, 'hex')
        sha256_bpk = hashlib.sha256(public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()

        ripemd160_bpk = hashlib.new('ripemd160')
        ripemd160_bpk.update(sha256_bpk_digest)
        ripemd160_bpk_digest = ripemd160_bpk.digest()
        ripemd160_bpk_hex = codecs.encode(ripemd160_bpk_digest, 'hex')

        network_byte = b'00'
        network_bitcoin_public_key = network_byte + ripemd160_bpk_hex
        network_bitcoin_public_key_bytes = codecs.decode(network_bitcoin_public_key, 'hex')

        sha256_2_nbpk_digest = hashlib.sha256(hashlib.sha256(network_bitcoin_public_key_bytes).digest()).digest()
        sha256_2_hex = codecs.encode(sha256_2_nbpk_digest, 'hex')
        checksum = sha256_2_hex[:8]

        address_hex = (network_bitcoin_public_key + checksum).decode('utf-8')
        address = Wallet.base58(address_hex)
        return address

    @staticmethod
    def bech32_address_from_compressed_publkey(compressed_publkey, network):
        if network is NETWORKS.BITCOIN:
            hrp = 'bc'
        elif network is NETWORKS.TESTNET:
            hrp = 'tb'
        else:
            prRed("bech32_address_from_compressed_publkey:\n[WRONG NETWORK TYPE]")
            return
        witver = 0

        sha256 = hashlib.sha256(bytes.fromhex(compressed_publkey))
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256.digest())
        witprog = ripemd160.digest()
        print(witprog.hex())

        bech32_addr = bech32.encode(hrp, witver, witprog)
        return bech32_addr

    @staticmethod
    def private_key_to_addr(key):
        return Wallet.public_key_to_addr(Wallet.private_to_public(key))

    @staticmethod
    def priv_to_WIF(key):
        vers_key = "80" + key
        hash_1 = hashlib.sha256(binascii.unhexlify(vers_key)).hexdigest()
        hash_2 = hashlib.sha256(binascii.unhexlify(hash_1)).hexdigest()
        wif = vers_key + str(hash_2)[:8]
        base_wif = base58.b58encode(binascii.unhexlify(wif))
        wif = base_wif.decode('utf-8')
        return wif

    @staticmethod
    def WIF_to_priv(privkey):
        base_decoded = base58.b58decode(privkey).hex()
        versioned_key = base_decoded[:-8]
        checksum = base_decoded[-8:]
        sha_1 = hashlib.sha256(binascii.unhexlify(versioned_key)).digest()
        sha_2 = hashlib.sha256(sha_1).hexdigest()
        ver_checksum = sha_2[:8]
        if checksum != ver_checksum:
            return None
        private_key = versioned_key[2:]
        return private_key

    @staticmethod
    def publkey_hash_from_addr(address):
        publkey_hash = None
        try:
            publkey_hash = base58.b58decode_check(address)[1:].hex()
        except Exception as e:
            prRed("publkey_hash_from_addr:")
            prRed(e)
        return publkey_hash

    @staticmethod
    def compressed_publkey_from_publkey(publkey):
        raw_key = publkey[2:]

        x_key = raw_key[0:int(len(raw_key)/2)]
        y_key = raw_key[int(len(raw_key)/2):]

        if int(y_key, 16) % 2 == 0:
            prefix = '02'
        else:
            prefix = '03'
        compressed_key = prefix + x_key
        return compressed_key

    @staticmethod
    def uncompress_publkey(compressed_publkey):
        def pow_mod(x, y, z):
            number = 1
            while y:
                if y & 1:
                    number = number * x % z
                y >>= 1
                x = x * x % z
            return number
        p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
        y_parity = int(compressed_publkey[:2]) - 2
        x = int(compressed_publkey[2:], 16)
        a = (pow_mod(x, 3, p) + 7) % p
        y = pow_mod(a, (p + 1) // 4, p)
        if y % 2 != y_parity:
            y = -y % p
        uncompressed_key = '04{:x}{:x}'.format(x, y)
        print(uncompressed_key)


    @staticmethod
    def sign_message(message, private_key):
        key_bytes = codecs.decode(private_key, 'hex')
        sk = ecdsa.SigningKey.from_string(key_bytes, curve=ecdsa.SECP256k1)
        signed_msg = sk.sign(message.encode('utf-8'))
        return (signed_msg.hex(), Wallet.private_to_public(private_key))

    @staticmethod
    def get_hashed_pbk_from_addr(addr):
        a = addr
        if a[0:2] in ('bc', 'tb'):
            lul, decoded = bech32.decode(a[0:2], a)
            hashed_pbk = "".join(list(map('{:02x}'.format, decoded)))
        else:
            hashed_pbk = base58.b58decode_check(a)[1:].hex()
        return hashed_pbk

    @staticmethod
    def bech32_addr_from_privkey(privkey, network):
        publkey = Wallet.private_to_public(privkey)
        compressed_publkey = Wallet.compressed_publkey_from_publkey(publkey)
        bech32_addr = Wallet.bech32_address_from_compressed_publkey(compressed_publkey, network)
        return bech32_addr

    @staticmethod
    def verify_message(message, public_key, signature):
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key[2:]), curve=ecdsa.SECP256k1)
        return (vk.verify(bytes.fromhex(signature), message.encode('utf-8')))

prkey = 'fb6cd59c1c9d8113eed551cf92e565f80cc646eb0a895792831496f421cf5fed'

pbk = Wallet.private_to_public(prkey)
print(pbk)
pbk_c = Wallet.compressed_publkey_from_publkey(pbk)
Wallet.bech32_address_from_compressed_publkey(pbk_c, NETWORKS.BITCOIN)
print(pbk_c)
sw_address = 'bc1qfxdgu3tt6x5jpls9s6y3nzk9f7yjczwvn6wetl'
wtf, pbk_hash = bech32.decode('bc', sw_address)
print(pbk_hash)
hex_str = "".join(list(map('{:02x}'.format, pbk_hash)))

print(hex_str)
after_decode = '[73, 154, 142, 69, 107, 209, 169, 32, 254, 5, 134, 137, 25, 138, 197, 79, 137, 44, 9, 204]'