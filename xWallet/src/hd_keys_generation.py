import bip39
import hashlib
import hmac
import ecdsa
import struct
import codecs
import binascii
import base58

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


def get_master_key(seed: bytes) -> (int, bytes):
    l = hmac.new(key=b'Bitcoin seed', msg=seed, digestmod=hashlib.sha512).digest()

    I_L = l[:(len(l)//2)]
    I_R = l[(len(l)//2):]

    key = parse_256(I_L)
    if key == 0 or key >= curve_order:
        return None
    return key, I_R


def extend_key(version: str, depth: int, fingerprint: bytes, child_number: int, chain_code: bytes, key):
    serialized = b''
    if version == 'main_public':
        serialized += binascii.unhexlify('0488B21E')
    elif version == 'main_private':
        serialized += binascii.unhexlify('0488ade4')
    elif version == 'testnet_public':
        serialized += binascii.unhexlify('043587CF')
    elif version == 'testnet_private':
        serialized += binascii.unhexlify('04358394')
    else:
        print("Wrong version!")
        print("Versions: ['main_public', 'main_private', 'testnet_public', 'testnet_private']")
        return None
    # Depth
    serialized += struct.pack("<B", depth)

    # Fingerprint
    if depth != 0:
        serialized += fingerprint
    else:
        serialized += struct.pack("<I", 0)

    # Child number
    if depth != 0:
        serialized += ser_32(child_number)
    else:
        serialized += struct.pack("<I", 0)

    # Chain code
    serialized += chain_code

    # Key
    if version in ('main_public', 'testnet_public'):
        serialized += ser_p(key)
    else:
        serialized += (binascii.unhexlify('00') + ser_256(key))
    print('----')
    print(serialized)
    print('----')
    h = hashlib.sha256(hashlib.sha256(serialized).digest()).digest()
    return base58.b58encode_check(serialized)

def hash160(x_bytes):
    sha_hash = hashlib.sha256(x_bytes).digest()
    ripemd160_h = hashlib.new('ripemd160')
    ripemd160_h.update(sha_hash)

    hashed_x = ripemd160_h.digest()
    return hashed_x


def N(params: (int, bytes)):
    K = point(params[0])
    c = params[1]
    return K, c


# Test Vector 1

test_seed = '000102030405060708090a0b0c0d0e0f'

test_key, test_c = get_master_key(binascii.unhexlify(test_seed))
test_pbk = point(test_key)

# Chain m

m_ext_pub = extend_key('main_public', 0, b'', 0, test_c, test_pbk)
m_ext_prv = extend_key('main_private', 0, b'', 0, test_c, test_key)

# print(m_ext_pub)
# print(m_ext_prv)

# Chain m/0h

fingerprint_m = hash160(binascii.unhexlify(str(test_pbk[0]) + str(test_pbk[1])))[:8]

# m_0h_pub, m_0h_pub_c = CKDpub((test_pbk, test_c), 1)
m_0h_pub, m_0h_pub_c = N((test_key, test_c))
m_0h_prk, m_0h_prk_c = CKDpriv((test_key, test_c), 1)

m_0h_ext_pub = extend_key('main_public', 1, fingerprint_m, 2**31, m_0h_pub_c, m_0h_pub)
print(m_0h_ext_pub)

m_0h_ext_prk = extend_key('main_private', 1, fingerprint_m, 2**31, m_0h_prk_c, m_0h_prk)
print(m_0h_ext_prk)
'xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw'
'7JJikZhTDxNJQqVU4Kz2X1fCsPUYQtnH5HN96Q8F9bK83mVyip3UbKt1Urred3Gwx7DycCTLZNz5Fn6XsaTm9LUeAxNdos4jpv9ET9oPoK5CLk2nqKKBX'
