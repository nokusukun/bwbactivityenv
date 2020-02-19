from .chain import Chain
from .transaction import Transaction


def makeTransaction(source="rave", destination="von", value=100):
    return Transaction.from_dict(dict(
        signature="rave's signature",
        data=dict(
            source=source,
            destination=destination,
            value=""
        )
    ))

def makeChain():
    chain = Chain()
    chain.resetAndInitialize("rave")

    return chain