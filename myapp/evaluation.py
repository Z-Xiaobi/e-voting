# -*- coding='utf-8' -*-
# @Author  : Xiaobi Zhang
# @FileName: evaluation.py

'''Throughput and Latency'''


import time
import requests
import random


if __name__ == '__main__':
    node = 'http://127.0.0.1:8000/'
    new_transaction_address = "{}/new_transaction".format(node)


    transaction_examples = [
        {
            'type': 'survey',
            'content': {
                'title': '',
                'description': '',
                'options': '',
                'timestamp': time.time(),
            },
        },
        {
            'type': 'vote',
            'content': {
                'corresponding-survey-id': 0,
                'user_option': '',
                'timestamp': time.time(),
            },
        }
    ]
    # requests.get(node)
    print("start posting...")
    for _ in range(5):
        post_object = random.choice(transaction_examples)
        requests.post(new_transaction_address,
                      json=post_object,
                      headers={'Content-type': 'application/json'})
    print("end.")
