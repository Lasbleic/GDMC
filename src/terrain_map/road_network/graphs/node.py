class Node:

    def __init__(self):
        self.arity = 0
        
        
    def __hash__(self):
        return id(self)