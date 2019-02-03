import cmd
import server
import requests

from pyfiglet import Figlet

from key_generator import KeyGenerator
from wallet import Wallet
from transaction import Transaction
from tx import RawTransaction
from tx_validator import transaction_validation
from serializer import Serializer, Deserializer
from blockchain import Blockchain
from colored_print import *
from globals import (
    TRANSACTIONS_POOL,
    PENDING_POOL_FILE,
    WALLET_PRIVKEY_FILE,
    WALLET_ADDRESS_FILE
)

# TODO: Fix wallet balance


class WalletCli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "(💰 Wallet-Cli 💰)$>"

        f = Figlet(font='big')
        s = f.renderText('K A C H K O I N')

        self.intro = s + "\n\nWelcome to Kachkoin wallet command-line interface!\n" \
                         "For reference type 'help'"
        self.doc_header = "Possible commands (for reference of specific command type 'help [command]'"

    def do_new(self, args):
        """new [filename] - generate new private and public key\nnew [filename] [seed] - generate keys with text seed"""
        keygen = KeyGenerator()

        if args:
            for arg in args:
                keygen.seed_input(arg)
        private_key = keygen.generate_key()

        while len(private_key) != 64:
            private_key = KeyGenerator().generate_key()

        prPurple('private key:')
        prLightPurple(private_key)
        prPurple('address:')
        address = Wallet.private_key_to_addr(private_key)
        prLightPurple(address)
        f = open(WALLET_ADDRESS_FILE, 'w')
        f.write(address)
        f.close()

    def do_balance(self, args):
        if args and len(args.split(' ')) == 1:
            address = args
            balance = 0

            blocks = Blockchain.recover_blockchain_from_fileblock()
            for block in blocks:
                b_dict = block.to_dict()
                for transactions in b_dict['transactions']:
                    deserialized_tx = Deserializer.deserialize(transactions)
                    prPurple("Sender addr " + deserialized_tx['sender_addr'])
                    prCyan("Recepient addr " + deserialized_tx['recepient_addr'])
                    if deserialized_tx['sender_addr'] == address:
                        prGreen("Added " + deserialized_tx['num_of_coins'] + " coins")
                        balance -= deserialized_tx['num_of_coins']
                    if deserialized_tx['recepient_addr'] == address:
                        prRed("Removed " + deserialized_tx['num_of_coins'] + " coins")
                        balance += deserialized_tx['num_of_coins']
            prPurple("Balance of address " + address + " is " + str(balance) + " coins")

    def do_import(self, args):
        """import [out_filename] [to_filename] - import private key in WIF format
                                            and convert it to private and public"""
        if not args or len(args.split(' ')) != 1:
            prRed(
                'usage:\n'
                'import [WIF key filename]'
            )
            return
        args_splitted = args.split(' ')

        out_file = open(args_splitted, 'r')
        wif_key = out_file.read()
        out_file.close()

        priv_key = Wallet.WIF_to_priv(wif_key)
        prPurple('private key:')
        prLightPurple(priv_key)
        prPurple('address:')
        address = Wallet.private_key_to_addr(priv_key)
        prLightPurple(address)

        in_file = open(WALLET_ADDRESS_FILE, 'w')
        in_file.write(address)
        in_file.close()

    def do_send_raw(self, args):
        """send [Recipient Address] [Amount]"""

        if not args or len(args.split(' ')) != 2:
            prRed(
                'usage:\n'
                'send [Recepient Address] [Amount]'
            )
            return
        args_splitted = args.split(' ')
        recipient_addr = args_splitted[0]
        amount = int(args_splitted[1])

        f = open(WALLET_ADDRESS_FILE, 'r')
        sender_addr = f.read()
        f.close()

        f = open(WALLET_PRIVKEY_FILE, 'r')
        privkey_wif = f.read()
        f.close()

        privkey = Wallet.WIF_to_priv(privkey_wif)

        tx = RawTransaction(sender_addr, recipient_addr, amount, amount, 0)
        tx_hash = tx.tx_id(privkey)

        # sign, publkey = tx.sign_transaction(privkey)

        tx_serialized = tx.raw_transaction(privkey).hex()

        # tx_serialized = Serializer.serialize(tx.amount, tx.sender_address, tx.recipient_address, publkey, sign)
        # transaction_validation(tx_serialized, tx_hash)
        prPurple('Send from [' + sender_addr + '] to [' + recipient_addr + '] amount -> [' + str(amount) + ']')
        prLightPurple('Serialized transaction : [' + tx_serialized + ']')
        f = open(TRANSACTIONS_POOL, 'a+')
        f.write(tx_serialized + '\n')
        f.close()

    def do_send(self, args):
        """send [Recipient Address] [Amount]"""

        if not args or len(args.split(' ')) != 2:
            prRed (
                'usage:\n'
                'send [Recepient Address] [Amount]'
            )
            return

        args_splitted = args.split(' ')
        recipient_addr = args_splitted[0]
        amount = int(args_splitted[1])

        f = open(WALLET_ADDRESS_FILE, 'r')
        sender_addr = f.read()
        f.close()

        tx = Transaction(sender_addr, recipient_addr, amount)

        tx_hash = tx.transaction_hash()

        f = open(WALLET_PRIVKEY_FILE, 'r')
        privkey_wif = f.read()
        f.close()

        privkey = Wallet.WIF_to_priv(privkey_wif)

        sign, publkey = Wallet.sign_message(tx_hash, privkey)

        tx_serialized = Serializer.serialize(tx.amount, tx.sender_address, tx.recipient_address, publkey, sign)
        transaction_validation(tx_serialized, tx_hash)
        prPurple('Send from [' + sender_addr + '] to [' + recipient_addr + '] amount -> [' + str(amount) + ']')
        prLightPurple('Serialized transaction : [' + tx_serialized + ']')
        f = open(TRANSACTIONS_POOL, 'a+')
        f.write(tx_serialized + '\n')
        f.close()

    def do_broadcast(self, args):
        """broadcast"""
        url = 'http://' + str(server.ip) + ':' + str(server.port) + '/transaction/new'

        tx_payload = {'transactions': []}
        try:
            f = open(TRANSACTIONS_POOL, 'r')
            rf = open(PENDING_POOL_FILE, 'w')

            while True:
                tx = f.readline()
                rf.write(tx)
                if not tx:
                    break
                tx_payload['transactions'].append(tx)
            f.close()
            rf.close()
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, json=tx_payload, headers=headers)
            prGreen("Transactions successfully broadcasted")

            # Clear transaction file
            f = open(TRANSACTIONS_POOL, 'w')
            f.write('')
            f.close()

        except Exception as e:
            prRed(e)
            prRed("Broadcast Error")


    def default(self, line):
        prRed('Wrong command')


if __name__ == '__main__':

    cli = WalletCli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        prLightGray("\nending....")
