import hashlib

def merkle(hash_list):
    while len(hash_list) < 4:
        hash_list.append(hash_list[-1])
    new_hash_list = []
    for list in hash_list:
        h_list = hashlib.sha256(list.encode('utf-8')).hexdigest()
        new_hash_list.append(h_list)
    return merkle_tree(new_hash_list)


def merkle_tree(hash_list):
    if len(hash_list) == 1:
        return hash_list[0]
    new_hash_list = []
    for i in range(0, len(hash_list)-1, 2):
        new_hash_list.append(hash2(hash_list[i], hash_list[i+1]))
    if len(hash_list) % 2 == 1:
        new_hash_list.append(hash2(hash_list[-1], hash_list[-1]))
    return merkle_tree(new_hash_list)


def hash2(a, b):
    s = (a + b).encode('utf-8')
    h = hashlib.sha256(hashlib.sha256(s).digest()).digest()
    return h.hex()
