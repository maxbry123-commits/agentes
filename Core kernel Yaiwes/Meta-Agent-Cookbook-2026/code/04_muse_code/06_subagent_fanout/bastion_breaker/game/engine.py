"""Bastion Breaker simulation — pure logic, no pygame, fully unit-testable.

World layout:
    - A brick wall (the "bastion") sits across the middle, with a few open
      columns so shots can pass through.
    - Enemy ships fly horizontally along the TOP and shoot DOWN.
    - The player flies horizontally along the BOTTOM and shoots UP.

Rules of the world:
    - The PLAYER's shot breaks exactly ONE brick per hit (or kills an enemy).
    - The ENEMY's shot must pass over the wall and can hit the player, but it
      must NOT destroy bricks — the enemies hide behind their own bastion.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

from . import config as C
from .entities import Brick, Player, Enemy, Laser, aabb


@dataclass
class GameState:
    bricks: List[Brick] = field(default_factory=list)
    player: Player = None
    enemies: List[Enemy] = field(default_factory=list)
    lasers: List[Laser] = field(default_factory=list)
    score: int = 0
    lives: int = 3
    over: bool = False
    _rng: random.Random = field(default_factory=lambda: random.Random(1234))


def new_game(seed: int = 1234) -> GameState:
    s = GameState(_rng=random.Random(seed))
    # Build the bastion wall with a few open columns.
    for row in range(C.WALL_ROWS):
        for col in range(C.WALL_COLS):
            if col in C.WALL_OPENINGS:
                continue
            x = C.WALL_LEFT + col * C.BRICK_W
            y = C.WALL_TOP + row * C.BRICK_H
            s.bricks.append(Brick(col, row, x, y, C.BRICK_W, C.BRICK_H))
    # Player centered at the bottom.
    s.player = Player(
        x=(C.WIDTH - C.PLAYER_W) / 2, y=C.PLAYER_Y, w=C.PLAYER_W, h=C.PLAYER_H
    )
    # Enemies spread across the top, alternating initial direction.
    gap = C.WIDTH / (C.ENEMY_COUNT + 1)
    for i in range(C.ENEMY_COUNT):
        vx = C.ENEMY_SPEED if i % 2 == 0 else -C.ENEMY_SPEED
        s.enemies.append(
            Enemy(x=gap * (i + 1) - C.ENEMY_W / 2, y=C.ENEMY_Y,
                  w=C.ENEMY_W, h=C.ENEMY_H, vx=vx)
        )
    return s


def player_shoot(s: GameState):
    if s.player.cooldown > 0 or s.over:
        return
    s.player.cooldown = C.PLAYER_COOLDOWN
    s.lasers.append(Laser(
        x=s.player.x + s.player.w / 2 - C.LASER_W / 2,
        y=s.player.y - C.LASER_H,
        w=C.LASER_W, h=C.LASER_H, vy=C.PLAYER_LASER_SPEED, owner="player",
    ))


def _enemy_shoot(s: GameState, e: Enemy):
    e.cooldown = C.ENEMY_COOLDOWN
    s.lasers.append(Laser(
        x=e.x + e.w / 2 - C.LASER_W / 2,
        y=e.y + e.h,
        w=C.LASER_W, h=C.LASER_H, vy=C.ENEMY_LASER_SPEED, owner="enemy",
    ))


def step(s: GameState, dt: float, move: int = 0, shoot: bool = False):
    """Advance the world by dt seconds.

    move:  -1 left, +1 right, 0 none (player input)
    shoot: fire the player cannon this step if off cooldown
    """
    if s.over:
        return

    # --- player ---
    s.player.cooldown = max(0.0, s.player.cooldown - dt)
    s.player.x += move * C.PLAYER_SPEED * dt
    s.player.x = max(0, min(C.WIDTH - s.player.w, s.player.x))
    if shoot:
        player_shoot(s)

    # --- enemies: bounce along the top, shoot down on cooldown ---
    for e in s.enemies:
        if not e.alive:
            continue
        e.cooldown = max(0.0, e.cooldown - dt)
        e.x += e.vx * dt
        if e.x <= 0:
            e.x = 0
            e.vx = abs(e.vx)
        elif e.x >= C.WIDTH - e.w:
            e.x = C.WIDTH - e.w
            e.vx = -abs(e.vx)
        if e.cooldown <= 0 and s._rng.random() < 0.5:
            _enemy_shoot(s, e)

    # --- lasers ---
    for laser in s.lasers:
        if not laser.alive:
            continue
        laser.y += laser.vy * dt
        if laser.y + laser.h < 0 or laser.y > C.HEIGHT:
            laser.alive = False
            continue
        _resolve_laser(s, laser)

    # cull dead lasers
    s.lasers = [l for l in s.lasers if l.alive]

    if s.enemies and all(not e.alive for e in s.enemies):
        s.over = True


def _resolve_laser(s: GameState, laser: Laser):
    # Brick collisions.
    for b in s.bricks:
        if not b.alive:
            continue
        if aabb(laser.rect, b.rect):
            # BUG (planted): the enemy laser destroys the brick too. The world
            # rules say only the PLAYER may break bricks; enemies hide behind
            # their bastion and must not chew through it.
            b.alive = False
            laser.alive = False
            if laser.owner == "player":
                s.score += C.POINTS_PER_BRICK
            return

    if laser.owner == "player":
        for e in s.enemies:
            if e.alive and aabb(laser.rect, e.rect):
                e.alive = False
                laser.alive = False
                s.score += C.POINTS_PER_ENEMY
                return
    else:  # enemy laser can hit the player
        if aabb(laser.rect, s.player.rect):
            laser.alive = False
            s.lives -= 1
            if s.lives <= 0:
                s.over = True
            return
