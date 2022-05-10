# standard imports
import logging
import os
import uuid
import importlib

# external imports
from chainlib.settings import ChainSettings
from chainsyncer.settings import ChainsyncerSettings
from chainlib.eth.connection import EthHTTPConnection

# local imports
from eth_monitor.rules import (
        AddressRules,
        RuleSimple,
        RuleMethod,
        RuleData,
        )

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


    #def process_address_arg_rules(rules, args):
    def process_address_arg_rules(self, config):
        include_inputs = config.get('ETHMONITOR_INPUTS')
        if include_inputs == None:
            include_inputs = []
        else:
            include_inputs = include_inputs.split(',')

        include_outputs = config.get('ETHMONITOR_OUTPUTS')
        if include_outputs == None:
            include_outputs = []
        else:
            include_outputs = include_outputs.split(',')

        include_exec = config.get('ETHMONITOR_EXEC')
        if include_exec == None:
            include_exec = []
        else:
            include_exec = include_exec.split(',')

        exclude_inputs = config.get('ETHMONITOR_X_INPUTS')
        if exclude_inputs == None:
            exclude_inputs = []
        else:
            exclude_inputs = exclude_inputs.split(',')

        exclude_outputs = config.get('ETHMONITOR_X_OUTPUTS')
        if exclude_outputs == None:
            exclude_outputs = []
        else:
            exclude_outputs = exclude_outputs.split(',')

        exclude_exec = config.get('ETHMONITOR_X_EXEC')
        if exclude_exec == None:
            exclude_exec = []
        else:
            exclude_exec = exclude_exec.split(',')


        address = config.get('ETHMONITOR_ADDRESS')
        if address != None:
            for address in address.split(','):
                include_inputs.append(address)
                include_outputs.append(address)
                include_exec.append(address)

        address = config.get('ETHMONITOR_X_ADDRESS')
        if address != None:
            for address in address.split(','):
                exclude_inputs.append(address)
                exclude_outputs.append(address)
                exclude_exec.append(address)

        includes = RuleSimple(include_outputs, include_inputs, include_exec, description='INCLUDE')
        self.o['RULES'].include(includes)

        excludes = RuleSimple(exclude_outputs, exclude_inputs, exclude_exec, description='EXCLUDE')
        self.o['RULES'].exclude(excludes)


    def process_arg_rules(self, config):
        address_rules = AddressRules(include_by_default=config.get('ETHMONITOR_INCLUDE_DEFAULT'))
        self.o['RULES'] = address_rules

        self.process_address_arg_rules(config)


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
        self.process_arg_rules(config)
