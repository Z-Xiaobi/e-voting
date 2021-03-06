# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: app.py

# from myapp.server.blockchain import Block, BlockChain, time, json
# from myapp.server.p2p import connected_ip, PeerNode
from server.blockchain import Block, BlockChain, time, json
from server.p2p import connected_ip, PeerNode
from flask import Flask, request, render_template, redirect, url_for, session, g
import datetime
import requests
from argparse import ArgumentParser

# Initialize Application
app = Flask(__name__)

# Node in the blockchain network that application will communicate with
# to fetch and add data.
# CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

# Initialize current node (identity, corresponding blockchain, peers etc)
p_node = PeerNode(host='127.0.0.1', port=8000)
CONNECTED_NODE_ADDRESS = p_node.node_address

valid_trans_num = 0
trans_num = 0
initial_time = time.time()

arrival = []
throughput = []
latency = []

''' App functions'''
def show_throughput():
    current_time = time.time()
    total_time = current_time - initial_time
    # app.logger.info('valid %d, all %d', valid_trans_num, trans_num)
    # app.logger.info('throughput %s tps, arrival trans rate %s tps',
    #                 str(valid_trans_num / total_time),
    #                 str(trans_num / total_time))
    global arrival
    global throughput
    arrival.append(trans_num / total_time)
    throughput.append(valid_trans_num / total_time)


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

        p_node.update_posts(sorted(content,
                                   key=lambda k: k['content']['timestamp'],
                                   reverse=True))

# root page
@app.route('/')
def index():
    fetch_posts()
    return render_template('survey.html',
                           title='My Blockchain based P2P Voting System',
                           # posts=posts,
                           port=p_node.get_port(),
                           host=p_node.get_host(),
                           posts=p_node.get_posts(),
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_timestamp=format_timestamp)

def format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y, %H:%M:%S")

def sign_message(post_object):
    """attach signature and identity to message"""
    encrypted_post_object = {
        'post_object': post_object,
        'signed_post_object': p_node.sign_msg(post_object),  # signed data string
        'identity': p_node.identity,
    }
    return encrypted_post_object

@app.route('/submit', methods=['POST'])
def submit_transaction_form():
    """
    Endpoint to create a new transaction via our application
    """
    post_object = {
        'type': 'survey',
        'content': {
            'title': request.form["title"],
            'description': request.form["description"],
            'options': request.form["options"],
            'timestamp': time.time(),
        },
    }
    encrypted_post_object = sign_message(post_object)
    # Submit a transaction
    new_transaction_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_transaction_address,
                  json=encrypted_post_object,
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
    encrypted_post_object = sign_message(post_object)
    # Submit a transaction
    new_transaction_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_transaction_address,
                  json=encrypted_post_object,
                  headers={'Content-type': 'application/json'})

    # Return to the homepage
    return redirect('/')


'''Basic Peer Operations'''

# Create new transaction
@app.route('/new_transaction', methods=['POST'])
def new_transaction():

    new_trans_start_time = time.time()

    encrypted_data = request.get_json()
    # print("new transaction type:")
    # print(type(encrypted_data))
    # print(encrypted_data)

    if not p_node.verify_msg(msg=encrypted_data["post_object"],
                             signature=encrypted_data["signed_post_object"],
                             sender=encrypted_data["identity"]):
        return "Invalid message", 401

    required_fields = ["type", "content"]
    data = encrypted_data["post_object"]

    global trans_num
    trans_num += 1

    # show_throughput()

    for field in required_fields:
        if not data.get(field):
            return "Invalid transaction data", 404

    # append transaction data to unconfirmed transaction list of current node
    # print("before add to transaction list:")
    # print(p_node.shared_ledger.unconfirmed_transactions)
    p_node.shared_ledger.add_new_transaction(data)
    # print("after add to transaction list:")
    # print(p_node.shared_ledger.unconfirmed_transactions)

    global valid_trans_num
    valid_trans_num += 1

    show_throughput()

    bc_transaction_address = "{}/broadcast_transaction".format(CONNECTED_NODE_ADDRESS)
    for transaction in p_node.shared_ledger.unconfirmed_transactions:
        requests.post(bc_transaction_address,
                      json=transaction,
                      headers={'Content-type': 'application/json'})
    curr_latency = time.time()- new_trans_start_time
    # app.logger.info('latency of transaction %d', curr_latency)
    global latency
    latency.append(curr_latency)
    print(arrival)
    print(throughput)
    print(latency)

    return "Successfully created new transaction on node {}".format(CONNECTED_NODE_ADDRESS), 201


