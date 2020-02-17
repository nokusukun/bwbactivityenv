import hashlib
import json
from dataclasses import dataclass
from typing import List, Any, TypeVar

from bclib.utils import from_int, from_str, from_list, to_class
from bclib.transaction import Transaction

T = TypeVar("T")

@dataclass
class BlockData:
    nonce: int
    difficulty: int
    blockNo: int
    prevHash: str
    transactions: List[Transaction]
    timestamp: str

    @staticmethod
    def from_dict(obj: Any) -> 'BlockData':
        assert isinstance(obj, dict)
        nonce = from_int(obj.get("nonce"))
        difficulty = from_int(obj.get("difficulty"))
        blockNo = from_int(obj.get("blockNo"))
        prevHash = from_str(obj.get("prevHash"))
        transactions = from_list(Transaction.from_dict, obj.get("transactions"))
        timestamp = from_str(obj.get("timestamp"))
        return BlockData(nonce, difficulty, blockNo, prevHash, transactions, timestamp)

    def to_dict(self) -> dict:
        result: dict = {}
        result["nonce"] = from_int(self.nonce)
        result["difficulty"] = from_int(self.difficulty)
        result["blockNo"] = from_int(self.blockNo)
        result["prevHash"] = from_str(self.prevHash)
        result["transactions"] = from_list(lambda x: to_class(Transaction, x), self.transactions)
        result["timestamp"] = from_str(self.timestamp)
        return result


@dataclass
class Block:
    data: BlockData
    hash: str

    @staticmethod
    def from_dict(obj: Any) -> 'Block':
        assert isinstance(obj, dict)
        data = BlockData.from_dict(obj.get("data"))
        hash = from_str(obj.get("hash"))
        return Block(data, hash)

    def to_dict(self) -> dict:
        result: dict = {}
        result["data"] = to_class(BlockData, self.data)
        result["hash"] = from_str(self.hash)
        return result

    def getHash(self) -> str:
            return hashlib.sha256(json.dumps(self.to_dict()).encode()).hexdigest()

    # Effectively 'locks' in the data including the transactions in the block
    #   usually chained with to_dict() afterwards.
    #   e.g. newBlock.export().to_dict()
    def export(self) -> 'Block':
        self.hash = self.getHash()
        return self

    # Appends transaction, asserts some basic expressions and checks if the transaction supplied is valid
    def appendTx(self, tx: Transaction, force=False):
        if force:
            self.hash = ""
        else:
            assert self.hash == "", "Block has already been 'locked', add 'force=True' to skip this " \
                                "and clear out the hash."

        assert tx.validate(), "transaction validation turned false"
        self.data.transactions.append(tx)

def block_from_dict(s: Any) -> Block:
    return Block.from_dict(s)


def block_to_dict(x: Block) -> Any:
    return to_class(Block, x)