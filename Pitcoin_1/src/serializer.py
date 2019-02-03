# TODO: Byte serialization and deserialization (optional)
from colored_print import *

class Serializer:
    @staticmethod
    def serialize(num_of_coins, sender_addr, recipient_addr, sender_public_key, signature):
        return (
            '%04x' % num_of_coins +
            sender_addr +
            recipient_addr +
            sender_public_key +
            signature
        )


class Deserializer:
    @staticmethod
    def deserialize(transaction):
        num_of_coins = int(transaction[0:4], 16)
        send_addr = transaction[4:38]
        recipient_addr = transaction[38:72]
        pub_key = transaction[72:202]
        signature = transaction[202:]
        return dict({
            'num_of_coins': num_of_coins,
            'sender_addr': send_addr,
            'recepient_addr': recipient_addr,
            'public_key': pub_key,
            'signature': signature
                    })


transaction = '01000000017967a5185e907a25225574544c31f7b059c1a191d65b53dcc1554d339c4f9efc010000006a47304402206a2eb16b7b92051d0fa38c133e67684ed064effada1d7f925c842da401d4f22702201f196b10e6e4b4a9fff948e5c5d71ec5da53e90529c8dbd122bff2b1d21dc8a90121039b7bcd0824b9a9164f7ba098408e63e5b7e3cf90835cceb19868f54f8961a825ffffffff014baf2100000000001976a914db4d1141d0048b1ed15839d0b7a4c488cd368b0e88ac00000000'

version = transaction[0:4]
# prRed(str(len('47304402206a2eb16b7b92051d0fa38c133e67684ed064effada1d7f925c842da401d4f22702201f196b10e6e4b4a9fff948e5c5d71ec5da53e90529c8dbd122bff2b1d21dc8a90121039b7bcd0824b9a9164f7ba098408e63e5b7e3cf90835cceb19868f54f8961a825')))


def swap_bits_in_str(str):
    tmp = ''
    for i in range(0, len(str), 2):
        tmp = str[i] + str[i + 1] + tmp
    return tmp


def get_varint(str):
    if str.startswith('fd'):
        length = 6
    elif str.startswith('fe'):
        length = 10
    elif str.startswith('ff'):
        length = 18
    else:
        return 2, int((str[0:2]), 16)
    swapped_str = swap_bits_in_str(str[2:length])
    # print(str)
    # print(length)
    # print((str[2:length]))
    return length, int(swapped_str, 16)

def make_varint(num):
    if num <= 0xfc:
        return swap_bits_in_str('%02x' % num)
    elif num <= 0xffff:
        return swap_bits_in_str('fd%04x' % num)
    elif num <= 0xffffffff:
        return swap_bits_in_str('fe%08x' % num)
    elif num <= 0xffffffffffffffff:
        return swap_bits_in_str('ff%016x' % num)


num = 106
num_fd = 550
num_fe = 998000

varint = make_varint(num)
varint_fd = make_varint(num_fd)
varint_fe = make_varint(num_fe)

def serialize(version, inputs, outputs, locktime):
    serialized_tx = ''

    # Version
    serialized_tx += '%08x' % version

    # Input Count
    inputs_count = len(inputs)
    serialized_tx += make_varint(inputs_count)

    # Input(s)
    for input in inputs:
        # TXID
        tx_id = swap_bits_in_str(input.prev_output_hash)
        serialized_tx += tx_id

        # VOUT
        vout = swap_bits_in_str(input.prev_output_idx)
        serialized_tx += vout

        # ScriptSig Size
        script_sig_size = make_varint(input.script_length)
        serialized_tx += script_sig_size

        # ScriptSig
        serialized_tx += input.sign_script

        # Sequence
        serialized_tx += input.sequence

    # Output Count
    outputs_count = len(outputs)
    serialized_tx += make_varint(outputs_count)

    # Output(s)
    for output in outputs:
        # Value
        value = swap_bits_in_str('%04x' % output.value)
        serialized_tx += value

        # ScriptPubKey Size
        script_pubkey_size = make_varint(output.script_length)
        serialized_tx += script_pubkey_size

        # ScriptPubKey
        serialized_tx += output.pubkey_script

    serialized_tx += swap_bits_in_str('%04x' % locktime)


def deserialize(serialized_tx):

    transaction_dict = dict()
    i = 0

    # Version
    transaction_dict['version'] = int(swap_bits_in_str(serialized_tx[0:8]), 16)
    i += 8

    # Input Count Varint
    in_count_varint_size, in_count = get_varint(serialized_tx[i:])
    transaction_dict['input_count'] = in_count
    i += in_count_varint_size

    # Input(s)
    transaction_dict['inputs'] = dict()
    for idx in range(transaction_dict['input_count']):
        transaction_dict['inputs'][idx] = dict()

        # TXID
        transaction_dict['inputs'][idx]['txid'] = swap_bits_in_str(serialized_tx[i:i + 64])
        i += 64

        # VOUT
        transaction_dict['inputs'][idx]['vout'] = swap_bits_in_str(serialized_tx[i:i + 8])
        i += 8

        # ScriptSig Size
        sig_varint_size, sig_size = get_varint(serialized_tx[i:])
        transaction_dict['inputs'][idx]['script_sig_size'] = sig_size
        i += sig_varint_size

        # ScriptSig
        transaction_dict['inputs'][idx]['script_sig'] = serialized_tx[i:i + (sig_size * 2)]
        i += (sig_size * 2)

        # Sequence
        transaction_dict['inputs'][idx]['sequence'] = serialized_tx[i:i + 8]
        i += 8

    # Output Count
    out_count_varint_size, out_count = get_varint(serialized_tx[i:])
    transaction_dict['output_count'] = out_count
    i += out_count_varint_size

    # Output(s)
    transaction_dict['outputs'] = dict()
    for idx in range(transaction_dict['output_count']):
        transaction_dict['outputs'][idx] = dict()

        # Values
        transaction_dict['outputs'][idx]['value'] = swap_bits_in_str(serialized_tx[i:i + 16])
        i += 16

        # ScriptPubKey Size
        script_varint_size, script_size = get_varint(serialized_tx[i:])
        transaction_dict['outputs'][idx]['script_pubkey_size'] = script_size
        i += script_varint_size

        # ScriptPubKey
        transaction_dict['outputs'][idx]['script_pubkey'] = serialized_tx[i:i + (script_size * 2)]
        i += (script_size * 2)

    # Locktime
    transaction_dict['locktime'] = int(swap_bits_in_str(serialized_tx[i:i + 8]), 16)

    return transaction_dict


tx_dict = deserialize(transaction)
# print(tx_dict)