# standard imports
import logging

# local imports
from eth_monitor.filters import RuledFilter

logg = logging.getLogger(__name__)


class Filter(RuledFilter):

    def ruled_filter(self, conn, block, tx, db_session=None):
        self.store.put_tx(tx, include_data=self.include_tx_data)


    def filter(self, conn, block, tx, db_session=None):
        r = super(Filter, self).filter(conn, block, tx, db_session=db_session)
        if r == False:
            return True

        self.ruled_filter(conn, block, tx, db_session=db_session)
        return True
