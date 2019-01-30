import hashlib
import codecs
import ecdsa

from wallet import Wallet
from colored_print import *
# TODO : Implement script.py

# P2PKH COMMANDS

OP_DUP = 0x76           # [TEST] lambda x = x x, Pop x and push 2 times x
OP_HASH256 = 0xaa       # [TEST] lambda x = hash256(x)
OP_HASH160 = 0xa9       # lambda x = hash160(x), Pop x and push hash160(x)
OP_CHECKSIG = 0xac      # lambda sig pubkey = ver
OP_VERIFY = 0x69        # Marks transaction as invalid if top stack value is not true. The top stack value is removed.
OP_EQUAL = 0x87         # [TEST] lambda x y = (x == y)
OP_EQUALVERIFY = 0x88   # Run OP_EQUAL and then OP_VERIFY

commands_tokens = [
    OP_DUP,
    OP_HASH256,
    OP_HASH160,
    OP_CHECKSIG,
    OP_VERIFY,
    OP_EQUAL,
    OP_EQUALVERIFY
]

ops = [0] * 256

def op_equal(stack):
    try:
        a = stack.pop()
        b = stack.pop()
        stack.append((a == b))
        return stack
    except Exception as e:
        prRed("op_equal :")
        prRed(e)
        return False


def op_dup(stack):
    try:
        a = stack.pop()
        stack.append(a)
        stack.append(a)
        return stack
    except Exception as e:
        prRed("op_dup :")
        prRed(e)
        return False


def op_hash256(stack):
    try:
        x = stack.pop()
        x_bytes = codecs.decode(x, 'hex')
        hashed_x = hashlib.sha256(hashlib.sha256(x_bytes).digest()).hexdigest()
        stack.append(hashed_x)
        return stack
    except Exception as e:
        prRed("op_hash256 :")
        prRed(e)
        return False


def hash160(x):
    x_bytes = codecs.decode(x, 'hex')
    sha_hash = hashlib.sha256(x_bytes).hexdigest()
    ripemd160_h = hashlib.new('ripemd160')
    ripemd160_h.update(sha_hash.encode('utf-8'))

    hashed_x = ripemd160_h.hexdigest()
    return hashed_x


def op_hash160(stack):
    try:
        x = stack.pop()
        hashed_x = hash160(x)
        stack.append(hashed_x)
        return stack
    except Exception as e:
        prRed("op_hash160 :")
        prRed(e)
        return False

def op_chechsig(stack):
    try:
        pk = stack.pop()
        sign = stack.pop()
        message = stack.pop()

        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(pk[2:]), curve=ecdsa.SECP256k1)
        verify = vk.verify(bytes.fromhex(sign), message.encode('utf-8'))

        stack.append(verify)
        return stack
    except Exception as e:
        prRed("op_chechsig :")
        prRed(e)

def op_verify(stack):
    try:
        x = stack.pop()
        if not bool(x):
            return False
    except Exception as e:
        prRed("op_verify :")
        prRed(e)

def op_equalverify(stack):
    try:
        a = stack.pop()
        b = stack.pop()

        if a != b:
            return False
        return stack
    except Exception as e:
        prRed("op_equalverify :")
        prRed(e)
# ops[OP_EQUAL] = op_equal
# ops[OP_DUP] = op_dup
# ops[OP_HASH256] = op_hash256
# ops[OP_CHECKSIG] = op_chechsig

# Transaction puzzle

scriptPubKey = hex(OP_HASH256) + " 6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000 " + hex(OP_EQUAL)
scriptSig = 'a4bfa8ab6435ae5f25dae9d89e4eb67dfa94283ca751f393c1ddc5a837bbc31b'

print(scriptPubKey)

def lexer(script):
    stack = []

    splitted = script.split(' ')

    for word in splitted:
        stack.append(word)
    return stack


pub_key_commands = lexer(scriptPubKey)
sig_commands = lexer(scriptSig)
commands = sig_commands + pub_key_commands

tokens_functors = {
    OP_CHECKSIG: op_chechsig,
    OP_DUP: op_dup,
    OP_EQUAL: op_equal,
    OP_EQUALVERIFY: op_equalverify,
    OP_HASH160: op_hash160,
    OP_HASH256: op_hash256
}

str_tokens = {
    OP_CHECKSIG: "OP_CHECKSIG",
    OP_DUP: "OP_DUP",
    OP_EQUAL: "OP_EQUAL",
    OP_EQUALVERIFY: "OP_EQUALVERIFY",
    OP_HASH160: "OP_HASH160",
    OP_HASH256: "OP_HASH256"
}

def execute_stack(commands):
    stack = []
    i = 0
    for command in commands:
        prPurple(i)
        prCyan(stack)
        # prCyan(type(stack))
        if int(command, 16) in commands_tokens:
            op_code = int(command, 16)
            prLightPurple(str_tokens[op_code])
            stack = tokens_functors[op_code](stack)
            if not stack:
                prRed("Transaction is invalid. Token " + str_tokens[op_code] + " returned FALSE")
                return
        else:
            stack.append(command)
        i += 1
    return stack

prkey = '40a5911c18651321e23d845287d084e76d99d53ffc0ca86ef1a0ac711efd05f5'
pubkey = '046b8fd99422ec9915b20e8481b58fbba527f8dd2e15725025a8b7545773d8d433b73e572c8bc740ca5185fb92e88404aca9c884de96614be75e06b336693870e3'
pubKeyHash = hash160(pubkey)
message = "AAAAAAAAAAAAAA"

sig, public_key = Wallet.sign_message(message, prkey)

address = '1NaTVwXDDUJaXDQajoa9MqHhz4uTxtgK14'

scriptPubKeyList = [hex(OP_DUP), hex(OP_HASH160), pubKeyHash, hex(OP_EQUALVERIFY), hex(OP_CHECKSIG)]
scriptSigList = [message, sig, public_key]

scriptList = scriptSigList + scriptPubKeyList
script = ' '.join(scriptList)

stack = lexer(script)
res = execute_stack(stack)
print(res)
