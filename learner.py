from matplotlib import pyplot as plt
import numpy as np
from time import time
import pandas as pd
import warnings

from sklearn.datasets import load_digits
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from cardinal.uncertainty import MarginSampler
from cardinal.clustering import KMeansSampler
from cardinal.random import RandomSampler
from cardinal.plotting import plot_confidence_interval
from cardinal.base import BaseQuerySampler
from cardinal.zhdanov2019 import TwoStepKMeansSampler
from cardinal.utils import ActiveLearningSplitter

from features import load, build


FEATURES = ['darkduration', 'darkspeed', 'deviationCos', 'deviationSin',
            'disappearBearingCos', 'disappearBearingSin', 'disappearDistance',
            'disappearEdgeRatio', 'reappearBearingCos', 'reappearBearingSin',
            'reappearDistance', 'reappearEdgeRatio']
BATCH_SIZE = 5
MISSING_LABEL = np.nan
SEED = 0

class Learner():
    
    def __init__(self, batchSize=BATCH_SIZE, features=FEATURES, missingLabel=MISSING_LABEL, seed=SEED):
        
        self.batchSize = batchSize
        data = build([load(name) for name in features])
        data = StandardScaler().fit_transform(data)
        self.data = data
        self.labels = np.full(shape=len(data), fill_value=missingLabel)
        
        self.randomGenerator = np.random.default_rng(seed)
        self.model = RandomForestClassifier(random_state=seed, verbose=False)
        self.sampler = TwoStepKMeansSampler(3, self.model, self.batchSize)
    
    def setLabels(self, labels):
        
        for ID in labels.keys():
            self.labels[ID] = labels[ID]
    
    def fitModel(self):
        
        self.model.fit(self.data[self.isLabeled()], self.labels[self.isLabeled()])
    
    def isLabeled(self):
        
        validLabels = [0.0, 1.0]
        testArrays = []
        for labelValue in validLabels:
            testArrays.append(self.labels == labelValue)
            
        return np.logical_or(*testArrays)
    
    def getRandomQuery(self):
        
        return self.randomGenerator.integers(0, len(self.data), self.batchSize)
    
    def getQuery(self):
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.sampler.fit(self.data[self.isLabeled()], self.labels[self.isLabeled()])
            
            return self.sampler.select_samples(self.data[np.logical_not(self.isLabeled())])


#l = Learner()