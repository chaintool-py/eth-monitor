# standard imports
import os
import logging

# external imports
from chainsyncer.backend.file import chain_dir_for
from leveldir.numeric import NumDir
from leveldir.hex import HexDir

logg = logging.getLogger(__name__)

base_dir = '/var/lib'


class RuledFilter:

    cache_root = os.path.join(base_dir, 'eth_monitor')
    chain_dir = None
    cache_dir = None
    block_num_path = None
    block_num_dir = None
    block_hash_path = None
    block_hash_dir = None
    tx_path = None
    tx_dir = None


    def __init__(self, rules_filter=None):
        if self.chain_dir == None:
            raise RuntimeError('filter must be initialized. call RuledFilter.init() first')
        self.rules_filter = rules_filter


    @staticmethod
    def init(chain_spec, cache_root=None, rules_filter=None):
        if cache_root != None:
            RuledFilter.cache_root = os.path.join(cache_root, 'eth_monitor')
        RuledFilter.chain_dir = chain_dir_for(RuledFilter.cache_root)
        RuledFilter.cache_dir = os.path.join(RuledFilter.chain_dir, 'cache')
        RuledFilter.block_num_path = os.path.join(RuledFilter.cache_dir, 'block', 'num')
        RuledFilter.block_num_dir = NumDir(RuledFilter.block_num_path, [100000, 1000])
        RuledFilter.block_hash_path = os.path.join(RuledFilter.cache_dir, 'block', 'hash')
        RuledFilter.block_hash_dir = HexDir(RuledFilter.block_hash_path, 32, levels=2)
        RuledFilter.tx_path = os.path.join(RuledFilter.cache_dir, 'tx')
        RuledFilter.tx_dir = HexDir(RuledFilter.tx_path, 32, levels=2)


    def filter(self, conn, block, tx, db_session=None):
        if self.rules_filter != None:
            if not self.rules_filter.apply_rules(tx):
                logg.debug('rule match failed for tx {}'.format(tx.hash))
                return
        logg.info('applying filter {}'.format(self))
        self.ruled_filter(conn, block, tx, db_session=db_session)
