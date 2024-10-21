import click
import os
from inference import Inference
import simpleaudio as sa

target_types = ['wav', 'aiff']

def traverse(start: str, dive = False):
    files = []

    for entry in os.scandir(start):
        if entry.is_dir():
            files = files + traverse(entry.path, dive) if dive else files
        else:
            files.append(entry)

    return files

def get_type(entry: os.DirEntry):
    return entry.name.split('.')[-1]

def play(entry: os.DirEntry):
    wave_obj = sa.WaveObject.from_wave_file(entry.path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

@click.command()
@click.option('--dir', default=os.getcwd())
@click.option('--dive/--no-dive', default=True)
def infer(dir: str, dive: bool):
    inference = Inference()
    files = traverse(dir, dive)

    for file in files:
        if get_type(file) in target_types:
            try:
                predicition = inference.predict(file.path)
                print(file.path, predicition)
                play(file)
            except IndexError:
                print(file.path, "Sample too long")



if __name__ == "__main__":
    infer()