# verify and add block
@app.route('/add_block', methods=['POST'])
def add_block():
    encrypted_data = request.get_json()
    if type(encrypted_data) == str:
        encrypted_data = json.loads(encrypted_data)
    # print(encrypted_data)
    # print(type(encrypted_data))
    if not p_node.verify_msg(msg=encrypted_data["post_object"],
                             signature=encrypted_data["signed_post_object"],
                             sender=encrypted_data["identity"]):
        return "Invalid message", 401

    block_data = encrypted_data["post_object"]
    if type(block_data) == str:
        block_data = json.loads(block_data)
    # print(block_data)
    # print(type(block_data))
    block = Block(block_data["index"],
                  block_data["timestamp"],
                  block_data["prev_block_hash"],
                  block_data["transaction_list"])
    # proof = block_data['block_hash']
    # execute transactions from received block and store into local chain
    # print("add block with transaction list:")
    # print(block.transaction_list)
    added = p_node.execute_transactions(block)
    # print("transaction list after execution:")
    # print(p_node.shared_ledger.last_block.transaction_list)

    if not added:
        return "The block was discarded by the node {}".format(CONNECTED_NODE_ADDRESS), 400

    return "Block added to the chain", 201

# Get a transaction from another node
@app.route('/get_transaction_from', methods=['POST'])
def get_transaction_from():
    # timestamp is the actual time for transaction creation
    # not created on current node
    required_fields = ["type", "content", "timestamp"]
    data = request.get_json()

    for field in required_fields:
        if not data.get(field):
            return "Invalid transaction data", 404

    # append transaction data to unconfirmed transaction list of current node
    p_node.shared_ledger.add_new_transaction(data)

    return "Successfully received new transaction", 201

# Get the unconfirmed transactions (not encrypted, just for demonstration)
@app.route('/unconfirmed', methods=['GET'])
def get_unconfirmed_transcations():
    return json.dumps(p_node.shared_ledger.unconfirmed_transactions)

# retrieve blockchain on local
@app.route('/local_blockchain', methods=['GET'])
def get_local_blockchain():
    """Blockchain on node"""
    chain = []
    # append all the Block class instances
    for block in p_node.shared_ledger.block_chain:
        chain.append(block.__dict__)
    # return json format data
    return json.dumps({"length": len(chain),
                       "block_chain": chain,
                       "peers": list(p_node.get_peers())})


# Get the whole blockchain (not encrypted, just for demonstration)
@app.route('/blockchain', methods=['GET'])
def get_blockchain():

    # Making sure we have the longest chain before announcing to the network
    len_chain = len(p_node.shared_ledger.block_chain)
    consensus()
    if len_chain == len(p_node.shared_ledger.block_chain):
        chain = []
        # append all the Block class instances
        # for block in blockchain.block_chain:
        for block in p_node.shared_ledger.block_chain:
            chain.append(block.__dict__)
    else:
        chain = p_node.shared_ledger
    # return json format data
    return json.dumps({"length": len(chain),
                       "block_chain": chain,
                       "peers": list(p_node.get_peers())})


# Mine the unconfirmed transactions or to say
# Add the pending(i.e. unconfirmed) transactions
# to the blockchain
@app.route('/mine', methods=['GET'])
def mine():
    # produce certificate for potential block
    # new block's index
    idx = p_node.shared_ledger.mine()
    if not idx:
        return "No transactions to mine."
    else:
        # Making sure we have the longest chain before announcing to the network
        len_chain = len(p_node.shared_ledger.block_chain)
        consensus()
        if len_chain == len(p_node.shared_ledger.block_chain):
            # broadcast the recently mined block to the network
            bc_block_address = "{}/broadcast_block".format(CONNECTED_NODE_ADDRESS)
            requests.post(bc_block_address,
                          json=json.dumps(p_node.shared_ledger.last_block.__dict__, sort_keys=True),
                          headers={'Content-type': 'application/json'})
        return "Block #{} is mined.".format(p_node.shared_ledger.last_block.index)

# Add a new peer/node to the network
@app.route('/register_peer', methods=['POST'])
def register_new_peers():
    # The host address to the peer node
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data: node_address", 400
    # Add the node to the peer list
    p_node.add_peer(node_address)
    # Return the blockchain to this newly registered peer
    # so that it can synchronize
    return get_blockchain()

# Register the remote node as current node's peer
# and sync the blockchain  with the remote node.
@app.route('/register_with_node', methods=['POST'])
def register_with_existing_node():
    # node_address = request.get_json()["node_address"]
    node_address = request.form["node_address"]
    if not node_address:
        return "Invalid data", 400

    # data = {"node_address": str(node_address)}
    # the data send to peers
    data = {"node_address": str(CONNECTED_NODE_ADDRESS)}
    headers = {'Content-Type': "application/json"}

    try:
        # Make a request to register with remote node and obtain information
        response = requests.post(node_address + "/register_peer",
                                 data=json.dumps(data), headers=headers)

        # if the target node has successfully registered current node as peer
        if response.status_code == 200:
            # update chain and the peers
            chain_dump = response.json()['block_chain']
            # update current node's peer list
            p_node.blockchain = create_chain_from_dump(chain_dump)
            peer_list = response.json()['peers']
            peer_list.append(node_address)
            peer_list.remove(CONNECTED_NODE_ADDRESS)
            p_node.update_peers(peer_list)
            chain_dump = sign_message(chain_dump)
            # new node download all the verified blocks in network
            peer_response = requests.post(node_address + "/create_chain_from",
                                          data=json.dumps(chain_dump),
                                          headers=headers)
            if peer_response.status_code == 201:
                return "Registration successful", 201
            else:
                return peer_response.content, peer_response.status_code
        else:
            # if something goes wrong, pass it on to the API response
            return response.content, response.status_code
    except requests.ConnectionError as rq_error:
        print("Connection refused by the server.")
        print(rq_error)

