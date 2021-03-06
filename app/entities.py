from .utils import sub, add, dist
from .constants import DIR_VECTORS, EMPTY, FOOD, SNAKE, SPOILED

from copy import deepcopy


class Snake(object):
    ATTRIBUTES = ('id', 'health', 'length')

    def __init__(self, **kwargs):
        # Create a snake from a battlesnake snake dict
        self.attributes = {k: kwargs[k] for k in Snake.ATTRIBUTES}
        self.coords = [(p['x'], p['y']) for p in kwargs['body']['data']]

        # remove tail from snakes that are > 2 long
        if len(self.coords) > 2:
            self.coords = self.coords[:-1]

    def __len__(self):
        return self.attributes['length']

    def _get_direction(self):
        assert len(self.coords) > 1
        return sub(self.coords[0], self.coords[1])
    direction = property(_get_direction)

    def _get_head(self):
        return self.coords[0]
    head = property(_get_head)

    def _get_tail(self):
        return self.coords[-1]
    tail = property(_get_tail)

    def _get_body(self):
        return self.coords[1:]
    body = property(_get_body)

    def potential_positions(self):
        return [add(self.head, d) for d in DIR_VECTORS if d != sub((0, 0), self.direction)]

    def closest_food(self, food):
        if not food:
            return None

        closest = (food[0], dist(food[0], self.head))
        for fud in food:
            distance = dist(fud, self.head)
            if distance < closest[1]:
                closest = (fud, distance)

        return closest


class Board(object):
    """
    Basically a 2d grid of cells represented by integers.
    A zero cell is unoccupied. 1 is snake. 2 is food.
    """

    def __init__(self, **kwargs):
        # Initialize a board from a battlesnake gamestate dict
        self.width = kwargs['width']
        self.height = kwargs['height']
        self.start_index = 0
        self.cells = []
        self.meta_cells = []
        self.own_snake_id = kwargs['you']['id']

        for x in range(self.width):
            self.cells.append([EMPTY] * self.height)
            self.meta_cells.append([None] * self.height)

        # Only take snakes that are alive
        self.snakes = [Snake(**s) for s in kwargs['snakes']['data']]
        self.enemies = [deepcopy(s) for s in self.snakes if s.attributes['id'] != self.own_snake_id]
        self.food = [(p['x'], p['y']) for p in kwargs['food']['data']]

        # Fill out initially occupied cells on board
        for snake in self.snakes:
            for pos in snake.coords:
                self.set_cell(pos, SNAKE)

        for fud in self.food:
            if self._contested_food(fud, kwargs['you']['id']):
                self.set_cell(fud, FOOD)
            else:
                self.set_cell(fud, SPOILED)

    def _contested_food(self, pos, snake_id):
        current_snake = self.snakes[0]

        for snake in self.snakes:
            if ((dist(snake.head, pos) < dist(current_snake.head, pos)) or
                    ((dist(snake.head, pos) == dist(current_snake.head, pos)) and (len(snake.coords) >= len(current_snake.coords)))):
                current_snake = snake

        return (current_snake.attributes['id'] == snake_id)

    def get_snake(self, snake_id):
        try:
            return next(s for s in self.snakes if s.attributes['id'] == snake_id)
        except StopIteration:
            return None

    def set_cell(self, pos, value, meta=None):
        self.cells[pos[0]][pos[1]] = value
        self.meta_cells[pos[0]][pos[1]] = meta

    def get_cell(self, pos):
        return self.cells[pos[0]][pos[1]]

    def set_cell_meta(self, pos, meta):
        self.meta_cells[pos[0]][pos[1]] = meta

    def get_cell_meta(self, pos):
        return self.meta_cells[pos[0]][pos[1]]

    def outside(self, pos):
        return pos[0] < self.start_index or pos[0] >= self.width or pos[1] < self.start_index or pos[1] >= self.height

    def inside(self, pos):
        return not self.outside(pos)

    def vacant(self, pos):
        # Inlined for performance:
        return self.inside(pos) and self.cells[pos[0]][pos[1]] != SNAKE

    def has_snake(self, pos):
        return (self.cells[pos[0]][pos[1]] == SNAKE)

    def has_food(self, pos):
        return (self.cells[pos[0]][pos[1]] == FOOD or self.cells[pos[0]][pos[1]] == SPOILED)

    def __str__(self):
        return self.format(lambda v: ' ' if v == 0 else '{:d}'.format(v))

    def format_meta(self):
        s = []

        for y in range(self.height):
            s.append('|')
            for x in range(self.width):
                v = str(self.meta_cells[x][y])
                s.append(v)
            s.append('|\n')

        bar = '-' * (len(self.meta_cells) * len(v) + 2) + '\n'
        s.insert(0, bar)
        s.append(bar)
        return '\t'.join(s)

    def format(self):
        s = []

        for y in range(self.height):
            s.append('|')
            for x in range(self.width):
                v = str(self.cells[x][y])
                s.append(v)
            s.append('|\n')

        bar = '-' * (len(self.cells) * len(v) + 2) + '\n'
        s.insert(0, bar)
        s.append(bar)
        return ' '.join(s)
