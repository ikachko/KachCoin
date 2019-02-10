import initializer
from key_generator import KeyGenerator
from wallet import Wallet
from miner_cli import MinerCli
from wallet_cli import WalletCli

# initializer.main()

privkey_1 = KeyGenerator().generate_key()
privkey_2 = KeyGenerator().generate_key()
privkey_3 = KeyGenerator().generate_key()

f = open('../miner_data/privkey_1', 'w+')
f.write(Wallet.priv_to_WIF(privkey_1))
f.close()
f = open('../miner_data/privkey_2', 'w+')
f.write(Wallet.priv_to_WIF(privkey_2))
f.close()
f = open('../miner_data/privkey_3', 'w+')
f.write(Wallet.priv_to_WIF(privkey_3))
f.close()

publkey_1 = Wallet.private_to_public(privkey_1)
publkey_2 = Wallet.private_to_public(privkey_2)
publkey_3 = Wallet.private_to_public(privkey_3)

f = open('../miner_data/publkey_1', 'w+')
f.write(publkey_1)
f.close()
f = open('../miner_data/publkey_2', 'w+')
f.write(publkey_2)
f.close()
f = open('../miner_data/publkey_3', 'w+')
f.write(publkey_3)
f.close()

minercli = MinerCli()
walletcli = WalletCli()

walletcli.do_send(Wallet.private_key_to_addr(privkey_1) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_2) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_3) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_1) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_2) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_3) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_1) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_2) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_3) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_1) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_2) + ' ' + str(10))
walletcli.do_send(Wallet.private_key_to_addr(privkey_3) + ' ' + str(10))

for i in range(10):
    minercli.do_mine('../miner_data/privkey_1')
