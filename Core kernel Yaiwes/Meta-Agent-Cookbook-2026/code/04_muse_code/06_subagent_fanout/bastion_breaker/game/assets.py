"""Asset loading. Only imported by the rendering layer (needs a video surface)."""
import os
import pygame

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_A = os.path.join(_ROOT, "assets")
_cache = {}


def load(path: str, size=None):
    key = (path, size)
    if key in _cache:
        return _cache[key]
    img = pygame.image.load(os.path.join(_A, path)).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    _cache[key] = img
    return img
