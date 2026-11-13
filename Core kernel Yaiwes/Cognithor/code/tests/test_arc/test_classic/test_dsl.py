"""Tests for the ARC DSL grid transformation primitives."""

from __future__ import annotations

from cognithor.arc.classic.dsl import (
    count_by_color,
    crop_to_content,
    fill,
    flip_h,
    flip_v,
    get_bounding_box,
    get_by_color,
    get_largest_object,
    get_objects,
    gravity,
    invert_colors,
    mask_where,
    overlay,
    pad,
    recolor,
    replace_background,
    rotate_90,
    rotate_180,
    rotate_270,
    scale_up,
    stack_h,
    stack_v,
    swap_colors,
    tile,
    transpose,
)

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def test_rotate_90_square():
    grid = [
        [1, 2],
        [3, 4],
    ]
    # 90 CW: top-left -> top-right, bottom-left -> top-left
    # col 0 becomes row 0 (reversed): [3,1]
    # col 1 becomes row 1 (reversed): [4,2]
    assert rotate_90(grid) == [[3, 1], [4, 2]]


def test_rotate_90_rectangle():
    grid = [
        [1, 2, 3],
        [4, 5, 6],
    ]
    # 2 rows, 3 cols -> 3 rows, 2 cols
    expected = [
        [4, 1],
        [5, 2],
        [6, 3],
    ]
    assert rotate_90(grid) == expected


def test_rotate_180():
    grid = [
        [1, 2],
        [3, 4],
    ]
    assert rotate_180(grid) == [[4, 3], [2, 1]]


def test_rotate_270():
    grid = [
        [1, 2],
        [3, 4],
    ]
    # 270 CW = 90 CCW
    assert rotate_270(grid) == [[2, 4], [1, 3]]


def test_rotate_90_then_270_is_identity():
    grid = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    assert rotate_270(rotate_90(grid)) == grid


def test_flip_h():
    grid = [
        [1, 2, 3],
        [4, 5, 6],
    ]
    assert flip_h(grid) == [[3, 2, 1], [6, 5, 4]]


def test_flip_v():
    grid = [
        [1, 2],
        [3, 4],
        [5, 6],
    ]
    assert flip_v(grid) == [[5, 6], [3, 4], [1, 2]]


def test_transpose():
    grid = [
        [1, 2, 3],
        [4, 5, 6],
    ]
    assert transpose(grid) == [[1, 4], [2, 5], [3, 6]]


def test_transpose_square():
    grid = [[1, 2], [3, 4]]
    assert transpose(grid) == [[1, 3], [2, 4]]


# ---------------------------------------------------------------------------
# Color
# ---------------------------------------------------------------------------


def test_recolor():
    grid = [[1, 2], [2, 3]]
    assert recolor(grid, 2, 5) == [[1, 5], [5, 3]]


def test_recolor_no_match():
    grid = [[1, 2], [3, 4]]
    assert recolor(grid, 9, 0) == [[1, 2], [3, 4]]


def test_fill():
    grid = [[1, 2], [3, 4]]
    assert fill(grid, 7) == [[7, 7], [7, 7]]


def test_swap_colors():
    grid = [[1, 2, 1], [2, 3, 2]]
    assert swap_colors(grid, 1, 2) == [[2, 1, 2], [1, 3, 1]]


def test_swap_colors_with_third_color_unchanged():
    grid = [[1, 3, 2]]
    assert swap_colors(grid, 1, 2) == [[2, 3, 1]]


def test_replace_background():
    # 0 is most common -> replace with 9
    grid = [[0, 0, 1], [0, 2, 0]]
    result = replace_background(grid, 9)
    assert result == [[9, 9, 1], [9, 2, 9]]


def test_invert_colors():
    grid = [[0, 9], [3, 6]]
    assert invert_colors(grid) == [[9, 0], [6, 3]]


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


def test_crop_to_content():
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    assert crop_to_content(grid) == [[1]]


def test_crop_to_content_multi():
    grid = [
        [0, 0, 0, 0],
        [0, 1, 2, 0],
        [0, 3, 4, 0],
        [0, 0, 0, 0],
    ]
    assert crop_to_content(grid) == [[1, 2], [3, 4]]


def test_crop_to_content_no_background():
    grid = [[1, 2], [3, 4]]
    assert crop_to_content(grid) == [[1, 2], [3, 4]]


def test_pad():
    grid = [[1, 2], [3, 4]]
    result = pad(grid, 1, 0)
    assert result == [
        [0, 0, 0, 0],
        [0, 1, 2, 0],
        [0, 3, 4, 0],
        [0, 0, 0, 0],
    ]


