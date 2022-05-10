# standard imports
import logging
import os
import uuid
import importlib

# external imports
from chainlib.settings import ChainSettings
from chainsyncer.settings import ChainsyncerSettings
from chainlib.eth.connection import EthHTTPConnection

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
            state_dir = os.path.join(config.get('_STATE_DIR'), config.get('SYNCER_BACKEND'))

        logg.info('using engine {} module {}.{}'.format(config.get('SYNCER_BACKEND'), syncer_store_module.__file__, syncer_store_class.__name__))

        #state_dir = os.path.join(state_dir, config.get('_SESSION_ID'))
        sync_store = syncer_store_class(state_dir, session_id=session.get('SESSION_ID'), state_event_callback=state_change_callback, filter_state_event_callback=filter_change_callback)

        self.o['STATE_DIR'] = state_dir
        self.o['SYNC_STORE'] = sync_store


    def process_common(self, config):
        super(EthMonitorSettings, self).process_common(config)
        # TODO: duplicate from chaind, consider move to chainlib-eth
        rpc_provider = config.get('RPC_PROVIDER')
        if rpc_provider == None:
            rpc_provider = 'http://localhost:8545'
        self.o['RPC'] = EthHTTPConnection(url=rpc_provider, chain_spec=self.o['CHAIN_SPEC'])


    def process(self, config):
        self.process_common(config)
        self.process_monitor_session(config)
