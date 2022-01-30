# standard imports
import os
import json
import logging

# external imports
from hexathon import strip_0x
from chainlib.eth.tx import (
        Tx,
        pack,
        )
from chainsyncer.backend.file import chain_dir_for
from leveldir.numeric import NumDir
from leveldir.hex import HexDir

logg = logging.getLogger(__name__)

base_dir = '/var/lib'


class FileStore:

    def put_tx(self, tx, include_data=False):
        raw = pack(tx.src(), self.chain_spec)
        tx_hash_dirnormal = strip_0x(tx.hash).upper()
        tx_hash_bytes = bytes.fromhex(tx_hash_dirnormal)
        self.tx_raw_dir.add(tx_hash_bytes, raw)
        if self.address_rules != None:
            for a in tx.outputs + tx.inputs:
                if self.address_rules.apply_rules_addresses(a, a, tx.hash):
                    a_hex = strip_0x(a).upper()
                    a = bytes.fromhex(a_hex)
                    self.address_dir.add_dir(tx_hash_dirnormal, a, b'')
                    dirpath = self.address_dir.to_filepath(a_hex)
                    fp = os.path.join(dirpath, '.start')
                    num = tx.block.number
                    num_compare = 0
                    try:
                        f = open(fp, 'rb')
                        r = f.read(8)
                        f.close()
                        num_compare = int.from_bytes(r, 'big')
                    except FileNotFoundError:
                        pass

                    if num_compare == 0 or num < num_compare:
                        logg.debug('recoding new start block {} for {}'.format(num, a))
                        num_bytes = num.to_bytes(8, 'big')
                        f = open(fp, 'wb')
                        f.write(num_bytes)
                        f.close()

        if include_data:
            src = json.dumps(tx.src()).encode('utf-8')
            self.tx_dir.add(bytes.fromhex(strip_0x(tx.hash)), src)


    def put_block(self, block, include_data=False):
        hash_bytes = bytes.fromhex(strip_0x(block.hash))
        self.block_num_dir.add(block.number, hash_bytes)
        num_bytes = block.number.to_bytes(8, 'big')
        self.block_hash_dir.add(hash_bytes, num_bytes)
        if include_data:
            src = json.dumps(block.src()).encode('utf-8')
            self.block_src_dir.add(hash_bytes, src)


    def __init__(self, chain_spec, cache_root=base_dir, address_rules=None):
        self.cache_root = os.path.join(
            cache_root,
            'eth_monitor',
            chain_spec.engine(),
            chain_spec.fork(),
            str(chain_spec.chain_id()),
            )
        self.cache_root = os.path.realpath(self.cache_root)
        self.chain_dir = chain_dir_for(self.cache_root)
        self.cache_dir = os.path.join(self.chain_dir, 'cache')
        self.block_src_path = os.path.join(self.cache_dir, 'block', 'src')
        self.block_src_dir = HexDir(self.block_src_path, 32, levels=2)
        self.block_num_path = os.path.join(self.cache_dir, 'block', 'num')
        self.block_num_dir = NumDir(self.block_num_path, [100000, 1000])
        self.block_hash_path = os.path.join(self.cache_dir, 'block', 'hash')
        self.block_hash_dir = HexDir(self.block_hash_path, 32, levels=2)
        self.tx_path = os.path.join(self.cache_dir, 'tx', 'src')
        self.tx_raw_path = os.path.join(self.cache_dir, 'tx', 'raw')
        self.tx_dir = HexDir(self.tx_path, 32, levels=2)
        self.tx_raw_dir = HexDir(self.tx_raw_path, 32, levels=2)
        self.address_path = os.path.join(self.cache_dir, 'address')
        self.address_dir = HexDir(self.address_path, 20, levels=2)
        self.chain_spec = chain_spec
        self.address_rules = address_rules


    def __str__(self):
        return 'FileStore: root {}'.format(self.cache_root)
