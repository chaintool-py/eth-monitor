# standard imports
import os
import logging

# external imports
from chainsyncer.backend.file import chain_dir_for
from leveldir.numeric import NumDir
from leveldir.hex import HexDir
from hexathon import strip_0x
from chainlib.eth.address import is_same_address

base_dir = '/var/lib'

logg = logging.getLogger()

class CacheFilter:

    def __init__(self, chain_spec, cache_root=base_dir, rules_filter=None):
        cache_root = os.path.join(cache_root, 'eth_monitor')
        chain_dir = chain_dir_for(cache_root)
        self.cache_dir = os.path.join(chain_dir, 'cache')
        block_num_path = os.path.join(self.cache_dir, 'block', 'num')
        self.block_num_dir = NumDir(block_num_path, [100000, 1000])
        block_hash_path = os.path.join(self.cache_dir, 'block', 'hash')
        self.block_hash_dir = HexDir(block_hash_path, 32, levels=2)
        tx_path = os.path.join(self.cache_dir, 'tx')
        self.tx_dir = HexDir(tx_path, 32, levels=2)
        self.rules_filter = rules_filter
   

    def block_callback(self, block, extra=None):
        src = str(block.src()).encode('utf-8')
        hash_bytes = bytes.fromhex(strip_0x(block.hash))
        self.block_hash_dir.add(hash_bytes, src)
        self.block_num_dir.add(block.number, hash_bytes)


    def filter(self, conn, block, tx, db_session=None):
        if self.rules_filter != None:
            if not self.rules_filter.apply_rules(tx):
                logg.debug('rule match failed for tx {}'.format(tx.hash))
                return
        src = str(tx.src()).encode('utf-8')
        self.tx_dir.add(bytes.fromhex(strip_0x(tx.hash)), src)
