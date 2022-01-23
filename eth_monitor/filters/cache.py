# standard imports
import logging

# local imports
from eth_monitor.filters import RuledFilter

logg = logging.getLogger(__name__)


class Filter(RuledFilter):

    def ruled_filter(self, conn, block, tx, db_session=None):
        self.store.put_tx(tx, include_data=self.include_tx_data)
