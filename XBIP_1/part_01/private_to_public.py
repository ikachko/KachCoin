import ecdsa

private_key = '0a56184c7a383d8bcce0c78e6e7a4b4b161b2f80a126caa48bde823a4625521f'

def privateKeyToPublicKey(s):
    sk = ecdsa.SigningKey.from_string(s.decode('hex'), curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    return ('\04' + sk.verifying_key.to_string()).encode('hex')

uncompressed_public_key = privateKeyToPublicKey(private_key)
