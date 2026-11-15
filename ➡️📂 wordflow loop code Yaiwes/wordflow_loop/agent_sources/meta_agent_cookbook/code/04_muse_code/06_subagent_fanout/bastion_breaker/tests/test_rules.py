"""Objective oracle for Bastion Breaker's world rules.

Pure simulation — no video, no window. This is the ground truth a subagent's
bug fix or feature must satisfy. Each test isolates one mechanic: enemies are
cleared so their random fire cannot contaminate the outcome, and a single
laser under test is injected by hand.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import config as C
from game import engine
from game.entities import Laser


def _isolated_game():
    s = engine.new_game(seed=1)
    s.enemies = []          # no random enemy fire; we inject the shot under test
    s.lasers = []
    return s


def _col_center_x(col):
    return C.WALL_LEFT + col * C.BRICK_W + C.BRICK_W / 2 - C.LASER_W / 2


def _fire_enemy_laser_at_column(s, col):
    s.lasers.append(Laser(x=_col_center_x(col), y=C.ENEMY_Y + C.ENEMY_H,
                          w=C.LASER_W, h=C.LASER_H,
                          vy=C.ENEMY_LASER_SPEED, owner="enemy"))


def _fire_player_laser_at_column(s, col):
    y = C.WALL_TOP + C.WALL_ROWS * C.BRICK_H + 4   # just below the wall, going up
    s.lasers.append(Laser(x=_col_center_x(col), y=y, w=C.LASER_W, h=C.LASER_H,
                          vy=C.PLAYER_LASER_SPEED, owner="player"))


def test_player_shot_breaks_exactly_one_brick():
    s = _isolated_game()
    before = sum(b.alive for b in s.bricks)
    _fire_player_laser_at_column(s, 4)
    for _ in range(120):
        engine.step(s, 1 / 60.0)
    after = sum(b.alive for b in s.bricks)
    assert before - after == 1, f"player shot should break exactly one brick, broke {before - after}"


def test_enemy_shot_does_not_destroy_bricks():
    """World rule: enemies hide behind their bastion and must NOT break it."""
    s = _isolated_game()
    before = sum(b.alive for b in s.bricks)
    _fire_enemy_laser_at_column(s, 4)
    for _ in range(120):
        engine.step(s, 1 / 60.0)
    after = sum(b.alive for b in s.bricks)
    assert before == after, f"enemy fire destroyed {before - after} brick(s); it must destroy none"


def test_enemy_shot_through_opening_can_hit_player():
    s = _isolated_game()
    open_col = C.WALL_OPENINGS[0]
    s.player.x = _col_center_x(open_col) + C.LASER_W / 2 - s.player.w / 2
    _fire_enemy_laser_at_column(s, open_col)
    lives_before = s.lives
    for _ in range(240):
        engine.step(s, 1 / 60.0)
    assert s.lives == lives_before - 1, "enemy shot through an opening should cost the player exactly one life"
