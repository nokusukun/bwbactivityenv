from flask import Flask, jsonify, request
import secrets
import json
import requests

# Instance our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = secrets.token_hex(4)

nodes = {}
args = None
messages = []

@app.route("/")
def status():
    return jsonify({
        "identifier": node_identifier,
        "connectedNodes": nodes,
        "messages": messages,
    })


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
    if identifier in nodes:
        return jsonify({"error": "already joined, please call /leave"}), 401

    sendto = [host for i, host in nodes.items() if i != node_identifier]
    for host in sendto:
        requests.post("http://" + host + "/member/join", json={
            "identifier": identifier,
            "host": nodeHost,
            "sentTo": sendto,
            "reference": node_identifier,
        })

    print(f"Adding '{identifier}@{request.remote_addr}' to the network.")
    nodes[identifier] = nodeHost
    return jsonify(nodes)


@app.route("/member/join", methods=["POST"])
def member_join():
    j = request.get_json()
    identifier = j["identifier"]
    nodeHost = j["host"]
    if nodeHost in nodes.values():
        return jsonify({"ok": True, "duplicate": True}), 200

    # Rebroadcast to other nodes, skipping if it's already in the sentTo
    sentTo = j["sentTo"]
    sendTo = [host for i, host in nodes.items() if host not in sentTo]
    # Append the new new nodes to the sentTo
    sentTo.extend(sendTo)
    for host in sendTo:
        requests.post("http://" + host + "/member/join", json={
            "identifier": identifier,
            "host": nodeHost,
            "sentTo": sentTo,
            "reference": node_identifier,
        })

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
