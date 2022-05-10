# standard imports
import logging
import os
import uuid
import importlib
import tempfile

# external imports
from chainlib.settings import ChainSettings
from chainsyncer.settings import ChainsyncerSettings
from chainlib.eth.connection import EthHTTPConnection
from eth_monitor.chain import EthChainInterface
from chainlib.eth.address import is_address
from eth_cache.rpc import CacheRPC
from eth_cache.store.file import FileStore


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


class EthMonitorSettings(ChainsyncerSettings):

    def process_monitor_session(self, config):
        session_id = config.get('_SESSION_ID')
        if session_id == None:
            if config.get('_SINGLE'):
                session_id = str(uuid.uuid4())
            else:
                session_id = 'default'
        
        self.o['SESSION_ID'] = session_id


    def process_monitor_session_dir(self, config):
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
            state_dir = os.path.join(config.get('ETHMONITOR_STATE_DIR'), config.get('SYNCER_BACKEND'))
            os.makedirs(state_dir, exist_ok=True)
        logg.info('using engine {} module {}.{}'.format(config.get('SYNCER_BACKEND'), syncer_store_module.__file__, syncer_store_class.__name__))

        session_dir = os.path.join(state_dir, self.o['SESSION_ID'])
        sync_store = syncer_store_class(session_dir, session_id=self.o['SESSION_ID'], state_event_callback=state_change_callback, filter_state_event_callback=filter_change_callback)

        self.o['STATE_DIR'] = state_dir
        self.o['SESSION_DIR'] = session_dir
        self.o['SYNC_STORE'] = sync_store


    def process_address_arg_rules(self, config):
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
        self.o['RULES'].include(includes)

        excludes = RuleSimple(
                category['output']['x'],
                category['input']['x'],
                category['exec']['x'],
                description='EXCLUDE',
                )
        self.o['RULES'].exclude(excludes)


    def process_data_arg_rules(self, config): #rules, args):
        include_data = []
        for v in config.get('ETHMONITOR_DATA'):
            include_data.append(v.lower())
        exclude_data = []
        for v in config.get('ETHMONITOR_X_DATA'):
            exclude_data.append(v.lower())

        includes = RuleMethod(include_data, description='INCLUDE')
        self.o['RULES'].include(includes)
       
        excludes = RuleMethod(exclude_data, description='EXCLUDE')
        self.o['RULES'].exclude(excludes)

        include_data = []
        for v in config.get('ETHMONITOR_DATA_IN'):
            include_data.append(v.lower())
        exclude_data = []
        for v in config.get('ETHMONITOR_X_DATA_IN'):
            exclude_data.append(v.lower())

        includes = RuleData(include_data, description='INCLUDE')
        self.o['RULES'].include(includes)
       
        excludes = RuleData(exclude_data, description='EXCLUDE')
        self.o['RULES'].exclude(excludes)


    def process_address_file_rules(self, config): #rules, includes_file=None, excludes_file=None, include_default=False, include_block_default=False):
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


    def process_arg_rules(self, config):
        address_rules = AddressRules(include_by_default=config.get('ETHMONITOR_INCLUDE_DEFAULT'))
        self.o['RULES'] = address_rules
        self.process_address_arg_rules(config)
        self.process_data_arg_rules(config)
        self.process_address_file_rules(config)


    def process_cache_store(self, config):
        cache_dir = config.get('_CACHE_DIR')
        store = None
        if cache_dir == None:
            logg.warning('no cache dir specified, will discard everything!!')
            from eth_cache.store.null import NullStore
            store = NullStore()
        else:
            store = FileStore(self.o['CHAIN_SPEC'], cache_dir)
            cache_dir = os.path.realpath(cache_dir)
            if cache_dir == None:
                import tempfile
                cache_dir = tempfile.mkdtemp()
        logg.info('using cache store {}'.format(store))

        self.o['CACHE_STORE'] = store


    def process_cache_filter(self, config):
        fltr = CacheFilter(self.o['CACHE_STORE'], rules_filter=self.o['RULES'], include_tx_data=config.true('ETHCACHE_STORE_TX'))
        self.o['SYNC_STORE'].register(fltr)

        fltr = BlockFilter(self.o['CACHE_STORE'], include_block_data=config.true('ETHCACHE_STORE_BLOCK'))
        self.o['BLOCK_HANDLER'].register(fltr)


    def process_tx_filter(self, config):
        for fltr in list_from_prefix(config, 'filter'):
            m = importlib.import_module(fltr)
            fltr_object = m.Filter(rules_filter=self.o['RULES'])
            self.o['SYNC_STORE'].register(fltr_object)
            logg.info('using filter module {}'.format(fltr))


    def process_block_filter(self, config):
        block_filter_handler = BlockCallbackFilter()
        for block_filter in list_from_prefix(config, 'block_filter'):
            m = importlib.import_module(block_filter)
            block_filter_handler.register(m)
            logg.info('using block filter module {}'.format(block_filter))

        self.o['BLOCK_HANDLER'] = block_filter_handler


    def process_out_filter(self, config):
        out_filter = OutFilter(
            self.o['CHAIN_SPEC'],
            rules_filter=self.o['RULES'],
            renderers=self.o['RENDERER'],
            )
        self.o['SYNC_STORE'].register(out_filter)


    def process_filter(self, config):
        self.o['FILTER'] = []

        self.process_renderer(config)

        self.process_block_filter(config)

        self.process_cache_filter(config)
        self.process_tx_filter(config)
        self.process_out_filter(config)


    def process_renderer(self, config):
        renderers_mods = []
        for renderer in list_from_prefix(config, 'renderer'):
            m = importlib.import_module(renderer)
            renderers_mods.append(m)
            logg.info('using renderer module {}'.format(renderer))
        self.o['RENDERER'] = renderers_mods


    def process_cache_rpc(self, config):
        if not config.true('_FRESH'):
            self.o['RPC'] = CacheRPC(self.o['RPC'], cache_store)
   

    def process_common(self, config):
        super(EthMonitorSettings, self).process_common(config)
        # TODO: duplicate from chaind, consider move to chainlib-eth
        rpc_provider = config.get('RPC_PROVIDER')
        if rpc_provider == None:
            rpc_provider = 'http://localhost:8545'
        self.o['RPC'] = EthHTTPConnection(url=rpc_provider, chain_spec=self.o['CHAIN_SPEC'])


    def process_sync_interface(self, config):
        self.o['SYNCER_INTERFACE'] = EthChainInterface()


    def process_sync(self, config):
        self.process_sync_interface(config)
        self.process_sync_backend(config)
        self.process_sync_range(config)


    def process_cache(self, config):
        self.process_cache_store(config)


    def process(self, config):
        self.process_common(config)
        self.process_monitor_session(config)
        self.process_monitor_session_dir(config)
        self.process_arg_rules(config)
        self.process_sync(config)
        self.process_cache(config)
        self.process_filter(config)
