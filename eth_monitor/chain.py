# external imports
from chainlib.interface import ChainInterface
from chainlib.eth.block import (
        block_latest,
        block_by_number,
        Block,
        )
from chainlib.eth.tx import (
        receipt,
        Tx,
        transaction,
        )

class EthChainInterface(ChainInterface):

    def __init__(self, dialect_filter=None, batch_limit=1):
        super(EthChainInterface, self).__init__(dialect_filter=dialect_filter, batch_limit=batch_limit)
        self.batch_limit = batch_limit
        self._block_latest = block_latest
        self._block_by_number = block_by_number
        self._block_from_src = Block.from_src
        self._tx_from_src = Tx.from_src
        self._tx_receipt = receipt
        self._src_normalize = Tx.src_normalize
        self._dialect_filter = dialect_filter
        self._tx_by_hash = transaction
