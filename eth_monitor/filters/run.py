# standard imports
import os


class Filter:

    def __init__(self, run_dir):
        self.run_dir = run_dir
        self.fp = os.path.join(run_dir, 'block')


    def filter(self, conn, block):
        f = open(self.fp, 'w')
        f.write(str(block.number))
        f.close()
        return False
