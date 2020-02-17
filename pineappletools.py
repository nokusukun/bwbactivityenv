from typing import Tuple, Any

from utils.flags import Flags
import sys

from bs4 import BeautifulSoup
import requests


def GenerateEcdsa() -> Tuple[Any, Any]:
    print("Generating keys....")
    data = requests.get("https://8gwifi.org/ecsignverify.jsp")
    s = BeautifulSoup(data.text, 'html.parser')
    return s.find(id="privatekeyparam").text, s.find(id="publickeyparam").text


@Flags.asCommand(
    "genkeys",
    usage="Generate a wallet with it's accomplanying seed",
    flags=[
        ["privout", "Save the private key on this file", "private_key.txt"],
        ["pubout", "Save the public key on this file", "public_key.txt"]
    ])
def generate(args, flags) -> None:
    public, private = GenerateEcdsa()
    print("\u001b[31mIMPORTANT: SAVE THIS FOR SAFE KEEPING, THIS KEY "
          "IS USED FOR ACCESSING YOUR WALLET AND FOR SIGNING TRANSACTIONS", "\u001b[0m")
    print("\u001b[32m")
    print(public, "\u001b[0m")
    print("\u001b[33m")
    print(private, "\u001b[0m")

    with open(flags["privout"], "w") as f:
        f.write(private)
        print("Private key saved at", flags["privout"])

    with open(flags["pubout"], "w") as f:
        f.write(public)
        print("Public key saved at", flags["pubout"])


@Flags.asCommand(
    "sign",
    usage="sign a message using a specified private key",
    flags=[
        ["name", "the person you want to say hello to", "sean"],
    ])
def hello(args, flags):
    print(flags)
    print("Hello", flags["name"])


if __name__ == "__main__":
    Flags(sys.argv).Execute()
