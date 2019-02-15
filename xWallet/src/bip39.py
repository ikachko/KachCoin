import hashlib
import secrets


def get_mnemnonic_words():
    f = open('../mnemonic_list_english.txt', 'r')
    words = f.read().split('\n')
    f.close()
    return words


def mnemonic_to_seed(words):
    salt = 'mnemonic'
    sequence = ''.join(words)
    seed = hashlib.pbkdf2_hmac('sha512', str.encode(sequence), str.encode(salt), 2048)
    return seed


def generate_mnemonic_words():
    words = get_mnemnonic_words()

    entropy = secrets.randbits(128)
    entropy_bits = format(entropy, '0128b')
    h = hashlib.sha256(hashlib.sha256(hex(entropy).encode()).digest()).digest()
    h_bits = format(int(h.hex(), 16), '0256b')
    checksum = h_bits[:(len(entropy_bits)//32)]
    entropy_bits += checksum
    words_seed = []
    for i in range(0, len(entropy_bits), 11):
        words_seed.append(words[int(entropy_bits[i:i+11], 2)])
    return words_seed
