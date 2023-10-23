from pandas import DataFrame, read_csv, concat
from os.path import isfile
from time import time


# This is the name of the directory within the main
# 'Archives' directory where archives will be stored.
ARCHIVE_DIRECTORY = 'Baudouin'


def makeDf(*args):
    
    if len(args) == 0:
        df = DataFrame({'time': [], 'gapID': [], 'label': []})
        df.set_index('time', inplace=True)
    
    else:
        df = DataFrame({'time': args[0], 'gapID': args[1], 'label': args[2]})
        df.set_index('time', inplace=True)
    
    return df

class Archive():
    
    def __init__(self, name=None, directory=ARCHIVE_DIRECTORY):
        """ Instantiate an Archive. If a name is given, will try to load a
        pre-existing Archive with the corresponding name, and create a new
        Archive if it does not already exist. If no nome is given, a new
        Archive is created, named after the time of creation."""
        
        if type(name) is str:
            self.name = name
            self.path = f'{directory}/{self.name}.csv'
            if isfile(self.path):
                self.df = DataFrame(data=read_csv(self.path))
                self.df.set_index('time', inplace=True)
            else:
                self.df = makeDf()
                
        else:
            self.name = str(time()).replace('.', '_')
            self.path = f'{directory}/{self.name}.csv'
            self.df = makeDf()
    
    def __repr__(self):
        
        temp = f'name: {self.name}\npath: {self.path}\n\n'
        temp += self.df.__repr__()
        
        return temp
        
    def save(self, answer=None):
        
        if answer is not None:
            gapIDs = list(answer.keys())
            labels = [answer[gapID] for gapID in gapIDs]
            times = [time() for gapID in gapIDs]
            newRow = makeDf(times, gapIDs, labels)
            self.df = concat([self.df, newRow])
                
        self.df.to_csv(self.path)