import cmd
import server
import requests

from pyfiglet import Figlet

from key_generator import KeyGenerator
import wallet
from transaction import Transaction
from utxo_set import Utxo
from tx import SwRawTransactionMultInputs
from tx_validator import transaction_validation
from serializer import Serializer
from colored_print import *
from globals import (
    TRANSACTIONS_POOL,
    PENDING_POOL_FILE,
    SW_TRANSACTIONS_POOL,
    WALLET_PRIVKEY_FILE,
    WALLET_ADDRESS_FILE,
    WALLET_SEGWIT_ADDRESS_FILE,
    WALLET_SEGWIT_PRIVKEY_FILE,
    NETWORKS
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
        """new - generate new private key and public address\nnew [seed] - generate key with text seed"""
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
        address = w.private_key_to_addr(private_key)
        prLightPurple(address)
        f = open(WALLET_ADDRESS_FILE, 'w')
        f.write(address)
        f.close()

    def do_balance(self, args):
        if args and len(args.split(' ')) == 1:
            address = args
            balance = w.get_balance(address)
            # utxo = Utxo.get_utxo_of_addr(address)
            # if not utxo:
            #     prPurple("No utxo of this address")
            #     return
            # for u in utxo:
            #     balance += u['value']
            prPurple("Balance of address " + address + " is " + str(balance) + " coins")

    def do_import(self, args):
        """import [out_filename] - import private key in WIF format
                                            and convert it to private and public"""
        if not args or len(args.split(' ')) != 1:
            prRed(
                'usage:\n'
                'import [WIF key filename]'
            )
            return
        args_splitted = args.split(' ')

        out_file = open(args_splitted[0], 'r')
        wif_key = out_file.read()
        out_file.close()

        priv_key = w.WIF_to_priv(wif_key)
        prPurple('private key:')
        prLightPurple(priv_key)
        prPurple('address:')
        address = w.private_key_to_addr(priv_key)
        prLightPurple(address)

        in_file = open(WALLET_ADDRESS_FILE, 'w')
        in_file.write(address)
        in_file.close()

    def do_send(self, args):
        """send [Recipient Address] [Amount]"""

        if not args or len(args.split(' ')) != 2:
            prRed(
                'usage:\n'
                + 'send [Recepient Address] [Amount]'
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



        # tx = SwRawTransaction(1, privkey_wif, )

        tx = Transaction(sender_addr, recipient_addr, amount)

        tx_hash = tx.transaction_hash()



        privkey = w.WIF_to_priv(privkey_wif)

        sign, publkey = w.sign_message(tx_hash, privkey)

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
                if not tx:
                    break
                rf.write(tx)
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


    # SEGREGATE WITNESS FUNCTIONS

    def do_swnew(self, args):
        """swnew [HRP] - generate new private key and public address\nswnew [HRP] [seed] - generate key with text seed\n
        HRP - Human Readable Part stands for type of network for which you want to create new address:\n
        BC - Bitcoin Network\n
        TB - Testnet Network\n"""

        usage = 'swnew [HRP] - generate new private key and public address\nswnew [HRP] [seed] - generate key with text seed\n' \
                'HRP - Human Readable Part stands for type of network for which you want to create new address:\n' \
                '0) BC - Bitcoin Network\n' \
                '1) TB - Testnet Network\n'

        keygen = KeyGenerator()

        splitted = args.split(' ')
        if len(list(splitted)) < 1 or splitted[0] not in ('BC', 'TB'):
            prRed("Wrong parameters!")
            prCyan(usage)
            return

        if splitted[0] == 'BC':
            network = NETWORKS.BITCOIN
        elif splitted[0] == 'TB':
            network = NETWORKS.TESTNET
        else:
            prRed("How i didn't found it in usage check? ")
            return

        for arg in args:
            keygen.seed_input(arg)

        private_key = keygen.generate_key()

        while len(private_key) != 64:
            private_key = KeyGenerator().generate_key()

        prPurple('raw private key:')
        prLightPurple(private_key)
        prPurple('segwit address:')
        swaddress = wallet.Wallet.bech32_addr_from_privkey(private_key, network)
        prLightPurple(swaddress)

        # Write new address to file
        f = open(WALLET_SEGWIT_ADDRESS_FILE, 'w')
        f.write(swaddress)
        f.close()

        privkey_wif = wallet.Wallet.priv_to_WIF(private_key)

        # Write privkey in WIF to file
        f = open(WALLET_SEGWIT_PRIVKEY_FILE, 'w')
        f.write(privkey_wif)
        f.close()

    def do_swsend(self, args):
        """send transaction\nFormat: send <% Recipient Address %>, <% Amount %>"""

        if not args or len(args.split(' ')) != 2:
            prRed(
                "usage:\n"
                + "send transaction\nFormat: send <% Recipient Address %>, <% Amount %>"
            )

        args_splitted = args.split(' ')
        recipient_addr = args_splitted[0]
        amount = int(args_splitted[1])

        f = open(WALLET_SEGWIT_PRIVKEY_FILE, 'r')
        privkey_wif = f.read()
        f.close()

        f = open(WALLET_SEGWIT_ADDRESS_FILE, 'r')
        sender_addr = f.read()
        f.close()

        inputs = Utxo.get_inputs(sender_addr, amount)
        if inputs:
            sw_tx = SwRawTransactionMultInputs(version=1,
                                               sender_priv_wif=privkey_wif,
                                               sender_addr=sender_addr,
                                               recipient_addr=recipient_addr,
                                               inputs=inputs,
                                               out_value=50,
                                               miner_fee=0,
                                               locktime=0)
            print(sw_tx.get_raw_transaction(hex=True))
            f = open(SW_TRANSACTIONS_POOL, 'a+')
            f.write(sw_tx.get_raw_transaction(hex=True) + '\n')
            f.close()
        # sw_tx = SwRawTransaction(1, privkey_wif, sender_addr, )

    def do_swbroadcast(self, args):
        url = 'http://' + str(server.ip) + ':' + str(server.port) + '/transaction/new'

        tx_payload = {'transactions': []}

        try:
            f = open(SW_TRANSACTIONS_POOL, 'r')
            rf = open(PENDING_POOL_FILE, 'a+')

            while True:
                tx = f.readline()
                if not tx:
                    break
                rf.write(tx)
                tx_payload['transactions'].append(tx)
            f.close()
            rf.close()
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, json=tx_payload, headers=headers)
            prGreen("Transactions successfully broadcasted")


        except Exception as e:
            prRed('Broadcast Error:')
            prRed(e)

    def default(self, line):
        prRed('Wrong command')


if __name__ == '__main__':

    cli = WalletCli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        prLightGray("\nending....")
