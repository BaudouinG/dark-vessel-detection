from learner import Learner
from labeler import Labeler

#%% Instantiations and Definitions

batchSize = 5

learner = Learner(seed=None, batchSize=batchSize)
labeler = Labeler(batchSize=batchSize)

batchCounter = 0

def cycle(queryMethod, batchCounter):
    
    labels = {}
    query = queryMethod()
    for i in range(len(query)):
        labels.update(labeler.askLabel(query[i], batch=batchCounter, batchProgress=i+1))
    learner.setLabels(labels)
    learner.fitModel()
    
    # here we should carry some model evaluation, e.g. learner.evaluate()

#%% Active Learning Loop

batchCounter += 1
cycle(learner.getRandomQuery, batchCounter)

while True:
    
   batchCounter += 1
   cycle(learner.getQuery, batchCounter)