# return all registered peers/nodes of current node
@app.route('/peers', methods=['GET'])
def get_peers():
    return " peer list:" + str(list(p_node.get_peers()))

'''Miner Functions'''
@app.route('/consensus', methods=['GET'])
def consensus():
    """
    If a longer valid chain is found,
    replace current chain with it.
    """

    longest_chain = None
    current_len = len(p_node.shared_ledger.block_chain)

    for peer in p_node.get_peers():
        try:
            response = requests.get('{}/local_blockchain'.format(peer))
            length = response.json()['length']
            chain = response.json()['block_chain']
            if length > current_len and \
                    p_node.shared_ledger.check_chain_validity(chain):
                # Longer valid chain found!
                current_len = length
                longest_chain = chain
        except requests.exceptions.ConnectionError:
            print('Connection Error on node: {}. Remove from network.'.format(peer))
            p_node.remove_peer(peer)

    # update chain as the longest chain in network
    if longest_chain:
        bc_chain_address = "{}/broadcast_blockchain".format(CONNECTED_NODE_ADDRESS)
        requests.post(bc_chain_address,
                      json=json.dumps(p_node.shared_ledger),
                      headers={'Content-type': 'application/json'})

        return True

    return False

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
    return blockchain_from_dump


@app.route('/create_chain_from', methods=['POST'])
def create_chain_from():
    """
    update the chain from miner node
    (who called register peer with current node)
    """
    encrypted_data = request.get_json()
    # print(encrypted_data)
    # print(type(encrypted_data))
    if type(encrypted_data) == str:
        encrypted_data = json.loads(encrypted_data)
    if not p_node.verify_msg(msg=encrypted_data["post_object"],
                             signature=encrypted_data["signed_post_object"],
                             sender=encrypted_data["identity"]):
        return "Invalid message", 401

    chain_dump = encrypted_data["post_object"]
    # print("create_chain_from")
    # print(chain_dump)
    new_block_chain = create_chain_from_dump(chain_dump)
    # update local chain
    p_node.shared_ledger = new_block_chain
    return "Update chain successful", 201

@app.route('/broadcast_transaction', methods=['POST'])
def broadcast_transaction():
    """
    Broadcast the transaction request (json) to the entire network from current node.
    """
    transaction_data = request.get_json()
    transaction_data = sign_message(transaction_data)
    for peer in p_node.get_peers():
        new_transaction_address = "{}/new_transaction".format(peer)
        peer_response = requests.post(new_transaction_address,
                                      json=transaction_data,
                                      headers={'Content-type': 'application/json'})
        if peer_response.status_code != 201:
            return peer_response.content, peer_response.status_code
    return "Broadcasting transactions successful", 201


@app.route('/broadcast_block', methods=['POST'])
def broadcast_block():
    """Once a block has been mined, broadcast it to the network
    Other blocks can simply verify the proof of work and add it
    to their respective chains."""
    block_data = request.get_json()
    block_data = sign_message(block_data)
    for peer in p_node.get_peers():
        url = "{}/add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        # requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)
        peer_response = requests.post(url, json=block_data, headers=headers)
        if peer_response.status_code != 201:
            return peer_response.content, peer_response.status_code
    return "Broadcasting block successful", 201

@app.route('/broadcast_blockchain', methods=['POST'])
def broadcast_blockchain():
    """
    Broadcast the longest blockchain to the entire network from current node.
    """
    response = requests.get('{}/local_blockchain'.format(CONNECTED_NODE_ADDRESS))
    chain_dump = response.json()['block_chain']
    chain_dump = sign_message(chain_dump)
    for peer in p_node.get_peers():
        update_chain_address = "{}/create_chain_from".format(peer)
        requests.post(update_chain_address,
                      json=chain_dump,
                      headers={'Content-type': 'application/json'})


# start app
if __name__ == '__main__':

    # if have arguments in command line, update
    parser = ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', type=str, help='host that app listen on')
    parser.add_argument('-p', '--port', default=8000, type=int, help='port that app listen on')
    args = parser.parse_args()

    # update value of global variables
    CONNECTED_NODE_ADDRESS = 'http://{host}:{port}'.format(host=args.host, port=args.port)
    print('Start node {}'.format(CONNECTED_NODE_ADDRESS))
    p_node = PeerNode(host=args.host, port=args.port)

    # run the app
    app.run(port=args.port, host=args.host, debug=True)