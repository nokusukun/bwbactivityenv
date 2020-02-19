from typing import List, TypeVar
import json

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
    def to_dict(self) -> List[dict]:
        return [x.to_dict() for x in self.blocks]

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
        assert block.data.prevHash == self.lastBlock.hash, \
            "preHash of new block is not equal to chain's last block"

        self.blocks.append(block)


    # Resets the chain with a genesis transaction to a specified address
    def resetAndInitialize(self, genesisAddress, value=1000000000, difficulty=3):
        genesisTransaction = Transaction.from_dict(dict(
            data=dict(
                source="genesis",
                destination=genesisAddress,
                value=value,
                timestamp="0"
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
                timestamp="0"
            ),
            hash="genesis"
        ))

        self.blocks = [genesisBlock.export()]

    # Retrieves a balance of a specific address
    # Note: This is not an optimal implementation of this mechanism,
    #       rather, this function prioritizes readability over performance. O(n), n = len(self.blocks)
    def getBalance(self, address):
        balance = 0

        # Loops over the blocks
        for block in self.blocks:
            balance += sum([
                tx.data.value if tx.data.destination == address else tx.data.value * -1
                for tx in block.data.transactions
                if tx.data.destination == address or tx.data.source == address
            ])
        return balance

    def getWalletFunds(self, w: Wallet) -> int:
        return self.getBalance(w.address)

    @property
    def lastBlock(self):
        return self.blocks[-1]
