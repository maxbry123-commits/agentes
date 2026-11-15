"""Plain data entities. Rects are (x, y, w, h) in world pixels."""
from dataclasses import dataclass, field


@dataclass
class Brick:
    col: int
    row: int
    x: float
    y: float
    w: float
    h: float
    alive: bool = True

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)


@dataclass
class Player:
    x: float
    y: float
    w: float
    h: float
    cooldown: float = 0.0

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)


@dataclass
class Enemy:
    x: float
    y: float
    w: float
    h: float
    vx: float
    cooldown: float = 0.0
    alive: bool = True

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)


@dataclass
class Laser:
    x: float
    y: float
    w: float
    h: float
    vy: float
    owner: str  # "player" or "enemy"
    alive: bool = True

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)


def aabb(a, b) -> bool:
    """Axis-aligned bounding-box overlap test."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
