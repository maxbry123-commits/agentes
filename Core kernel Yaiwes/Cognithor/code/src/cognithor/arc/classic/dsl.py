"""DSL grid transformation primitives for ARC-AGI-3.

All functions are pure: (Grid, *params) -> Grid.
Grid = list[list[int]], values 0-9.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

__all__ = [
    "count_by_color",
    "crop_to_content",
    "fill",
    "flip_h",
    "flip_v",
    "get_bounding_box",
    "get_by_color",
    "get_largest_object",
    "get_objects",
    "gravity",
    "invert_colors",
    "mask_where",
    "overlay",
    "pad",
    "recolor",
    "replace_background",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "scale_up",
    "stack_h",
    "stack_v",
    "swap_colors",
    "tile",
    "transpose",
]

Grid = list[list[int]]


# ---------------------------------------------------------------------------
# Geometry (6)
# ---------------------------------------------------------------------------


def rotate_90(grid: Grid) -> Grid:
    """Rotate grid 90 degrees clockwise."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    return [[grid[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]


def rotate_180(grid: Grid) -> Grid:
    """Rotate grid 180 degrees."""
    return [row[::-1] for row in grid[::-1]]


def rotate_270(grid: Grid) -> Grid:
    """Rotate grid 270 degrees clockwise (90 degrees counter-clockwise)."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    return [[grid[j][cols - 1 - i] for j in range(rows)] for i in range(cols)]


def flip_h(grid: Grid) -> Grid:
    """Flip grid horizontally (mirror left-right)."""
    return [row[::-1] for row in grid]


def flip_v(grid: Grid) -> Grid:
    """Flip grid vertically (mirror top-bottom)."""
    return grid[::-1]


def transpose(grid: Grid) -> Grid:
    """Transpose grid (swap rows and columns)."""
    return [list(col) for col in zip(*grid, strict=False)]


# ---------------------------------------------------------------------------
# Color (5)
# ---------------------------------------------------------------------------


def recolor(grid: Grid, from_color: int, to_color: int) -> Grid:
    """Replace all occurrences of from_color with to_color."""
    return [[to_color if cell == from_color else cell for cell in row] for row in grid]


def fill(grid: Grid, color: int) -> Grid:
    """Fill entire grid with a single color."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    return [[color] * cols for _ in range(rows)]


def swap_colors(grid: Grid, a: int, b: int) -> Grid:
    """Swap two colors throughout the grid."""

    def _swap(cell: int) -> int:
        if cell == a:
            return b
        if cell == b:
            return a
        return cell

    return [[_swap(cell) for cell in row] for row in grid]


def replace_background(grid: Grid, new_bg: int) -> Grid:
    """Replace the most common color (background) with new_bg."""
    counts: Counter[int] = Counter(cell for row in grid for cell in row)
    if not counts:
        return grid
    bg = counts.most_common(1)[0][0]
    return recolor(grid, bg, new_bg)


def invert_colors(grid: Grid) -> Grid:
    """Invert each cell: new_value = 9 - old_value."""
    return [[9 - cell for cell in row] for row in grid]


# ---------------------------------------------------------------------------
# Shape (4)
# ---------------------------------------------------------------------------


def crop_to_content(grid: Grid, background: int = 0) -> Grid:
    """Remove rows and columns that consist entirely of background color."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    min_r, max_r, min_c, max_c = rows, -1, cols, -1
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != background:
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c

    if max_r == -1:
        # All background — return empty
        return [[]]

    return [row[min_c : max_c + 1] for row in grid[min_r : max_r + 1]]


def pad(grid: Grid, n: int, color: int = 0) -> Grid:
    """Add an n-cell border of color around the grid."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    new_cols = cols + 2 * n
    top_bottom = [[color] * new_cols for _ in range(n)]
    middle = [[color] * n + list(row) + [color] * n for row in grid]
    return top_bottom + middle + top_bottom


def tile(grid: Grid, nx: int, ny: int) -> Grid:
    """Repeat grid nx times horizontally and ny times vertically."""
    tiled_rows = [row * nx for row in grid]
    return tiled_rows * ny


def scale_up(grid: Grid, factor: int) -> Grid:
    """Scale each cell into a factor x factor block."""
    result = []
    for row in grid:
        scaled_row = []
        for cell in row:
            scaled_row.extend([cell] * factor)
        result.extend([scaled_row[:] for _ in range(factor)])
    return result


# ---------------------------------------------------------------------------
# Extraction (5)
# ---------------------------------------------------------------------------


