# Pitcoin

Simple implementation of bitcoin.
Bitcoin: A Peer-to-Peer Electronic Cash System

## Getting Started

You need python 3.6.2 and pip 19.0.1 versions

```
~>> python3 --version
Python 3.6.2
```

```
~>> pip --version
pip 19.0.1
```

### Prerequisites

First of all download my project from git repository:

```
~>> git clone https://github.com/kloffer/Kachkoin.git
```

Then:

```
~>> cd Kachkoin
```

To install all packages you need to run this cash system use:
```
~>> pip install -r requirements.txt
```

### Using

Okay, now you can use this node.
First of all run the rpc server.
For communication of two nodes - run initializer.py at both Pictoin_1 and Pitcoin_2
```
~>> python3 initializer.py
```

Open a new terminal window and go to the current directory.
Launch the command line interface to create you private key:
```
~>> python3 wallet_cli.py
```
Use the new command to generate a new private key and public address.
Then use privtowif to save your private key in WIF format.
This will further allow you to mine.

![ScreenShot](https://i.imgur.com/1hbbXp3.png)
![ScreenShot](https://i.imgur.com/cl3CLLB.png)

Call the send command in wallet cli with two parameters - sender address
and amount (Example of bitcoin address -  15Pdb6opS18FSfnQb3KjcbEU9sAwQPxHXN).
Then broadcast transaction to the network:

![ScreenShot](https://i.imgur.com/RxJ1SCT.png)

Okay, now you have two files: public_key and private_key.wif.

Open a new terminal window and go to the current directory.
Run miner-cli to start mining.
```
~>> python3 miner_cli.py
```
To mine one block use command mine:

![ScreenShot](https://i.imgur.com/cQaCBhW.png)

Also you can run script premine.py.
In this mode, the following actions occured:
   - Generation of three key pairs, which are saved to the separate file.
    -Genesis block launching
    -Using public addresses from generated keys above, mine ten (10) blocks, that
    -will contain different transactions between these addresses.

```
~>> python3 premine.py
```


### Routes

/transaction/pendings - return pendings transactions

/chain - return all blockchain in JSON format

/chain/length - return length of blockchain

/block/last - return last block of blockchain in JSON format

/block?height=<int> - return block of given height

/balance?addr=<address> - return the balance of given address
