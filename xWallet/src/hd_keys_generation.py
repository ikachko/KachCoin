import bip39
import hashlib
import hmac
import ecdsa
import struct
import codecs

curve_order = 347376267711948586270712955026063723559809953996921692118372752023745174652793


def ser_32(i: int) -> bytes:
    return struct.pack("<I", i)


def ser_256(p: int) -> bytes:
    s = (('%064x' % int(hex(p)[2:66], 16)))
    return bytes.fromhex(s)


def ser_p(P: (int, int)) -> bytes:
    if P[1] % 2 == 0:
        prefix = b'\x02'
    else:
        prefix = b'\x03'
    return prefix + ser_256(P[0])


def parse_256(p: bytes) -> int:
    return int.from_bytes(p, byteorder='big', signed=False)


def point(p: int) -> (int, int):
    sk = ecdsa.SigningKey.from_string(ser_256(p), curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    return vk.pubkey.point.x(), vk.pubkey.point.y()


def add_points(a: (int, int), b: (int, int)):
    return (a[0] + b[0]), (a[1] + b[1])


# Private parent key → private child key
def CKDpriv(m: (int, bytes), i: int) -> (int, bytes):
    k_par = m[0]
    c_par = m[1]
    if i >= 2**31:
        l = hmac.new(key=c_par, msg=(b'0x00' + ser_256(k_par) + ser_32(i)), digestmod=hashlib.sha512).digest()
    else:
        message = (ser_p(point(k_par)) + ser_32(i))
        l = hmac.new(key=c_par, msg=message, digestmod=hashlib.sha512).digest()

    I_L = l[:(len(l) // 2)]
    I_R = l[(len(l) // 2):]

    k_i = parse_256(I_L) + k_par % curve_order

    if parse_256(I_L) >= curve_order or k_i == 0:
        return None
    return k_i, I_R


# Public parent key → public child key
def CKDpub(M: ((int, int), bytes), i: int):
    k_par = M[0]
    c_par = M[1]
    if i >= 2**31:
        return None
    else:
        l = hmac.new(key=c_par, msg=(ser_p(k_par) + ser_32(i)), digestmod=hashlib.sha512).digest()

    I_L = l[:(len(l) // 2)]
    I_R = l[(len(l) // 2):]

    if parse_256(I_L) >= curve_order:
        return None

    k_ch = add_points(point(parse_256(I_L)), k_par)
    return k_ch, I_R


def get_master_key(seed: str) -> (int, bytes):
    l = hmac.new(key=b'Bitcoin seed', msg=seed.encode(), digestmod=hashlib.sha512).digest()

    I_L = l[:(len(l)//2)]
    I_R = l[(len(l)//2):]

    key = parse_256(I_L)
    if key == 0 or key >= curve_order:
        return None
    return key, I_R


def extend_key(version: str, depth: int, fingerprint: bytes, child_number: int, chain_code: bytes, key):
    serialized = b''
    if version == 'main_public':
        serialized += bytes.fromhex('0488B21E')
    elif version == 'main_private':
        serialized += bytes.fromhex('0488ADE4')
    elif version == 'testnet_public':
        serialized += bytes.fromhex('043587CF')
    elif version == 'testnet_private':
        serialized += bytes.fromhex('04358394')

    # Depth
    serialized += struct.pack("<B", depth)

    # Fingerprint
    if depth != 0:
        serialized += fingerprint
    else:
        serialized += bytes(4)

    # Child number
    if depth != 0:
        serialized += ser_32(child_number)
    else:
        serialized += bytes(4)

    # Chain code
    serialized += chain_code

    # Key
    if version in ('main_public', 'testnet_public'):
        serialized += ser_p(key)
    else:
        serialized += (bytes(1) + ser_256(key))

    return serialized

def hash160(x_bytes):
    sha_hash = hashlib.sha256(x_bytes).digest()
    ripemd160_h = hashlib.new('ripemd160')
    ripemd160_h.update(sha_hash)

    hashed_x = ripemd160_h.digest()
    return hashed_x

import base58

test_seed = '000102030405060708090a0b0c0d0e0f'

test_key, test_c = get_master_key(test_seed)

version = 'main_private'
depth = 0
extended_key = extend_key(version, depth, b'', 0, test_c, test_key)
serialized = base58.b58encode(extended_key.hex())

print(extended_key.hex())
print(serialized.hex())
# mnemonic_words = bip39.generate_mnemonic_words()
# seed = bip39.mnemonic_to_seed(mnemonic_words)
#
# key, c = get_master_key(seed)


# l_0 = CKDpriv((key, c), 2**31 + 3)
# print('private key layer 0: ', l_0)
# l_1 = CKDpriv(l_0, 2)
# print('private key layer 1: ', l_1)
# l_2 = CKDpriv(l_1, 5)
# print('private key layer 2: ', l_2)
#
# pbk = point(key)
# l_p_0 = CKDpub((pbk, c), 3)
# print('public key layer 0: ', l_p_0)
# l_p_1 = CKDpub(l_p_0, 2)
# print('public key layer 1: ', l_p_1)
# l_p_2 = CKDpub(l_p_1, 5)
# print('public key layer 1: ', l_p_2)





# print(len(seed))
# k = seed[:(len(seed)//2)]
# c = seed[(len(seed)//2):]
#
# print(seed)
# layer_0 = CKDpriv(int(k, 16), bytes.fromhex(c), (2**31 + 3))
# layer_1 = CKDpriv(layer_0[0], layer_0[1], 2)
# key = CKDpriv(layer_1[0], layer_1[1], 5)
# print(key)
