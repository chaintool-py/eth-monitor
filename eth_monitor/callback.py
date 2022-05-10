# standard imports
import logging

logg = logging.getLogger(__name__)


class BlockCallbackFilter:

    def __init__(self):
        self.filters = []


    def register(self, fltr):
        self.filters.append(fltr)


    def filter(self, block, tx=None):
        for fltr in self.filters:
            fltr.filter(block, tx=tx)


def state_change_callback(k, old_state, new_state):
    logg.log(logging.STATETRACE, 'state change: {} {} -> {}'.format(k, old_state, new_state)) 


def filter_change_callback(k, old_state, new_state):
    logg.log(logging.STATETRACE, 'filter change: {} {} -> {}'.format(k, old_state, new_state)) 


def pre_callback():
    logg.debug('starting sync loop iteration')


def post_callback():
    logg.debug('ending sync loop iteration')


def block_callback(block, tx):
    logg.info('processing {} {}'.format(block, datetime.datetime.fromtimestamp(block.timestamp)))
