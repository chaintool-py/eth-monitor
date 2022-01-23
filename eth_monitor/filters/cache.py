# standard imports
import os
import logging
import json

# external imports
from hexathon import strip_0x
from chainlib.eth.tx import (
        Tx,
        pack,
        )

# local imports
from eth_monitor.filters import RuledFilter

logg = logging.getLogger(__name__)


class Filter(RuledFilter):

    def ruled_filter(self, conn, block, tx, db_session=None):
        raw = pack(tx.src(), self.chain_spec)
        tx_hash_dirnormal = strip_0x(tx.hash).upper()
        tx_hash_bytes = bytes.fromhex(tx_hash_dirnormal)
        self.tx_raw_dir.add(tx_hash_bytes, raw)
        address = bytes.fromhex(strip_0x(tx.inputs[0]))
        self.address_dir.add_dir(tx_hash_dirnormal, address, b'')
        address = bytes.fromhex(strip_0x(tx.outputs[0]))
        self.address_dir.add_dir(tx_hash_dirnormal, address, b'')
        if self.include_tx_data:
            src = json.dumps(tx.src()).encode('utf-8')
            self.tx_dir.add(bytes.fromhex(strip_0x(tx.hash)), src)
