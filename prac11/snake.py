"""
Snake – Practice 11, Task 2
Extends Practice 10 Snake with:
  1. Randomly generated food with different weights
     (common food worth 10 pts; rare food worth 50 pts)
  2. Food disappears after a set timer if not collected
  3. Full comments throughout
"""

import pygame
import random
import sys

# ── Constants ──────────────────────────────────────────────────────────────────
CELL   = 20
COLS   = 25
ROWS   = 25
WIDTH  = COLS * CELL
HEIGHT = ROWS * CELL + 50   # +50 px HUD strip
FPS    = 10

# Colours
BG_COLOR    = (15,  15,  15)
GRID_COLOR  = (30,  30,  30)
SNAKE_HEAD  = (50, 220,  80)
SNAKE_BODY  = (30, 160,  60)
WALL_COLOR  = (80,  80,  80)
HUD_BG      = (25,  25,  40)
TEXT_COLOR  = (230, 230, 230)
SCORE_COLOR = (100, 220, 255)
LEVEL_COLOR = (255, 200,  50)

# Directions
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

FOODS_PER_LEVEL = 3
MIN_FPS         = 25

# ── Weighted food table ────────────────────────────────────────────────────────
# (points, weight, color, lifetime_seconds)
# Higher weight → appears more often.
# Shorter lifetime → must be grabbed quickly.
FOOD_TYPES = [
    (10,  50, (220,  50,  50), 8.0),    # red    – very common, 8 s lifetime
    (20,  30, (255, 150,  30), 6.0),    # orange – common,      6 s
    (30,  15, (200,  80, 255), 5.0),    # purple – uncommon,    5 s
    (50,   5, (  0, 220, 255), 3.5),    # cyan   – rare,        3.5 s
]


def _pick_food_type():
    """
    Weighted random selection from FOOD_TYPES.
    Returns (points, color, lifetime) for the chosen food.
    """
    total  = sum(w for _, w, _, _ in FOOD_TYPES)
    roll   = random.randint(0, total - 1)
    cumul  = 0
    for pts, weight, color, lifetime in FOOD_TYPES:
        cumul += weight
        if roll < cumul:
            return pts, color, lifetime
    return FOOD_TYPES[0][0], FOOD_TYPES[0][2], FOOD_TYPES[0][3]   # fallback


# ── Grid helpers ───────────────────────────────────────────────────────────────
def cell_rect(col, row):
    return pygame.Rect(col * CELL, row * CELL + 50, CELL, CELL)


def random_free_cell(occupied: set) -> tuple[int, int]:
    while True:
        col = random.randint(1, COLS - 2)
        row = random.randint(1, ROWS - 2)
        if (col, row) not in occupied:
            return col, row


# ── Snake ──────────────────────────────────────────────────────────────────────
class Snake:
    """Snake body, direction, movement, and drawing."""

    def __init__(self):
        mid_col        = COLS // 2
        mid_row        = ROWS // 2
        self.body      = [(mid_col, mid_row),
                          (mid_col - 1, mid_row),
                          (mid_col - 2, mid_row)]
        self.direction = RIGHT
        self.grew      = False

    def set_direction(self, new_dir):
        opposite = (-new_dir[0], -new_dir[1])
        if new_dir != opposite or len(self.body) == 1:
            self.direction = new_dir

    def move(self):
        head     = self.body[0]
        new_head = (head[0] + self.direction[0],
                    head[1] + self.direction[1])
        self.body.insert(0, new_head)
        if self.grew:
            self.grew = False
        else:
            self.body.pop()

    def head(self):
        return self.body[0]

    def body_set(self):
        return set(self.body)

    def check_self_collision(self):
        return self.head() in set(self.body[1:])

    def grow(self):
        self.grew = True

    def draw(self, surface):
        for i, (col, row) in enumerate(self.body):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            rect  = cell_rect(col, row)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            inner   = rect.inflate(-4, -4)
            lighter = tuple(min(255, c + 40) for c in color)
            pygame.draw.rect(surface, lighter, inner, border_radius=3)


