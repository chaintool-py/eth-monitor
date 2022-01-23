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
        v = False

        for rule in self.includes:
            if rule[0] != None and is_same_address(tx.outputs[0], rule[0]):
                logg.debug('tx {} rule INCLUDE match in SENDER {}'.format(tx.hash, tx.outputs[0]))
                v = True
            elif rule[1] != None and is_same_address(tx.inputs[0], rule[1]):
                logg.debug('tx {} rule INCLUDE match in RECIPIENT {}'.format(tx.hash, tx.inputs[0]))
                v = True
            elif rule[2] != None and is_same_address(tx.inputs[0], rule[2]):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx.hash, tx.inputs[0]))
                v = True
        for rule in self.excludes:
            if rule[0] != None and is_same_address(tx.outputs[0], rule[0]):
                logg.debug('tx {} rule INCLUDE match in SENDER {}'.format(tx.hash, tx.outputs[0]))
                v = False
            elif rule[1] != None and is_same_address(tx.inputs[0], rule[1]):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx.hash, tx.inputs[0]))
                v = False
            elif rule[2] != None and is_same_address(tx.inputs[0], rule[2]):
                logg.debug('tx {} rule INCLUDE match in ExECUTABLE {}'.format(tx.hash, tx.inputs[0]))
                v = False
        return v
