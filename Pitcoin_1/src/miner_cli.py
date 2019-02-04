import cmd
import time
import json

from pyfiglet import Figlet

from blockchain import Blockchain
from colored_print import *
from block import Block
from transaction import CoinbaseTransaction
from wallet import Wallet
from serializer import Serializer

from globals import (
    BLOCKS_DIRECTORY,
    MINER_NODES,
    MINER_PRIVKEY_FILE
)


class MinerCli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "(⛏ ️Miner-Cli  ⛏️)$>"

        f = Figlet(font='big')
        s = f.renderText("K A C H K O I N")

        self.intro = s + "\n\nWelcome to Kachcoin miner command-line interface!\n" \
                         "For reference type 'help'"
        self.doc_header = "Possible commands (for reference of specific command type 'help [command]'"
        self.blockchain = Blockchain()
        self.chain = Blockchain.recover_blockchain_from_fileblock()
        self.nodes = Blockchain.recover_nodes_from_file()

    def do_show_blocks(self, args):
        i = 0
        for block in self.chain:
            prLightPurple('----------------------------------------')
            prPurple('Height = ' + str(i))
            prCyan(block.to_dict())
            prLightPurple('----------------------------------------')
            i += 1

    def add_new_blocks(self, n, blocks):
        for i in range(n, len(blocks)):
            f = open(BLOCKS_DIRECTORY + ('%08i' % i) + '.block', 'w+')
            json.dump(blocks[i].to_dict(), f)
            f.close()

    def do_consensus(self, args):
        chains = Blockchain.get_new_chains()
        if chains is None:
            prRed("Failed to load chains from peers. Keeping current chain")
            return
        my_chain = self.chain

        consensus = Blockchain.resolve_conflicts(my_chain, chains)
        if not consensus:
            prLightPurple("Your chain is already the longest")
        else:
            prPurple("Chain was changed\nYour chain len -> "
                  + str(len(my_chain))
                  + '\nNew chain len -> '
                  + str(len(consensus)))
            self.chain = consensus
            self.add_new_blocks(abs(len(my_chain) - len(consensus)), consensus)

        prGreen("Consesus reached")

    def do_show_pending_pool(self, args):
        pool = Blockchain.get_pool_of_transactions()
        prCyan('---------------------')
        prPurple("PENDING TRANSACTIONS")
        for tx in pool:
            prLightPurple(tx)
        prCyan('---------------------')

    def do_add_node(self, args):
        try:
            if args:
                args_splitted = args.split(' ')
                node = args_splitted[0]
                if Blockchain.validate_node(node):
                    f = open(MINER_NODES, 'a+')
                    f.write(node + '\n')
                    f.close()
                    prGreen("Node successfully added")
        except Exception as e:
            prRed(e)
            prRed("Error while trying to add node")

    def do_show_nodes(self, args):
        nodes = Blockchain.recover_nodes_from_file()
        prLightPurple(nodes)

    def prepare_miner_block(self, args):
        if args:
            args_splitted = args.split(' ')
            privkey_addr = args_splitted[0]
            f = open(privkey_addr, 'r')
            miner_privkey_wif = f.read()
            f.close()
        else:
            f = open(MINER_PRIVKEY_FILE, 'r')
            miner_privkey_wif = f.read()
            f.close()
        transactions = Blockchain.get_transactions_to_block()


        miner_privkey = Wallet.WIF_to_priv(miner_privkey_wif)

        coinbase = CoinbaseTransaction()
        coinbase.recipient_address = Wallet.private_key_to_addr(miner_privkey)

        coinbase_hash = coinbase.transaction_hash()

        sign, publkey = Wallet.sign_message(coinbase_hash, miner_privkey)

        serialized_coinbase = Serializer.serialize(coinbase.amount,
                                                   coinbase.sender_address,
                                                   coinbase.recipient_address,
                                                   publkey,
                                                   sign)
        if transactions[0] == '':
            transactions = [serialized_coinbase]
        else:
            transactions.append(serialized_coinbase)
        prGreen(transactions)
        last_block = Blockchain.get_chain()[-1]
        last_block_h = last_block.hash_block()

        timestamp = int(time.time())

        new_block = Block(timestamp, last_block_h, transactions)

        return new_block

    def do_mine(self, args):
        if args:
            args_splitted = args.split(' ')
            privkey_addr = args_splitted[0]
            new_block = self.prepare_miner_block(privkey_addr)
        else:
            new_block = self.prepare_miner_block(None)
        prPurple("Mining starting")
        h, block = self.blockchain.mine(new_block)
        prGreen("MINED")
        prPurple('height : ' + str(len(self.chain)))
        prPurple('nonce : ' + str(block.nonce))

        prPurple('hash : ' + h)
        self.chain.append(block)


if __name__ == '__main__':

    cli = MinerCli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        prLightGray("\nending....")


