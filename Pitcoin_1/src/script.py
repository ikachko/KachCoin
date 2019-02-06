import hashlib
import codecs
import ecdsa

from wallet import Wallet
from colored_print import *
from serializer import get_varint

# TODO : Implement script.py

# P2PKH COMMANDS

OP_DUP = 0x76           # [TEST] lambda x = x x, Pop x and push 2 times x
OP_HASH256 = 0xaa       # [TEST] lambda x = hash256(x)
OP_HASH160 = 0xa9       # lambda x = hash160(x), Pop x and push hash160(x)
OP_CHECKSIG = 0xac      # lambda sig pubkey = ver
OP_VERIFY = 0x69        # Marks transaction as invalid if top stack value is not true. The top stack value is removed.
OP_EQUAL = 0x87         # [TEST] lambda x y = (x == y)
OP_EQUALVERIFY = 0x88   # Run OP_EQUAL and then OP_VERIFY

OP_PUSHDATA = [i for i in range(1, 75)]

commands_tokens = [
    OP_DUP,
    OP_HASH256,
    OP_HASH160,
    OP_CHECKSIG,
    OP_VERIFY,
    OP_EQUAL,
    OP_EQUALVERIFY
]

hex_str_tokens = {
    OP_CHECKSIG: "OP_CHECKSIG",
    OP_DUP: "OP_DUP",
    OP_EQUAL: "OP_EQUAL",
    OP_EQUALVERIFY: "OP_EQUALVERIFY",
    OP_HASH160: "OP_HASH160",
    OP_HASH256: "OP_HASH256"
}

str_tokens = {
    OP_CHECKSIG: "ac",
    OP_DUP: "76",
    OP_EQUAL: "87",
    OP_EQUALVERIFY: "88",
    OP_HASH160: "a9",
    OP_HASH256: "aa"
}


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


tokens_functors = {
    OP_CHECKSIG: op_chechsig,
    OP_DUP: op_dup,
    OP_EQUAL: op_equal,
    OP_EQUALVERIFY: op_equalverify,
    OP_HASH160: op_hash160,
    OP_HASH256: op_hash256
}


# ops[OP_EQUAL] = op_equal
# ops[OP_DUP] = op_dup
# ops[OP_HASH256] = op_hash256
# ops[OP_CHECKSIG] = op_chechsig

# Transaction puzzle

scriptPubKey = hex(OP_HASH256) + " 6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000 " + hex(OP_EQUAL)
scriptSig = 'a4bfa8ab6435ae5f25dae9d89e4eb67dfa94283ca751f393c1ddc5a837bbc31b'


def lexer(script):
    commands_list = []
    prRed(script)
    i = 0
    while i < len(script):
        plus_i = 2
        ch = script[i:i + 2]
        # prGreen(commands_list)
        # prGreen(int(ch, 16))
        prRed(ch)
        if int(ch, 16) in commands_tokens:
            prRed("COMMAND " + str_tokens[int(ch, 16)])
            commands_list.append(ch)
        else:
            plus_i, varint = get_varint(script[i:])
            slice = script[i + 2:i + 2 + varint]
            prYellow("SLICE " + slice)
            prGreen("PLUS I " + str(plus_i))
            if slice:
                commands_list.append(slice)
            plus_i += varint
        i += plus_i
    return commands_list


# pub_key_commands = lexer(scriptPubKey)
# sig_commands = lexer(scriptSig)
# commands = sig_commands + pub_key_commands

def execute_stack(commands):
    stack = []
    i = 0
    for command in commands:
        if int(command, 16) in commands_tokens:
            op_code = int(command, 16)
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

# stack = lexer(script)
# res = execute_stack(stack)
# print(res)

script_str = '9a01fd3046022100b408d547ffe841d869e8287414930600ce43bc68827b41c703a36539772ad53b0221008e5bb700fa4163cbb11af95c6b9dc50a8c8f6a1dd700dba2ac296645cf9dc932303182303466386132353665323631383664653561626634373337356437333730333466303034376166653530393330623532306466363831636636323061366238616464366531343131366139333333656266633639353734376561666534396637373732306533623335643031336639336430636139346236653166363134666263313276a914e6cb7a9ee8ced98297292b40aadadc964ad1e60688ac'
script_list = lexer(script_str)
print(script_list)