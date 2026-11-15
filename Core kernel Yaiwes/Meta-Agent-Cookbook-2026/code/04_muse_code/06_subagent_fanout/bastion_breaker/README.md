# Bastion Breaker

A brick-out × space-invaders hybrid. Enemy ships fly along the top and shoot
down through the openings in a brick "bastion"; the player flies along the
bottom and shoots up. The player's cannon breaks one brick per hit. The enemies
hide *behind* the bastion and must not break it.

## Run
```bash
pip install -r requirements.txt
python3 main.py                 # windowed
```

## Controls
`←` / `→` move · `SPACE` shoot · `ESC` quit

## Test (headless, no window)
```bash
SDL_VIDEODRIVER=dummy python3 -m pytest tests/ -q
```

## Layout
- `game/engine.py` — pure simulation (no pygame); the world rules live here.
- `game/render.py` — pygame drawing + input.
- `game/entities.py`, `game/config.py` — data + tunables.
- `tests/test_rules.py` — objective oracle for the world rules.

## Assets
Sprites are CC0. Ship + lasers from Kenney *Space Shooter Redux/Remastered*;
bricks from Kenney *Puzzle Pack 2*. See `assets/`.
