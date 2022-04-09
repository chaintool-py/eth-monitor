# standard imports
import sys
import logging
import datetime

# external imports
from hexathon import (
        strip_0x,
        )

# local imports
from .base import RuledFilter

logg = logging.getLogger(__name__)


# Interface defining the signature for renderer in OutFilter
# return string after local transformation
def apply_interface(c, s, chain_str, conn, block, tx, db_session=None):
    pass


class OutResult:

    def __init__(self):
        self.content = ''


    def set(self, v):
        self.content = v 


    def get(self):
        return self.content


    def __str__(self):
        return self.content


class OutFilter(RuledFilter):

    def __init__(self, chain_spec, writer=sys.stdout, renderers=[], rules_filter=None):
        super(OutFilter, self).__init__(rules_filter=rules_filter)
        self.w = writer
        self.renderers = renderers
        self.c = 0
        self.chain_spec = chain_spec
        self.result = OutResult()


    def filter(self, conn, block, tx, db_session=None):
        r = super(OutFilter, self).filter(conn, block, tx, db_session=db_session)
        if r == True:
            return True

        for renderer in self.renderers:
            r = renderer.apply(self.c, self.result, self.chain_spec, conn, block, tx)
            if not r:
                break

        s = str(self.result)

        if s == '':
            data = tx.payload
            if len(data) > 8:
                data = data[:8] + '...'
            if len(data) > 0:
                data = 'data {}'.format(data)
            #s = '{} {} {} {}'.format(self.c, block, tx, data)
            tx_count = len(block.txs)
            s = '{} {} block {} {} tx {}/{} {} {} {}'.format(
                    self.c,
                    datetime.datetime.fromtimestamp(block.timestamp),
                    block.number,
                    strip_0x(block.hash),
                    tx.index,
                    tx_count,
                    strip_0x(tx.hash),
                    tx.status.name,
                    data,
                    )

        self.w.write(s + '\n')
        self.c += 1
        return False
