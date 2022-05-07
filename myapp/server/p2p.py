# -*- coding='utf-8' -*-
# @Time    : 4/30/22 16:47
# @Author  : Xiaobi Zhang
# @FileName: p2p.py


# import os
# import sys
# import json
# import time
# import node
import socket
import threading
import Crypto
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
import binascii

# from message import Message
from myapp.server.blockchain import BlockChain


# peer-to-peer node
class PeerNode():
    def __init__(self, host, port, timeout):
        super(PeerNode, self).__init__()
        self._host_ = host
        self._port_ = port
        # private key and public key
        random = Crypto.Random.new().read
        self._private_key = RSA.generate(1024, random)
        self._public_key = self._private_key.publickey()
        self._signer = PKCS1_v1_5.new(self._private_key)
        # peers of current node
        self._peers_ = set()
        self._nodesIn_ = [] # In node
        self._nodesOut_ = [] # Out node
        self.shared_transactions = []
        self.shared_ledger = []
        self.alive = False
        self.timeout = timeout
        self.bc = BlockChain()

        @property
        def identity(self):
            return binascii.hexlify(self._public_key.exportKey(format='DER')).decode('ascii')

        def sign_transaction(self, transaction):
            private_key = self._private_key
            signer = PKCS1_v1_5.new(private_key)
            h = SHA.new(str(self.to_dict()).encode('utf8'))
            return binascii.hexlify(signer.sign(h)).decode('ascii')

        ## Peers
        def get_peers(self):
            return self.peers

'''
    def setserveralive(self):
        self.alive = True

    def is_any_node_alive(self):
        if self._nodesIn_ or self._nodesOut_:
            return True
        return False

    def scale_up(self):
        self._sock_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_.bind(('', self._port_))
        self._sock_.listen()
        self._sock_.settimeout(self.timeout)
        self.setserveralive()
        logging.info('Server: is waiting for income connections.')

    def write_message(self, type, flag, content=None):
        m = Message()
        message = m.create(type, flag, [content])
        self.send_to_nodes(message)

    def send_to_nodes(self, data):
        nodes_alive = False
        if self._nodesIn_:
            for node in self._nodesIn_:
                node.send(data)
                nodes_alive = True

        if self._nodesOut_:
            for node in self._nodesOut_:
                node.send(data)
                nodes_alive = True

        if not nodes_alive:
            logging.info('Server: could not send message! No node connected.')

    def create_newserverconnection(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
        except socket.timeout:
            self.closeserverconnection('timeout')
        except:
            logging.error("Server: could not connect to OutPeer: {0}:{1}!".format(host, port))
            return False
        return sock

    def connect_with_peer(self, host, port):
        if self.validate_new_peer_connection(host, port):
            index = len(self._nodesOut_)
            sock = self.create_newserverconnection(host, port)
            if not sock:
                return False
            outbound_peer = node.Node(self, sock, (host, port), index, 'Out')
            outbound_peer.start()
            self._nodesOut_.append(outbound_peer)
            logging.info('Server: connected to OutPeer: #{0} {1}:{2}.'.format(index, host, port))

    def validate_new_peer_connection(self, host, port):
        if host == self._host_ and port == self._port_:
            logging.error('Server: cannot connect to own host!')
            return False

        for node in self._nodesOut_:
            if node._host_ == host and node._port_ == port:
                logging.critical('Server: Already connected with this Outpeer!')
                return False

        for node in self._nodesIn_:
            if node._host_ == host and node._port_ == port:
                logging.critical('Server: Already connected with this Inpeer!')
                return False
        return True

    def closeserverconnection(self, msg):
        if not self._stop_flag_.is_set():
            self.stop()
            self.close_connected_nodes()
            logging.info('Server: closed his connection due to {}.'.format(msg))
            self._sock_.close()
        sys.exit(1)

    def close_connected_nodes(self):
        for node in self._nodesIn_:
            if not node._stop_flag_.is_set():
                node.close_connection('Server being shut down')
                node.join()

        for node in self._nodesOut_:
            if not node._stop_flag_.is_set():
                node.close_connection('Server being shut down')
                node.join()

    def stop(self):
        if not self._stop_flag_.is_set():
            self._stop_flag_.set()

    def run(self):
        self.scale_up()
        while not self._stop_flag_.is_set():
            index = len(self._nodesIn_)
            try:
                peer_socket, peer_addr = self._sock_.accept()
            except socket.timeout:
                self.closeserverconnection('timeout')
            inbound_peer = node.Node(self, peer_socket, peer_addr, index, 'In')
            inbound_peer.start()
            logging.info('Server: connected to InPeer: #{0} {1}:{2}.'.format(index, peer_addr[0], peer_addr[1]))
            self._nodesIn_.append(inbound_peer)

        self.closeserverconnection('finished run.')
'''