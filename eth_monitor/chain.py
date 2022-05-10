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
        )

class EthChainInterface(ChainInterface):

    def __init__(self):
        self._block_latest = block_latest
        self._block_by_number = block_by_number
        self._block_from_src = Block.from_src
        self._tx_receipt = receipt
        self._src_normalize = Tx.src_normalize
