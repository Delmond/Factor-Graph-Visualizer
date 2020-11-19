#!/usr/bin/python

#
# This script converts a dense matrix into an image of the underlying graph.
# There are multiple ways to use this script:
#    By passing the input through a pipelike in this example:
#	cat factors.txt | ./visualizer.py
#    By provigin the location of the input file:
#       ./visualizer -i factors.txt
#
# The first line of the pipe must contain the size of the matrix.
#

import sys

from graph_tool.all import Graph
from graph_tool.draw import graph_draw, sfdp_layout
from argparse import ArgumentParser

EPSILON = 1e-10
COLORS = ["white", "green", "blue", "yellow", "purple", "brown", "orange", "teal", "magenta", "cyan", "grey", "pink"]


def check_matrix_dimensions(matrix, height, width):
    if height is not None:
        # Check if the provided height is the same as the actual height
        assert height == len(matrix), "The matrix is incorrect."
    else:
        height = len(matrix)

    if width is None:
        width = len(matrix[0])

    for i in range(height):
        assert width == len(matrix[i]), "The matrix width is incorrect."


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument("--no-size",
                        action="store_false",
                        help="Provide this flag if the there is not size information in the first row of the input.",
                        default=True
                       )

    parser.add_argument("-i", "--input",
                        help="The location of the file containing the input matrix. Leave this out to get the input matrix from the pipe.",
                        type=str
                       )

    parser.add_argument("-m", "--mapping",
                        help="File that is used to split the nodes of the graph into clusters.",
                        type=str
                       )

    parser.add_argument("-o", "--output",
                        help="The location of the output file.",
                        type=str,
                        default="result.png"
                       )

    args, _ = parser.parse_known_args()

    options = {
        "has_size": args.no_size,
        "matrix_location": args.input,
        "mapping_location": args.mapping,
        "output_file": args.output
    }

    return options

def parse_input(content, has_size):

    assert content != '', "Input/Pipe is empty, aborting..."

    matrix = []
    for index, line in enumerate(content):
        row = line.split()
        if has_size and index == 0:
            height, width = list(map(int, row))
            continue

        matrix.append(list(map(float, row)))

    if ~has_size:
        height, width = len(matrix), len(matrix[0])

    check_matrix_dimensions(matrix, height, width)
    return height, width, matrix

def parse_mapping(content, has_size):

    assert content != '', "Mapping is empty, aborting..."

    mapping = list(map(int, content.split()))
    if has_size:
       height, width = mapping[:2]
       mapping = mapping[2:]
       assert height == len(mapping) or width == len(mapping), "Incorrect mapping size..."
    return mapping

def main():
    options = parse_arguments()

    # Get the string containing the input matrix form a file/pipe
    if options["matrix_location"] is not None:
        with open(options["matrix_location"], 'r') as file:
            matrix_string = file.read().strip().split("\n")
    else:
        matrix_string = sys.stdin

    # Parse the input matrix string
    height, width, matrix = parse_input(matrix_string, options["has_size"])

    # Get the string containing the mapping if specified
    if options["mapping_location"] is not None:
        with open(options["mapping_location"], 'r') as file:
            mapping_string = file.read().strip()
        mapping = parse_mapping(mapping_string, options["has_size"])
    else:
        mapping = None


    graph = Graph()
    graph.add_vertex(height + width)

    shape = graph.new_vertex_property("string")
    color = graph.new_vertex_property("string")
    index = graph.new_vertex_property("string")


    for i in range(height):
        v = graph.vertex(i)
        shape[v] = "square"
        color[v] = "red"
        index[v] = str(i)

    for i in range(width):
        v = graph.vertex(height + i)
        shape[v] = "circle"
        if mapping is not None:
            color[v] = COLORS[mapping[i] % len(COLORS)]
        else:
            color[v] = COLORS[0]
        index[v] = str(i)

    for i in range(height):
        for j in range(width):
            if abs(matrix[i][j]) < EPSILON:
                continue
            graph.add_edge(graph.vertex(i), graph.vertex(height + j))

    graph.set_directed(False)

    if mapping is not None:
        groups = graph.new_vertex_property("int")
        for i in range(width):
            v = graph.vertex(height + i)
            groups[v] = mapping[i]
        position = sfdp_layout(graph, groups=groups)
    else:
        position = None

    graph_draw(graph,
        pos=position,
        vertex_text=index,
        vertex_shape=shape,
        vertex_fill_color=color,
        vertex_pen_width=1.2,
        vertex_color="black",
        edge_pen_width=3.4,
        fit_view=True,
        bg_color=(255, 255, 255, 1),
        output=options["output_file"])

if __name__ == "__main__":
    main()
