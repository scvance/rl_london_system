import json
import random
from enum import Enum

from card import Card
from graph import CardType, Edge, Graph, Node, NodeLocation


class LondonSystem:
    def __init__(self):
        self.cards = [
            Card(CardType.CIRCLE, "red"),
            Card(CardType.CIRCLE, "blue"),
            Card(CardType.TRIANGLE, "red"),
            Card(CardType.TRIANGLE, "blue"),
            Card(CardType.SQUARE, "red"),
            Card(CardType.SQUARE, "blue"),
            Card(CardType.PENTAGON, "red"),
            Card(CardType.PENTAGON, "blue"),
            Card(CardType.RANDOM, "red"),
            Card(CardType.RANDOM, "blue"),
            Card(CardType.RAILROAD, None),
        ]
        self.red_cards_played = 0
        self.graph = None
        self.colors = ["red", "blue", "green", "purple"]
        self.curr_card = None

    def start_game(self):
        self.reset_game()
        self.graph.curr_color = random.choice(self.colors)
        self.colors.remove(self.graph.curr_color)
        self.graph.curr_node = self.graph.get_start_node()
        self.graph.curr_node.highlighted = True

    def reset_game(self):
        self.red_cards_played = 0
        self.reset_deck()
        self.colors = ["red", "blue", "green", "purple"]
        self.graph.railroad_edges = {"red": [], "blue": [], "green": [], "purple": []}
        self.graph.railroad_nodes = {"red": [], "blue": [], "green": [], "purple": []}
        self.graph.reset_graph()

    def next_color(self):
        try:
            self.graph.curr_color = random.choice(self.colors)
            self.colors.remove(self.graph.curr_color)
            self.reset_deck()
        except:
            print("No more colors left")
            return None
        try:
            self.graph.curr_node = self.graph.get_start_node()
            self.graph.curr_node.highlighted = True
        except:
            print(f"No start node for color: {self.graph.curr_color}")
            return None
        return self.graph.curr_color

    def draw_card(self):
        if self.graph.curr_color is None:
            self.graph.curr_color = random.choice(self.colors)
            self.colors.remove(self.graph.curr_color)
            try:
                self.graph.curr_node = self.graph.get_start_node()
                self.graph.curr_node.highlighted = True
            except:
                print("graph has not been set up")
                return None

        if self.graph.curr_node is None:
            # this would only happen in a custom game where the start node is not set
            raise Exception(f"No start node found for color {self.graph.curr_color}")

        if self.red_cards_played == 5 or len(self.cards) == 0:
            return None

        card = random.choice(self.cards)
        self.cards.remove(card)
        if card.color == "red":
            self.red_cards_played += 1
        self.curr_card = card
        if card.type == CardType.RAILROAD:
            self.graph.swap = True
            self.graph.chose_after_swap = False
            self.graph.highlight_all_color()
        return card

    def choose_card(self, type, color):
        for card in self.cards:
            if card.type == type and card.color == color:
                self.cards.remove(card)
                return card
        return None  # TODO: add some kind of error handling

    def reset_deck(self):
        self.cards = [
            Card(CardType.CIRCLE, "red"),
            Card(CardType.CIRCLE, "blue"),
            Card(CardType.TRIANGLE, "red"),
            Card(CardType.TRIANGLE, "blue"),
            Card(CardType.SQUARE, "red"),
            Card(CardType.SQUARE, "blue"),
            Card(CardType.PENTAGON, "red"),
            Card(CardType.PENTAGON, "blue"),
            Card(CardType.RANDOM, "red"),
            Card(CardType.RANDOM, "blue"),
            Card(CardType.RAILROAD, None),
        ]
        self.red_cards_played = 0
        if self.graph.curr_node is not None:
            self.graph.curr_node.highlighted = False

    def save_graph(self, filename):
        graph_data = {
            "nodes": [node.to_dict() for node in self.graph.nodes],
            "edges": [edge.to_dict() for edge in self.graph.edges],
        }

        with open(filename, "w") as file:
            json.dump(graph_data, file, indent=4)

        print(f"Graph saved to {filename}")

    def load_graph(self, filename):
        with open(filename, "r") as file:
            graph_data = json.load(file)

        graph = Graph()
        for node_data in graph_data["nodes"]:
            node = Node()
            node.from_dict(node_data)
            graph.add_node(node)

        for edge_data in graph_data["edges"]:
            edge = Edge()
            edge.from_dict(edge_data)
            graph.add_edge(edge)

        self.graph = graph
        print(f"Graph loaded from {filename}")

    def calculate_score(self):
        color_scores = {}
        for color in ["red", "blue", "green", "purple"]:
            used_nodes = []
            used_edges = []
            different_areas = {}
            most_in_area = 0
            river_crossings = 0
            for node in self.graph.railroad_nodes[color]:
                # if someone visits a node twice it shouldn't be counted twice
                if node in used_nodes:
                    continue
                if node.location not in different_areas:
                    different_areas[node.location] = 1
                else:
                    different_areas[node.location] += 1
                if different_areas[node.location] > most_in_area:
                    most_in_area = different_areas[node.location]
                used_nodes.append(node)
            num_areas = len(different_areas)

            for edge in self.graph.railroad_edges[color]:
                # just in case a duplicate edge somehow gets added
                if edge in used_edges:
                    continue
                used_edges.append(edge)
                if edge.crosses_river:
                    river_crossings += 1
            # each river crossing is worth 2 points
            color_scores[color] = num_areas * most_in_area + 2 * river_crossings
            print(
                f"{color} areas: {num_areas}, most in area: {most_in_area}, river crossings: {river_crossings}"
            )

        # find nodes that are in multiple colors or tourist stations
        color_scores["bi-color"] = 0
        color_scores["tri-color"] = 0
        color_scores["quad-color"] = 0
        color_scores["tourist"] = 0
        for node in self.graph.nodes:
            num_in_colors = 0
            for color in ["red", "blue", "green", "purple"]:
                if node in self.graph.railroad_nodes[color]:
                    num_in_colors += 1
                    if node.tourist:
                        color_scores["tourist"] += 1
            if num_in_colors == 2:
                color_scores["bi-color"] += 1
            elif num_in_colors == 3:
                color_scores["tri-color"] += 1
            elif num_in_colors == 4:
                color_scores["quad-color"] += 1
        # these counts are worth 2,5, and 9 point each based on the board game rules.
        color_scores["bi-color"] = color_scores["bi-color"] * 2
        color_scores["tri-color"] = color_scores["tri-color"] * 5
        color_scores["quad-color"] = color_scores["quad-color"] * 9
        # this array of tourist scores is just the scoring given in the board game
        tourist_scores = [0, 1, 2, 4, 6, 8, 11, 14, 17, 21, 25]
        if color_scores["tourist"] < len(tourist_scores):
            color_scores["tourist"] = tourist_scores[color_scores["tourist"]]
        else:
            color_scores["tourist"] = 25
        return color_scores

    def setup_graph(self):
        graph = Graph()
        # Define all the nodes first
        topl_pent = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.TOP_LEFT_SMALL,
            xy=(0, 9),
        )
        topl_tri = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.TOP_LEFT_LARGE,
            xy=(1, 9),
        )
        topl_square_large = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.TOP_LEFT_LARGE,
            xy=(2, 9),
        )
        topl_circle_large = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.TOP_LEFT_LARGE,
            xy=(0, 7),
        )
        topl_pent_large = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.TOP_LEFT_LARGE,
            xy=(1, 8),
        )

        top_mid_square = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.TOP_MIDDLE,
            xy=(3, 8),
        )
        top_mid_tri_start = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.TOP_MIDDLE,
            start=True,
            color="green",
            xy=(3, 7),
        )
        top_mid_tri_1 = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.TOP_MIDDLE,
            number=1,
            xy=(4, 9),
        )
        top_mid_circle = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.TOP_MIDDLE,
            xy=(5, 9),
        )
        top_mid_pent_tourist = Node(
            type=CardType.PENTAGON,
            tourist=True,
            location=NodeLocation.TOP_MIDDLE,
            xy=(6, 8),
        )
        top_mid_square_1 = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.TOP_MIDDLE,
            number=1,
            xy=(6, 7),
        )

        top_right_tri = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.TOP_RIGHT_LARGE,
            xy=(7, 9),
        )
        top_right_square = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.TOP_RIGHT_LARGE,
            xy=(8, 8),
        )
        top_right_pent = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.TOP_RIGHT_LARGE,
            xy=(9, 8),
        )
        top_right_tri_1 = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.TOP_RIGHT_LARGE,
            number=1,
            xy=(9, 7),
        )

        top_right_circle_small = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.TOP_RIGHT_SMALL,
            xy=(9, 9),
        )

        mid_left_square_tourist = Node(
            type=CardType.SQUARE,
            tourist=True,
            location=NodeLocation.MIDDLE_LEFT,
            xy=(0, 6),
        )
        mid_left_pent = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.MIDDLE_LEFT,
            xy=(2, 6),
        )
        mid_left_tri = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.MIDDLE_LEFT,
            xy=(1, 5),
        )
        mid_left_pent_1 = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.MIDDLE_LEFT,
            number=1,
            xy=(0, 4),
        )
        mid_left_square = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.MIDDLE_LEFT,
            xy=(2, 5),
        )
        mid_left_square_1_start = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.MIDDLE_LEFT,
            number=1,
            start=True,
            color="purple",
            xy=(2, 4),
        )

        mid_mid_tri = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            xy=(4, 6),
        )
        mid_mid_circle = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            xy=(6, 6),
        )
        mid_mid_pent = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            xy=(4, 5),
        )
        mid_mid_square = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            xy=(5, 5),
        )
        mid_mid_tri_1 = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            number=1,
            xy=(4, 3),
        )
        mid_mid_circle_1 = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            number=1,
            xy=(4, 4),
        )
        mid_mid_pent_1 = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            number=1,
            xy=(3, 3),
        )
        mid_mid_square_1 = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.MIDDLE_MIDDLE,
            number=1,
            xy=(6, 3),
        )
        mid_mid_random_tourist = Node(
            type=CardType.RANDOM,
            tourist=True,
            location=NodeLocation.MIDDLE_MIDDLE,
            xy=(5, 6),
        )

        mid_right_circle_start = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.MIDDLE_RIGHT,
            start=True,
            color="red",
            xy=(7, 6),
        )
        mid_right_tri = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.MIDDLE_RIGHT,
            xy=(7, 3),
        )
        mid_right_square = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.MIDDLE_RIGHT,
            xy=(9, 6),
        )
        mid_right_pent = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.MIDDLE_RIGHT,
            xy=(8, 5),
        )
        mid_right_circle_1 = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.MIDDLE_RIGHT,
            number=1,
            xy=(7, 4),
        )
        mid_right_tri_1_tourist = Node(
            type=CardType.TRIANGLE,
            tourist=True,
            location=NodeLocation.MIDDLE_RIGHT,
            number=1,
            xy=(9, 3),
        )

        bottom_left_tri_small = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.BOTTOM_LEFT_SMALL,
            xy=(0, 0),
        )

        bottom_left_circle_large = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.BOTTOM_LEFT_LARGE,
            xy=(0, 2),
        )
        bottom_left_square_large = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.BOTTOM_LEFT_LARGE,
            xy=(1, 0),
        )
        bottom_left_circle_1_large = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.BOTTOM_LEFT_LARGE,
            number=1,
            xy=(1, 1),
        )
        bottom_left_square_1_large = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.BOTTOM_LEFT_LARGE,
            number=1,
            xy=(2, 2),
        )

        bottom_mid_circle = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.BOTTOM_MIDDLE,
            xy=(3, 2),
        )
        bottom_mid_pent = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.BOTTOM_MIDDLE,
            xy=(3, 0),
        )
        bottom_mid_circle_1_tourist = Node(
            type=CardType.CIRCLE,
            tourist=True,
            location=NodeLocation.BOTTOM_MIDDLE,
            number=1,
            xy=(4, 0),
        )
        bottom_mid_tri = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.BOTTOM_MIDDLE,
            xy=(5, 0),
        )
        bottom_mid_pent_start_1 = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.BOTTOM_MIDDLE,
            start=True,
            color="blue",
            number=1,
            xy=(5, 2),
        )
        bottom_mid_pent_2 = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.BOTTOM_MIDDLE,
            number=2,
            xy=(6, 1),
        )

        bottom_right_circle_large = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.BOTTOM_RIGHT_LARGE,
            xy=(7, 0),
        )
        bottom_right_tri_large = Node(
            type=CardType.TRIANGLE,
            tourist=False,
            location=NodeLocation.BOTTOM_RIGHT_LARGE,
            xy=(8, 1),
        )
        bottom_right_pent_large = Node(
            type=CardType.PENTAGON,
            tourist=False,
            location=NodeLocation.BOTTOM_RIGHT_LARGE,
            xy=(9, 2),
        )
        bottom_right_circle_1_large = Node(
            type=CardType.CIRCLE,
            tourist=False,
            location=NodeLocation.BOTTOM_RIGHT_LARGE,
            number=1,
            xy=(8, 2),
        )

        bottom_right_square_small = Node(
            type=CardType.SQUARE,
            tourist=False,
            location=NodeLocation.BOTTOM_RIGHT_SMALL,
            xy=(9, 0),
        )

        # Add nodes to the graph
        graph.add_node(topl_pent)
        graph.add_node(topl_tri)
        graph.add_node(topl_square_large)
        graph.add_node(topl_circle_large)
        graph.add_node(topl_pent_large)

        graph.add_node(top_mid_square)
        graph.add_node(top_mid_tri_start)
        graph.add_node(top_mid_tri_1)
        graph.add_node(top_mid_circle)
        graph.add_node(top_mid_pent_tourist)
        graph.add_node(top_mid_square_1)

        graph.add_node(top_right_tri)
        graph.add_node(top_right_square)
        graph.add_node(top_right_pent)
        graph.add_node(top_right_tri_1)

        graph.add_node(top_right_circle_small)

        graph.add_node(mid_left_square_tourist)
        graph.add_node(mid_left_pent)
        graph.add_node(mid_left_tri)
        graph.add_node(mid_left_pent_1)
        graph.add_node(mid_left_square)
        graph.add_node(mid_left_square_1_start)

        graph.add_node(mid_mid_tri)
        graph.add_node(mid_mid_circle)
        graph.add_node(mid_mid_pent)
        graph.add_node(mid_mid_square)
        graph.add_node(mid_mid_tri_1)
        graph.add_node(mid_mid_circle_1)
        graph.add_node(mid_mid_pent_1)
        graph.add_node(mid_mid_square_1)
        graph.add_node(mid_mid_random_tourist)

        graph.add_node(mid_right_circle_start)
        graph.add_node(mid_right_tri)
        graph.add_node(mid_right_square)
        graph.add_node(mid_right_pent)
        graph.add_node(mid_right_circle_1)
        graph.add_node(mid_right_tri_1_tourist)

        graph.add_node(bottom_left_tri_small)

        graph.add_node(bottom_left_circle_large)
        graph.add_node(bottom_left_square_large)
        graph.add_node(bottom_left_circle_1_large)
        graph.add_node(bottom_left_square_1_large)

        graph.add_node(bottom_mid_circle)
        graph.add_node(bottom_mid_pent)
        graph.add_node(bottom_mid_circle_1_tourist)
        graph.add_node(bottom_mid_tri)
        graph.add_node(bottom_mid_pent_start_1)
        graph.add_node(bottom_mid_pent_2)

        graph.add_node(bottom_right_circle_large)
        graph.add_node(bottom_right_tri_large)
        graph.add_node(bottom_right_pent_large)
        graph.add_node(bottom_right_circle_1_large)

        graph.add_node(bottom_right_square_small)

        self.graph = graph
