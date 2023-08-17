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
        data = b''
        outs = [self.alice]
        ins = []
        execs = []
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)

        outs = []
        ins = [self.alice]
        execs = []
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertTrue(r)

        outs = []
        ins = []
        execs = [self.x]
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.x, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)

        data = b'deadbeef0123456789'
        data_match = [data[:8]]
        rule = RuleMethod(data_match)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.x, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, b'abcd' + data, self.hsh)
        self.assertFalse(r)

        rule = RuleData(data_match)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.x, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, b'abcd' + data, self.hsh)
        self.assertTrue(r)


    def test_address_exclude(self):
        data = b''
        outs = [self.alice]
        ins = []
        execs = []
        rule = RuleSimple(outs, ins, execs)

        c = AddressRules()
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)

        c = AddressRules(include_by_default=True)
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertTrue(r)

        outs = []
        ins = [self.alice]
        execs = []
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules(include_by_default=True)
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)

        outs = []
        ins = []
        execs = [self.x]
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules(include_by_default=True)
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.x, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertTrue(r)

        data = b'deadbeef0123456789'
        data_match = [data[:8]]
        rule = RuleMethod(data_match)
        c = AddressRules(include_by_default=True)
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.x, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, b'abcd' + data, self.hsh)
        self.assertTrue(r)

        rule = RuleData(data_match)
        c = AddressRules(include_by_default=True)
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.x, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, b'abcd' + data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, b'abcd', self.hsh)
        self.assertTrue(r)

    
    def test_address_include_exclude(self):
        data = b''
        outs = [self.alice]
        ins = []
        execs = []
        rule = RuleSimple(outs, ins, execs)
        c = AddressRules()
        c.include(rule)
        c.exclude(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)



if __name__ == '__main__':
    unittest.main()
