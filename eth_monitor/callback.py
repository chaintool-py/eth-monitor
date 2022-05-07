class BlockCallbackFilter:

    def __init__(self):
        self.filters = []


    def register(self, fltr):
        self.filters.append(fltr)


    def filter(self, block, tx=None):
        for fltr in self.filters:
            fltr.filter(block, tx=tx)
