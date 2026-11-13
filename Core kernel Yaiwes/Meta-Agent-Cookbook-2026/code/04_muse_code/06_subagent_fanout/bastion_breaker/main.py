"""Bastion Breaker — playable entry point.

Controls: <- / -> move, SPACE shoot, ESC quit.
Run headless (no window) for CI/screenshots with SDL_VIDEODRIVER=dummy.
"""
import sys
import pygame

from game import config as C
from game import engine
from game.render import draw


def main():
    pygame.init()
    screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT))
    pygame.display.set_caption(C.TITLE)
    font = pygame.font.SysFont("monospace", 24, bold=True)
    clock = pygame.time.Clock()

    s = engine.new_game()
    running = True
    while running:
        dt = clock.tick(C.FPS) / 1000.0
        shoot = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    shoot = True

        keys = pygame.key.get_pressed()
        move = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT])
        engine.step(s, dt, move=move, shoot=shoot)

        draw(screen, s, font)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
