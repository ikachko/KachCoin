import Crypto
from Crypto.Hash import SHA256, SHA, SHA512

fname = 'msg'
with open(fname) as f:
    message = f.read()
print(message)
