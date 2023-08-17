# standard imports
import logging
import uuid

# external imports
from chainlib.eth.address import is_same_address
from .error import RuleFail

logg = logging.getLogger()



class RuleData:

    def __init__(self, fragments, description=None, match_all=False):
        self.fragments = fragments
        self.description = description
        if self.description == None:
            self.description = str(uuid.uuid4())
        self.match_all = match_all


    def check(self, sender, recipient, data, tx_hash):
        have_fail = False
        have_match = False
        if len(self.fragments) == 0:
            return False

        for fragment in self.fragments:
            l = len(fragment)
            if len(fragment) > len(data):
                continue
            if fragment in data:
                logg.debug('tx {} rule {} match in DATA FRAGMENT {}'.format(tx_hash, self.description, fragment))
                if not self.match_all:
                    return True
                have_match = True
            else:
                logg.debug('data match all {}'.format(self.match_all))
                if self.match_all:
                    return False
                have_fail = True
        
        return have_match


    def __str__(self):
        return 'Fragment ' + self.description + ' {}'.format(
                self.fragments,
                )


class RuleMethod:

    def __init__(self, methods, description=None, match_all=False):
        self.methods = methods
        self.description = description
        if self.description == None:
            self.description = str(uuid.uuid4())
        if match_all:
            logg.warning('match_all ignord for RuleMethod rule')


    def check(self, sender, recipient, data, tx_hash):
        if len(self.methods) == 0:
            return False

        for method in self.methods:
            l = len(method)
            if len(method) > len(data):
                continue
            if data[:l] == method:
                logg.debug('tx {} rule {} match in DATA {}'.format(tx_hash, self.description, method))
                return True
        
        return False


    def __str__(self):
        return 'Method ' + self.description + ' {}'.format(
                self.methods,
                )


class RuleSimple:

    def __init__(self, outputs, inputs, executables, description=None, match_all=False):
        self.description = description
        if self.description == None:
            self.description = str(uuid.uuid4())
        self.outputs = outputs
        self.inputs = inputs
        self.executables = executables
        self.match_all = match_all

    
    def check(self, sender, recipient, data, tx_hash):
        r = None
        try:
            r = self.__check(sender, recipient, data, tx_hash)
        except RuleFail:
            return False
        return r


    def __check(self, sender, recipient, data, tx_hash):
        have_fail = False
        have_match = False
        for rule in self.outputs:
            if rule != None and is_same_address(sender, rule):
                logg.debug('tx {} rule {} match in SENDER {}'.format(tx_hash, self.description, sender))
                if not self.match_all:
                    return True
                have_match = True
            else:
                if self.match_all:
                    raise RuleFail(rule)
                have_fail = True
        if recipient == None:
            return False
        for rule in self.inputs:
            if rule != None and is_same_address(recipient, rule):
                logg.debug('tx {} rule {} match in RECIPIENT {}'.format(tx_hash, self.description, recipient))
                if not self.match_all:
                    return True
                have_match = True
            else:
                if self.match_all:
                    raise RuleFail(rule)
                have_fail = True
        for rule in self.executables:
            if rule != None and is_same_address(recipient, rule):
                logg.debug('tx {} rule {} match in EXECUTABLE {}'.format(tx_hash, self.description, recipient))
                if not self.match_all:
                    return True
                have_match = True
            else:
                if self.match_all:
                    raise RuleFail(rule)
                have_fail = True

        return have_match


    def __str__(self):
        return 'Simple ' + self.description + ' outputs {} inputs {} execs {}'.format(
                self.outputs,
                self.inputs,
                self.executables,
                )


class AddressRules:

    def __init__(self, include_by_default=False, match_all=False):
        self.excludes = []
        self.includes = []
        self.include_by_default = include_by_default
        self.match_all = match_all


    def exclude(self, rule):
        self.excludes.append(rule)
        logg.info('cache filter added EXCLUDE rule {}'.format(rule))

    
    def include(self, rule):
        self.includes.append(rule)
        logg.info('cache filter added INCLUDE rule {}'.format(rule))


    def apply_rules(self, tx):
        return self.apply_rules_addresses(tx.outputs[0], tx.inputs[0], tx.payload, tx.hash)


    def apply_rules_addresses(self, sender, recipient, data, tx_hash):
        v = self.include_by_default
        have_fail = False
        have_match = False

        for rule in self.includes:
            if rule.check(sender, recipient, data, tx_hash):
                v = True
                logg.info('match in includes rule: {}'.format(rule))
                if not self.match_all:
                    break
            elif self.match_all:
                v = False
                break

        if not v:
            return v

        for rule in self.excludes:
            if rule.check(sender, recipient, data, tx_hash):
                v = False
                logg.info('match in excludes rule: {}'.format(rule))
                if not self.match_all:
                    break
    
        return v
