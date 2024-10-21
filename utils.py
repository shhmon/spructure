import os

class PathBuilder:
    def __init__(self, *args):
        self.args = args

    def add(self, *args):
        return PathBuilder(*self.args, *args)

    def settle(self):
        return os.path.join(*self.args)