# ── Weighted Food with Timer ───────────────────────────────────────────────────
class Food:
    """
    A food item with a random value (weighted) and a disappear timer.
    The food pulses visually to warn the player it is about to vanish.
    """

    def __init__(self, occupied: set):
        self.col, self.row = random_free_cell(occupied)
        self.points, self.color, self.lifetime = _pick_food_type()
        self.age        = 0.0      # seconds since this food was spawned
        self.expired    = False    # True when lifetime is exceeded

    def position(self):
        return (self.col, self.row)

    def update(self, dt: float):
        """
        Advance the age timer.
        Mark as expired when lifetime is reached.
        dt is in seconds (passed from the game loop).
        """
        self.age += dt
        if self.age >= self.lifetime:
            self.expired = True

    def time_left(self):
        return max(0.0, self.lifetime - self.age)

    def draw(self, surface):
        rect = cell_rect(self.col, self.row)

        # When less than 2 s remain, flash by skipping every other draw call
        # based on a coarse blink derived from age
        if self.time_left() < 2.0:
            if int(self.age * 6) % 2 == 0:   # blink ~3 times/sec
                return

        # Draw as a filled ellipse in the food's colour
        pygame.draw.ellipse(surface, self.color, rect)

        # Shine dot
        shine = pygame.Rect(rect.x + 4, rect.y + 4, 5, 5)
        pygame.draw.ellipse(surface, (255, 255, 255), shine)

        # Small points label above the food
        font  = pygame.font.SysFont("Arial", 9, bold=True)
        label = font.render(f"+{self.points}", True, self.color)
        surface.blit(label, (rect.x, rect.y - 12))


# ── Walls ──────────────────────────────────────────────────────────────────────
def draw_walls(surface):
    for col in range(COLS):
        for row in range(ROWS):
            if col == 0 or col == COLS - 1 or row == 0 or row == ROWS - 1:
                rect = cell_rect(col, row)
                pygame.draw.rect(surface, WALL_COLOR, rect)
                pygame.draw.rect(surface, (50, 50, 50), rect, 1)


def is_wall(col, row):
    return col <= 0 or col >= COLS - 1 or row <= 0 or row >= ROWS - 1


# ── HUD ────────────────────────────────────────────────────────────────────────
class HUD:
    def __init__(self):
        self.font    = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_sm = pygame.font.SysFont("Consolas", 13)

    def draw(self, surface, score, level, food_time_left):
        pygame.draw.rect(surface, HUD_BG, (0, 0, WIDTH, 50))
        pygame.draw.line(surface, WALL_COLOR, (0, 50), (WIDTH, 50), 2)

        surface.blit(self.font.render("Score:", True, TEXT_COLOR), (10, 13))
        surface.blit(self.font.render(str(score), True, SCORE_COLOR), (80, 13))

        lx = WIDTH - 140
        surface.blit(self.font.render("Level:", True, TEXT_COLOR), (lx, 13))
        surface.blit(self.font.render(str(level), True, LEVEL_COLOR), (lx + 72, 13))

        # Food timer bar (bottom of HUD strip)
        if food_time_left is not None:
            # Background bar
            bar_rect = pygame.Rect(10, 38, WIDTH - 20, 8)
            pygame.draw.rect(surface, (50, 50, 70), bar_rect, border_radius=4)
            # Filled portion
            max_life = max(f[3] for f in FOOD_TYPES)   # longest possible lifetime
            fill_w   = int(bar_rect.width * (food_time_left / max_life))
            # Colour shifts red as time runs out
            ratio     = food_time_left / max_life
            bar_color = (int(255 * (1 - ratio)), int(200 * ratio), 60)
            if fill_w > 0:
                pygame.draw.rect(surface, bar_color,
                                 (bar_rect.x, bar_rect.y, fill_w, bar_rect.height),
                                 border_radius=4)
            surface.blit(
                self.font_sm.render(f"Food: {food_time_left:.1f}s", True, TEXT_COLOR),
                (bar_rect.right - 72, 36))


