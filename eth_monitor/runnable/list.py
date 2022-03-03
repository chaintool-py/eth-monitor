# standard imports
import sys
import argparse
import confini
import logging
import os
import importlib

# external imports
from chainlib.chain import ChainSpec
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.block import (
        block_by_hash,
        Block,
        )
from chainlib.eth.tx import (
        receipt,
        Tx,
        )
from eth_cache.store.file import FileStore
from eth_cache.rpc import CacheRPC

# local imports
from eth_monitor.index import AddressIndex
from eth_monitor.filters.out import OutFilter
from eth_monitor.rules import AddressRules
        

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

default_eth_provider = os.environ.get('RPC_PROVIDER', 'http://localhost:8545')

script_dir = os.path.realpath(os.path.dirname(__file__))
exec_dir = os.path.realpath(os.getcwd())
#default_config_dir = os.environ.get('CONFINI_DIR', os.path.join(exec_dir, 'config'))
base_config_dir = os.path.join(script_dir, '..', 'data', 'config')


argparser = argparse.ArgumentParser('list transactions')
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-c', type=str, help='config file')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, help='Chain specification string')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('-a', '--address', dest='a', default=[], action='append', type=str, help='Add address to includes list')
argparser.add_argument('--filter', type=str, action='append', help='Add python module filter path')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('--fresh', action='store_true', help='Do not read block and tx data from cache, even if available')
argparser.add_argument('--renderer', type=str, action='append', default=[], help='Python modules to dynamically load for rendering of transaction output')
argparser.add_argument('cache_dir', type=str, help='Directory to read cache data from')
args = argparser.parse_args(sys.argv[1:])


if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

config_dir = args.c
config = confini.Config(base_config_dir, os.environ.get('CONFINI_ENV_PREFIX'), override_dirs=args.c)
config.process()
args_override = {
        'CHAIN_SPEC': getattr(args, 'i'),
        }
config.dict_override(args_override, 'cli')
config.add(getattr(args, 'cache_dir'), '_CACHE_DIR')
logg.debug('loaded config:\{}'.format(config))

chain_spec = ChainSpec.from_chain_str(args.i)

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
rpc = EthHTTPConnection(args.p)


def main():
    store = FileStore(chain_spec, config.get('_CACHE_DIR'))
    use_rpc = rpc
    if not args.fresh:
        use_rpc = CacheRPC(rpc, store)

    renderers_mods = []
    for renderer in args.renderer:
        m = importlib.import_module(renderer)
        renderers_mods.append(m)

    idx = AddressIndex(rpc, store)

    for address in args.a:
        idx.load_address_tx(address)

    OutFilter.init(store)
    out_filter = OutFilter(chain_spec, renderers=renderers_mods)

    for tx_src in idx.get_address(address):
        o = block_by_hash(tx_src['block_hash'])
        block_src = use_rpc.do(o)

        o = receipt(tx_src['hash'])
        rcpt = use_rpc.do(o)
    
        block = Block(block_src)
        tx = Tx(tx_src, block=block, rcpt=rcpt)
        out_filter.filter(use_rpc, block, tx, db_session=None)
    

if __name__ == '__main__':
    main()
