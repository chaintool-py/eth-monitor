# standard imports
import os
import logging
import json

# external imports
from hexathon import strip_0x
from chainsyncer.filter import SyncFilter

logg = logging.getLogger(__name__)


class RuledFilter(SyncFilter):

    def __init__(self, rules_filter=None, store=None):
        self.rules_filter = rules_filter


    def filter(self, conn, block, tx, db_session=None):
        if self.rules_filter != None:
            if not self.rules_filter.apply_rules(tx):
                logg.debug('rule match failed for tx {}'.format(tx.hash))
                return True
        return False
