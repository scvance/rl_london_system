from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Button

from graph import CardType, NodeLocation
from london_system import LondonSystem


def draw_boundaries(graph_ax):
    # draw outline around board
    graph_ax.plot([-0.5, -0.5], [-0.5, 9.7], "k-")
    graph_ax.plot([-0.5, 9.5], [-0.5, -0.5], "k-")
    graph_ax.plot([9.5, 9.5], [9.7, -0.5], "k-")
    graph_ax.plot([9.5, -0.5], [9.7, 9.7], "k-")
    # draw top left corner line
    graph_ax.plot([-0.5, 0.5], [8.5, 8.5], "k-")
    graph_ax.plot([0.5, 0.5], [8.5, 9.7], "k-")
    # draw top right corner line
    graph_ax.plot([9.5, 8.5], [8.5, 8.5], "k-")
    graph_ax.plot([8.5, 8.5], [8.5, 9.7], "k-")
    # draw bottom left corner line
    graph_ax.plot([-0.5, 0.5], [0.5, 0.5], "k-")
    graph_ax.plot([0.5, 0.5], [0.5, -0.5], "k-")
    # draw bottom right corner line
    graph_ax.plot([9.5, 8.5], [0.5, 0.5], "k-")
    graph_ax.plot([8.5, 8.5], [0.5, -0.5], "k-")

    # draw inner boundaries
    graph_ax.plot([-0.5, 9.5], [6.5, 6.5], "k-")
    graph_ax.plot([-0.5, 9.5], [2.5, 2.5], "k-")
    graph_ax.plot([2.5, 2.5], [-0.5, 9.7], "k-")
    graph_ax.plot([6.5, 6.5], [-0.5, 9.7], "k-")


def draw_nodes(graph, graph_ax):
    for node in graph.nodes:
        if node.type == CardType.CIRCLE:
            icon = "●" if node.tourist or node.start else "○"
        elif node.type == CardType.SQUARE:
            icon = "■" if node.tourist or node.start else "□"
        elif node.type == CardType.TRIANGLE:
            icon = "▲" if node.tourist or node.start else "△"
        elif node.type == CardType.PENTAGON:
            icon = "✪" if node.tourist or node.start else "⬠"
        else:
            icon = "?"
        color = node.color if node.start else "black"
        fontweight = "bold" if node.start else "normal"
        graph_ax.text(
            node.xy[0],
            node.xy[1] - 0.08,
            icon,
            fontsize=12,
            color=color,
            ha="center",
            fontweight=fontweight,
        )

        if node.highlighted:
            # draw a box around the node
            graph_ax.plot(
                [node.xy[0] - 0.2, node.xy[0] + 0.2],
                [node.xy[1] + 0.22, node.xy[1] + 0.22],
                "r-",
            )
            graph_ax.plot(
                [node.xy[0] - 0.2, node.xy[0] + 0.2],
                [node.xy[1] - 0.22, node.xy[1] - 0.22],
                "r-",
            )
            graph_ax.plot(
                [node.xy[0] - 0.2, node.xy[0] - 0.2],
                [node.xy[1] - 0.22, node.xy[1] + 0.22],
                "r-",
            )
            graph_ax.plot(
                [node.xy[0] + 0.2, node.xy[0] + 0.2],
                [node.xy[1] - 0.22, node.xy[1] + 0.22],
                "r-",
            )


def draw_edges(graph, graph_ax):
    for edge in graph.edges:
        x_values = [edge.node1.xy[0], edge.node2.xy[0]]
        y_values = [edge.node1.xy[1], edge.node2.xy[1]]
        color = edge.color
        line_width = 0.2
        if color != "black":
            line_width = 0.8
        # draw the edge dotted and thin
        graph_ax.plot(
            x_values, y_values, color=color, linestyle="--", linewidth=line_width
        )


def redraw_graph(graph, graph_ax):
    graph_ax.cla()  # Clear only the graph axes
    graph_ax.set_xlim(-1, 10)
    graph_ax.set_ylim(-1, 10)
    draw_nodes(graph, graph_ax)
    draw_edges(graph, graph_ax)
    draw_boundaries(graph_ax)

    def river(x):
        if -0.5 <= x <= 2:
            return 5.5
        elif 2 < x <= 4:
            return 7.5 - x
        elif 4 < x <= 5:
            return 3.5
        elif 5 < x <= 6:
            return x - 1.5
        elif 6 < x <= 9.5:
            return 4.5

    x_river = np.linspace(-0.5, 9.5, 1000)
    y_river = np.array([river(x) for x in x_river])
    graph_ax.plot(x_river, y_river, "b-")
    graph_ax.axis("off")
    plt.draw()  # Refresh the plot


