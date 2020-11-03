from graphs.node import Node
from utils import Point2D

type_switcher = {
    0: 'None',
    1: 'Deadend',
    2: 'Street',
    3: 'Junction',
    4: 'Crossroads',
    5: 'Square'
}

class RoadNode(Node, Point2D):

    def __init__(self, point):
        Node.__init__()
        Point2D.__init__(point.x, point.z)
        
    def get_type(self):
        return type_switcher.get(min(5, self.arity), 'InvalidType')

        
def test():
    roadnode = RoadNode(Point2D(0, 5))
    print(roadnode.x)

test()
