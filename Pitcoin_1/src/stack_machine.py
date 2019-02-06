import ecdsa
import codecs
import hashlib

from colored_print import *
from tx import *

OP_DUP = 0x76           # [TEST] lambda x = x x, Pop x and push 2 times x
OP_HASH256 = 0xaa       # [TEST] lambda x = hash256(x)
OP_HASH160 = 0xa9       # [TEST] lambda x = hash160(x), Pop x and push hash160(x)
OP_CHECKSIG = 0xac      # [TEST] lambda sig pubkey = ver
OP_VERIFY = 0x69        # [TEST] Marks transaction as invalid if top stack value is not true. The top stack value is removed.
OP_EQUAL = 0x87         # [TEST] lambda x y = (x == y)
OP_EQUALVERIFY = 0x88   # [TEST] Run OP_EQUAL and then OP_VERIFY

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


def stack_parser(script_str):
    stack = []

    i = 0
    while i < len(script_str):
        ch = script_str[i:i + 2]
        if int(ch, 16) in commands_tokens:
            stack.append(ch)
            i += 2
        else:
            plus_i, varint = get_varint(script_str[i:])
            i += plus_i

            data = script_str[i:i + (varint * 2)]
            stack.append(data)
            i += len(data)
    return stack


def get_message_from_sw_tx(tx):
    deserialized_tx = raw_deserialize(tx)
    in_txs = b''
    for in_tx in deserialized_tx['inputs']:
        in_txs += bytes.fromhex(flip_byte_order(in_tx['txid']))
        in_txs += struct.pack("<L", in_tx['tx_index'])
        in_txs += struct.pack("<B", int((deserialized_tx['outputs'][0]['pk_script_length'] / 2)))
        in_txs += bytes.fromhex(deserialized_tx['outputs'][0]['pk_script'])
        in_txs += bytes.fromhex(in_tx['sequence'])

    out_txs = b''
    for out_tx in deserialized_tx['outputs']:
        out_txs += struct.pack("<Q", out_tx['value'])
        out_txs += struct.pack("<B", int((out_tx['pk_script_length'] / 2)))
        out_txs += bytes.fromhex(out_tx['pk_script'])

    prRed(deserialized_tx['locktime'])
    msg = (
        struct.pack("<L", deserialized_tx['version'])
        + struct.pack("<B", 0)
        + struct.pack("<B", 1)
        + struct.pack("<B", deserialized_tx['input_count'])
        + in_txs
        + struct.pack("<B", deserialized_tx['output_count'])
        + out_txs
        + struct.pack("<L", deserialized_tx['locktime'])
        + struct.pack("<L", 1)
    )
    return msg


def validate_transaction(tx):
    deserialized = raw_deserialize(tx)

    witness_data = []
    if deserialized['is_sw']:
        for witness in deserialized['witness']:
            prYellow(witness)
            witness_to_add = []
            for w in witness:
                witness_data.append(w)
            witness_data += witness_to_add

    message = get_message_from_sw_tx(tx).hex()






# parsed_stack = stack_parser(pk_script)
# print(parsed_stack)
# execute_stack(parsed_stack)

sw_tx = '01000000000101d98232d9db6fc89777eb011f0077585c34c644ffda76b3b2a2b5667fd9a12c3e0100000000ffffffff02a0860100000000001976a914ef08298d2a5312687de8544f6a9f69ac78eb804088ac60ae0a00000000001976a9149f5e9ced489eb7ed8157b533e4199aad1a9b50b288ac0247304402203e311e594a6bbc7d9517f036fe67f17f6cde40e3d6fe32dcc5cb8bc4376f6a93022036ac1c425b3e0fb3e85763dfeeafce45b9c34bcc3a52051df114c0e441b781b9012102c3c6a89e01b4b62621233c8e0c2c26078a2449abaa837e18f96a1f65d7b8cc8c00000000'
validate_transaction(sw_tx)

print(get_message_from_sw_tx(sw_tx).hex())

# old_tx = '0100000001d98232d9db6fc89777eb011f0077585c34c644ffda76b3b2a2b5667fd9a12c3e010000006a473044022075b394b3da94b069dd0174c9c99f551e27f8817cc9a3acd15a45a40e5bde5ae102203fc7bb2b1dfe7cd4bef0aca029fbb73cdfcc0e9eb67e1161495853b79defd194012102c3c6a89e01b4b62621233c8e0c2c26078a2449abaa837e18f96a1f65d7b8cc8cffffffff02a0860100000000001976a914ef08298d2a5312687de8544f6a9f69ac78eb804088ac60ae0a00000000001976a9149f5e9ced489eb7ed8157b533e4199aad1a9b50b288ac00000000'
# validate_transaction(old_tx)