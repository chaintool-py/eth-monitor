# standard imports
import sys

# local imports
from .base import RuledFilter


class OutFilter(RuledFilter):

    def __init__(self, writer=sys.stdout, renderers=[], rules_filter=None):
        super(OutFilter, self).__init__(rules_filter=rules_filter)
        self.w = writer
        self.renderers = renderers
        self.c = 0


    def filter(self, con, block, tx, db_session=None):
        data = tx.payload
        if len(data) > 8:
            data = data[:8] + '...'
        if len(data) > 0:
            data = 'data {}'.format(data)
        self.w.write('{} {} {} {}\n'.format(self.c, block, tx, data))
        self.c += 1
