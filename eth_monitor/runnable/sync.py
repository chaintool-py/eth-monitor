# standard imports
import sys
import signal
import argparse
import confini
import logging
import os

# external imports
from chainlib.chain import ChainSpec
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.block import block_latest
from hexathon import (
        strip_0x,
        add_0x,
        )
from chainsyncer.driver.head import HeadSyncer
from chainsyncer.driver.history import HistorySyncer
from chainsyncer.backend.file import FileBackend
from chainsyncer.filter import NoopFilter

# local imports
from eth_monitor.chain import EthChainInterface
from eth_monitor.filters.cache import Filter as CacheFilter
from eth_monitor.rules import AddressRules
from eth_monitor.filters import RuledFilter
from eth_monitor.store.file import FileStore

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()
#logging.getLogger('leveldir.hex').setLevel(level=logging.DEBUG)
#logging.getLogger('leveldir.numeric').setLevel(level=logging.DEBUG)

default_eth_provider = os.environ.get('RPC_PROVIDER')
if default_eth_provider == None:
    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

script_dir = os.path.realpath(os.path.dirname(__file__))
exec_dir = os.path.realpath(os.getcwd())
default_config_dir = os.environ.get('CONFINI_DIR', os.path.join(exec_dir, 'config'))

argparser = argparse.ArgumentParser('master eth events monitor')
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-c', type=str, default=default_config_dir, help='config file')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, default='evm:ethereum:1', help='Chain specification string')
argparser.add_argument('--offset', type=int, default=0, help='Start sync on this block')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('--skip-history', action='store_true', dest='skip_history', help='Skip history sync')
argparser.add_argument('--includes-file', type=str, dest='includes_file', help='Load include rules from file')
argparser.add_argument('--include-default', dest='include_default', action='store_true', help='Include all transactions by default')
argparser.add_argument('--store-tx-data', dest='store_tx_data', action='store_true', help='Include all transaction data objects by default')
argparser.add_argument('--store-block-data', dest='store_block_data', action='store_true', help='Include all block data objects by default')
argparser.add_argument('--excludes-file', type=str, dest='excludes_file', help='Load exclude rules from file')
argparser.add_argument('-f', '--filter', type=str, action='append', help='Add python module filter path')
argparser.add_argument('--cache-dir', dest='cache_dir', type=str, help='Directory to store tx data')
argparser.add_argument('--single', action='store_true', help='Execute a single sync, regardless of previous states')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
args = argparser.parse_args(sys.argv[1:])

if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

config_dir = args.c
config = confini.Config(config_dir, os.environ.get('CONFINI_ENV_PREFIX'))
config.process()
args_override = {
        'CHAIN_SPEC': getattr(args, 'i'),
        }
config.dict_override(args_override, 'cli')
config.add(args.offset, '_SYNC_OFFSET', True)
config.add(args.skip_history, '_NO_HISTORY', True)
config.add(args.single, '_SINGLE', True)

logg.debug('config loaded:\n{}'.format(config))

chain_spec = ChainSpec.from_chain_str(args.i)

state_dir = os.path.join(exec_dir, 'state')

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
rpc = EthHTTPConnection(args.p)


def setup_address_rules(includes_file=None, excludes_file=None, include_default=False, include_block_default=False):

    rules = AddressRules(include_by_default=include_default)

    if includes_file != None:
        f = open(includes_file, 'r')
        logg.debug('reading includes rules from {}'.format(os.path.realpath(includes_file)))
        while True:
            r = f.readline()
            if r == '':
                break
            r = r.rstrip()
            v = r.split(",")

            sender = None
            recipient = None
            executable = None

            if v[0] != '':
                sender = v[0]
            if v[1] != '':
                recipient = v[1]
            if v[2] != '':
                executable = v[2]

            rules.include(sender=sender, recipient=recipient, executable=executable)

    if excludes_file != None:
        f = open(includes_file, 'r')
        logg.debug('reading excludes rules from {}'.format(os.path.realpath(excludes_file)))
        while True:
            r = f.readline()
            if r == '':
                break
            r = r.rstrip()
            v = r.split(",")

            sender = None
            recipient = None
            executable = None

            if v[0] != '':
                sender = v[0]
            if v[1] != '':
                recipient = v[1]
            if v[2] != '':
                executable = v[2]

            rules.exclude(sender=sender, recipient=recipient, executable=executable)

    return rules


