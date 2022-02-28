# standard imports
import json
from jsonrpc_std.parse import jsonrpc_from_dict
import logging

# external imports
from hexathon import strip_0x

logg = logging.getLogger(__name__)

class CacheRPC:

    def __init__(self, rpc, store):
        self.rpc = rpc
        self.store = store


    def do(self, o):
        req = jsonrpc_from_dict(o)
        r = None
        if req['method'] == 'eth_getBlockByNumber':
            block_number = req['params'][0]
            v = int(strip_0x(block_number), 16)
            try:
                j = self.store.get_block_number(v)
                r = json.loads(j)
                logg.debug('using cached block {} -> {}'.format(v, r['hash']))
            except FileNotFoundError:
                pass
        elif req['method'] == 'eth_getBlockByHash':
            block_hash = req['params'][0]
            v = strip_0x(block_hash)
            try:
                j = self.store.get_block(v)
                r = json.loads(j)
                logg.debug('using cached block {}'.format(r['hash']))
            except FileNotFoundError as e:
                logg.debug('not found {}'.format(e))
                pass
        elif req['method'] == 'eth_getTransactionReceipt':
            tx_hash = req['params'][0]
            j = None
            try:
                tx_hash = strip_0x(tx_hash)
                j = self.store.get_rcpt(tx_hash)
                r = json.loads(j)
                logg.debug('using cached rcpt {}'.format(tx_hash))
            except FileNotFoundError as e:
                logg.debug('no file {}'.format(e))
                pass
                
#        elif req['method'] == 'eth_getTransactionByHash':
#            raise ValueError(o)
#        elif req['method'] == 'eth_getTransactionByBlockHashAndIndex':
#            logg.debug('trying tx index {}'.format(o))
#            v = req['params'][0]
#            j = None
#            try:
#                j = self.store.get_block(v)
#            except FileNotFoundError:
#                pass
#               
#            if j != None:
#                o = json.loads(j)
#                idx = int(req['params'][1], 16)
#                v = r['transactions'][idx] 
#                j = None
#                try:
#                    j = self.store.get_tx(v)
#                except FileNotFoundError:
#                    pass
#
#                if j != None:
#                    r = json.loads(j)
#                    logg.debug('using cached tx {} -> {}'.format(req['params'], r['hash']))

        if r == None:
            logg.debug('passthru {}'.format(o))
            r = self.rpc.do(o)

        return r
