from pandas import DataFrame, read_csv, concat
from os import listdir
from os.path import isfile

FEATURES_DIRECTORY_PATH = 'Features/'

class Feature(DataFrame):
    
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rename(lambda x: name, axis=1, inplace=True)
        self.name = name
        
    def save(self):
        self.to_csv(f'{FEATURES_DIRECTORY_PATH}{self.name}.csv', index=False)

def load(name):
    df = read_csv(f'{FEATURES_DIRECTORY_PATH}{name}.csv')
    return Feature(name, df)

def ennumerate():
    return [file.split('.')[0] for file in listdir(FEATURES_DIRECTORY_PATH) if isfile(f'{FEATURES_DIRECTORY_PATH}{file}')]

def build(names):
    return concat(names, axis=1)