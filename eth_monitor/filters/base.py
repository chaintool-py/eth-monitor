# standard imports
import os
import logging
import json

# external imports
from chainsyncer.backend.file import chain_dir_for
from leveldir.numeric import NumDir
from leveldir.hex import HexDir
from hexathon import strip_0x

logg = logging.getLogger(__name__)

base_dir = '/var/lib'


class RuledFilter:

    cache_root = None
    chain_dir = None
    cache_dir = None
    block_num_path = None
    block_src_path = None
    block_hash_path = None
    block_num_dir = None
    block_src_dir = None
    block_hash_dir = None
    address_path = None
    address_dir = None
    tx_path = None
    tx_dir = None
    tx_raw_dir = None


    def __init__(self, rules_filter=None):
        if self.chain_dir == None:
            raise RuntimeError('filter must be initialized. call RuledFilter.init() first')
        self.rules_filter = rules_filter


    @staticmethod
    def init(chain_spec, cache_root=base_dir, rules_filter=None, include_block_data=False, include_tx_data=False):
        RuledFilter.cache_root = os.path.join(
            cache_root,
            'eth_monitor',
            chain_spec.engine(),
            chain_spec.fork(),
            str(chain_spec.chain_id()),
            )
        RuledFilter.chain_dir = chain_dir_for(RuledFilter.cache_root)
        RuledFilter.cache_dir = os.path.join(RuledFilter.chain_dir, 'cache')
        RuledFilter.block_src_path = os.path.join(RuledFilter.cache_dir, 'block', 'src')
        RuledFilter.block_src_dir = NumDir(RuledFilter.block_src_path, [100000, 1000])
        RuledFilter.block_num_path = os.path.join(RuledFilter.cache_dir, 'block', 'num')
        RuledFilter.block_num_dir = NumDir(RuledFilter.block_num_path, [100000, 1000])
        RuledFilter.block_hash_path = os.path.join(RuledFilter.cache_dir, 'block', 'hash')
        RuledFilter.block_hash_dir = HexDir(RuledFilter.block_hash_path, 32, levels=2)
        RuledFilter.tx_path = os.path.join(RuledFilter.cache_dir, 'tx', 'src')
        RuledFilter.tx_raw_path = os.path.join(RuledFilter.cache_dir, 'tx', 'raw')
        RuledFilter.tx_dir = HexDir(RuledFilter.tx_path, 32, levels=2)
        RuledFilter.tx_raw_dir = HexDir(RuledFilter.tx_raw_path, 32, levels=2)
        RuledFilter.address_path = os.path.join(RuledFilter.cache_dir, 'address')
        RuledFilter.address_dir = HexDir(RuledFilter.address_path, 20, levels=2)
        RuledFilter.chain_spec = chain_spec
        RuledFilter.include_block_data = include_block_data
        RuledFilter.include_tx_data = include_tx_data


    @classmethod
    def block_callback(cls, block, extra=None):
        hash_bytes = bytes.fromhex(strip_0x(block.hash))
        cls.block_num_dir.add(block.number, hash_bytes)
        num_bytes = block.number.to_bytes(8, 'big')
        cls.block_hash_dir.add(hash_bytes, num_bytes)
        if cls.include_block_data:
            src = json.dumps(block.src()).encode('utf-8')
            cls.block_src_dir.add(hash_bytes, src)


    def filter(self, conn, block, tx, db_session=None):
        if self.rules_filter != None:
            if not self.rules_filter.apply_rules(tx):
                logg.debug('rule match failed for tx {}'.format(tx.hash))
                return
        logg.info('applying filter {}'.format(self))
        self.ruled_filter(conn, block, tx, db_session=db_session)
