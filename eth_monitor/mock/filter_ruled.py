# standard imports
import logging

# local imports
from eth_monitor.filters import RuledFilter

logg = logging.getLogger(__name__)


class Filter(RuledFilter):

    def __init__(self, *args, **kwargs):
        super(Filter, self).__init__(rules_filter=kwargs.get('rules_filter'))


    def ruled_filter(self, conn, block, tx, db_session=None):
        logg.debug('RULE MOCK for {} {}'.format(block.number, tx.index))
