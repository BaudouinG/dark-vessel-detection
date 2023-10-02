from features import load, build


FEATURES = ['darkduration', 'darkspeed', 'deviationCos', 'deviationSin',
            'disappearBearingCos', 'disappearBearingSin', 'disappearDistance',
            'disappearEdgeRatio', 'reappearBearingCos', 'reappearBearingSin',
            'reappearDistance', 'reappearEdgeRatio']


class Learner():
    
    def __init__(self, answers, queries, querySize, features=FEATURES):
        self.answers = answers
        self.queries = queries
        self.querySize = querySize
        self.data = build([load(name) for name in features])
    
    def run(self):
        lastAnswer = self.answers.get()
        # process answer
        
        # fit the model
        newQuery = []
        self.queries.put(newQuery)
    
    def initialQuery(self):
        query = []
        self.queries.put(query)
        self.queries.put(query)