# standard imports
import datetime
import logging

logg = logging.getLogger(__name__)


def apply(c, result, chain_spec, conn, block, tx, db_session=None):
    timestamp = datetime.datetime.fromtimestamp(block.timestamp)
    value = str(tx.value)
    if len(value) < 19:
        value = '{:018d}'.format(tx.value)
        value = '0.' + value
    else:
        ridx = len(value) - 18
        value = '{}.{}'.format(value[:ridx], value[ridx:])
    value = value.rstrip('0')
    if value[len(value)-1] == '.':
        value += '0'
    s = '{} {}\t{} -> {} = {}'.format(timestamp, tx.hash, tx.outputs[0], tx.inputs[0], value)
    result.set(s)
    return False
