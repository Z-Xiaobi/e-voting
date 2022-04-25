# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: app.py
# @Github: https://github.com/Z-Xiaobi

from flask import Flask, request
from blockchain import Block, BlockChain, time, json, requests
# import time
# import requests

# Initialize Application
app = Flask(__name__)

# Initialize Blockchain
blockchain = BlockChain()

# Initialize peers (nodes / the host addresses of
# other participating members of the network)
peers = set()

# Create new transaction
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    required_fields = ["author", "content"]
    data = request.get_json()
    for field in required_fields:
        if not data.get(field):
            return "Invalid transaction data", 404
    # specify the creation time
    data["timestamp"] = time.time()
    # append transaction data to unconfirmed transaction list
    blockchain.add_new_transaction(data)
    return "Successfully created new transaction", 201

# Get the whole blockchain
@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    chain = []
    # append all the Block class instances
    for block in blockchain.block_chain:
        chain.append(block.__dict__)
    # return json format data
    return json.dumps({"length": len(chain),
                       "chain": chain})

# Mine the unconfirmed transactions or to say
# Add the pending(i.e. unconfirmed) transactions
# to the blockchain
@app.route('/mine', methods=['GET'])
def mine():
    # new block's index
    idx = blockchain.mine()
    if not idx:
        return "No transactions to mine"
    return "Block #{} is mined.".format(idx)

# Get the unconfirmed transactions
@app.route('/unconfirmed', methods=['GET'])
def get_unconfirmed_transcations():
    return json.dumps(blockchain.unconfirmed_transactions)


'''
Mechanism that let a new node become aware of 
other peers in the network
'''

# Add new peers to the network
@app.route('/register_peer', methods=['POST'])
def register_new_peers():
    # The host address to the peer node
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data: node_address", 400
    # Add the node to the peer list
    peers.add(node_address)
    # Return the blockchain to this newly registered peer
    # so that it can synchronize
    return get_blockchain()

# Register current node with the remote node
# specified in the request,
# and sync the blockchain  with the remote node.
@app.route('/register_with_node', methods=['POST'])
def register_with_existing_node():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_peer",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    blockchain_from_dump = BlockChain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["transactions"])

        proof = block_data['hash']
        if idx > 0:
            added = blockchain_from_dump.add_block(block, proof)
            if not added:
                raise Exception(
                    "The chain dump is tampered!!")
        else:  # the block is the initial block, no verification needed
            blockchain_from_dump.block_chain.append(block)
    return blockchain_from_dump


def consensus():
    """
    Simple consensus algorithm from RUOCHI.
    If a longer valid chain is found,
    replace current chain with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            # Longer valid chain found!
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False