from dataclasses import dataclass
from typing import Any, TypeVar
import hashlib, json

from bclib import wallet

from bclib.utils import from_str, from_int, to_class

T = TypeVar("T")

@dataclass
class TransactionData:
    source: str
    destination: str
    value: int
    timestamp: int

    @staticmethod
    def from_dict(obj: Any) -> 'TransactionData':
        assert isinstance(obj, dict)
        source = from_str(obj.get("source"))
        destination = from_str(obj.get("destination"))
        value = from_int(obj.get("value"))
        ts = from_int(obj.get("timestamp"))
        return TransactionData(source, destination, value, ts)

    def to_dict(self) -> dict:
        result: dict = {}
        result["source"] = from_str(self.source)
        result["destination"] = from_str(self.destination)
        result["value"] = from_int(self.value)
        result["timestamp"] = from_int(self.timestamp)
        return result


@dataclass
class Transaction:
    signature: str
    data: TransactionData

    @staticmethod
    def from_dict(obj: Any) -> 'Transaction':
        if type(obj) == Transaction:
            obj = obj.to_dict()
        assert isinstance(obj, dict)
        signature = from_str(obj.get("signature"))
        data = TransactionData.from_dict(obj.get("data"))
        return Transaction(signature, data)

    def to_dict(self) -> dict:
        result: dict = {}
        result["signature"] = from_str(self.signature)
        result["data"] = to_class(TransactionData, self.data)
        return result

    def validate(self) -> bool:
        verify, extractedHash = wallet.validate(self.signature, self.data.source)
        return all([verify, extractedHash == self.hash()])

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.data.to_dict()).encode()).hexdigest()

    def signWithWallet(self, w: wallet.Wallet):
        assert self.data.source == w.address, "transaction sender(source) is not the wallet owner"
        self.signature = w.sign(self.hash())

    def to_json(self) -> str:
        return json.dumps(self.to_dict())