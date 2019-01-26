import cmd
import os
import time

from pyfiglet import Figlet
from key_generator import KeyGenerator
from wallet import Wallet
from transaction import Transaction

class WalletCli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "(PitCoin-Cli)$>"

        f = Figlet(font='slant')
        s = f.renderText('Pitcoin')

        self.intro = s + "\n\n\n\nWelcome to Pitcoin command-line interface!\n" \
                         "For reference type 'help'"
        self.doc_header = "Possible commands (for reference of specific command type 'help [command]'"

    def do_new(self, args):
        """new [filename] - generate new private and public key\nnew [filename] [seed] - generate keys with text seed"""
        key_gen = KeyGenerator()

        if args:
            for arg in args:
                key_gen.seed_input(arg)
        private_key = key_gen.generate_key()

        f = open('address', 'w')
        print('private key:')
        print(private_key)
        print('address:')
        address = Wallet.private_key_to_addr(private_key)
        f.write(address)
        f.close()

    def do_import(self, args):
        """import [out_filename] [to_filename] - import private key in WIF format
                                            and convert it to private and public"""
        if not args or len(args.split(' ')) != 1:
            print(
                'usage:\n'
                'import [WIF key filename]'
            )
            return
        args_splitted = args.split(' ')
        out_file = open(args_splitted, 'r')
        in_file = open('address', 'w')

        wif_key = out_file.read()
        out_file.close()

        priv_key = Wallet.WIF_to_priv(wif_key)
        print('private key:')
        print(priv_key)
        print('address:')
        address = Wallet.private_key_to_addr(priv_key)
        print(address)

        in_file.write(address)
        in_file.close()

    def do_send(self, args):
        """send [Recipient Address] [Amount]"""

        if not args or len(args.split(' ')) != 2:
            print (
                'usage:\n'
                'import [Recepient Address] [Amount]'
            )
            return

        args_splitted = args.split(' ')
        recipient_addr = args_splitted[0]
        amount = int(args_splitted[1])

        f = open('address', 'r')
        sender_addr = f.read()

        tx = Transaction(sender_addr, recipient_addr, amount)

        tx_hash = tx.transaction_hash()


    def default(self, line):
        print('Wrong command')


if __name__ == '__main__':

    cli = WalletCli()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nending....")
