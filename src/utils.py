import os
import shutil

class Path:
    def __init__(self, *args):
        self.args = args

    def append(self, *args):
        return Path(*self.args, *args)

    def fuzzy_find(self, query):
        path = str(self)
        file = None

        try:
            if os.path.isdir(path):
                file = next(entry.path for entry in os.scandir(path) if query in entry.name)
        except: pass

        return file

    def make_directory(self):
        path = str(self)
        if not os.path.isdir(path): os.mkdir(path)
        return self

    def clear_directory(self):
        path = str(self)
        if os.path.isdir(path): shutil.rmtree(path)
        os.mkdir(path)
        return self

    def __str__(self):
        return os.path.join(*self.args)

class SampleWrapper:
    def __init__(self, sample: list, path: Path):
        self.sample = sample
        self.path = sample[1]
        self.hash = sample[8]
        self.filename = sample[10]
        self.link_path = str(path.append(self.filename))

    def generate_symlink(self):
        print(f'Generating symlink {self.link_path}')
        if not os.path.exists(self.link_path):
            os.symlink(self.path, self.link_path)
