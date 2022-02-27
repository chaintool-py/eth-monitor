# standard imports
import os
import logging
import json

# external imports
from hexathon import strip_0x

logg = logging.getLogger(__name__)


class RuledFilter:

    def __init__(self, rules_filter=None):
        if self.store.chain_dir == None:
            raise RuntimeError('store must be initialized. call RuledFilter.init() first')
        self.rules_filter = rules_filter


    @staticmethod
    def init(store, include_block_data=False, include_tx_data=False):
        RuledFilter.store = store
        RuledFilter.include_block_data = include_block_data
        RuledFilter.include_tx_data = include_tx_data


    @classmethod
    def block_callback(cls, block, extra=None):
        logg.info('processing {}'.format(block))
        cls.store.put_block(block, include_data=cls.include_block_data)


    def filter(self, conn, block, tx, db_session=None):
        if self.rules_filter != None:
            if not self.rules_filter.apply_rules(tx):
                logg.debug('rule match failed for tx {}'.format(tx.hash))
                return False
        return True
