from enum import Enum


class CardType(Enum):
    CIRCLE = 1
    TRIANGLE = 2
    SQUARE = 3
    PENTAGON = 4
    RANDOM = 5
    RAILROAD = 6


class NodeLocation(Enum):
    TOP_LEFT_SMALL = 1
    TOP_LEFT_LARGE = 2
    TOP_MIDDLE = 3
    TOP_RIGHT_LARGE = 4
    TOP_RIGHT_SMALL = 5
    MIDDLE_LEFT = 6
    MIDDLE_MIDDLE = 7
    MIDDLE_RIGHT = 8
    BOTTOM_LEFT_SMALL = 9
    BOTTOM_LEFT_LARGE = 10
    BOTTOM_MIDDLE = 11
    BOTTOM_RIGHT_LARGE = 12
    BOTTOM_RIGHT_SMALL = 13


class Node:
    def __init__(
        self,
        type=None,
        tourist=None,
        location=None,
        xy=None,
        number=0,
        start=False,
        color=None,
    ):
        self.type = type
        self.tourist = tourist
        self.location = location
        self.xy = xy
        self.start = start
        self.color = color
        self.highlighted = False

    def to_dict(self):
        return {
            "type": self.type.name,
            "tourist": self.tourist,
            "location": self.location.name,
            "xy": self.xy,
            "start": self.start,
            "color": self.color,
        }

    def from_dict(self, data):
        self.type = CardType[data["type"]]
        self.tourist = data["tourist"]
        self.location = NodeLocation[data["location"]]
        self.xy = data["xy"]
        self.start = data["start"]
        self.color = data["color"]

    def __eq__(self, other):
        return self.xy == other.xy


class Edge:
    def __init__(self, node1=None, node2=None, blocks_edges=[], crosses_river=False):
        self.node1 = node1
        self.node2 = node2
        self.blocks_edges = blocks_edges
        self.blocked = False
        self.crosses_river = crosses_river
        self.highlighted = False
        self.target = False
        self.color = "black"

    def block(self):
        self.blocked = True

    def unblock(self):
        self.blocked = False

    def to_dict(self):
        serialized_blocks_edges = list(self.blocks_edges)
        return {
            "node1": self.node1.to_dict(),
            "node2": self.node2.to_dict(),
            "blocks_edges": serialized_blocks_edges,
            "blocked": self.blocked,
            "crosses_river": self.crosses_river,
        }

    def from_dict(self, data):
        self.node1 = Node()
        self.node1.from_dict(data["node1"])
        self.node2 = Node()
        self.node2.from_dict(data["node2"])
        self.blocks_edges = data["blocks_edges"]
        self.blocked = data["blocked"]
        self.crosses_river = data["crosses_river"]

    def __eq__(self, other):
        return self.node1 == other.node1 and self.node2 == other.node2


class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.curr_node = None
        self.railroad_nodes = {"red": [], "blue": [], "green": [], "purple": []}
        self.railroad_edges = {"red": [], "blue": [], "green": [], "purple": []}
        self.curr_color = None
        self.swap = False
        self.chose_after_swap = True

    def add_node(self, node):
        self.nodes.append(node)

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_start_node(self):
        for node in self.nodes:
            if node.start and node.color == self.curr_color:
                return node
        return None

    def highlight_all_color(self):
        for node in self.railroad_nodes[self.curr_color]:
            node.highlighted = True

    def unhighlight_all_color(self):
        for node in self.railroad_nodes[self.curr_color]:
            node.highlighted = False

    def get_adjacent(self, card=None, start_node=None):
        adj = []
        # we have the start node as none initially so that the railroad use case can recursively call this function
        if start_node is None:
            start_node = self.curr_node

        # if we are using the card AFTER the railroad, we need to get all adjacent nodes that can be reached from any node in the current color track
        if card is not None and card.type != CardType.RAILROAD and self.swap:
            self.swap = False
            # all of the valid nodes next to any node in the current color track are valid
            for node in self.railroad_nodes[self.curr_color]:
                adj += self.get_adjacent(card, node)
            return adj

        # search the edges that connect to our current node and add them to the adjacent list if they are not blocked
        # and the next node is of the correct type
        for edge in self.edges:
            if edge.node1 == start_node and not edge.blocked:
                if card is not None and (
                    edge.node2.type == card.type
                    or card.type == CardType.RANDOM
                    or edge.node2.type == CardType.RANDOM
                ):
                    adj.append(edge.node2)
                elif card is None:
                    adj.append(edge.node2)
            elif edge.node2 == start_node and not edge.blocked:
                if card is not None and (
                    edge.node1.type == card.type
                    or card.type == CardType.RANDOM
                    or edge.node1.type == CardType.RANDOM
                ):
                    adj.append(edge.node1)
                elif card is None:
                    adj.append(edge.node1)
        return adj

    # this searches all of the edges for the edge that contains the two nodes
    def get_edge(self, node1, node2):
        for edge in self.edges:
            if edge.node1 == node1 and edge.node2 == node2:
                return edge
            elif edge.node1 == node2 and edge.node2 == node1:
                return edge
        return None

    # given two nodes, find the edge that connects them and block it
    def block_edge(self, node1, node2):
        edge = self.get_edge(node1, node2)
        if edge:
            edge.block()

    def unblock_edge(self, node1, node2):
        edge = self.get_edge(node1, node2)
        if edge:
            edge.unblock()

    # we must turn all edges back into black, and ensure they are not highlighted, blocked, or targeted
    def reset_graph(self):
        for edge in self.edges:
            edge.blocked = False
            edge.highlighted = False
            edge.target = False
            edge.color = "black"

    # this function will add a desired edge to the graph. by default it'll use the current node, but it can be overridden
    def choose_edge(self, target, color, curr_node=None):
        if curr_node is None:
            curr_node = self.curr_node

        # if we haven't chosen after the railroad swap, we need to unhighlight all nodes (every node in the color will be currently highlighted)
        if not self.chose_after_swap:
            self.chose_after_swap = True
            self.unhighlight_all_color()
            for node in self.railroad_nodes[color]:
                # this returns false if it fails to choose the edge.
                if self.choose_edge(target, color, node):
                    return True
            return False

        edge = self.get_edge(curr_node, target)
        if edge and not edge.blocked:
            # after choosing an edge, we must block it, change it to the correct color, and then block all edges that intersect with it
            edge.block()
            edge.color = color
            for block_edge in edge.blocks_edges:
                b_edge = self.edges[block_edge]
                node1 = b_edge.node1
                node2 = b_edge.node2
                self.block_edge(node1, node2)
            # then we will update the current node to be our target node
            self.curr_node = target
            # finally we ensure that our list of edges in this color is updated
            self.railroad_edges[color].append(edge)
            return True
        return False

    # this just finds the node that starts a particular color track.
    def start_color(self, color):
        for node in self.nodes:
            if node.start:
                if node.color == color:
                    self.curr_node = node
                    return True
