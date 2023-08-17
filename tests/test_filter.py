# standard imports
import logging
import unittest
import os

# local imports
from eth_monitor.rules import *

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestRule(unittest.TestCase):

    def setUp(self):
        self.alice = os.urandom(20).hex()
        self.bob = os.urandom(20).hex()
        self.carol = os.urandom(20).hex()
        self.dave = os.urandom(20).hex()
        self.x = os.urandom(20).hex()
        self.y = os.urandom(20).hex()
        self.hsh = os.urandom(32).hex()

    
    def test_address_include(self):
        outs = [self.alice]
        ins = []
        execs = []
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules()
        c.include(rule)
        data = b''
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)


if __name__ == '__main__':
    unittest.main()
