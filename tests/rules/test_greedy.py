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


    def test_greedy_includes(self):
        data = b''
        outs = [self.alice]
        ins = [self.carol]
        execs = []
        rule = RuleSimple(outs, ins, execs, match_all=True)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.carol, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.alice, self.carol, data, self.hsh)
        self.assertTrue(r)

        rule = RuleSimple(outs, ins, execs)
        c = AddressRules(match_all=True)
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.bob, self.alice, data, self.hsh)
        self.assertFalse(r)
        r = c.apply_rules_addresses(self.bob, self.carol, data, self.hsh)
        self.assertTrue(r)
        r = c.apply_rules_addresses(self.alice, self.carol, data, self.hsh)
        self.assertTrue(r)


    def test_greedy_data(self):
        data = os.urandom(128).hex()
        data_match_one = data[4:8]
        data_match_two = data[32:42]
        data_match_fail = os.urandom(64).hex()
        data_match = [data_match_one]

        rule = RuleData(data_match, match_all=True)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)

        data_match = [data_match_two]
        rule = RuleData(data_match, match_all=True)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)

        data_match = [data_match_two, data_match_one]
        rule = RuleData(data_match, match_all=True)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertTrue(r)

        data_match = [data_match_two, data_match_fail, data_match_one]
        rule = RuleData(data_match, match_all=True)
        c = AddressRules()
        c.include(rule)
        r = c.apply_rules_addresses(self.alice, self.bob, data, self.hsh)
        self.assertFalse(r)


if __name__ == '__main__':
    unittest.main()
