"""Render a scripted headless run to PNG frames — used for docs/screenshots.

Usage: SDL_VIDEODRIVER=dummy python3 tools/render_frames.py OUTDIR
Drives a deterministic scenario: an enemy fires straight down at a solid brick
column, so the frames show whether the bastion survives the enemy's own fire.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
from game import config as C
from game import engine
from game.entities import Laser
from game.render import draw


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT))
    font = pygame.font.SysFont("monospace", 24, bold=True)

    s = engine.new_game(seed=7)
    # Aim an enemy laser straight down at a solid brick column (col 4).
    bx = C.WALL_LEFT + 4 * C.BRICK_W + C.BRICK_W / 2 - C.LASER_W / 2
    s.lasers.append(Laser(x=bx, y=C.ENEMY_Y + C.ENEMY_H,
                          w=C.LASER_W, h=C.LASER_H,
                          vy=C.ENEMY_LASER_SPEED, owner="enemy"))
    bricks_before = sum(b.alive for b in s.bricks)

    frame = 0
    for i in range(90):
        engine.step(s, 1 / 60.0, move=0, shoot=False)
        if i in (0, 20, 45, 89):
            draw(screen, s, font)
            pygame.image.save(screen, os.path.join(outdir, f"frame_{frame:02d}.png"))
            frame += 1

    bricks_after = sum(b.alive for b in s.bricks)
    print(f"bricks_before={bricks_before} bricks_after={bricks_after} "
          f"destroyed_by_enemy={bricks_before - bricks_after}")
    pygame.quit()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/bb_frames")