# ── Game ───────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake – Practice 11")
        self.clock  = pygame.time.Clock()

        self.snake = Snake()
        self.hud   = HUD()

        self.score       = 0
        self.level       = 1
        self.foods_eaten = 0
        self.current_fps = FPS

        occupied   = self.snake.body_set()
        self.food  = Food(occupied)   # first food

        self.game_over = False
        self.paused    = False

        self.font_big = pygame.font.SysFont("Consolas", 40, bold=True)
        self.font_med = pygame.font.SysFont("Consolas", 22)

    def _respawn_food(self):
        occupied  = self.snake.body_set()
        self.food = Food(occupied)

    def _advance_level(self):
        self.level       += 1
        self.foods_eaten  = 0
        self.current_fps  = min(MIN_FPS, FPS + (self.level - 1) * 2)

    def run(self):
        while True:
            # clock.tick returns milliseconds; convert to seconds for timers
            dt_ms = self.clock.tick(self.current_fps)
            dt    = dt_ms / 1000.0

            self._handle_events()

            if not self.game_over and not self.paused:
                self._update(dt)

            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()
                    return
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                if not self.game_over:
                    if event.key in (pygame.K_UP,    pygame.K_w): self.snake.set_direction(UP)
                    if event.key in (pygame.K_DOWN,  pygame.K_s): self.snake.set_direction(DOWN)
                    if event.key in (pygame.K_LEFT,  pygame.K_a): self.snake.set_direction(LEFT)
                    if event.key in (pygame.K_RIGHT, pygame.K_d): self.snake.set_direction(RIGHT)

    def _update(self, dt: float):
        # ── Update food timer ────────────────────────────────────────────────
        self.food.update(dt)
        if self.food.expired:
            # Food timed out — spawn a new one without awarding points
            self._respawn_food()

        # ── Move snake (one step per tick) ───────────────────────────────────
        self.snake.move()
        head = self.snake.head()

        # ── Border collision ─────────────────────────────────────────────────
        if is_wall(*head):
            self.game_over = True
            return

        # ── Self collision ────────────────────────────────────────────────────
        if self.snake.check_self_collision():
            self.game_over = True
            return

        # ── Food collection ───────────────────────────────────────────────────
        if head == self.food.position():
            self.snake.grow()
            # Points scaled by level × food value
            self.score       += self.food.points * self.level
            self.foods_eaten += 1

            if self.foods_eaten >= FOODS_PER_LEVEL:
                self._advance_level()

            self._respawn_food()

    def _draw(self):
        self.screen.fill(BG_COLOR)

        # Subtle grid
        for col in range(COLS):
            for row in range(ROWS):
                pygame.draw.rect(self.screen, GRID_COLOR, cell_rect(col, row), 1)

        draw_walls(self.screen)
        self.food.draw(self.screen)
        self.snake.draw(self.screen)

        food_tl = self.food.time_left() if not self.food.expired else None
        self.hud.draw(self.screen, self.score, self.level, food_tl)

        if self.game_over:
            self._draw_game_over()
        elif self.paused:
            self._draw_paused()

    def _draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        cx = WIDTH // 2
        cy = HEIGHT // 2
        lines = [
            self.font_big.render("GAME OVER",                          True, (220, 50, 50)),
            self.font_med.render(f"Score: {self.score}  Level: {self.level}", True, TEXT_COLOR),
            self.font_med.render("Press R to restart",                 True, LEVEL_COLOR),
        ]
        for i, surf in enumerate(lines):
            self.screen.blit(surf, surf.get_rect(center=(cx, cy - 40 + i * 44)))

    def _draw_paused(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        paused = self.font_big.render("PAUSED", True, LEVEL_COLOR)
        self.screen.blit(paused, paused.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


if __name__ == "__main__":
    Game().run()