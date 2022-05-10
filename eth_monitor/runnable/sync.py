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

from eth_cache.rpc import CacheRPC
from eth_cache.store.file import FileStore

# local imports
from eth_monitor.chain import EthChainInterface
from eth_monitor.filters.cache import Filter as CacheFilter
from eth_monitor.rules import (
        AddressRules,
        RuleSimple,
        RuleMethod,
        RuleData,
        )
from eth_monitor.filters import RuledFilter
from eth_monitor.filters.out import OutFilter
from eth_monitor.config import override, list_from_prefix
from eth_monitor.callback import BlockCallbackFilter
from eth_monitor.settings import EthMonitorSettings
import eth_monitor.cli

logging.STATETRACE = 5
logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

#default_eth_provider = os.environ.get('RPC_PROVIDER')
#if default_eth_provider == None:
#    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

#exec_dir = os.path.realpath(os.getcwd())
#default_config_dir = os.environ.get('CONFINI_DIR', os.path.join(exec_dir, 'config'))
script_dir = os.path.realpath(os.path.dirname(__file__))
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC | chainlib.cli.Flag.PROVIDER
argparser = chainlib.cli.ArgumentParser(arg_flags)
eth_monitor.cli.process_flags(argparser, 0)

argparser.add_argument('--store-tx-data', dest='store_tx_data', action='store_true', help='Include all transaction data objects by default')
argparser.add_argument('--store-block-data', dest='store_block_data', action='store_true', help='Include all block data objects by default')
argparser.add_argument('--renderer', type=str, action='append', default=[], help='Python modules to dynamically load for rendering of transaction output')
argparser.add_argument('--filter', type=str, action='append', help='Add python module to tx filter path')
argparser.add_argument('--block-filter', type=str, dest='block_filter', action='append', help='Add python module to block filter path')
argparser.add_argument('--fresh', action='store_true', help='Do not read block and tx data from cache, even if available')
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

if args.vvv:
    logg.setLevel(logging.STATETRACE)
else:
    logging.getLogger('chainlib.connection').setLevel(logging.WARNING)
    logging.getLogger('chainlib.eth.tx').setLevel(logging.WARNING)
    logging.getLogger('chainsyncer.driver.history').setLevel(logging.WARNING)
    logging.getLogger('chainsyncer.driver.head').setLevel(logging.WARNING)
    logging.getLogger('chainsyncer.backend.file').setLevel(logging.WARNING)
    logging.getLogger('chainsyncer.backend.sql').setLevel(logging.WARNING)
    logging.getLogger('chainsyncer.filter').setLevel(logging.WARNING)

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

#rpc_id_generator = None
#if args.seq:
#    rpc_id_generator = IntSequenceGenerator()

#auth = None
#if os.environ.get('RPC_AUTHENTICATION') == 'basic':
#    from chainlib.auth import BasicAuth
#    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
#rpc = EthHTTPConnection(args.p)




def setup_data_arg_rules(rules, args):
    include_data = []
    for v in args.data:
        include_data.append(v.lower())
    exclude_data = []
    for v in args.xdata:
        exclude_data.append(v.lower())

    includes = RuleMethod(include_data, description='INCLUDE')
    rules.include(includes)
   
    excludes = RuleMethod(exclude_data, description='EXCLUDE')
    rules.exclude(excludes)

    include_data = []
    for v in args.data_in:
        include_data.append(v.lower())
    exclude_data = []
    for v in args.xdata_in:
        exclude_data.append(v.lower())

    includes = RuleData(include_data, description='INCLUDE')
    rules.include(includes)
   
    excludes = RuleData(exclude_data, description='EXCLUDE')
    rules.exclude(excludes)

    return rules


def setup_address_file_rules(rules, includes_file=None, excludes_file=None, include_default=False, include_block_default=False):

    if includes_file != None:
        f = open(includes_file, 'r')
        logg.debug('reading includes rules from {}'.format(os.path.realpath(includes_file)))
        while True:
            r = f.readline()
            if r == '':
                break
            r = r.rstrip()
            v = r.split("\t")

            sender = []
            recipient = []
            executable = []

            try:
                if v[0] != '':
                    sender = v[0].split(',')
            except IndexError:
                pass

            try:
                if v[1] != '':
                    recipient = v[1].split(',')
            except IndexError:
                pass

            try:
                if v[2] != '':
                    executable = v[2].split(',')
            except IndexError:
                pass

            rule = RuleSimple(sender, recipient, executable)
            rules.include(rule)

    if excludes_file != None:
        f = open(includes_file, 'r')
        logg.debug('reading excludes rules from {}'.format(os.path.realpath(excludes_file)))
        while True:
            r = f.readline()
            if r == '':
                break
            r = r.rstrip()
            v = r.split("\t")

            sender = None
            recipient = None
            executable = None

            if v[0] != '':
                sender = v[0].strip(',')
            if v[1] != '':
                recipient = v[1].strip(',')
            if v[2] != '':
                executable = v[2].strip(',')

            rule = RuleSimple(sender, recipient, executable)
            rules.exclude(rule)

    return rules


