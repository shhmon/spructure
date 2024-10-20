import click
import os
from inference import Inference
import simpleaudio as sa

target_types = ['wav', 'aiff']

def traverse(start: str, dive = False):
    files = []

    for entry in os.listdir(start):
        path = os.path.join(start, entry)

        if os.path.isdir(path):
            files = files + traverse(path, dive) if dive else files
        else:
            files.append(path)

    return files

def get_type(path: str):
    return path.split('/')[-1].split('.')[-1]

def play(path: str):
    wave_obj = sa.WaveObject.from_wave_file(path)
    play_obj = wave_obj.play()
    play_obj.wait_done()

@click.command()
@click.option('--dir', default=os.getcwd())
@click.option('--dive/--no-dive', default=True)
def main(dir: str, dive: bool):
    inference = Inference()
    files = traverse(dir, dive)

    for file in files:
        if get_type(file) in target_types:
            try:
                predicition = inference.predict(file)
                print(file, predicition)
            except:
                print(file, "Failed prediction")

            play(file)


if __name__ == "__main__":
    main()

