from multiprocessing import Process, Queue

from learner import Learner
from oracle import Oracle


QUERY_SIZE = 5


answers = Queue()
queries = Queue()
learner = Learner(answers, queries, QUERY_SIZE)
oracle = Oracle(answers, queries)


learner.initialQuery()
oracle.answer()

if __name__ == '__main__':
    while True:
        learning = Process(target=learner.run)
        labeling = Process(target=oracle.answer)
        learning.start()
        labeling.start()
        learning.join()
        labeling.join()
        
        