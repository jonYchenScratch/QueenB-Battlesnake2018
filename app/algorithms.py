from .utils import neighbours, surrounding, sub, dist, touching, next_to_wall
from .entities import Board
from .constants import DIR_NAMES, DIR_VECTORS, SNAKE, EMPTY, FOOD, SPOILED, SAFE_SPACE_FACTOR, ENABLE_CHECKERBOARD_SIZE,\
                       FOOD_RATING, SPOILED_RATING, EMPTY_RATING, BODY_RATING, ENEMY_RATING, OUT_SIDE_BOARD_RATING

import time
import random
from functools import reduce
from math import floor
from copy import deepcopy
from collections import deque


def rate_cell(cell, board, bloom_level=4):
    """ rates a cell based on proximity to other snakes, food, the edge of the board, etc """

    cells = []
    # Get all the cells of "bloom_level" number of circles surrounding the given cell.
    for x in range(-bloom_level, bloom_level+1):
        for y in range(-bloom_level, bloom_level+1):
            division_factor = dist((cell[0]+x, cell[1]+y), cell)
            if division_factor == 0:
                division_factor = 1
            cells.append(((cell[0]+x, cell[1]+y), division_factor))

    # EMPTY = 0
    # SNAKE = 1
    # FOOD = 2
    # SPOILED = 3
    own_snake = board.get_snake(board.own_snake_id)
    cell_weightings = [EMPTY_RATING, ENEMY_RATING, FOOD_RATING, SPOILED_RATING, BODY_RATING, OUT_SIDE_BOARD_RATING]
    cell_values = []

    for m_cell in cells:
        weight_key = 5  # Outside the board
        if board.inside(m_cell[0]):
            weight_key = board.get_cell(m_cell[0])
            if m_cell[0] in own_snake.coords:
                weight_key = 4
        cell_values.append((weight_key, m_cell[1]))

    return reduce(lambda carry, m_cell: carry + cell_weightings[m_cell[0]]/m_cell[1], cell_values, 0)


def flood_fill(board, start_pos, allow_start_in_occupied_cell=False):
    """
    Flood fill is an algorithm that expands from a starting position into adjacent
    vacant cells. Returns the set of all vacant cells found.

    If allow_start_in_occupied_cell is True, the flood fill start position may be occupied
    and the start position will be included in the resulting set.
    """
    visited = set()

    if not allow_start_in_occupied_cell and not board.vacant(start_pos):
        return visited

    visited.add(start_pos)
    todo = deque([start_pos])

    while todo:
        current = todo.popleft()
        for p in neighbours(current):
            if p not in visited and board.vacant(p):
                visited.add(p)
                todo.append(p)

    return visited


def _touching_flood(flood, pos):
    for point in flood:
        if touching(pos, point):
            return True
    return False


def find_safest_positions(snake, board, bad_positions):
    # account for bad_positions
    temp_board = Board(clone=board)
    for pos in bad_positions:
        temp_board.set_cell(pos, SNAKE)

    # Setup bounds and modulous
    bounds = [(1, 1), (board.width-2, board.height-2)]
    skip_cell_modulous = 1 if (board.width*board.height) <= ENABLE_CHECKERBOARD_SIZE else 2
    checkerboard_count = 0

    # Create a checkerboard of positions to check
    potential_cells = []
    for x in range(bounds[0][0], bounds[1][0]+1):
        for y in range(bounds[0][1], bounds[1][1]+1):
            if board.get_cell((x, y)) in [SNAKE, FOOD, SPOILED]:
                continue
            if (x, y) in bad_positions:
                continue

            flood = flood_fill(temp_board, (x, y))
            if len(flood) <= snake.attributes['length'] * SAFE_SPACE_FACTOR and not _touching_flood(flood, snake.head):
                continue

            checkerboard_count += 1
            if (checkerboard_count % skip_cell_modulous) != 0:
                continue
            potential_cells.append(((x, y), rate_cell((x, y), temp_board)))
        checkerboard_count += 1

    results = sorted(potential_cells, key=lambda x: x[1], reverse=True)
    return results[:5]


def rate_food(current_position, board, board_food):
    """ finds and rates food positions """
    rated_food = [(food, rate_cell(food, board)) for food in board_food]
    return sorted(rated_food, key=lambda x: x[1], reverse=True)


def bfs(starting_position, target_position, board, exclude, return_list, include_start=False):
    def _find_paths(starting_position, target_position, board, return_list, include_start):
        def _get_path_from_nodes(node, include_start):
            path = []
            while(node):
                path.insert(0, (node[0], node[1]))
                node = node[2]
            if not include_start:
                path = path[1:]
            return_list.append(path)
            return True

        queue = deque([(starting_position[0], starting_position[1], None)])
        while len(queue) > 0:
            node = queue.popleft()
            x = node[0]
            y = node[1]

            if (x, y) == target_position:  # If we reach target_position
                return _get_path_from_nodes(node, include_start)  # Rebuild path

            if board.get_cell((x, y)) == SNAKE and not (x, y) == starting_position:
                continue

            board.set_cell((x, y), SNAKE)  # Mark as explored

            for i in neighbours(node):
                if board.inside((i[0], i[1])):
                    queue.append((i[0], i[1], node))

        return False  # No path

    found_path = False
    board_copy = Board(clone=board)

    for point in exclude:
        board_copy.set_cell(point, SNAKE)

    # We want to avoid going along the wall if possible. Make new board that excludes the outside
    small_board = Board(clone=board_copy)
    small_board.height = small_board.height - 1
    small_board.width = small_board.width - 1
    small_board.start_index = 1

    if not next_to_wall(starting_position, board_copy) and not next_to_wall(target_position, board_copy):
        found_path = _find_paths(starting_position, target_position, small_board, return_list, include_start)

    if not found_path:
        _find_paths(starting_position, target_position, board_copy, return_list, include_start)
    return


def longest_path(starting_position, target_position, board, exclude):
    """ Gets the longest path between two points - can be very slow if given a large enough area (NP hard problem)"""
    def _create_path(start, end, board, path):
        if start == end:
            return (path[1:], len(path))

        highest = ([], 0)
        for point in neighbours(start):
            if point in path or board.outside(point) or board.get_cell(point) == SNAKE:
                continue

            path.append(point)
            value = _create_path(point, end, board, path)
            path.remove(point)

            if value and value[1] > highest[1]:
                highest = value

        return highest

    board_copy = Board(clone=board)
    board_copy.set_cell(starting_position, EMPTY)

    for excluded_point in exclude:
        board_copy.set_cell(excluded_point, SNAKE)

    return _create_path(starting_position, target_position, board_copy, [starting_position])[0]
