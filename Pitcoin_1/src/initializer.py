import json

from flask import (Flask,
                   request)

from blockchain import Blockchain
from colored_print import prRed

from globals import (
    PENDING_POOL_FILE,
    MINER_NODES,
    MINER_NETWORK_DATA
)

# TODO: Server config file
# TODO: Server must be in separate file - initializer.py

node = Flask(__name__)


@node.route("/")
def index():
    return "HELLO WORLD"


@node.route('/transaction/pendings', methods=['GET'])
def get_pool_of_transaction():
    raw_pool = Blockchain.get_pool_of_transactions()
    json_pool = json.dumps(raw_pool)
    return json_pool


@node.route('/transaction/new', methods=['GET', 'POST'])
def submit_tx():
    if request.method == 'POST':
        new_tx_json = request.get_json()
        my_pool = Blockchain.get_pool_of_transactions()
        for transaction in new_tx_json['transactions']:
            my_pool.append(transaction[-1])
        my_pool = list(set(my_pool))
        f = open(PENDING_POOL_FILE, 'w')
        for tx in my_pool:
            f.write(tx)
        f.close()
        return "Transaction added"
    elif request.method == 'GET':
        transactions = Blockchain.get_pool_of_transactions()
        json_txs = json.dumps(transactions)
        return json_txs


@node.route('/nodes/new', methods=['POST'])
def add_node():
    new_node = request.get_json()
    if Blockchain.validate_node(new_node):
        f = open(MINER_NODES, 'a+')
        f.write(new_node + '\n')
        f.close()
        print(new_node + ' added to node pool')
    else:
        print("Wrong node format !")


@node.route('/nodes', methods=['GET'])
def get_nodes():
    raw_nodes = Blockchain.recover_nodes_from_file()
    json_nodes = json.dumps(raw_nodes)
    return json_nodes


@node.route('/chain', methods=['GET'])
def get_chain():
    chain = Blockchain.recover_blockchain_from_fileblock()
    dict_chain = []
    for block in chain:
        dict_chain.append(block.to_dict())
    json_chain = json.dumps(dict_chain)
    return json_chain


@node.route('/chain/length', methods=['GET'])
def get_chain_length():
    chain_len = Blockchain.recover_chain_length_from_file()
    json_length = json.dumps(chain_len)
    return json_length


@node.route('/block/', methods=['GET'])
def get_n_block():
    height = int(request.args.get('height'))
    if height:
        block = Blockchain.get_n_block(height)
    else:
        block = Blockchain.get_n_block(last=True)
    json_block = json.dumps(block.to_dict())
    return json_block


@node.route('/block/last', methods=['GET'])
def get_last_block():
    block = Blockchain.get_n_block(last=True)
    json_block = json.dumps(block.to_dict())
    return json_block


@node.route('/balance', methods=['GET'])
def get_balance():
    addr = request.args.get('address')
    im_sorry = "500"
    return im_sorry


def get_miner_ip_and_port():
    try:
        f = open(MINER_NETWORK_DATA)
        json_data = json.load(f)
        read_ip = json_data["ip"]
        read_port = json_data["port"]
        return read_ip, read_port
    except Exception as e:
        print(e)


def main():
    ip, port = get_miner_ip_and_port()
    if not ip or not port:
        prRed("INVALID ./miner_data/network_data")
    else:
        node.run(host=ip, port=port, debug=True)


if __name__ == "__main__":
    ip, port = get_miner_ip_and_port()
    if not ip or not port:
        prRed("INVALID ./miner_data/network_data")
    else:
        node.run(host=ip, port=port, debug=True)