# standard imports
import logging
import os
import uuid
import importlib
import tempfile

# external imports
from chainlib.settings import ChainSettings
from chainlib.eth.connection import EthHTTPConnection
from chainsyncer.settings import *
from eth_monitor.chain import EthChainInterface
from chainlib.eth.address import is_address
from eth_cache.rpc import CacheRPC
from eth_cache.store.file import FileStore
from chainsyncer.settings import process_sync_range


# local imports
from eth_monitor.rules import (
        AddressRules,
        RuleSimple,
        RuleMethod,
        RuleData,
        )
from eth_monitor.cli.rules import to_config_names
from eth_monitor.callback import (
        state_change_callback,
        filter_change_callback,
        BlockCallbackFilter,
        )
from eth_monitor.filters import RuledFilter
from eth_monitor.filters.cache import Filter as CacheFilter
from eth_monitor.config import override, list_from_prefix
from eth_monitor.filters.out import OutFilter
from eth_monitor.filters.block import Filter as BlockFilter

logg = logging.getLogger(__name__)


def process_monitor_session(settings, config):
    session_id = config.get('_SESSION_ID')
    if session_id == None:
        if config.get('_SINGLE'):
            session_id = str(uuid.uuid4())
        else:
            session_id = 'default'
    
    settings.set('SESSION_ID', session_id)
    return settings


def process_monitor_session_dir(settings, config):
    syncer_store_module = None
    syncer_store_class = None
    sync_store = None
    session_id = settings.get('SESSION_ID')
    state_dir = None
    if config.get('SYNCER_BACKEND') == 'mem':
        syncer_store_module = importlib.import_module('chainsyncer.store.mem')
        syncer_store_class = getattr(syncer_store_module, 'SyncMemStore')
        sync_store = syncer_store_class(
            session_id=session_id,
            state_event_callback=state_change_callback,
            filter_state_event_callback=filter_change_callback,
            )

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
        state_dir = os.path.join(config.get('ETHMONITOR_STATE_DIR'), config.get('SYNCER_BACKEND'))
        os.makedirs(state_dir, exist_ok=True)
        session_dir = os.path.join(state_dir, session_id)
        sync_store = syncer_store_class(
                session_dir,
                session_id=session_id,
                state_event_callback=state_change_callback,
                filter_state_event_callback=filter_change_callback,
                )
        settings.set('SESSION_DIR', session_dir)

    logg.info('using engine {} module {}.{}'.format(config.get('SYNCER_BACKEND'), syncer_store_module.__file__, syncer_store_class.__name__))

    settings.set('STATE_DIR', state_dir)
    settings.set('SYNC_STORE', sync_store)

    return settings


def process_address_arg_rules(settings, config):
    rules = settings.get('RULES')
    category = {
        'input': {
            'i': [],
            'x': [],
            },
        'output': {
            'i': [],
            'x': [],
            },
        'exec':  {
            'i': [],
            'x': [],
            },
        }
    for rules_arg in [
            'input',
            'output',
            'exec',
            ]:
        (vy, vn) = to_config_names(rules_arg)
        for address in config.get(vy):
            if not is_address(address):
                raise ValueError('invalid address in config {}: {}'.format(vy, address))
            category[rules_arg]['i'].append(address)
        for address in config.get(vn):
            if not is_address(address):
                raise ValueError('invalid address in config {}: {}'.format(vn, address))
            category[rules_arg]['x'].append(address)

    includes = RuleSimple(
            category['output']['i'],
            category['input']['i'],
            category['exec']['i'],
            description='INCLUDE',
            )
    rules.include(includes)

    excludes = RuleSimple(
            category['output']['x'],
            category['input']['x'],
            category['exec']['x'],
            description='EXCLUDE',
            )
    rules.exclude(excludes)

    return settings


def process_data_arg_rules(settings, config):
    rules = settings.get('RULES')

    include_data = []
    for v in config.get('ETHMONITOR_DATA'):
        include_data.append(v.lower())
    exclude_data = []
    for v in config.get('ETHMONITOR_X_DATA'):
        exclude_data.append(v.lower())

    includes = RuleMethod(include_data, description='INCLUDE')
    rules.include(includes)
   
    excludes = RuleMethod(exclude_data, description='EXCLUDE')
    rules.exclude(excludes)

    include_data = []
    for v in config.get('ETHMONITOR_DATA_IN'):
        include_data.append(v.lower())
    exclude_data = []
    for v in config.get('ETHMONITOR_X_DATA_IN'):
        exclude_data.append(v.lower())

    includes = RuleData(include_data, description='INCLUDE')
    rules.include(includes)
   
    excludes = RuleData(exclude_data, description='EXCLUDE')
    rules.exclude(excludes)

    return settings


