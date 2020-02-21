from flask import Flask, jsonify, request, send_from_directory
import secrets
import json
import requests
import asyncio
from flask_cors import CORS

from bclib.chain import Chain
from bclib.transaction import Transaction

# Instance our Node
app = Flask(__name__)
CORS(app)

# Generate a globally unique address for this node
node_identifier = secrets.token_hex(4)

chain = Chain()

nodes = {}
args = None
messages = []


@app.route("/")
def main():
    return send_from_directory("templates", "index.html")


@app.route("/status")
def status():
    return jsonify({
        "identifier": node_identifier,
        "connectedNodes": nodes,
        "messages": messages,
        "chain": chain.to_dict()
    })


@app.route("/chain/initialize", methods=["POST"])
def initializeBlockChain():
    add = request.get_json(force=True)
    err = None
    try:
        chain.resetAndInitialize(genesisAddress=add["address"])
    except Exception as e:
        err = str(e)
    return jsonify({"error": err})


@app.route("/chain/balance", methods=["POST"])
def getBalance():
    add = request.get_json(force=True)
    err = None
    value = 0
    try:
        value = chain.getBalance(add["address"])
    except Exception as e:
        err = str(e)

    return jsonify({
        "error": err,
        "value": value
    })


@app.route("/chain/blocks/add", methods=["POST"])
def addBlocks():
    rawblock = request.get_json(force=True)
    txObj = Transaction.from_dict(rawblock)

    err = None
    try:
        chain.addTransaction(txObj)
    except Exception as e:
        err = str(e)


    sentTo = rawblock.get("sentTo", [])
    sendTo = [host for i, host in nodes.items() if host not in sentTo]
    # Append the new new nodes to the sentTo
    sentTo.extend(sendTo)
    async def broadcastBlock(rawTx):
        rawblock.update({
            "sentTo": sentTo
        })
        for host in sendTo:
            requests.post("http://" + host + "/chain/blocks/add", json=rawblock)
    asyncio.run(broadcastBlock(rawblock))

    return jsonify({"error": err})


@app.route("/chain/mine", methods=["POST"])
def mineChain():
    miner = request.get_json(force=True)
    block = chain.mineBlock(miner["minerAddress"])
    requests.post(f"http://{args.host}:{args.port}/chain/blocks/add", json=block.to_dict())
    return jsonify(block.to_dict())

@app.route("/chain/tx/add", methods=["POST"])
def addTranscation():
    rawtx = request.get_json(force=True)
    txObj = Transaction.from_dict(rawtx)

    err = None
    try:
        chain.addTransaction(txObj)
    except Exception as e:
        err = str(e)


    sentTo = rawtx.get("sentTo", [])
    sendTo = [host for i, host in nodes.items() if host not in sentTo]
    # Append the new new nodes to the sentTo
    sentTo.extend(sendTo)
    async def broadcastTx(rawTx):
        rawtx.update({
            "sentTo": sentTo
        })
        for host in sendTo:
            requests.post("http://" + host + "/chain/tx/add", json=rawtx)
    asyncio.run(broadcastTx(rawtx))

    return jsonify({"error": err})


@app.route("/bootstrap/<host>/<port>", methods=["GET"])
def bootstrap(host, port):
    response = requests.get(f"http://{host}:{port}/join/{args.host}:{args.port}/{node_identifier}").json()
    if "error" not in response:
        nodes.update(response)

    return jsonify(nodes)


@app.route("/send/<identifier>/<message>", methods=["GET"])
def send(identifier, message):
    if identifier not in nodes:
        return jsonify({"error": "not in network"})

    host = nodes[identifier]
    response = requests.post("http://" + host + "/mail/rec", json={
        "message": message,
        "source": node_identifier
    })

    return jsonify(response.json())


@app.route("/broadcast/<message>", methods=["GET"])
def broadcast_get(message):
    for id, host in nodes.items():
        response = requests.post("http://" + host + "/mail/rec", json={
            "data": message,
            "type": "text",
            "source": node_identifier
        })


@app.route("/broadcast", methods=["POST"])
def broadcast_post():
    body = request.get_json(force=True)

    async def _broadcast_async():
        for id, host in nodes.items():
            requests.post("http://" + host + "/mail/rec", json={
                "data": body["data"],
                "type": body["type"],
                "source": node_identifier
            })

    asyncio.run(_broadcast_async(body))
    pass


@app.route("/mail/rec", methods=["POST"])
def recmail():
    messages.append(request.get_json())
    return jsonify({
        "error": None
    })


@app.route("/mail/get", methods=["GET"])
def getmail():
    return jsonify(messages)


@app.route("/join/<nodeHost>/<identifier>", methods=["GET"])
def join(nodeHost, identifier):
    print(f"Join command from {nodeHost}:{identifier}")
    if identifier in nodes:
        return jsonify({"error": "already joined, please call /leave"}), 401

    async def broadcastJoin(_id, _nh):
        sendto = [host for i, host in nodes.items() if i != node_identifier]
        for host in sendto:
            requests.post("http://" + host + "/member/join", json={
                "identifier": _id,
                "host": _nh,
                "sentTo": sendto,
                "reference": node_identifier,
            })

    asyncio.run(broadcastJoin(identifier, nodeHost))
    print(f"Adding '{identifier}@{request.remote_addr}' to the network.")
    nodes[identifier] = nodeHost
    return jsonify(nodes)


@app.route("/member/join", methods=["POST"])
def member_join():
    j = request.get_json()
    identifier = j["identifier"]
    nodeHost = j["host"]
    print(f"New node propagation broadcast for {nodeHost}:{identifier}")
    if nodeHost in nodes.values():
        return jsonify({"ok": True, "duplicate": True}), 200

    # Rebroadcast to other nodes, skipping if it's already in the sentTo
    sentTo = j["sentTo"]
    sendTo = [host for i, host in nodes.items() if host not in sentTo]
    # Append the new new nodes to the sentTo
    sentTo.extend(sendTo)

    async def broadcastJoin(_id, _nh):
        for host in sendTo:
            requests.post("http://" + host + "/member/join", json={
                "identifier": _id,
                "host": _nh,
                "sentTo": sentTo,
                "reference": node_identifier,
            })

    asyncio.run(broadcastJoin(identifier, nodeHost))

    print(f"Adding '{identifier}@{nodeHost}' to the network")
    nodes[identifier] = nodeHost
    return jsonify({"ok": True})


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-host', '--host', default="localhost", type=str, help='bind to interface')
    args = parser.parse_args()

    nodes[node_identifier] = f"{args.host}:{args.port}"
    app.run(host=args.host, port=args.port, debug=True)
