class Filter:

    def __init__(self, store, include_block_data=False):
        self.store = store
        self.include_block_data = include_block_data


    def filter(self, block, tx=None):
        self.store.put_block(block, include_data=self.include_block_data)
