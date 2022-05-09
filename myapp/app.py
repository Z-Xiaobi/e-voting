# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: app.py

from myapp.server.blockchain import Block, BlockChain, time, json
from myapp.server.p2p import PeerNode
from flask import Flask, request, render_template, redirect, url_for
import datetime
import requests
from argparse import ArgumentParser
import socket

# Initialize Application
app = Flask(__name__)

# Node in the blockchain network that application will communicate with
# to fetch and add data.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

# Initialize current node (identity, corresponding blockchain, peers etc)
# curr_node = PeerNode(host='127.0.0.1', port=8000)
# need to safe remove following
blockchain = BlockChain()
peers = set()
posts = []

''' Block Chain on one node '''
# root page
@app.route('/')
def index():
    fetch_posts()
    return render_template('survey.html',
                           title='My Blockchain based P2P Voting System',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_timestamp=format_timestamp)

# Create new transaction
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    required_fields = ["type", "content"]
    data = request.get_json()
    for field in required_fields:
        if not data.get(field):
            return "Invalid transaction data", 404
    # specify the creation time
    data["timestamp"] = time.time()
    # append transaction data to unconfirmed transaction list of current node
    blockchain.add_new_transaction(data)
    # curr_node.add_new_transaction(data)
    return "Successfully created new transaction", 201


# Get the whole blockchain (not encrypted, just for demonstration)
@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    print("get_blockchain() called.")
    chain = []
    # append all the Block class instances
    for block in blockchain.block_chain:
        chain.append(block.__dict__)
    # return json format data
    return json.dumps({"length": len(chain),
                       "block_chain": chain,
                       "peers": list(peers)})

@app.route('/signed_blockchain', methods=['GET'])
def get_encrypted_blockchain():
    """blockchain with signed transactions"""
    chain = []
    # append all the Block class instances
    for block in curr_node.shared_ledger.block_chain:
        chain.append(block.__dict__)
    # return json format data
    return json.dumps({"length": len(chain),
                       "block_chain": chain,
                       "peers": list(peers)})

# Mine the unconfirmed transactions or to say
# Add the pending(i.e. unconfirmed) transactions
# to the blockchain
@app.route('/mine', methods=['GET'])
def mine():
    # new block's index
    idx = blockchain.mine()
    if not idx:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before announcing to the network
        len_chain = len(blockchain.block_chain)
        consensus()
        if len_chain == len(blockchain.block_chain):
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        # Broadcast this new block to peers


        return "Block #{} is mined.".format(blockchain.last_block.index)
    # return "Block #{} is mined.".format(idx)

# Get the unconfirmed transactions (not encrypted, just for demonstration)
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
    # node_address = request.get_json()["node_address"]
    node_address = request.form["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": str(node_address)}
    headers = {'Content-Type': "application/json"}


    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_peer",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['block_chain']
        blockchain = create_chain_from_dump(chain_dump) #
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code

# return all the registered peers
@app.route('/peers', methods=['GET'])
def get_peers():
    return str(list(peers))

def create_chain_from_dump(chain_dump):
    blockchain_from_dump = BlockChain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["timestamp"],
                      block_data["prev_block_hash"],
                      block_data["transaction_list"])

        proof = block_data['block_hash']
        if idx > 0:
            added = blockchain_from_dump.add_block(block, proof)
            if not added:
                raise Exception(
                    "The chain dump is tampered!!")
        else:  # the block is the initial block, no verification needed
            blockchain_from_dump.block_chain.append(block)
    return blockchain_from_dump

# verify and add block
@app.route('/add_block', methods=['POST'])
def add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["timestamp"],
                  block_data["prev_block_hash"],
                  block_data["transaction_list"])
    proof = block_data['block_hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201

# Once a block has been mined, announce it to the network
# Other blocks can simply verify the proof of work and add it to their
#     respective chains.
def announce_new_block(block):
    for peer in peers:
        url = "{}/add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)

def consensus():
    """
    Simple consensus algorithm.
    If a longer valid chain is found,
    replace current chain with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.block_chain)

    for node in peers:
        response = requests.get('{}/blockchain'.format(node))
        length = response.json()['length']
        chain = response.json()['block_chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            # Longer valid chain found!
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False

def fetch_posts():
    """
    Fetch the chain from a blockchain node, parse the
    data, and store it locally.
    """
    get_chain_address = "{}/blockchain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)

        for block in chain["block_chain"]:
            for transaction in block["transaction_list"]:
                transaction["index"] = block["index"]
                transaction["hash"] = block["prev_block_hash"]
                content.append(transaction)

        global posts
        posts = sorted(content,
                       key=lambda k: k['timestamp'],
                       reverse=True)

def format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y, %H:%M:%S")

''' Survey voting operations nodes'''

@app.route('/submit', methods=['POST'])
def submit_transaction_form():
    """
    Endpoint to create a new transaction via our application
    """
    print("submit_transaction_form() is called.")
    options_list = request.form["options"].split('|')
    options_object = {}
    # for opt in options_list:
    #     options_object[opt] =

    post_object = {
        'type': 'survey',
        'content': {
            'title': request.form["title"],
            'description': request.form["description"],
            'options': request.form["options"],
            'timestamp': time.time(),
        },
    }
    # print("post:")
    # print(post_object)

    # Submit a transaction
    new_transaction_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_transaction_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    # Return to the homepage
    return redirect('/')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    idx = request.args.get('index')
    # description = request.args.get('description')
    # user_option = request.args.get('user_option')
    user_option = request.form["bcusr-option-select"]
    post_object = {
        'type': 'vote',
        'content': {
            'corresponding-survey-id': idx,
            'user_option': user_option,
            'timestamp': time.time(),
        },
    }
    print("vote:")
    print(post_object)
    # Submit a transaction
    new_transaction_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_transaction_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    # Return to the homepage
    return redirect('/')

# start app
if __name__ == '__main__':

    # if have arguments in command line, update
    parser = ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', type=str, help='host that app listen on')
    parser.add_argument('-p', '--port', default=8000, type=int, help='port that app listen on')
    args = parser.parse_args()

    # update value of global variables
    CONNECTED_NODE_ADDRESS = 'http://{host}:{port}'.format(host=args.host, port=args.port)
    curr_node = PeerNode(host=args.host, port=args.port)

    # run the app
    app.run(port=args.port, host=args.host, debug=True)