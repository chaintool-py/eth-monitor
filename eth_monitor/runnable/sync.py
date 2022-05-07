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

logging.STATETRACE = 5
logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

default_eth_provider = os.environ.get('RPC_PROVIDER')
if default_eth_provider == None:
    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

script_dir = os.path.realpath(os.path.dirname(__file__))
exec_dir = os.path.realpath(os.getcwd())
#default_config_dir = os.environ.get('CONFINI_DIR', os.path.join(exec_dir, 'config'))
base_config_dir = os.path.join(script_dir, '..', 'data', 'config')

argparser = argparse.ArgumentParser('master eth events monitor')
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-c', type=str, help='config file')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, help='Chain specification string')
argparser.add_argument('--offset', type=int, default=0, help='Start sync on this block')
argparser.add_argument('--until', type=int, default=0, help='Terminate sync on this block')
argparser.add_argument('--head', action='store_true', help='Start at current block height (overrides --offset, assumes --keep-alive)')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('--skip-history', action='store_true', dest='skip_history', help='Skip history sync')
argparser.add_argument('--keep-alive', action='store_true', dest='keep_alive', help='Continue to sync head after history sync complete')
argparser.add_argument('--input', default=[], action='append', type=str, help='Add input (recipient) addresses to includes list')
argparser.add_argument('--output', default=[], action='append', type=str, help='Add output (sender) addresses to includes list')
argparser.add_argument('--exec', default=[], action='append', type=str, help='Add exec (contract) addresses to includes list')
argparser.add_argument('--data', default=[], action='append', type=str, help='Add data prefix strings to include list')
argparser.add_argument('--data-in', default=[], action='append', dest='data_in', type=str, help='Add data contain strings to include list')
argparser.add_argument('--x-data', default=[], action='append', dest='xdata', type=str, help='Add data prefix string to exclude list')
argparser.add_argument('--x-data-in', default=[], action='append', dest='xdata_in', type=str, help='Add data contain string to exclude list')
argparser.add_argument('--address', default=[], action='append', type=str, help='Add addresses as input, output and exec to includes list')
argparser.add_argument('--x-input', default=[], action='append', type=str, dest='xinput', help='Add input (recipient) addresses to excludes list')
argparser.add_argument('--x-output', default=[], action='append', type=str, dest='xoutput', help='Add output (sender) addresses to excludes list')
argparser.add_argument('--x-exec', default=[], action='append', type=str, dest='xexec', help='Add exec (contract) addresses to excludes list')
argparser.add_argument('--x-address', default=[], action='append', type=str, dest='xaddress', help='Add addresses as input, output and exec to excludes list')
argparser.add_argument('--includes-file', type=str, dest='includes_file', help='Load include rules from file')
argparser.add_argument('--include-default', dest='include_default', action='store_true', help='Include all transactions by default')
argparser.add_argument('--store-tx-data', dest='store_tx_data', action='store_true', help='Include all transaction data objects by default')
argparser.add_argument('--store-block-data', dest='store_block_data', action='store_true', help='Include all block data objects by default')
argparser.add_argument('--address-file', type=str, dest='excludes_file', help='Load exclude rules from file')
argparser.add_argument('--renderer', type=str, action='append', default=[], help='Python modules to dynamically load for rendering of transaction output')
argparser.add_argument('--filter', type=str, action='append', help='Add python module to tx filter path')
argparser.add_argument('--block-filter', type=str, dest='block_filter', action='append', help='Add python module to block filter path')
argparser.add_argument('--cache-dir', dest='cache_dir', type=str, help='Directory to store tx data')
argparser.add_argument('--state-dir', dest='state_dir', default=exec_dir, type=str, help='Directory to store sync state')
argparser.add_argument('--fresh', action='store_true', help='Do not read block and tx data from cache, even if available')
argparser.add_argument('--single', action='store_true', help='Execute a single sync, regardless of previous states')
argparser.add_argument('--session-id', dest='session_id', type=str, help='Use state from specified session id')
argparser.add_argument('--backend', type=str, help='State store backend')
argparser.add_argument('--list-backends', dest='list_backends', action='store_true', help='List built-in store backends')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('-vvv', action='store_true', help='Be incredibly verbose')
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

