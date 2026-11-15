"""Bastion Breaker — central config. No pygame import here so tests stay cheap."""

# --- window ---
WIDTH = 960
HEIGHT = 720
FPS = 60
TITLE = "Bastion Breaker"

# --- brick wall (the bastion the enemies hide behind) ---
BRICK_W = 64
BRICK_H = 32
WALL_COLS = 13          # 13 * 64 = 832, centered in 960
WALL_ROWS = 4
WALL_TOP = 240          # y of the first brick row
WALL_LEFT = (WIDTH - WALL_COLS * BRICK_W) // 2
# Column indices that are left open so shots can pass through.
WALL_OPENINGS = (2, 6, 10)

# --- player (bottom, moves horizontally, shoots up) ---
PLAYER_W = 66
PLAYER_H = 50
PLAYER_Y = HEIGHT - 90
PLAYER_SPEED = 420.0    # px/sec
PLAYER_COOLDOWN = 0.28  # sec between shots

# --- enemies (top, fly horizontally, shoot down through openings) ---
ENEMY_W = 62
ENEMY_H = 56
ENEMY_Y = 120
ENEMY_SPEED = 150.0
ENEMY_COOLDOWN = 1.1
ENEMY_COUNT = 3

# --- lasers ---
LASER_W = 9
LASER_H = 36
PLAYER_LASER_SPEED = -640.0   # up
ENEMY_LASER_SPEED = 360.0     # down

# --- scoring ---
POINTS_PER_BRICK = 10
POINTS_PER_ENEMY = 100
