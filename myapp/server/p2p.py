# -*- coding='utf-8' -*-
# @Time    : 4/30/22 16:47
# @Author  : Xiaobi Zhang
# @FileName: p2p.py


# import os
import sys
import json
# import time
# import node
import socket
import threading
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA512
import binascii

# from message import Message
from myapp.server.blockchain import BlockChain


class PeerConnection(threading.Thread):
    def __init__(self, host: str, port: int, peer_node, c_socket: socket):
        """
        :param host: host of current input peer node
        :param port: port of current input peer node
        :param peer_node: node that connect to another PeerNode's server service
        :param c_socket: socket that is associated with the client connection.
        """
        super(PeerConnection, self).__init__()
        self._host_ = host
        self._port_ = port
        self.peer_node = peer_node
        self.c_socket = c_socket

# peer-to-peer node, each node is also a miner in my project
class PeerNode(threading.Thread):
    def __init__(self, host: str, port: int, timeout=3):
        super(PeerNode, self).__init__()
        self._host_ = host
        self._port_ = port
        self._address_head = "http://"
        self._server_sock = None
        self._client_sock = None
        self.timeout = timeout
        self._stop_flag_ = threading.Event()
        # private key and public key
        random = Crypto.Random.new().read
        self._private_key = RSA.generate(1024, random)
        self._public_key = self._private_key.publickey()
        self._signer = PKCS1_v1_5.new(self._private_key)
        # peer nodes' info (in json) of current node
        self._peers_ = set()
        # self._nodesIn_ = [] # In node
        # self._nodesOut_ = [] # Out node
        self.shared_transactions = []
        # shared_ledger / blockchain
        self.shared_ledger = BlockChain()
        self.start_listening()


    @property
    def identity(self):
        """hex representation with binary encoding (DER) of the public key"""
        return binascii.hexlify(self._public_key.exportKey(format='DER')).decode('ascii')

    # sender
    def sign_transaction(self, transaction):
        """sign given transaction"""
        private_key = self._private_key
        signer = PKCS1_v1_5.new(private_key)
        h = SHA512.new(str(transaction).encode('utf8')) # hash
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    def add_new_transaction(self, transaction):
        """
        add a single signed transaction to current node's transaction list
        :param transaction: signed transaction
        """
        self.shared_transactions.append(transaction)
        self.shared_ledger.add_new_transaction(self.sign_transaction(transaction))

    # receiver
    def verify_transaction(self, transaction, sender):
        """
        validate a signed transaction, confirmed it belongs to sender
        :param transaction: transaction data
        :param sender: identity of sender
        :return: if given transaction is valid or not
        """
        # get the public key from sender's identity
        sender_public_key = RSA.importKey(binascii.unhexlify(sender.encode('ascii')))

        # decode the encoded signature
        sign = self.sign_transaction(transaction)
        signed_h = binascii.unhexlify(sign.encode('ascii'))

        # verify via hash of transaction message and signature
        verifier = PKCS1_v1_5.new(sender_public_key)
        h = SHA512.new(str(transaction).encode('utf8'))
        verification = verifier.verify(h, signed_h)
        return verification

    def add_new_transaction_from(self, transaction, sender):
        verification = self.verify_transaction(transaction, sender)
        if verification:
            self.shared_ledger.add_new_transaction(self.sign_transaction(transaction))
            return True
        else:
            return False

    # manipulation on node's temporary transaction list
    def get_transaction_list_size(self):
        return len(self.shared_transactions)

    def clear_transaction_list(self):
        self.shared_transactions = []

    ## Getters
    def get_host(self):
        host = self._host_
        return host

    def get_port(self):
        port = self._port_
        return port

    def get_addr_head(self):
        addr = self._address_head
        return addr

    def get_addr(self):
        return "{0}{1}:{2}".format(self._address_head, self._host_, self._port_)

    def get_peers(self):
        peers = list(self._peers_)
        return peers

    def get_stop_flag(self):
        sf = self._stop_flag_
        return sf

    ## connections
    def start_listening(self):
        # TCP/IP
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.bind((self._host_, self._port_))
        self._server_sock.listen()
        self._server_sock.settimeout(self.timeout)
        print('Waiting for incoming connections.')

    def send_to_peers(self, msg) -> None:
        """ Send a message to all the peer nodes that are connected with this node."""
        for peer_node in self.get_peers():
            self.send_to_peer(msg, peer_node)

    def send_to_peer(self, msg, peer_node) -> None:
        """Send a message to given peer node"""
        if peer_node in self._peers_:
            peer_node.send(msg, compression='None')
        else:
            print("Can not send message to node: {}, "
                  "because it is not peer of current node".format(peer_node.get_addr()))

    # add new peer node
    def connect_with_node(self, host: str, port: int, reconnect: bool = False) -> bool:
        if host == self._host_ and port == self._port_:
            print("Cannot connect with yourself.")
            return False
        for peer_node in self._peers_:
            if peer_node.get_host() == host and peer_node.get_port() == port:
                print("Peer node already in list.")
                return False

        peer_node_ids = [peer_node_info['identity'] for peer_node_info in self._peers_]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connecting to {host} port {port}".format(host=host, port=port))
            sock.connect((host, port))

            # Send current node's identity and port to the connected node
            curr_node_info_data = {
                'identity': self.identity,
                'host': self.get_host(),
                'port': self.get_port(),
                'address_head': self.get_addr_head(),
            }
            sock.send(str(curr_node_info_data).encode('utf-8'))
            # When a node is connected, it sends its info data
            peer_node_info_data = json.loads(sock.recv(4096).decode('utf-8'))

            # Just in case received wrong information (self or node in peer list)
            if self.identity == peer_node_info_data['identity'] \
                    or self.identity in peer_node_ids:
                sock.send("A connection already exits.".encode('utf-8'))
                sock.close()
                return True

            # thread_client = self.create_new_connection(sock, connected_node_id, host, port)
            # thread_client.start()
            #
            # self.nodes_outbound.append(thread_client)
            # self.outbound_node_connected(thread_client)

            return True

        except Exception as error:
            print(f"connect_with_node: Could not connect with node. ({error})")
            return False



# test code
if __name__ == '__main__':
    node = PeerNode(host='127.0.0.1', port=8000)
    print("identity: " + str(node.identity))
    print(node.verify_transaction({'type': 'survey'}, node.identity))