config_dir = args.c
config = confini.Config(base_config_dir, os.environ.get('CONFINI_ENV_PREFIX'), override_dirs=args.c)
config.process()
args_override = {
        'CHAIN_SPEC': getattr(args, 'i'),
        'SYNCER_BACKEND': getattr(args, 'backend'),
        }
config.dict_override(args_override, 'cli')
config.add(args.offset, '_SYNC_OFFSET', True)
config.add(args.skip_history, '_NO_HISTORY', True)
config.add(args.single, '_SINGLE', True)
config.add(args.head, '_HEAD', True)
config.add(args.keep_alive, '_KEEP_ALIVE', True)
config.add(os.path.realpath(args.state_dir), '_STATE_DIR', True)
config.add(args.cache_dir, '_CACHE_DIR', True)
config.add(args.session_id, '_SESSION_ID', True)
override(config, 'renderer', env=os.environ, args=args)
override(config, 'filter', env=os.environ, args=args)
override(config, 'block_filter', env=os.environ, args=args)

if config.get('_SESSION_ID') == None:
    if config.get('_SINGLE'):
        config.add(str(uuid.uuid4()), '_SESSION_ID', True)
    else:
        config.add('default', '_SESSION_ID', True)
logg.debug('loaded config:\n{}'.format(config))

chain_spec = ChainSpec.from_chain_str(args.i)

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
rpc = EthHTTPConnection(args.p)


def setup_address_arg_rules(rules, args):
    include_inputs = args.input
    include_outputs = args.output
    include_exec = args.exec
    exclude_inputs = args.xinput
    exclude_outputs = args.xoutput
    exclude_exec = args.xexec

    for address in args.address:
        include_inputs.append(address)
        include_outputs.append(address)
        include_exec.append(address)

    for address in args.xaddress:
        exclude_inputs.append(address)
        exclude_outputs.append(address)
        exclude_exec.append(address)

    includes = RuleSimple(include_outputs, include_inputs, include_exec, description='INCLUDE')
    rules.include(includes)

    excludes = RuleSimple(exclude_outputs, exclude_inputs, exclude_exec, description='EXCLUDE')
    rules.exclude(excludes)

    return rules


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

    address_rules = AddressRules(include_by_default=args.include_default)
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
            chain_spec,
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

    out_filter = OutFilter(chain_spec, rules_filter=address_rules, renderers=renderers_mods)
    filters.append(out_filter)

    syncer_store_module = None
    syncer_store_class = None
    state_dir = None
    if config.get('SYNCER_BACKEND') == 'mem':
        syncer_store_module = importlib.import_module('chainsyncer.store.mem')
        syncer_store_class = getattr(syncer_store_module, 'SyncMemStore')
    else:
        if config.get('SYNCER_BACKEND') == 'fs': 
            syncer_store_module = importlib.import_module('chainsyncer.store.fs')
            syncer_store_class = getattr(syncer_store_module, 'SyncFsStore')
        elif config.get('SYNCER_BACKEND') == 'rocksdb':
            syncer_store_module = importlib.import_module('chainsyncer.store.rocksdb')
            syncer_store_class = getattr(syncer_store_module, 'SyncRocksDbStore')
        else:
            syncer_store_module = importlib.import_module(config.get('SYNCER_BACKEND'))
            syncer_store_class = getattr(syncer_store_module, 'SyncStore')
        state_dir = os.path.join(config.get('_STATE_DIR'), config.get('SYNCER_BACKEND'))

    logg.info('using engine {} module {}.{}'.format(config.get('SYNCER_BACKEND'), syncer_store_module.__file__, syncer_store_class.__name__))

    state_dir = os.path.join(state_dir, config.get('_SESSION_ID'))
    if state_dir == None:
        sync_store = syncer_store_class(session_id=config.get('_SESSION_ID'), state_event_callback=state_change_callback, filter_state_event_callback=filter_change_callback)
    else:
        sync_store = syncer_store_class(state_dir, session_id=config.get('_SESSION_ID'), state_event_callback=state_change_callback, filter_state_event_callback=filter_change_callback)
    logg.info('session is {}'.format(sync_store.session_id))

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
