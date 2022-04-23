# -*- coding='utf-8' -*-
# @Time    : 4/23/22 16:06
# @Author  : Xiaobi Zhang
# @FileName: BlockChain.py
# @Github: https://github.com/Z-Xiaobi

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
    def __init__(self):
        self.block_chain = []
        self.create_initial_block()

    def create_initial_block(self):
        """
        Generate and appends initial block to the block chain.
        Initialize this block with index 0, previous_hash 0, and a valid hash.
        """
        initial_block = Block(0, [], time.time(), "0")
        initial_block.block_hash = initial_block.generate_hash()
        self.block_chain.append(initial_block)

    def get_last_block(self):
        """
        Retrieve the most recent block in the block chain.
        Note that The block chain will always have at least one block.
        """
        return self.block_chain[-1]
