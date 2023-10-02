class Oracle():
    
    def __init__(self, answers, queries):
        self.answers = answers
        self.queries = queries
        
    def answer(self):
        query = self.queries.get()
        answer = self.label(query)
        self.answers.put(answer)
        
    def label(self, query):
        
        labels = {self.test}
        return labels