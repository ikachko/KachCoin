import hashlib
import ecdsa
import codecs
import binascii
import base58

from key_generator import KeyGenerator
from globals import WALLET_PRIVKEY_FILE
from colored_print import prRed
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
    def sign_message(message, private_key):
        key_bytes = codecs.decode(private_key, 'hex')
        sk = ecdsa.SigningKey.from_string(key_bytes, curve=ecdsa.SECP256k1)
        signed_msg = sk.sign(message.encode('utf-8'))
        return (signed_msg.hex(), Wallet.private_to_public(private_key))

    @staticmethod
    def verify_message(message, public_key, signature):
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key[2:]), curve=ecdsa.SECP256k1)
        return (vk.verify(bytes.fromhex(signature), message.encode('utf-8')))