def _flood_fill(
    grid: Grid,
    visited: list[list[bool]],
    r: int,
    c: int,
    color: int,
) -> list[tuple[int, int]]:
    """Iterative flood-fill returning all (r, c) cells in the component."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    stack = [(r, c)]
    component: list[tuple[int, int]] = []
    while stack:
        cr, cc = stack.pop()
        if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
            continue
        if visited[cr][cc]:
            continue
        if grid[cr][cc] != color:
            continue
        visited[cr][cc] = True
        component.append((cr, cc))
        stack.extend([(cr + 1, cc), (cr - 1, cc), (cr, cc + 1), (cr, cc - 1)])
    return component


def get_objects(grid: Grid, background: int = 0) -> list[Grid]:
    """Return connected components (4-connected) as separate grids.

    Each returned grid is the same size as the input, with only the
    cells of that component filled in (background elsewhere).
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    visited = [[False] * cols for _ in range(rows)]
    objects: list[Grid] = []

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            if cell != background and not visited[r][c]:
                component = _flood_fill(grid, visited, r, c, cell)
                obj: Grid = [[background] * cols for _ in range(rows)]
                for cr, cc in component:
                    obj[cr][cc] = grid[cr][cc]
                objects.append(obj)

    return objects


def get_largest_object(grid: Grid, background: int = 0) -> Grid:
    """Return the largest connected component as a grid."""
    objects = get_objects(grid, background)
    if not objects:
        return grid
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    def _size(obj: Grid) -> int:
        return sum(1 for r in range(rows) for c in range(cols) if obj[r][c] != background)

    return max(objects, key=_size)


def get_by_color(grid: Grid, color: int) -> Grid:
    """Return a grid with only the specified color; all other cells become 0."""
    return [[cell if cell == color else 0 for cell in row] for row in grid]


def count_by_color(grid: Grid) -> dict[int, int]:
    """Return a dict mapping each color to its count in the grid."""
    counts: Counter[int] = Counter(cell for row in grid for cell in row)
    return dict(counts)


def get_bounding_box(grid: Grid, color: int) -> Grid:
    """Crop grid to the bounding box of all cells with the given color."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    min_r, max_r, min_c, max_c = rows, -1, cols, -1
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == color:
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c
    if max_r == -1:
        return [[]]
    return [row[min_c : max_c + 1] for row in grid[min_r : max_r + 1]]


# ---------------------------------------------------------------------------
# Composition (5)
# ---------------------------------------------------------------------------


def overlay(base: Grid, top: Grid, transparent: int = 0) -> Grid:
    """Overlay top onto base; transparent cells in top reveal base."""
    rows = len(base)
    cols = len(base[0]) if rows else 0
    result = []
    for r in range(rows):
        row = []
        for c in range(cols):
            t = top[r][c] if r < len(top) and c < len(top[r]) else transparent
            row.append(base[r][c] if t == transparent else t)
        result.append(row)
    return result


def stack_h(a: Grid, b: Grid) -> Grid:
    """Concatenate two grids horizontally (side by side)."""
    return [list(ra) + list(rb) for ra, rb in zip(a, b, strict=False)]


def stack_v(a: Grid, b: Grid) -> Grid:
    """Concatenate two grids vertically (one on top of the other)."""
    return [list(row) for row in a] + [list(row) for row in b]


def mask_where(grid: Grid, color: int) -> Grid:
    """Alias for get_by_color: keep only the given color, rest becomes 0."""
    return get_by_color(grid, color)


def gravity(
    grid: Grid,
    direction: Literal["down", "up", "left", "right"] = "down",
) -> Grid:
    """Simulate gravity: slide non-zero cells in the given direction."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0

    def _apply_gravity_to_line(line: list[int], reverse: bool) -> list[int]:
        """Push all non-zero values to one end, filling the other with zeros."""
        non_zero = [v for v in line if v != 0]
        zeros = [0] * (len(line) - len(non_zero))
        if reverse:
            return non_zero + zeros
        return zeros + non_zero

    if direction == "down":
        # Process each column; non-zero cells fall to the bottom
        result = [[0] * cols for _ in range(rows)]
        for c in range(cols):
            col = [grid[r][c] for r in range(rows)]
            new_col = _apply_gravity_to_line(col, reverse=False)
            for r in range(rows):
                result[r][c] = new_col[r]
        return result

    if direction == "up":
        result = [[0] * cols for _ in range(rows)]
        for c in range(cols):
            col = [grid[r][c] for r in range(rows)]
            new_col = _apply_gravity_to_line(col, reverse=True)
            for r in range(rows):
                result[r][c] = new_col[r]
        return result

    if direction == "right":
        return [_apply_gravity_to_line(list(row), reverse=False) for row in grid]

    # direction == "left"
    return [_apply_gravity_to_line(list(row), reverse=True) for row in grid]
