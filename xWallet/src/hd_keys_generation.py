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
    return bytes.fromhex(('%064x' % p))


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
def CKDpriv(k_par: int, c_par: bytes, i: int):
    if i >= curve_order:
        l = hmac.new(key=c_par, msg=(b'\x00' + ser_256(k_par) + ser_32(i)), digestmod=hashlib.sha512).hexdigest()
    else:
        print(k_par)
        message = (ser_p(point(k_par)) + ser_32(i))
        l = hmac.new(key=c_par, msg=message, digestmod=hashlib.sha512).hexdigest()

    # print(len(l))
    I_L = bytes.fromhex(l[64:])
    I_R = l[:64]

    k_i = (parse_256(I_L) + k_par) % curve_order

    if parse_256(I_L) >= curve_order or k_i == 0:
        return None
    return k_i, I_R


# Public parent key → public child key
def CKDpub(k_par: (int, int), c_par: bytes, i: int):
    if i >= curve_order:
        return None
    else:
        l = hmac.new(key=c_par, msg=(ser_p(k_par) + ser_32(i)), digestmod=hashlib.sha512).hexdigest()

    I_L = l[64:]
    I_R = bytes.fromhex(l[:64])

    if parse_256(I_L) >= curve_order:
        return None

    k_ch = add_points(point(parse_256(I_L)), k_par)
    return k_ch, I_R


mnemonic_words = bip39.generate_mnemonic_words()
seed = bip39.mnemonic_to_seed(mnemonic_words)
# print(len(seed))
k = seed[:(len(seed)//2)]
c = seed[(len(seed)//2):]

# print(seed)
layer_0 = CKDpriv(int(k, 16), bytes.fromhex(c), (2**31 + 3))
layer_1 = CKDpriv(layer_0[0], layer_0[1], 2)
key = CKDpriv(layer_1[0], layer_1[1], 5)
print(key)
