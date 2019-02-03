from block import Block

from colored_print import prRed, prGreen, prCyan, prLightPurple

# TODO : Create tests for
# block.py
# blockchain.py
# merkle.py
# pending_pool.py
# serializer.py
# transaction.py
# tx_validator.py
# wallet.py

def block_test():
    transactions = ["",
                    "0032000000000000000000000000000000000013S1c17McFscyQrpo1ZjYk8WMAh4UsYdNs049d83ee5a724cb0ca0a48de08af64bc9d774173b961047c004b89c27d9b31199ea44df0e69098b37afcbc6864bdf23226d64fff630ec7f717573b6d20cefb85f929a0a8378a2312403e18964054a77e3885138198aa9977b351a1af5167574ed757ce304418db0830f30380f48433a95fd67cd1d1d66038044a2b0158374a5b59",
                    "0032000000000000000000000000000000000013S1c17McFscyQrpo1ZjYk8WMAh4UsYdNs049d83ee5a724cb0ca0a48de08af64bc9d774173b961047c004b89c27d9b31199ea44df0e69098b37afcbc6864bdf23226d64fff630ec7f717573b6d20cefb85f929a0a8378a2312403e18964054a77e3885138198aa9977b351a1af5167574ed757ce304418db0830f30380f48433a95fd67cd1d1d66038044a2b0158374a5b59",
                    "0032000000000000000000000000000000000013S1c17McFscyQrpo1ZjYk8WMAh4UsYdNs049d83ee5a724cb0ca0a48de08af64bc9d774173b961047c004b89c27d9b31199ea44df0e69098b37afcbc6864bdf23226d64fff630ec7f717573b6d20cefb85f929a0a8378a2312403e18964054a77e3885138198aa9977b351a1af5167574ed757ce304418db0830f30380f48433a95fd67cd1d1d66038044a2b0158374a5b59"]
    timestamp = 1548768810
    prev_hash = "e5f49583628105035f0295d1ad31000a97fde17b2dbc053c9936f7c1d4f783be"
    nonce = 561
    block = Block(timestamp=timestamp, previous_hash=prev_hash, transactions=transactions, nonce=nonce)

    test_hash_block = "00297a00e77761f46c98f8515a17b3a4e8eaf1340db8ae6719c3fec3f15c90d5"
    block_hash = block.hash_block()

    prLightPurple('----------------------------------')
    prCyan("BLOCK TEST START:")

    if test_hash_block != block_hash:
        prRed("BLOCK TEST 1 [KO] - WRONG BLOCK HASH")
    else:
        prGreen("BLOCK TEST 1 [OK]")

    test_merkle_root = "383acaff48cc4368e25635c7798c8de10408345c937f68fe36a041007c8a6999"
    block_merkle_root = block.merkle_root

    if test_merkle_root != block_merkle_root:
        prRed("BLOCK TEST 2 [KO] - WRONG MERKLE ROOT")
    else:
        prGreen("BLOCK TEST 2 [OK]")

    block_dict = block.to_dict()

    if block_dict['nonce'] != nonce:
        prRed("BLOCK TEST 3 [KO] - WRONG NONCE IN DICTIONARY")
    else:
        prGreen("BLOCK TEST 3 [OK]")

    if block_dict['previous_hash'] != prev_hash:
        prRed("BLOCK TEST 4 [KO] - WRONG PREVIOUS HASH IN DICTIONARY")
    else:
        prGreen("BLOCK TEST 4 [OK]")

    if block_dict['transactions'] != transactions:
        prRed("BLOCK TEST 5 [KO] - WRONG TRANSACTIONS IN DICTIONARY")
    else:
        prGreen("BLOCK TEST 5 [OK]")

    if block_dict['timestamp'] != timestamp:
        prRed("BLOCK TEST 6 [KO] - WRONG TIMESTAMP IN DICTIONARY")
    else:
        prGreen("BLOCK TEST 6 [OK]")

    if block_dict['merkle_root'] != block_merkle_root:
        prRed("BLOCK TEST 7 [KO] - WRONG MERKLE ROOT IN DICTIONARY")
    else:
        prGreen("BLOCK TEST 7 [OK]")

    if block_dict['block_hash'] != block_hash:
        prRed("BLOCK TEST 8 [KO] - WRONG NONCE IN DICTIONARY")
    else:
        prGreen("BLOCK TEST 8 [OK]")
    prLightPurple('----------------------------------')


def full_tests():
    block_test()


if __name__ == '__main__':
    full_tests()
