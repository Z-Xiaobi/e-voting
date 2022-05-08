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
from Crypto.Hash import SHA512
import binascii

# from message import Message
from myapp.server.blockchain import BlockChain


# peer-to-peer node, each node is also a miner in my project
class PeerNode(threading.Thread):
    def __init__(self, host, port, timeout=3):
        super(PeerNode, self).__init__()
        self._host_ = host
        self._port_ = port
        self.address_head = "http://"
        # private key and public key
        random = Crypto.Random.new().read
        self._private_key = RSA.generate(1024, random)
        self._public_key = self._private_key.publickey()
        self._signer = PKCS1_v1_5.new(self._private_key)
        # peer data of current node
        self._peers_ = set()
        # self._nodesIn_ = [] # In node
        # self._nodesOut_ = [] # Out node
        self.shared_transactions = []
        # shared_ledger / blockchain
        self.shared_ledger = BlockChain()
        # other
        # self.alive = False
        self.timeout = timeout


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

    def get_peers(self):
        return self._peers_

    def add_peer(self, node_address):
        self._peers_.add(node_address)

    # manipulation on node's temporary transaction list
    def get_transaction_list_size(self):
        return len(self.shared_transactions)

    def clear_transaction_list(self):
        self.shared_transactions = []

# test code
if __name__ == '__main__':
    node = PeerNode(host='127.0.0.1', port=8000)
    print("identity: " + str(node.identity))
    print(node.verify_transaction({'type': 'survey'}, node.identity))