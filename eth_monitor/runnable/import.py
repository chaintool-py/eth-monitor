# standard imports
import argparse
import logging
import sys
import os
import time

# external imports
from chainlib.encode import TxHexNormalizer
from chainlib.eth.connection import EthHTTPConnection
from chainlib.chain import ChainSpec
from eth_cache.store.file import FileStore

# local imports
from eth_monitor.filters.cache import Filter as CacheFilter
from eth_monitor.filters import RuledFilter
from eth_monitor.rules import (
        AddressRules,
        RuleSimple,
        )

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

normalize_address = TxHexNormalizer().wallet_address

services = [
    'etherscan',
        ]

argparser = argparse.ArgumentParser('master eth events monitor')
argparser.add_argument('--api-key-file', dest='api_key_file', type=str, help='File to read API key from')
argparser.add_argument('--cache-dir', dest='cache_dir', type=str, default='.eth-monitor/cache', help='Directory to store tx data')
argparser.add_argument('--store-tx-data', dest='store_tx_data', action='store_true', help='Include all transaction data objects by default')
argparser.add_argument('--store-block-data', dest='store_block_data', action='store_true', help='Include all block data objects by default')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, default='evm:ethereum:1', help='Chain specification string')
argparser.add_argument('--address-file', dest='address_file', default=[], type=str, action='append', help='Add addresses from file')
argparser.add_argument('--list-services', dest='list', action='store_true', help='List all supported services')
argparser.add_argument('-a', '--address', default=[], type=str, action='append', help='Add address')
argparser.add_argument('--socks-host', dest='socks_host', type=str, help='Conect through socks host')
argparser.add_argument('--socks-port', dest='socks_port', type=int, help='Conect through socks port')
argparser.add_argument('--delay', type=float, default=0.2, help='Seconds to wait between each retrieval from importer')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('-p', type=str, help='RPC provider')
argparser.add_argument('service', nargs='?', type=str, help='Index service to import from')
args = argparser.parse_args(sys.argv[1:])

if args.list:
    for s in services:
        sys.stdout.write('{}\n'.format(s))
    sys.exit(0)

if not args.service:
    argparser.error('the following arguments are required: service')
    sys.exit(1)

if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

api_key = os.environ.get('API_KEY')
if args.api_key_file != None:
    f = open(args.api_key_file, 'r')
    api_key = f.read()
    f.close()

rpc = EthHTTPConnection(args.p)

chain_spec = ChainSpec.from_chain_str(args.i)

def conn_socks(host, port):
    import socks
    import socket

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, host, port, True)
    socket.socket = socks.socksocket


def collect_addresses(addresses=[], address_files=[]):
    address_collection = []
    for a in addresses:
        a = normalize_address(a)
        if a in address_collection:
            logg.debug('skipping duplicate address {}'.format(a))
        address_collection.append(a)
        logg.info('added address {}'.format(a))

    for fp in address_files:
        logg.debug('processing file ' + fp)
        f = open(fp, 'r')
        while True:
            a = f.readline()
            if a == '':
                break
            a = a.rstrip()
            a = normalize_address(a)
            if a in address_collection:
                logg.debug('skipping duplicate address {}'.format(a))
            address_collection.append(a)
            logg.info('added address {}'.format(a))
        f.close()

    return address_collection


def setup_address_rules(addresses):
    rules = AddressRules()
    outputs = []
    inputs = []
    execs = []
    for address in addresses:
        outputs.append(address)
        inputs.append(address)
        execs.append(address)
    rule = RuleSimple(outputs, inputs, execs, description='etherscan import')
    rules.include(rule)
    return rules


def setup_filter(chain_spec, cache_dir, include_tx_data, include_block_data, address_rules):
    store = FileStore(chain_spec, cache_dir, address_rules=address_rules)
    cache_dir = os.path.realpath(cache_dir)
    if cache_dir == None:
        import tempfile
        cache_dir = tempfile.mkdtemp()
    logg.info('using chain spec {} and dir {}'.format(chain_spec, cache_dir))
    RuledFilter.init(store, include_tx_data=include_tx_data, include_block_data=include_block_data)


def main():
    if args.socks_host != None:
        conn_socks(args.socks_host, args.socks_port)
    addresses = collect_addresses(args.address, args.address_file)

    from eth_monitor.importers.etherscan import Importer as EtherscanImporter
  
    address_rules = setup_address_rules(args.address)

    setup_filter(
            chain_spec,
            args.cache_dir,
            bool(args.store_tx_data),
            bool(args.store_block_data),
            address_rules,
            )

    cache_filter = CacheFilter(
            rules_filter=address_rules,
            )

    filters = [
            cache_filter,
            ]

    importer = []
    if args.service == 'etherscan':
        importer = EtherscanImporter(rpc, api_key, filters=filters, block_callback=RuledFilter.block_callback)
    else:
        raise ValueError('invalid service: {}'.format(args.service))
    for a in addresses:
        importer.get(a)
        time.sleep(args.delay)


if __name__ == '__main__':
    main()
