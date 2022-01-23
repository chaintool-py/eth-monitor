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
#from chainsyncer.driver.history import HistorySyncer
from chainsyncer.driver.threadrange import ThreadPoolRangeHistorySyncer
from chainsyncer.backend.file import FileBackend
from chainsyncer.filter import NoopFilter

# local imports
from eth_monitor.chain import EthChainInterface
from eth_monitor.filters.cache import CacheFilter

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
argparser.add_argument('--offset', type=int, default=0, help='Use sequential rpc ids')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('--skip-history', action='store_true', dest='skip_history', help='Skip history sync')
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

if __name__ == '__main__':
    o = block_latest()
    r = rpc.do(o)
    block_offset = int(strip_0x(r), 16) + 1
    logg.debug('current block height {}'.format(block_offset))
    syncers = []

    syncer_backends = FileBackend.resume(chain_spec, block_offset, base_dir=state_dir)

    import tempfile
    tmp_dir = tempfile.mkdtemp()
    logg.info('using dir {}'.format(tmp_dir))
    cache_filter = CacheFilter(chain_spec, tmp_dir)
    filters = [
            cache_filter, 
            ]

    if len(syncer_backends) == 0:
        initial_block_start = block_offset - 1
        if config.get('_SYNC_OFFSET') != None:
            initial_block_start = config.get('_SYNC_OFFSET')
        initial_block_offset = block_offset
        if config.get('_NO_HISTORY'):
            initial_block_start = block_offset
            initial_block_offset += 1
        syncer_backends.append(FileBackend.initial(chain_spec, initial_block_offset, start_block_height=initial_block_start, base_dir=state_dir))
        logg.info('found no backends to resume, adding initial sync from history start {} end {}'.format(initial_block_start, initial_block_offset))
    else:
        for syncer_backend in syncer_backends:
            logg.info('resuming sync session {}'.format(syncer_backend))
   
    chain_interface = EthChainInterface()
    for syncer_backend in syncer_backends:
        #syncers.append(HistorySyncer(syncer_backend, chain_interface, block_callback=cache_filter.block_callback))
        syncers.append(ThreadPoolRangeHistorySyncer(8, syncer_backend, chain_interface, block_callback=cache_filter.block_callback))

    syncer_backend = FileBackend.live(chain_spec, block_offset+1, base_dir=state_dir)
    syncers.append(HeadSyncer(syncer_backend, chain_interface, block_callback=cache_filter.block_callback))
   
    i = 0
    for syncer in syncers:
        logg.debug('running syncer index {} {}'.format(i, str(syncer)))
        for f in filters:
            syncer.add_filter(f)

        r = syncer.loop(int(config.get('SYNCER_LOOP_INTERVAL')), rpc)
        sys.stderr.write("sync {} done at block {}\n".format(syncer, r))

        i += 1
