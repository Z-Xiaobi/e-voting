# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: p2p.py
import socket
import Cryptodome
import Cryptodome.Random
from Cryptodome.PublicKey import RSA
# from Crypto.Signature import PKCS1_v1_5 # outdated package
from Cryptodome.Signature import pkcs1_15
from Cryptodome.Hash import SHA512
import binascii

# from message import Message
# from myapp.server.blockchain import BlockChain
from .blockchain import BlockChain, Block
import time


''' Some functions for peer communications '''


def connected_ip(remote):
    if remote != '127.0.0.1':
        return remote
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('0.0.255.255', 1))
        address = s.getsockname()[0]
    except socket.error:
        address = '127.0.0.1'
    finally:
        s.close()
    return address


class PeerNode:
    def __init__(self, host: str, port: int):
        self._host_ = host
        self._port_ = port
        self._address_head = "http://"
        # private key and public key
        random = Cryptodome.Random.new().read
        self._private_key = RSA.generate(1024, random)
        self._public_key = self._private_key.publickey()
        self._signer = pkcs1_15.new(self._private_key)
        # peer nodes' address
        self._peers = set()
        self._posts = [] # local pool for executed shared_transactions
        # shared_ledger / blockchain
        self.shared_ledger = BlockChain()


    @property
    def identity(self):
        """hex representation with binary encoding (DER) of the public key"""
        return binascii.hexlify(self._public_key.exportKey(format='DER')).decode('ascii')

    # sender
    def sign_msg(self, msg):
        """sign given message"""
        private_key = self._private_key
        signer = pkcs1_15.new(private_key)
        h = SHA512.new(str(msg).encode('utf8')) # message hash
        # sign message hash, get
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    # receiver
    def verify_msg(self, msg, signature, sender):
        """
        validate a signed transaction, confirmed it belongs to sender
        :param msg: message from sender
        :param signature: signature of the message from sender
        :param sender: identity of sender
        :return: if given transaction is valid or not
        """
        # get the public key from sender's identity
        # binascii.hexlify(self._public_key.exportKey(format='DER')).decode('ascii')
        sender_public_key = RSA.importKey(binascii.unhexlify(sender.encode('ascii')))

        # decode the encoded signature, get the byte string of signature
        # sign = self.sign_msg(msg)
        # signed_h = binascii.unhexlify(sign.encode('ascii'))
        signed_h = binascii.unhexlify(signature.encode('ascii'))

        # verify via hash of transaction message and signature
        verifier = pkcs1_15.new(sender_public_key)
        h = SHA512.new(str(msg).encode('utf8'))
        try:
            verifier.verify(msg_hash=h, signature=signed_h)
            valid = True
        except ValueError:
            valid = False
        return valid

    @property
    def node_address(self):
        return "{0}{1}:{2}".format(self._address_head, self._host_, self._port_)

    def execute_transactions(self, received_block: Block):
        """post the transactions on local app"""
        # upcoming new added block's transactions date
        global_transactions = received_block.transaction_list
        # transaction need to be uploaded to local chain
        local_transactions = []
        for unconfirmed_transaction in self.shared_ledger.unconfirmed_transactions:
            # check if this transaction is broadcasted from miner (in the upcoming new added block)
            if unconfirmed_transaction in global_transactions:
                self._posts.append(unconfirmed_transaction)
                local_transactions.append(unconfirmed_transaction)

        # submit validated transactions to local chain
        new_block = Block(index=self.shared_ledger.last_block.index + 1,
                          timestamp=time.time(),
                          prev_block_hash=self.shared_ledger.last_block.block_hash,
                          transaction_list=local_transactions, )

        proof = self.shared_ledger.proof_of_work(new_block)
        added = self.shared_ledger.add_block(new_block, proof)

        if not added:
            return False

        # remove submitted transactions in unconfirmed list
        # self.shared_ledger.unconfirmed_transactions = list(set(self.shared_ledger.unconfirmed_transactions))
        for confirmed_transaction in local_transactions:
            self.shared_ledger.unconfirmed_transactions.remove(confirmed_transaction)

        return True

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

    def get_posts(self):
        posts = self._posts
        return posts

    def update_posts(self, posts):
        self._posts = posts
        if self._posts == posts:
            return True
        else:
            return False

    def get_peers(self):
        peers = self._peers
        return peers

    def update_peers(self, peer_data):
        return self._peers.update(peer_data)

    def update_all_peers(self, peer_list):
        self._peers = peer_list
        if self._peers == peer_list:
            return True
        else:
            return False

    def add_peer(self, peer_addr):
        return self._peers.add(peer_addr)

    def remove_peer(self, peer_addr):
        return self._peers.remove(peer_addr)

if __name__ == '__main__':
    # random = Cryptodome.Random.new().read
    # private_key = RSA.generate(1024, random)
    # public_key = private_key.publickey()
    # print("pub")
    # print(public_key)
    # identity = binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    # # identity = binascii.hexlify(public_key.exportKey(format='DER'))
    # # identity = public_key.exportKey(format='DER')
    # print("identity")
    # print(identity)
    # public_key_from_id = RSA.importKey(binascii.unhexlify(identity.encode('ascii')))
    # # public_key_from_id = RSA.importKey(binascii.unhexlify(identity))
    # # public_key_from_id = RSA.importKey(identity)
    # print("pub from id")
    # print(public_key_from_id)
    # print(public_key.n, public_key.e)
    # print(public_key_from_id.n, public_key_from_id.e)
    # msg = 'hello world'
    # a = SHA512.new(str(msg).encode('utf8'))
    # b = SHA512.new(str(msg).encode('utf8'))
    # print(a)
    # print(b)
    # signer = pkcs1_15.new(private_key)
    # signed_a = signer.sign(a)
    # verifier = pkcs1_15.new(public_key)
    # print("received message hash")
    # print(verifier.verify(msg_hash=b, signature=signed_a))


    p_node = PeerNode('0.0.0.0', 6666)
    msg = 'hello world'
    sig = p_node.sign_msg(msg)
    print("message:", msg)
    print("signature", sig)
    print("verify:", str(p_node.verify_msg(msg=msg, signature=sig, sender=p_node.identity)))

