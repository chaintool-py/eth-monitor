# standard imports
import logging
import uuid

# external imports
from chainlib.eth.address import is_same_address

logg = logging.getLogger()


class RuleSimple:

    def __init__(self, outputs, inputs, executables, description=None):
        self.description = description
        if self.description == None:
            self.description = str(uuid.uuid4())
        self.outputs = outputs
        self.inputs = inputs
        self.executables = executables


    def check(self, sender, recipient, tx_hash):
        for rule in self.outputs:
            if rule != None and is_same_address(sender, rule):
                logg.debug('tx {} rule INCLUDE match in SENDER {}'.format(tx_hash, sender))
                return True
        for rule in self.inputs:
            if rule != None and is_same_address(recipient, rule):
                logg.debug('tx {} rule INCLUDE match in RECIPIENT {}'.format(tx_hash, recipient))
                return True
        for rule in self.executables:
            if rule != None and is_same_address(recipient, rule):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx_hash, recipient))
                return True


    def __str__(self):
        return 'Simple ' + self.description + ' outputs {} inputs {} execs {}'.format(
                self.outputs,
                self.inputs,
                self.executables,
                )


class AddressRules:

    def __init__(self, include_by_default=False):
        self.excludes = []
        self.includes = []
        self.include_by_default = include_by_default


    def exclude(self, rule):
        self.excludes.append(rule)
        logg.info('cache filter added EXCLUDE rule {}'.format(rule))

    
    def include(self, rule):
        self.includes.append(rule)
        logg.info('cache filter added EXCLUDE rule {}'.format(rule))


    def apply_rules(self, tx):
        return self.apply_rules_addresses(tx.outputs[0], tx.inputs[0], tx.hash)


    def apply_rules_addresses(self, sender, recipient, tx_hash):
        v = self.include_by_default

        for rule in self.includes:
            if rule.check(sender, recipient, tx_hash):
                v = True
                logg.info('match in includes rule: {}'.format(rule))
                break

        for rule in self.excludes:
            if rule.check(sender, recipient, tx_hash):
                v = False
                logg.info('match in excludes rule: {}'.format(rule))
                break

        return v
