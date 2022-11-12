# standard imports
import logging

# external imports
from chainlib.cli.log import process_log as base_process_log

logging.STATETRACE = 5


def process_log(args, logger):
    if args.vvv:
        logger.setLevel(logging.STATETRACE)
    else:
        logger = base_process_log(args, logger)

    logging.getLogger('chainlib.connection').setLevel(logging.WARNING)
    logging.getLogger('chainlib.eth.tx').setLevel(logging.WARNING)
    logging.getLogger('chainlib.eth.src').setLevel(logging.WARNING)

    return logger

