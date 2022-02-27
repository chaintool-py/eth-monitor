# standard imports
import os
import logging
import json

logg = logging.getLogger(__name__)


class NullStore:

    def put_tx(self, tx, include_data=False):
        pass


    def put_block(self, block, include_data=False):
        pass


    def get_block_number(self, v):
        raise FileNotFoundError(v)


    def get_block(self, v):
        raise FileNotFoundError(v)


    def get_tx(self, v):
        raise FileNotFoundError(v)


    def get_rcpt(self, v):
        raise FileNotFoundError(v)


    def __init__(self):
        self.chain_dir = '/dev/null'

    def __str__(self):
        return "Nullstore"