def show_card(card, card_ax):
    card_ax.cla()
    try:
        card_ax.text(
            0.5, 0.5, f"{card.type.name} {card.color}", fontsize=12, ha="center"
        )
    except AttributeError:
        card_ax.text(0.5, 0.5, f"Switching Colors To {card}!", fontsize=12, ha="center")
    card_ax.axis("off")
    plt.draw()


def restart_game(event, london_system, graph_ax):
    if london_system.colors == []:
        # add a calculate score function
        london_system.start_game()
        redraw_graph(london_system.graph, graph_ax)
    else:
        london_system.start_game()
        redraw_graph(london_system.graph, graph_ax)


def play_game(london_system):
    london_system.start_game()
    fig, graph_ax = plt.subplots(
        figsize=(8, 8)
    )  # Create a separate figure and axes for the graph
    plt.subplots_adjust(bottom=0.2)  # Adjust the bottom to make space for the button
    # create axes to put the card in
    card_ax = plt.axes([0.1, 0.05, 0.1, 0.1])
    card_ax.axis("off")

    reset_button_ax = plt.axes([0.7, 0.01, 0.1, 0.075])
    reset_button = Button(
        reset_button_ax, "Restart", color="lightgray", hovercolor="gray"
    )

    # Draw the initial graph
    redraw_graph(london_system.graph, graph_ax)

    # Add a button in a separate axes below the graph
    ax_button = plt.axes([0.8, 0.01, 0.1, 0.075])
    button = Button(ax_button, "Draw Card", color="lightgray", hovercolor="gray")

    def draw_card(event):
        if london_system.graph.railroad_nodes[london_system.graph.curr_color] == []:
            london_system.graph.railroad_nodes[london_system.graph.curr_color].append(
                london_system.graph.get_start_node()
            )
            print(f"London System railroad_nodes: {london_system.graph.railroad_nodes}")
        card = london_system.draw_card()
        redraw_graph(london_system.graph, graph_ax)
        try:
            print(f"Card: {card.type.name} {card.color}")
            show_card(card, card_ax)
        except AttributeError:
            print(f"Time To Switch Colors!")
            new_color = london_system.next_color()
            print(f"New Color: {new_color}")
            if new_color is None:
                show_card("No More Colors!", card_ax)
                scores = london_system.calculate_score()
                total_score = sum(scores.values())
                print(f"Scores: {scores}")
                print(f"Total Score: {total_score}")
                card_ax.cla()
                card_ax.axis("off")
                scores_text = "\n".join(
                    f"{key}: {value}" for key, value in scores.items()
                )
                scores_text += f"\nTotal: {total_score}"
                card_ax.text(
                    0.5, 0.01, f"Scores:\n{scores_text}", fontsize=8, ha="center"
                )
            else:
                show_card(new_color, card_ax)

    def on_click(event):
        if event.inaxes == graph_ax:  # Ensure the click is on the graph axes
            if event.button == MouseButton.LEFT:
                distances = [
                    np.linalg.norm(
                        np.array([event.xdata, event.ydata]) - np.array(node.xy)
                    )
                    for node in london_system.graph.nodes
                ]
                closest_node = london_system.graph.nodes[np.argmin(distances)]
                if closest_node.highlighted:
                    london_system.graph.unhighlight_all_color()
                    closest_node.highlighted = True
                    london_system.graph.curr_node = closest_node
                    london_system.graph.chose_after_swap = True
                    london_system.graph.swap = False
                else:
                    adjacent_nodes = london_system.graph.get_adjacent(
                        london_system.curr_card
                    )
                    if (
                        closest_node in adjacent_nodes
                        and london_system.curr_card is not None
                    ):
                        london_system.graph.curr_node.highlighted = False
                        # this will need to be updated if I add a confirm button
                        london_system.graph.railroad_nodes[
                            london_system.graph.curr_color
                        ].append(closest_node)
                        london_system.graph.choose_edge(
                            closest_node, london_system.graph.curr_color
                        )
                        closest_node.highlighted = not closest_node.highlighted
                        london_system.curr_card = None
                redraw_graph(london_system.graph, graph_ax)  # Redraw the graph

    fig.canvas.mpl_connect("button_press_event", on_click)
    button.on_clicked(draw_card)
    reset_button.on_clicked(lambda event: restart_game(event, london_system, graph_ax))
    plt.show()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--custom", "-c", default="london_system_default.json", help="Custom graph file"
    )
    args = parser.parse_args()
    london_system = LondonSystem()
    london_system.load_graph(args.custom)
    london_system.reset_deck()
    play_game(london_system)
