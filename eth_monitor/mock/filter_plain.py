# standard imports
import logging

logg = logging.getLogger(__name__)


class Filter:


    def __init__(self, *args, **kwargs):
        pass


    def filter(self, conn, block, tx, db_session=None):
        logg.debug('PLAIN MOCK for {} {}'.format(block.number, tx.index))
