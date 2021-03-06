# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: BlockChain.py

# hashing
from hashlib import sha256
import json
# timestamp
import time


class Block:
    def __init__(self, index, timestamp, prev_block_hash, transaction_list):
        """
        Constructor for class Block
        :param index: unique id of a Block
        :param timestamp: the time when content was created
        :param prev_block_hash: previous block's hash
        :param transaction_list: transactions
        """
        self.index = index
        self.timestamp = timestamp
        self.prev_block_hash = prev_block_hash
        self.transaction_list = transaction_list
        self.nonce = 0
        # # block data
        # self.data = "|".join(transaction_list) + "|" + prev_block_hash
        # # current block hash
        # self.block_hash = sha256(self.data.encode()).hexdigest()

    def generate_hash(self):
        """
        :return: hash of json format block object instance
        """
        data = json.dumps(self.__dict__, sort_keys=True)
        return sha256(data.encode()).hexdigest()


class BlockChain:

    difficulty = 3

    def __init__(self):
        self.block_chain = []
        self.unconfirmed_transactions = []
        self.create_initial_block()

    def create_initial_block(self):
        """
        Generate and appends initial block to the block chain.
        Initialize this block with index 0, previous_hash 0, and a valid hash.
        """
        initial_block = Block(index=0,
                              timestamp=time.time(),
                              prev_block_hash="0",
                              transaction_list=[])
        initial_block.block_hash = initial_block.generate_hash()
        self.block_chain.append(initial_block)

    @property
    def last_block(self):
        """
        Retrieve the most recent block in the block chain.
        Note that The block chain will always have at least one block.
        """
        return self.block_chain[-1]

    def proof_of_work(self, block):
        """
        Avoid hash update with old prev_block_hash value.
        Exploit asymmetry Function that tries different values of
        the nonce (editable dummy data) to get a hash
        that satisfies difficulty criteria.
        """
        block.nonce = 0

        generated_hash = block.generate_hash()

        while not generated_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            generated_hash = block.generate_hash()

        return generated_hash

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid and satisfies the difficulty criteria.
        """
        return (block_hash.startswith('0' * self.difficulty) and
                block_hash == block.generate_hash())

    def add_block(self, block, proof):
        """
        Verify the data (proof of work)
        Verify order of transactions is preserved (prev_block_hash field)
        :param block: a created block
        :param proof: hash
        :return:
        """
        prev_block_hash = self.last_block.block_hash

        if prev_block_hash != block.prev_block_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False
        # dynamic attribute
        block.block_hash = proof
        self.block_chain.append(block)
        return True

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        The transactions will be initially stored as a pool of unconfirmed transactions.
        Mining process on miner: Add the pending transactions to the blockchain
        by adding them to the block and calculate Proof Of Work.
        """
        # if no unconfirmed transactions
        if not self.unconfirmed_transactions:
            return False

        new_block = Block(index=self.last_block.index + 1,
                          timestamp=time.time(),
                          prev_block_hash=self.last_block.block_hash,
                          transaction_list=self.unconfirmed_transactions,)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        return new_block.index

    def check_chain_validity(cls, chain):
        """
        A helper method to check if the entire blockchain is valid.
        """
        result = True
        previous_hash = "0"

        # Iterate through every block
        for block in chain:
            block_hash = block.block_hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block.block_hash) or \
                    previous_hash != block.prev_block_hash:
                result = False
                break

            block.block_hash, previous_hash = block_hash, block_hash

        return result

