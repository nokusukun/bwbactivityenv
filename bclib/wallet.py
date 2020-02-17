import hashlib
import base64

from ellipticcurve.ecdsa import Ecdsa, Signature
from ellipticcurve.privateKey import PrivateKey
from ellipticcurve.publicKey import PublicKey

def depublicize(key):
    return key\
        .replace("\r\n", "")\
        .replace("\n", "")\
        .replace("-----BEGIN PUBLIC KEY-----", "")\
        .replace("-----END PUBLIC KEY-----", "")

def publicize(key):
    return f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"


def validate(signature, address):
    pem = publicize(address)
    s = base64.b64decode(signature.encode()).decode().split(":")
    sig = Signature(int(s[0]), int(s[1]))
    messageHash = s[2]

    pubKey = PublicKey.fromPem(pem)
    return Ecdsa.verify(messageHash, sig, pubKey)


class Wallet:

    def __init__(self, privateKeyFile):
        with open(privateKeyFile) as w:
            self.private = PrivateKey.fromPem(w.read())
            self.address = depublicize(self.private.publicKey().toPem())

    def sign(self, messageHash):
        # hs = hashlib.sha224(message.encode()).hexdigest()
        s = Ecdsa.sign(messageHash, self.private)
        return base64.b64encode(f"{s.r}:{s.s}:{messageHash}".encode()).decode()

    def verify(self, signature):
        return validate(signature, self.address)