def setup_filter(chain_spec, cache_dir, include_tx_data, include_block_data):
    store = None
    if cache_dir == None:
        logg.warning('no cache dir specified, will discard everything!!')
        from eth_cache.store.null import NullStore
        store = NullStore()
    else:
        store = FileStore(chain_spec, cache_dir)
        cache_dir = os.path.realpath(cache_dir)
        if cache_dir == None:
            import tempfile
            cache_dir = tempfile.mkdtemp()
    logg.info('using chain spec {} and store {}'.format(chain_spec, store))
    RuledFilter.init(store, include_tx_data=include_tx_data, include_block_data=include_block_data)

    return store


def setup_cache_filter(rules_filter=None):
    return CacheFilter(rules_filter=rules_filter)


def pre_callback():
    logg.debug('starting sync loop iteration')


def post_callback():
    logg.debug('ending sync loop iteration')


def block_callback(block, tx):
    logg.info('processing {} {}'.format(block, datetime.datetime.fromtimestamp(block.timestamp)))


def state_change_callback(k, old_state, new_state):
    logg.log(logging.STATETRACE, 'state change: {} {} -> {}'.format(k, old_state, new_state)) 


def filter_change_callback(k, old_state, new_state):
    logg.log(logging.STATETRACE, 'filter change: {} {} -> {}'.format(k, old_state, new_state)) 


def main():
    rpc = settings.get('RPC')
    o = block_latest()
    r = rpc.do(o)
    block_offset = int(strip_0x(r), 16) + 1
    logg.info('network block height is {}'.format(block_offset))

    keep_alive = False
    session_block_offset = 0
    block_limit = 0
    if args.head:
        session_block_offset = block_offset
        block_limit = -1
        keep_alive = True
    else:
        session_block_offset = args.offset

    if args.until > 0:
        if not args.head and args.until <= session_block_offset:
            raise ValueError('sync termination block number must be later than offset ({} >= {})'.format(session_block_offset, args.until))
        block_limit = args.until
    elif config.true('_KEEP_ALIVE'):
        keep_alive=True
        block_limit = -1

    if session_block_offset == -1:
        session_block_offset = block_offset
    elif not config.true('_KEEP_ALIVE'):
        if block_limit == 0:
            block_limit = block_offset

    sys.exit(0)

    #address_rules = AddressRules(include_by_default=args.include_default)
    address_rules = setup_data_arg_rules(
            address_rules,
            args,
            )
    address_rules = setup_address_file_rules(
            address_rules,
            includes_file=args.includes_file,
            excludes_file=args.excludes_file,
            )
    address_rules = setup_address_arg_rules(
            address_rules,
            args,
            )

    store = setup_filter(
            settings.get('CHAIN_SPEC'),
            config.get('_CACHE_DIR'),
            bool(args.store_tx_data),
            bool(args.store_block_data),
            )

    cache_filter = setup_cache_filter(
            rules_filter=address_rules,
            )
     
    filters = [
            cache_filter, 
            ]

    for fltr in list_from_prefix(config, 'filter'):
        m = importlib.import_module(fltr)
        fltr_object = m.Filter(rules_filter=address_rules)
        filters.append(fltr_object)
        logg.info('using filter module {}'.format(fltr))

    renderers_mods = []
    for renderer in list_from_prefix(config, 'renderer'):
        m = importlib.import_module(renderer)
        renderers_mods.append(m)
        logg.info('using renderer module {}'.format(renderer))

    block_filter_handler = BlockCallbackFilter()
    for block_filter in list_from_prefix(config, 'block_filter'):
        m = importlib.import_module(block_filter)
        block_filter_handler.register(m)
        logg.info('using block filter module {}'.format(block_filter))

    chain_interface = EthChainInterface()

    out_filter = OutFilter(
            settings.get('CHAIN_SPEC'),
            rules_filter=address_rules,renderers=renderers_mods,
            )
    filters.append(out_filter)

    logg.info('session is {}'.format(settings.get('SESSION_ID')))

    for fltr in filters:
        sync_store.register(fltr)
    drv = ChainInterfaceDriver(sync_store, chain_interface, offset=session_block_offset, target=block_limit, pre_callback=pre_callback, post_callback=post_callback, block_callback=block_filter_handler.filter)
    
    use_rpc = rpc
    if not args.fresh:
        use_rpc = CacheRPC(rpc, store)
   
    i = 0
    try:
        r = drv.run(use_rpc)
    except SyncDone as e:
        sys.stderr.write("sync {} done at block {}\n".format(drv, e))

    i += 1


if __name__ == '__main__':
    main()
