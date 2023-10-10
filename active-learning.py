from learner import Learner
from labeler import Labeler

#%% Instantiations and Definitions

batchSize = 5

learner = Learner(seed=None, batchSize=batchSize)
labeler = Labeler(batchSize=batchSize)

batchCounter = 0

def cycle(queryMethod, batchCounter):
    print(f'entering batch{batchCounter}')
    
    labels = {}
    query = queryMethod()
    
    if batchCounter > 1:
        prediction = {}
        for ID in query:
            prediction[ID] = int(learner.predict(learner.data[ID].reshape(1, -1))[0])
    
    for i in range(len(query)):
        answer = labeler.askLabel(query[i], batch=batchCounter, batchProgress=i+1)
        labels.update(answer)
    learner.setLabels(labels)
    learner.fitModel()
    
    total = learner.getPositiveTotal()
    print('total: ', total)
    if batchCounter > 1:
        accuracy = []
        for ID in labels.keys():
            accuracy.append(labels[ID] == prediction[ID])
    else:
        accuracy = [False]
    print('accuracy: ', accuracy)
            
    labeler.dashboard.update(total=total, accuracy=accuracy)
    print(f'exiting batch{batchCounter}')

#%% Active Learning Loop

batchCounter += 1
cycle(learner.getRandomQuery, batchCounter)

while True:
    
   batchCounter += 1
   cycle(learner.getQuery, batchCounter)