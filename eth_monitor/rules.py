# standard imports
import logging

# external imports
from chainlib.eth.address import is_same_address

logg = logging.getLogger()


class AddressRules:

    def __init__(self, include_by_default=False):
        self.excludes = []
        self.includes = []
        self.include_by_default = include_by_default


    def exclude(self, sender=None, recipient=None, executable=None):
        self.excludes.append((sender, recipient, executable,))
        logg.info('cache filter added EXCLUDE rule sender {} recipient {} executable {}'.format(sender, recipient, executable))


    def include(self, sender=None, recipient=None, executable=None):
        self.includes.append((sender, recipient, executable,))
        logg.info('cache filter added INCLUDE rule sender {} recipient {} executable {}'.format(sender, recipient, executable))


    def apply_rules(self, tx):
        return self.apply_rules_addresses(tx.outputs[0], tx.inputs[0], tx.hash)


    def apply_rules_addresses(self, sender, recipient, tx_hash):
        v = self.include_by_default

        for rule in self.includes:
            if rule[0] != None and is_same_address(sender, rule[0]):
                logg.debug('tx {} rule INCLUDE match in SENDER {}'.format(tx_hash, sender))
                v = True
            elif rule[1] != None and is_same_address(recipient, rule[1]):
                logg.debug('tx {} rule INCLUDE match in RECIPIENT {}'.format(tx_hash, recipient))
                v = True
            elif rule[2] != None and is_same_address(recipient, rule[2]):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx_hash, recipient))
                v = True
        for rule in self.excludes:
            if rule[0] != None and is_same_address(sender, rule[0]):
                logg.debug('tx {} rule INCLUDE match in SENDER {}'.format(tx_hash, sender))
                v = False
            elif rule[1] != None and is_same_address(recipient, rule[1]):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx_hash, recipient))
                v = False
            elif rule[2] != None and is_same_address(recipient, rule[2]):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx_hash, recipient))
                v = False
        return v
