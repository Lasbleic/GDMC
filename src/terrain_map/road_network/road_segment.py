from graphs.edge import Edge

class RoadSegment(Edge):

    def __init__(self, node1, node2, road_blocks = [], height_map = None):
        super().__init__(node2, node2)
        self.road_blocks = road_blocks

        
        if len(road_blocks) == 0 and height_map is not None:
            road_blocks = self.__find_road(height_map)

    #TODO
    def __find_road(self, height_map):
        return []