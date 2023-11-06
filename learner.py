import numpy as np
import warnings

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from cardinal.zhdanov2019 import TwoStepKMeansSampler

from features import load, build



FEATURES = ['darkduration', 'darkspeed', 'deviationCos', 'deviationSin',
            'disappearBearingCos', 'disappearBearingSin', 'disappearDistance',
            'disappearEdgeRatio', 'reappearBearingCos', 'reappearBearingSin',
            'reappearDistance', 'reappearEdgeRatio', 'localrate', 'overallrate']
BATCH_SIZE = 5
INITIAL_BATCH_SIZE = 17
MISSING_LABEL = np.nan
SEED = None


class Learner():
    
    def __init__(self,
                 batchSize=BATCH_SIZE,
                 initialBatchSize=INITIAL_BATCH_SIZE,
                 features=FEATURES,
                 missingLabel=MISSING_LABEL,
                 seed=SEED):
        
        self.batchSize = batchSize
        self.initialBatchSize = initialBatchSize
        data = build([load(name) for name in features])
        data = StandardScaler().fit_transform(data)
        self.data = data
        
        self.labels = np.full(shape=len(data), fill_value=missingLabel)
        
        self.randomGenerator = np.random.default_rng(seed)
        self.model = GradientBoostingClassifier()
        self.sampler = TwoStepKMeansSampler(3, self.model, self.batchSize)
    
    def setLabels(self, labels):
        
        for ID in labels.keys():
            self.labels[ID] = labels[ID]
    
    def fitModel(self):
        
        self.model.fit(self.data[self.isLabeled()], self.labels[self.isLabeled()])
    
    def predict(self, data=None):
        
        if data is None:
            data = self.data
            
        return self.model.predict(data)
    
    def getPositiveTotal(self):
        
        return np.sum(self.predict())
    
    def isLabeled(self):
        
        validLabels = [0.0, 1.0]
        testArrays = []
        for labelValue in validLabels:
            testArrays.append(self.labels == labelValue)
            
        return np.logical_or(*testArrays)
    
    def getRandomQuery(self):
        
        return self.randomGenerator.integers(0, len(self.data), self.initialBatchSize)
    
    def getQuery(self):
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.sampler.fit(self.data[self.isLabeled()], self.labels[self.isLabeled()])
            
            return self.sampler.select_samples(self.data[np.logical_not(self.isLabeled())])