def process_address_file_rules(settings, config): #rules, includes_file=None, excludes_file=None, include_default=False, include_block_default=False):
    rules = settings.get('RULES')
    includes_file = config.get('ETHMONITOR_INCLUDES_FILE')
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

    excludes_file = config.get('ETHMONITOR_EXCLUDES_FILE')
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
    return settings


def process_arg_rules(settings, config):
    address_rules = AddressRules(include_by_default=config.get('ETHMONITOR_INCLUDE_DEFAULT'))
    settings.set('RULES', address_rules)
    settings = process_address_arg_rules(settings, config)
    settings = process_data_arg_rules(settings, config)
    settings = process_address_file_rules(settings, config)
    return settings


def process_cache_store(settings, config):
    cache_dir = config.get('_CACHE_DIR')
    store = None
    if cache_dir == None:
        logg.warning('no cache dir specified, will discard everything!!')
        from eth_cache.store.null import NullStore
        store = NullStore()
    else:
        store = FileStore(settings.get('CHAIN_SPEC'), cache_dir)
        cache_dir = os.path.realpath(cache_dir)
        if cache_dir == None:
            import tempfile
            cache_dir = tempfile.mkdtemp()
    logg.info('using cache store {}'.format(store))

    settings.set('CACHE_STORE', store)

    return settings


def process_cache_filter(settings, config):
    cache_store = settings.get('CACHE_STORE')
    fltr = CacheFilter(cache_store, rules_filter=settings.o['RULES'], include_tx_data=config.true('ETHCACHE_STORE_TX'))
    sync_store = settings.get('SYNC_STORE')
    sync_store.register(fltr)
    
    fltr = BlockFilter(cache_store, include_block_data=config.true('ETHCACHE_STORE_BLOCK'))
    hndlr = settings.get('BLOCK_HANDLER')
    hndlr.register(fltr)
    
    return settings


def process_tx_filter(settings, config):
    for fltr in list_from_prefix(config, 'filter'):
        m = importlib.import_module(fltr)
        fltr_object = m.Filter(rules_filter=settings.get('RULES'))
        store = settings.get('SYNC_STORE')
        store.register(fltr_object)
        logg.info('using filter module {}'.format(fltr))
    return settings


def process_block_filter(settings, config):
    block_filter_handler = BlockCallbackFilter()
    for block_filter in list_from_prefix(config, 'block_filter'):
        m = importlib.import_module(block_filter)
        block_filter_handler.register(m)
        logg.info('using block filter module {}'.format(block_filter))

    settings.set('BLOCK_HANDLER', block_filter_handler)
    return settings


def process_out_filter(settings, config):
    out_filter = OutFilter(
        settings.o['CHAIN_SPEC'],
        rules_filter=settings.o['RULES'],
        renderers=settings.o['RENDERER'],
        )
    store = settings.get('SYNC_STORE')
    store.register(out_filter)
    return settings


def process_arg_filter(settings, config):
    store = settings.get('SYNC_STORE')
    for k in config.get('ETHMONITOR_FILTER'):
        m = importlib.import_module(k)
        fltr = m.Filter()
        store.register(fltr)
    return settings


def process_filter(settings, config):
    settings.set('FILTER', [])
    settings = process_renderer(settings, config)
    settings = process_block_filter(settings, config)
    settings = process_cache_filter(settings, config)
    settings = process_tx_filter(settings, config)
    settings = process_out_filter(settings, config)
    settings = process_arg_filter(settings, config)
    return settings


def process_renderer(settings, config):
    renderers_mods = []
    for renderer in config.get('ETHMONITOR_RENDERER'):
        m = importlib.import_module(renderer)
        renderers_mods.append(m)
        logg.info('using renderer module {}'.format(renderer))
    settings.set('RENDERER', renderers_mods)
    return settings


def process_cache_rpc(settings, config):
    if not config.true('_FRESH'):
        rpc = CacheRPC(settings.get('RPC'), cache_store)
        settings.set('RPC', rpc)
    return settings


def process_sync_interface(settings, config):
    ifc = EthChainInterface()
    settings.set('SYNCER_INTERFACE', ifc)
    return settings


def process_sync(settings, config):
    settings.set('SYNCER_INTERFACE', EthChainInterface())
    settings = process_sync_range(settings, config)
    return settings
#def process_sync(settings, config):
#    settings = process_sync_interface(settings, config)
#    settings = process_sync_backend(settings, config)
#    settings = process_sync_range(settings, config)
#    return settings


def process_cache(settings, config):
    settings = process_cache_store(settings, config)
    return settings


def process_settings(settings, config):
    settings = process_monitor_session(settings, config)
    settings = process_monitor_session_dir(settings, config)
    settings = process_arg_rules(settings, config)
    settings = process_sync(settings, config)
    settings = process_cache(settings, config)
    settings = process_filter(settings, config)
    return settings