def test_pad_custom_color():
    grid = [[5]]
    result = pad(grid, 1, 9)
    assert result == [
        [9, 9, 9],
        [9, 5, 9],
        [9, 9, 9],
    ]


def test_tile():
    grid = [[1, 2], [3, 4]]
    result = tile(grid, 2, 2)
    assert result == [
        [1, 2, 1, 2],
        [3, 4, 3, 4],
        [1, 2, 1, 2],
        [3, 4, 3, 4],
    ]


def test_tile_horizontal_only():
    grid = [[1, 2]]
    assert tile(grid, 3, 1) == [[1, 2, 1, 2, 1, 2]]


def test_scale_up():
    grid = [[1, 2], [3, 4]]
    result = scale_up(grid, 2)
    assert result == [
        [1, 1, 2, 2],
        [1, 1, 2, 2],
        [3, 3, 4, 4],
        [3, 3, 4, 4],
    ]


def test_scale_up_factor_1_is_identity():
    grid = [[1, 2], [3, 4]]
    assert scale_up(grid, 1) == grid


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def test_get_by_color():
    grid = [[1, 2, 1], [3, 1, 2]]
    result = get_by_color(grid, 1)
    assert result == [[1, 0, 1], [0, 1, 0]]


def test_get_by_color_not_present():
    grid = [[1, 2], [3, 4]]
    assert get_by_color(grid, 9) == [[0, 0], [0, 0]]


def test_count_by_color():
    grid = [[1, 2, 1], [2, 3, 2]]
    counts = count_by_color(grid)
    assert counts[1] == 2
    assert counts[2] == 3
    assert counts[3] == 1


def test_get_bounding_box():
    grid = [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
    ]
    result = get_bounding_box(grid, 1)
    assert result == [[1, 1], [1, 0]]


def test_get_objects_returns_two():
    # Two separate blobs of color 1
    grid = [
        [1, 0, 1],
        [0, 0, 0],
        [0, 0, 0],
    ]
    objects = get_objects(grid, background=0)
    assert len(objects) == 2
    # Each object has exactly one non-zero cell
    assert sum(cell for row in objects[0] for cell in row) == 1
    assert sum(cell for row in objects[1] for cell in row) == 1


def test_get_objects_single_blob():
    grid = [
        [0, 1, 0],
        [1, 1, 0],
        [0, 0, 0],
    ]
    objects = get_objects(grid, background=0)
    assert len(objects) == 1


def test_get_objects_empty():
    grid = [[0, 0], [0, 0]]
    objects = get_objects(grid, background=0)
    assert objects == []


def test_get_largest_object():
    # Two objects: one 1-cell, one 3-cell
    grid = [
        [1, 0, 2],
        [0, 0, 2],
        [0, 0, 2],
    ]
    largest = get_largest_object(grid, background=0)
    # The largest object should have the 3 cells of color 2
    non_zero = [(r, c) for r in range(3) for c in range(3) if largest[r][c] != 0]
    assert len(non_zero) == 3


def test_mask_where_alias():
    grid = [[1, 2, 1], [3, 1, 2]]
    assert mask_where(grid, 1) == get_by_color(grid, 1)


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


def test_overlay():
    base = [[1, 1], [1, 1]]
    top = [[0, 2], [3, 0]]
    # 0 is transparent in top
    result = overlay(base, top, transparent=0)
    assert result == [[1, 2], [3, 1]]


def test_overlay_fully_opaque():
    base = [[1, 1], [1, 1]]
    top = [[5, 6], [7, 8]]
    assert overlay(base, top) == [[5, 6], [7, 8]]


def test_stack_h():
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    assert stack_h(a, b) == [[1, 2, 5, 6], [3, 4, 7, 8]]


def test_stack_v():
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    assert stack_v(a, b) == [[1, 2], [3, 4], [5, 6], [7, 8]]


def test_gravity_down():
    grid = [
        [1, 0],
        [0, 2],
        [0, 0],
    ]
    result = gravity(grid, "down")
    assert result == [
        [0, 0],
        [0, 0],
        [1, 2],
    ]


def test_gravity_up():
    grid = [
        [0, 0],
        [0, 2],
        [1, 0],
    ]
    result = gravity(grid, "up")
    assert result == [
        [1, 2],
        [0, 0],
        [0, 0],
    ]


def test_gravity_left():
    grid = [[0, 1, 0, 2]]
    result = gravity(grid, "left")
    assert result == [[1, 2, 0, 0]]


def test_gravity_right():
    grid = [[1, 0, 2, 0]]
    result = gravity(grid, "right")
    assert result == [[0, 0, 1, 2]]


def test_gravity_all_zeros():
    grid = [[0, 0], [0, 0]]
    assert gravity(grid, "down") == [[0, 0], [0, 0]]
