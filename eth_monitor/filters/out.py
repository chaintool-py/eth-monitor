# standard imports
import sys
import logging

# local imports
from .base import RuledFilter

logg = logging.getLogger(__name__)


# Interface defining the signature for renderer in OutFilter
# return string after local transformation
def apply_interface(c, s, chain_str, conn, block, tx, db_session=None):
    pass


class OutFilter(RuledFilter):

    def __init__(self, chain_spec, writer=sys.stdout, renderers=[], rules_filter=None):
        super(OutFilter, self).__init__(rules_filter=rules_filter)
        self.w = writer
        self.renderers = renderers
        self.c = 0
        self.chain_spec = chain_spec


    def filter(self, conn, block, tx, db_session=None):
        s = None
    
        for renderer in self.renderers:
            s = renderer.apply(self.c, s, self.chain_spec, conn, block, tx)
            if s != None:
                break

        if s == None:
            data = tx.payload
            if len(data) > 8:
                data = data[:8] + '...'
            if len(data) > 0:
                data = 'data {}'.format(data)
            s = '{} {} {} {}'.format(self.c, block, tx, data)

        self.w.write(s + '\n')
        self.c += 1
