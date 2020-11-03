from node import Node
from edge import Edge

class Graph:

    def __init__(self):
        self.nodes = dict()
        self.representative = dict()


    def add_connex_component(self, root):
        if root in self.nodes:
            return
        self.nodes[root] = dict()
        self.representative[root] = root

    def attach(self, node_to_insert, node_to_attach_to, edge = None):
        self.add_connex_component(node_to_insert)
        self._connect(node_to_insert, node_to_attach_to, edge)

    def _connect(self, node1, node2, edge = None):
        if edge is None:
            edge = Edge(node1, node2)

        node1.arity += 1
        node2.arity += 1
        self.nodes[node1][node2] = edge
        self.nodes[node2][node1] = edge
        self.representative[self.get_representative(node1)] = self.get_representative(node2)

    def get_representative(self, node):
        previous_representative = node
        current_representative = self.representative[node]
        while previous_representative != current_representative:
            previous_representative = current_representative
            current_representative = self.representative[current_representative]
        return current_representative

    def get_nodes(self):
        return self.nodes.keys()

    def delete_node(self, node):
        for neighbour in self.nodes[node].keys():
            del self.nodes[neighbour][node]
            neighbour.arity -= 1
            if neighbour.arity == 0:
                self.representative[neighbour] = neighbour
        
        del self.nodes[node]
        del self.representative[node]
        

def test():
    graph = Graph()

    node1 = Node()
    node2 = Node()
    node3 = Node()

    node4 = Node()
    node5 = Node()
    node6 = Node()

    graph.add_connex_component(node1)
    graph.attach(node2, node1)
    graph.attach(node3, node2)

    graph.add_connex_component(node4)
    graph.attach(node5, node4)
    graph.attach(node6, node5)

    graph._connect(node1, node4)
    print(graph.get_representative(node3) == graph.get_representative(node6))
    print("Hello World")
    

#test()