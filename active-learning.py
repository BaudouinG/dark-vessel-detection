from learner import Learner
from labeler import Labeler


learner = Learner()
labeler = Labeler()


labels = {}
for ID in learner.getRandomQuery():
    labels.update(labeler.askLabel(ID))
learner.setLabels(labels)
learner.fitModel()

# here we should carry some model evaluation, e.g. learner.evaluate()

while True:
    labels = {}
    for ID in learner.getQuery():
        labels.update(labeler.askLabel(ID))
    learner.setLabels(labels)
    learner.fitModel()
    
    # here we should carry some model evaluation, e.g. learner.evaluate()