import tensorflow as tf
import numpy as np
import librosa
import os

class Inference:
    drum_types = ['Clap', 'Closed Hat', 'Kick', 'Open Hat', 'Snare']
    unknown = 'Unknown'
    model: tf.keras.Model

    def __init__(self):
        self.model = tf.keras.models.load_model(os.getcwd() + "/model") 
        self.model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
              metrics=['accuracy'])

    def prepare(self, location: str):
        # Creates Empty Numpy Array the size required to fit into the model
        # Loads the Audio File, converts it to a melspectogram, and fits it into Numpy Array
        sample_data = []
        sample = np.zeros((128, 100, 3))
        y, sr = librosa.load(location,sr=22050)
        y, _ = librosa.effects.trim(y, top_db=50)
        y = librosa.resample(y=y, orig_sr=sr, target_sr=22050)
        melspect = librosa.feature.melspectrogram(y=y)    

        for i, _ in enumerate(melspect): #128
            for j, _ in enumerate(melspect[i]): #LENGTH
                sample[i][j] = melspect[i][j]

        sample_data = [sample]
    
        return np.array(sample_data)

    def predict(self, location: str):
        prepared = self.prepare(location)
        prediction = self.model.predict(prepared) 
        index = int(np.argmax(prediction,axis=1))

        if 0 <= index < len(self.drum_types):
            return self.drum_types[index]
        
        return self.unknown
