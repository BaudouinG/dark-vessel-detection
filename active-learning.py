from learner import Learner
from labeler import Labeler
from Archives.archive import Archive

#%% Instantiations

learner = Learner(initialBatchSize=10, batchSize=5)
labeler = Labeler()
archive = Archive(directory='Archives/Tests')

#%% Definitions

batchCounter = 0

def cycle(queryMethod, batchCounter):
    
    labels = {}
    query = queryMethod()
    
    if batchCounter > 1:
        prediction = {}
        for ID in query:
            prediction[ID] = int(learner.predict(learner.data[ID].reshape(1, -1))[0])
    
    for i in range(len(query)):
        answer = labeler.askLabel(query[i], batch=batchCounter, batchProgress=i+1)
        archive.save(answer)
        labels.update(answer)
    learner.setLabels(labels)
    learner.fitModel()
    
    total = learner.getPositiveTotal()
    if batchCounter > 1:
        accuracy = []
        for ID in labels.keys():
            accuracy.append(labels[ID] == prediction[ID])
    else:
        accuracy = [False]
            
    labeler.dashboard.update(total=total, accuracy=accuracy)

#%% Active Learning Loop

batchCounter += 1
labeler.setBatchSize(learner.initialBatchSize)
cycle(learner.getRandomQuery, batchCounter)

while True:
    
   batchCounter += 1
   labeler.setBatchSize(learner.batchSize)
   cycle(learner.getQuery, batchCounter)