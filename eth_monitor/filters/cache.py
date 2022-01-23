# standard imports
import os
import logging

# external imports
from hexathon import strip_0x

# local imports
from eth_monitor.filters import RuledFilter

logg = logging.getLogger(__name__)


class CacheFilter(RuledFilter):

    def ruled_filter(self, conn, block, tx, db_session=None):
        src = str(tx.src()).encode('utf-8')
        self.tx_dir.add(bytes.fromhex(strip_0x(tx.hash)), src)