def setup_filter(chain_spec, cache_dir, include_tx_data, include_block_data):
    store = FileStore(chain_spec, cache_dir)
    cache_dir = os.path.realpath(cache_dir)
    if cache_dir == None:
        import tempfile
        cache_dir = tempfile.mkdtemp()
    logg.info('using chain spec {} and dir {}'.format(chain_spec, cache_dir))
    RuledFilter.init(store, include_tx_data=include_tx_data, include_block_data=include_block_data)


def setup_cache_filter(rules_filter=None):
    return CacheFilter(rules_filter=rules_filter)


def setup_backend_resume(chain_spec, block_offset, state_dir, callback, sync_offset=0, skip_history=False):
    syncers = []
    syncer_backends = FileBackend.resume(chain_spec, block_offset, base_dir=state_dir)
    if len(syncer_backends) == 0:
        initial_block_start = block_offset - 1
        if config.get('_SYNC_OFFSET') != None:
            initial_block_start = config.get('_SYNC_OFFSET')
        initial_block_offset = block_offset
        if skip_history:
            initial_block_start = block_offset
            initial_block_offset += 1
        syncer_backends.append(FileBackend.initial(chain_spec, initial_block_offset, start_block_height=initial_block_start, base_dir=state_dir))
        logg.info('found no backends to resume, adding initial sync from history start {} end {}'.format(initial_block_start, initial_block_offset))
    else:
        for syncer_backend in syncer_backends:
            logg.info('resuming sync session {}'.format(syncer_backend))
   
    for syncer_backend in syncer_backends:
        syncers.append(HistorySyncer(syncer_backend, chain_interface, block_callback=RuledFilter.block_callback))

    syncer_backend = FileBackend.live(chain_spec, block_offset+1, base_dir=state_dir)
    syncers.append(HeadSyncer(syncer_backend, chain_interface, block_callback=cache_filter.block_callback))
    return syncers  


def setup_backend_single(chain_spec, block_offset, state_dir, callback, chain_interface, sync_offset=0, skip_history=False):
    syncer_backend = FileBackend.initial(chain_spec, block_offset, start_block_height=sync_offset, base_dir=state_dir)
    syncer = HistorySyncer(syncer_backend, chain_interface, block_callback=cache_filter.block_callback)
    return [syncer]


if __name__ == '__main__':
    o = block_latest()
    r = rpc.do(o)
    block_offset = int(strip_0x(r), 16) + 1
    logg.debug('current block height {}'.format(block_offset))


    address_rules = setup_address_rules(
            includes_file=args.includes_file,
            excludes_file=args.excludes_file,
            include_default=bool(args.include_default),
            )

    setup_filter(
            chain_spec,
            args.cache_dir,
            bool(args.store_tx_data),
            bool(args.store_block_data),
            )

    cache_filter = setup_cache_filter(
            rules_filter=address_rules,
            )
     
    filters = [
            cache_filter, 
            ]

    if args.filter != None:
        import importlib
        for fltr in args.filter:
            m = importlib.import_module(fltr)
            fltr_object = m.Filter(rules_filter=address_rules)
            filters.append(fltr_object)
        
    syncer_setup_func = None
    if config.true('_SINGLE'):
        syncer_setup_func = setup_backend_single
    else:
        syncer_setup_func = setup_backend_resume

    chain_interface = EthChainInterface()
    syncers = syncer_setup_func(
                chain_spec,
                block_offset,
                state_dir,
                cache_filter.block_callback,
                chain_interface,
                sync_offset=config.get('_SYNC_OFFSET'),
                skip_history=config.true('_NO_HISTORY'),
                )

    i = 0
    for syncer in syncers:
        logg.info('running syncer index {} {}'.format(i, str(syncer)))
        for f in filters:
            syncer.add_filter(f)

        r = syncer.loop(int(config.get('SYNCER_LOOP_INTERVAL')), rpc)
        sys.stderr.write("sync {} done at block {}\n".format(syncer, r))

        i += 1
