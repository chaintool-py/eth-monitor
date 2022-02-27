# standard imports
import urllib.request
import json

# external imports
from hexathon import add_0x
from chainlib.eth.block import (
        block_by_hash,
        Block,
        )
from chainlib.eth.tx import (
        Tx,
        receipt,
        )


class Importer:

    def __init__(self, rpc, api_key, filters=[], block_callback=None):
        self.api_key = api_key
        self.filters = filters
        self.rpc = rpc
        self.block_callback = block_callback


    def get(self, address):
        #f = open('sample_import.json', 'r')
        #o = json.load(f)
        #f.close()
        o = self.get_api(address)

        for v in o['result']:
            o = block_by_hash(v['blockHash'])
            r = self.rpc.do(o)
            block = Block(r)

            if self.block_callback != None:
                self.block_callback(block)

            tx_src = block.txs[int(v['transactionIndex'])]

            o = receipt(tx_src['hash'])
            r = self.rpc.do(o)

            tx = Tx.from_src(tx_src, block=block, rcpt=r)

            for fltr in self.filters:
                fltr.filter(self.rpc, block, tx)


    def get_api(self, address):
        a = add_0x(address)
        req = urllib.request.Request(url='https://api.etherscan.io/api?module=account&action=txlist&address={}&tag=latest&api_key={}'.format(a, self.api_key))
        req.add_header('Content-Length', 0)
        req.add_header('Accept', 'application/json')
        r = urllib.request.urlopen(req)
        return json.load(r)
