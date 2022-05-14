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
from chainsyncer.cli.arg import (
        apply_arg as apply_arg_sync,
        apply_flag as apply_flag_sync,
        )
from chainsyncer.cli.config import process_config as process_config_sync
from chainsyncer.driver.chain_interface import ChainInterfaceDriver
from chainsyncer.error import SyncDone
from chainsyncer.data import config_dir as chainsyncer_config_dir
from chainlib.settings import ChainSettings
from chainlib.eth.settings import process_settings
from chainlib.eth.cli.arg import (
        Arg,
        ArgFlag,
        process_args,
        )
from chainlib.eth.cli.config import (
        Config,
        process_config,
        )

# local imports
from eth_monitor.callback import (
        pre_callback,
        post_callback,
        )
import eth_monitor.cli
from eth_monitor.cli.log import process_log
from eth_monitor.settings import process_settings as process_settings_local

logg = logging.getLogger()

script_dir = os.path.realpath(os.path.dirname(__file__))
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = ArgFlag()
arg_flags = apply_flag_sync(arg_flags)

arg = Arg(arg_flags)
arg = apply_arg_sync(arg)


flags = arg_flags.STD_BASE_READ | arg_flags.PROVIDER | arg_flags.CHAIN_SPEC | arg_flags.VERYVERBOSE | arg_flags.SYNC_RANGE_EXT | arg_flags.STATE
argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('--list-backends', dest='list_backends', action='store_true', help='List built-in store backends')
eth_monitor.cli.process_args(argparser, arg, flags)

args = argparser.parse_args(sys.argv[1:])

if args.list_backends:
    for v in [
            'fs',
            'rocksdb',
            'mem',
            ]:
        print(v)
    sys.exit(0)

logg = process_log(args, logg)

config = Config()
config.add_schema_dir(config_dir)
config.add_schema_dir(chainsyncer_config_dir)
config = process_config(config, arg, args, flags)
config = process_config_sync(config, arg, args, flags)
config = eth_monitor.cli.process_config(config, arg, args, flags)

settings = ChainSettings()
settings = process_settings(settings, config)
settings = process_settings_local(settings, config)
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
        r = drv.run(settings.get('CONN'))
    except SyncDone as e:
        sys.stderr.write("sync {} done at block {}\n".format(drv, e))


if __name__ == '__main__':
    main()
