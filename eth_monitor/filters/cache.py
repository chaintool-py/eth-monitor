# standard imports
import os
import logging

# external imports
from hexathon import strip_0x

# local imports
from eth_monitor.filters import RuledFilter

logg = logging.getLogger(__name__)


class CacheFilter(RuledFilter):

    def block_callback(self, block, extra=None):
        src = str(block.src()).encode('utf-8')
        hash_bytes = bytes.fromhex(strip_0x(block.hash))
        self.block_hash_dir.add(hash_bytes, src)
        self.block_num_dir.add(block.number, hash_bytes)


    def ruled_filter(self, conn, block, tx, db_session=None):
        src = str(tx.src()).encode('utf-8')
        self.tx_dir.add(bytes.fromhex(strip_0x(tx.hash)), src)
