"""Pygame rendering + input. Kept separate from engine so the sim stays testable."""
import pygame

from . import config as C
from .assets import load

_BRICK_IMG = "bricks/brick_blue.png"


def draw(screen, s, font):
    screen.fill((11, 14, 28))
    # bricks
    brick = load(_BRICK_IMG, (C.BRICK_W, C.BRICK_H))
    for b in s.bricks:
        if b.alive:
            screen.blit(brick, (b.x, b.y))
    # enemies
    enemy = load("ships/enemy.png", (C.ENEMY_W, C.ENEMY_H))
    for e in s.enemies:
        if e.alive:
            screen.blit(enemy, (e.x, e.y))
    # player
    player = load("ships/player.png", (C.PLAYER_W, C.PLAYER_H))
    screen.blit(player, (s.player.x, s.player.y))
    # lasers
    p_laser = load("lasers/player_laser.png", (C.LASER_W, C.LASER_H))
    e_laser = load("lasers/enemy_laser.png", (C.LASER_W, C.LASER_H))
    for l in s.lasers:
        screen.blit(p_laser if l.owner == "player" else e_laser, (l.x, l.y))
    # hud
    hud = font.render(f"SCORE {s.score}    LIVES {s.lives}", True, (230, 230, 245))
    screen.blit(hud, (16, 12))
    if s.over:
        msg = font.render("GAME OVER", True, (255, 90, 90))
        screen.blit(msg, (C.WIDTH // 2 - msg.get_width() // 2, C.HEIGHT // 2))
