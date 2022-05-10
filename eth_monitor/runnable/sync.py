# standard imports
import sys
import signal
import argparse
import confini
import logging
import os
import importlib
import uuid
import datetime

# external imports
import chainlib.cli
import chainsyncer.cli
from chainlib.chain import ChainSpec
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.block import block_latest
from hexathon import (
        strip_0x,
        add_0x,
        )
#from chainsyncer.store.fs import SyncFsStore
from chainsyncer.driver.chain_interface import ChainInterfaceDriver
from chainsyncer.error import SyncDone

# local imports
from eth_monitor.callback import (
        pre_callback,
        post_callback,
        )
from eth_monitor.settings import EthMonitorSettings
import eth_monitor.cli

logging.STATETRACE = 5
logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.realpath(os.path.dirname(__file__))
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC | chainlib.cli.Flag.PROVIDER
argparser = chainlib.cli.ArgumentParser(arg_flags)
eth_monitor.cli.process_flags(argparser, 0)

argparser.add_argument('--list-backends', dest='list_backends', action='store_true', help='List built-in store backends')
argparser.add_argument('-vvv', action='store_true', help='Be incredibly verbose')

sync_flags = chainsyncer.cli.SyncFlag.RANGE | chainsyncer.cli.SyncFlag.HEAD
chainsyncer.cli.process_flags(argparser, sync_flags)

args = argparser.parse_args(sys.argv[1:])

if args.list_backends:
    for v in [
            'fs',
            'rocksdb',
            'mem',
            ]:
        print(v)
    sys.exit(0)

logging.getLogger('chainlib.connection').setLevel(logging.WARNING)
logging.getLogger('chainlib.eth.tx').setLevel(logging.WARNING)
logging.getLogger('chainlib.eth.src').setLevel(logging.WARNING)

if args.vvv:
    logg.setLevel(logging.STATETRACE)
else:
    if args.vv:
        logg.setLevel(logging.DEBUG)
    elif args.v:
        logg.setLevel(logging.INFO)

base_config_dir = [
    chainsyncer.cli.config_dir,
    config_dir,
        ]
config = chainlib.cli.Config.from_args(args, arg_flags, base_config_dir=base_config_dir)
config = chainsyncer.cli.process_config(config, args, sync_flags)
config = eth_monitor.cli.process_config(config, args, 0)


settings = EthMonitorSettings()
settings.process(config)
logg.debug('loaded settings:\n{}'.format(settings))


def main():
    logg.info('session is {}'.format(settings.get('SESSION_ID')))

    drv = ChainInterfaceDriver(
            settings.get('SYNC_STORE'),
            settings.get('SYNCER_INTERFACE'),
            offset=settings.get('SYNCER_OFFSET'),
            target=settings.get('SYNCER_LIMIT'),
            pre_callback=pre_callback,
            post_callback=post_callback,
            block_callback=settings.get('BLOCK_HANDLER').filter,
            )
    
    try:
        r = drv.run(settings.get('RPC'))
    except SyncDone as e:
        sys.stderr.write("sync {} done at block {}\n".format(drv, e))


if __name__ == '__main__':
    main()
