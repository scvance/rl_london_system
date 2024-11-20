import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Button

from london_system import Edge, LondonSystem

system = LondonSystem()
system.setup_graph()
graph = system.graph

# Extract node positions
node_positions = [node.xy for node in graph.nodes]

edges = []
selected_points = []  # To keep track of selected points for edge creation
system_edges = []


def river(x):
    if 0 <= x <= 2:
        return 5.5
    elif 2 < x <= 4:
        return 7.5 - x
    elif 4 < x <= 5:
        return 3.5
    elif 5 < x <= 6:
        return x - 1.5
    elif 6 < x <= 9:
        return 4.5


# Generate x values for the river
x_river = np.linspace(0, 9, 1000)
y_river = np.array([river(x) for x in x_river])


# Draw the graph
def draw_graph():
    plt.figure(figsize=(8, 8))
    plt.title("London System Graph")
    plt.xlabel("X")
    plt.ylabel("Y")

    # Plot the nodes
    for i, (x, y) in enumerate(node_positions):
        plt.plot(x, y, "bo")  # Blue dots for nodes
        plt.text(x, y + 0.2, f"{i}", fontsize=9, ha="center")  # Label nodes

    # Plot the edges
    for edge in edges:
        x_values = [edge[0][0], edge[1][0]]
        y_values = [edge[0][1], edge[1][1]]
        plt.plot(x_values, y_values, "black")  # Black lines for edges

    # Plot the river
    plt.plot(x_river, y_river, "b-")

    plt.xlim(-1, 10)
    plt.ylim(-1, 10)


def redraw_graph():
    """Redraw the graph with updated edges."""
    plt.cla()

    # Plot points
    for idx, (x, y) in enumerate(node_positions):
        plt.scatter(x, y, color="blue")
        plt.text(x, y, f"{idx}", fontsize=9, ha="right")

    # Plot edges
    for edge in edges:
        x_values = [edge[0][0], edge[1][0]]
        y_values = [edge[0][1], edge[1][1]]
        plt.plot(x_values, y_values, color="black")

    # Plot the river
    plt.plot(x_river, y_river, "b-")

    plt.xlim(-1, 10)
    plt.ylim(-1, 10)
    plt.draw()


def on_click(event):
    """Handle mouse clicks for selecting points and creating edges."""
    global selected_points

    if event.button == MouseButton.LEFT:
        # Find the closest point
        clicked_point = (event.xdata, event.ydata)
        if clicked_point is None:
            return

        closest_idx = None
        min_dist = float("inf")
        for idx, point in enumerate(graph.nodes):
            dist = (point.xy[0] - clicked_point[0]) ** 2 + (
                point.xy[1] - clicked_point[1]
            ) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_idx = idx

        if closest_idx is not None:
            selected_points.append(closest_idx)
            print(f"Selected point {closest_idx}:")

        if len(selected_points) == 2:
            # Create an edge between the two selected points
            edge_start = graph.nodes[selected_points[0]].xy
            edge_end = graph.nodes[selected_points[1]].xy
            edges.append((edge_start, edge_end))
            edge = Edge(
                graph.nodes[selected_points[0]], graph.nodes[selected_points[1]]
            )
            system_edges.append(edge)
            selected_points = []  # Reset selections
            print(f"Added edge: {edges[-1]}")
            redraw_graph()
            intersections = get_intersections()
            if intersections:
                print("Intersecting edges:")
                for edge1, edge2 in intersections:
                    print(f"Edge {edge1} intersects with edge {edge2}")


def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0:
        return 0  # Collinear
    return 1 if val > 0 else 2  # Clockwise or Counterclockwise


def do_segments_intersect(p1, q1, p2, q2):
    def orientation(p, q, r):
        # Calculate the orientation of the triplet (p, q, r)
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0:
            return 0  # Collinear
        return 1 if val > 0 else 2  # Clockwise or Counterclockwise

    def on_segment(p, q, r):
        # Check if q lies on segment pr
        return min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and min(p[1], r[1]) <= q[
            1
        ] <= max(p[1], r[1])

    # Find the 4 orientations
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if o1 != o2 and o3 != o4:
        # Exclude intersection at endpoints
        if p1 in [p2, q2] or q1 in [p2, q2]:
            return False
        return True

    # Collinear cases
    if o1 == 0 and on_segment(p1, p2, q1):
        return p2 not in [p1, q1]  # Exclude endpoints
    if o2 == 0 and on_segment(p1, q2, q1):
        return q2 not in [p1, q1]  # Exclude endpoints
    if o3 == 0 and on_segment(p2, p1, q2):
        return p1 not in [p2, q2]  # Exclude endpoints
    if o4 == 0 and on_segment(p2, q1, q2):
        return q1 not in [p2, q2]  # Exclude endpoints

    return False


def check_edge_intersection_with_river(edge_start, edge_end):
    """Check if the edge intersects with the river."""
    river_segments = [(x_river[i], y_river[i]) for i in range(len(x_river) - 1)]

    for i in range(len(river_segments) - 1):
        river_start = river_segments[i]
        river_end = river_segments[i + 1]
        if do_segments_intersect(edge_start, edge_end, river_start, river_end):
            return True
    return False


def get_intersections():
    intersecting_edges = []

    for i, edge1 in enumerate(edges):
        for j, edge2 in enumerate(edges):
            if i >= j:
                continue  # Avoid duplicate checks
            if do_segments_intersect(edge1[0], edge1[1], edge2[0], edge2[1]):
                intersecting_edges.append((i, j))

    system_edges_copy = [Edge(edge.node1, edge.node2) for edge in system_edges]
    for edge in system_edges_copy:
        intersects_river = check_edge_intersection_with_river(
            edge.node1.xy, edge.node2.xy
        )
        if intersects_river:
            edge.crosses_river = True
        edge.blocks_edges = set()
    for i, j in intersecting_edges:
        system_edges_copy[i].blocks_edges.add(j)
        system_edges_copy[j].blocks_edges.add(i)

    london_system_copy = LondonSystem()
    london_system_copy.setup_graph()
    london_system_copy.graph.edges = system_edges_copy
    london_system_copy.save_graph("london_system_copy.json")

    return intersecting_edges


# Main function
def main():
    draw_graph()
    plt.gcf().canvas.mpl_connect("button_press_event", on_click)
    plt.show()


if __name__ == "__main__":
    main()
