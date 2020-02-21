from typing import List, TypeVar, Dict, Union
import json
import time

from bclib.block import Block, block_from_dict
from bclib.transaction import Transaction
from bclib.wallet import Wallet
from bclib.utils import from_str, from_int, to_class, from_list


class Chain:
    def __init__(self):
        self.pendingTx: List[Transaction] = []
        self.blocks: List[Block] = []
        self.maxTransactionsPerBlock = 1000

    # Loads blocks from a dictionary, usually coming from self.to_dict
    def loadChainFromDict(self, d) -> int:
        self.blocks = [Block.from_dict(x) for x in d]
        return len(self.blocks)

    # Exports the blocks into a portable dictionary.
    def to_dict(self) -> Dict[str, Union[List[dict], list]]:
        return {
            "blocks": [x.to_dict() for x in self.blocks],
            "pending": [tx.to_dict() for tx in self.pendingTx],
        }

    def loadChainFromFile(self, filename) -> int:
        with open(filename, "r") as f:
            self.loadChainFromDict(json.loads(f.read()))
        return len(self.blocks)

    def saveChainToFile(self, filename):
        with open(filename, "w") as f:
            f.write(json.dumps(self.to_dict(), indent=True))

    # Appends a new block to the end of the chain, only does basic assertion if the block is compatible
    #   with the chain, transaction validation and block integrity checks is not performed here.
    def _appendBlock(self, block: Block):
        if not block.data.prevHash == self.lastBlock.hash:
            raise Exception(f"prevHash of new block({block.data.prevHash}) is not equal to chain's last block({self.lastBlock.hash})")

        if not block.hash.startswith("0" * block.data.difficulty):
            raise Exception("difficulty does not match")

        # Check all transactions for validity, except the coinbase transcation
        if not all([tx.validate() for i, tx in enumerate(block.data.transactions) if i != 0 ]):
            raise Exception("block contains invalid transcation")

        if len(block.data.transactions):
            cbtx = block.data.transactions[0]
            if cbtx.data.value != 1000 or cbtx.data.source != "coinbase":
                raise Exception(f"invalid coinbase transaction: {cbtx}")

        acceptedHashes = [tx.hash() for tx in block.data.transactions]
        self.pendingTx = [tx for tx in self.pendingTx if tx.hash() not in acceptedHashes]
        self.blocks.append(block)

    # Resets the chain with a genesis transaction to a specified address
    def resetAndInitialize(self, genesisAddress, value=1000000000, difficulty=3):
        genesisTransaction = Transaction.from_dict(dict(
            data=dict(
                source="genesis",
                destination=genesisAddress,
                value=value,
                timestamp=int(time.time())
            ),
            signature="genesis"
        ))

        genesisBlock = block_from_dict(dict(
            data=dict(
                blockNo=0,
                prevHash="genesis",
                transactions=[genesisTransaction],
                nonce=0,
                difficulty=difficulty,
                timestamp=int(time.time())
            ),
            hash="genesis"
        ))

        self.blocks = [genesisBlock.export()]

    def addTransaction(self, tx: Transaction):
        # assert tx.validate(), "transaction not valid"
        # assert self.getBalance(tx.data.source) >= tx.data.value, "sender does not have enough funds"
        if not tx.validate():
            raise Exception("transaction not valid")

        if self.getBalance(tx.data.source) < tx.data.value:
            raise Exception(f"sender({tx.data.source}) does not have enough funds")

        self.pendingTx.append(tx)

    # Retrieves a balance of a specific address
    # Note: This is not an optimal implementation of this mechanism,
    #       rather, this function prioritizes readability over performance. O(n), n = len(self.blocks)
    def getBalance(self, address):
        # Get balance state with the pending transactions first
        balance = sum([
            tx.data.value if tx.data.destination == address else tx.data.value * -1
            for tx in self.pendingTx
            if tx.data.destination == address or tx.data.source == address
        ])

        # Loops over the blocks
        for block in self.blocks:
            balance += sum([
                tx.data.value if tx.data.destination == address else (tx.data.value * -1)
                for tx in block.data.transactions
                if tx.data.destination == address or tx.data.source == address
            ])
        return balance

    # Complete this!
    # The function basically iterates through the nonce until block.export().hash accomplishes the difficulty
    def mineBlock(self, minerAddress: str) -> Block:
        # sets the initial variables
        nonce = 0
        block = None

        mytx = {
            "signature": "",
            "data": {
                "source": "coinbase",
                "destination": minerAddress,
                "value": 1000,
                "timestamp": int(time.time())
            }
        }

        txs = [Transaction.from_dict(mytx)]
        txs.extend([x for x in self.pendingTx])

        while True:
            block = Block.from_dict(dict(
                data=dict(
                    difficulty=self.lastBlock.data.difficulty,
                    nonce=nonce,
                    blockNo=self.lastBlock.data.blockNo + 1,
                    prevHash=self.lastBlock.hash,
                    transactions=txs,
                    timestamp=int(time.time())
                ),
                hash="",
            ))
            # block.export().hash would return the block hash
            if block.export().hash.startswith("0" * self.lastBlock.data.difficulty):
                break

            # Increment nonce
            nonce += 1

        self._appendBlock(block)
        return block

    def getWalletFunds(self, w: Wallet) -> int:
        return self.getBalance(w.address)

    @property
    def lastBlock(self):
        return self.blocks[-1]
