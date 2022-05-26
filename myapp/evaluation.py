# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: evaluation.py

"""Throughput and Latency"""


import time
import requests
# import random
from server.p2p import *
import threading
import math

# example sender
irandom = Cryptodome.Random.new().read
private_key = RSA.generate(1024, irandom)
public_key = private_key.publickey()
signer = pkcs1_15.new(private_key)
identity = binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
node_addr = 'http://127.0.0.1:8000/'
new_transaction_address = "{}/new_transaction".format(node_addr)

# example transactions
transaction_examples = [
        {
            'type': 'survey',
            'content': {
                'title': '',
                'description': '',
                'options': 'A|B',
                'timestamp': time.time(),
            },
        },
        {
            'type': 'vote',
            'content': {
                'corresponding-survey-id': 0,
                'user_option': 'A',
                'timestamp': time.time(),
            },
        }
    ]
trans = {
            'type': 'survey',
            'content': {
                'title': '',
                'description': '',
                'options': 'A|B',
                'timestamp': time.time(),
            },
        }
# post_object = random.choice(transaction_examples)
# sign post_object
h = SHA512.new(str(trans).encode('utf8'))  # message hash
signed_h = binascii.hexlify(signer.sign(h)).decode('ascii')

encrypted_post_object = {
    'post_object': trans,
    'signed_post_object': signed_h,  # signed data string
    'identity': identity,
}

def send_transaction(encrypted_post_obj):
    """
    post one example transaction
    """
    requests.post(new_transaction_address,
                  json=encrypted_post_obj,
                  headers={'Content-type': 'application/json'})

num = 150
start_trans_time = time.time()
for _ in range(num):
    t = threading.Thread(target=send_transaction, args=(encrypted_post_object,))
    t.start()
    t.join()

end_time = time.time() - start_trans_time
print(end_time)
print("tps: ", str(num / end_time))
# 1 thread 0.2978811264038086, 3.3570438385 tps





