# standard imports
import logging
import json

# externa imports
from hexathon import (
        uniform as hex_uniform,
        strip_0x,
        )

logg = logging.getLogger(__name__)


class AddressIndex:

    def __init__(self, rpc, store):
        self.rpc = rpc
        self.store = store
        self.addresses = {}


    def load_address_tx(self, address):
        address = hex_uniform(strip_0x(address))
        if self.addresses.get(address) == None:
            self.addresses[address] = []
        txs = {}
        for tx_hash in self.store.get_address_tx(address):
            j = self.store.get_tx(tx_hash)
            tx = json.loads(j)
            logg.debug('tx {}'.format(tx))

            block_number = None
            try:
                block_number = int(tx['block_number'], 16)
            except: 
                block_number = int(tx['block_number'])

            tx_index = None
            try:
                tx_index = int(tx['transaction_index'], 16)
            except: 
                tx_index = int(tx['transaction_index'])

            k = '{}.{}'.format(block_number, tx_index)

            txs[float(k)] = tx

        ks = list(txs.keys())
        ks.sort()
        ks.reverse()
        for k in ks:
            self.addresses[address].append(txs[k])
        
        return len(ks)


    def get_address(self, address):
        address = hex_uniform(strip_0x(address))
        return self.addresses[address]
