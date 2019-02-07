import os

project_path = os.path.dirname(os.path.realpath(__file__))

path_dirs = project_path.split('/')
project_path = "/".join(path_dirs[:-1])

BLOCKS_DIRECTORY = project_path + '/blocks/'

BLOCKS_LENGTH_FILE = project_path + '/blocks/length'

MINER_NODES = project_path + '/miner_data/nodes'

MINER_NETWORK_DATA = project_path + '/miner_data/network_data'

MINER_PRIVKEY_FILE = project_path + '/miner_data/privkey.wif'

PENDING_POOL_FILE = project_path + '/pending_pool'

TRANSACTIONS_POOL = project_path + '/transactions'

WALLET_PRIVKEY_FILE = project_path + '/privkey.wif'

WALLET_ADDRESS_FILE = project_path + '/address'

UTXO_POOL_FILE = project_path + '/utxo_pool.db'

