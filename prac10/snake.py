"""
Snake Game – Practice 10, Task 2
Classic snake extended with:
  - Border (wall) collision detection
  - Random food that avoids walls and the snake body
  - Levels that increase every 3 foods eaten
  - Speed increase per level
  - On-screen score and level counter
  - Full comments throughout
"""

import pygame
import random
import sys

# ── Constants ──────────────────────────────────────────────────────────────────
CELL   = 20          # size of one grid cell in pixels
COLS   = 25          # number of columns
ROWS   = 25          # number of rows
WIDTH  = COLS * CELL
HEIGHT = ROWS * CELL + 50   # +50 px for the HUD strip at the top
FPS    = 10          # base frames per second (also controls snake speed)

# Colours
BG_COLOR       = (15,  15,  15)   # near-black background
GRID_COLOR     = (30,  30,  30)   # subtle grid lines
SNAKE_HEAD     = (50, 220,  80)   # bright green for head
SNAKE_BODY     = (30, 160,  60)   # slightly darker for body
FOOD_COLOR     = (220,  50,  50)  # red food
WALL_COLOR     = (80,  80,  80)   # dark grey walls
HUD_BG         = (25,  25,  40)   # HUD background
TEXT_COLOR     = (230, 230, 230)  # main text
SCORE_COLOR    = (100, 220, 255)  # score highlight
LEVEL_COLOR    = (255, 200,  50)  # level highlight

# Direction vectors (dx, dy) in grid units
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# Foods eaten before levelling up
FOODS_PER_LEVEL = 3

# Minimum tick-rate cap (so the game doesn't get impossibly fast)
MIN_FPS = 25

# ── Grid helpers ───────────────────────────────────────────────────────────────
def cell_rect(col, row):
    """Return a pygame.Rect for the grid cell at (col, row), offset by HUD height."""
    return pygame.Rect(col * CELL, row * CELL + 50, CELL, CELL)


def random_free_cell(occupied: set) -> tuple[int, int]:
    """
    Pick a random grid cell that:
      - is inside the playable area (not on the border wall)
      - is not already occupied by the snake or another item
    Returns (col, row).
    """
    while True:
        col = random.randint(1, COLS - 2)   # 1..COLS-2 avoids border columns
        row = random.randint(1, ROWS - 2)   # 1..ROWS-2 avoids border rows
        if (col, row) not in occupied:
            return col, row


# ── Snake ──────────────────────────────────────────────────────────────────────
class Snake:
    """Represents the snake: body segments, direction, movement, and drawing."""

    def __init__(self):
        # Start in the middle of the board, 3 segments long, moving right
        mid_col = COLS // 2
        mid_row = ROWS // 2
        self.body      = [(mid_col, mid_row),
                          (mid_col - 1, mid_row),
                          (mid_col - 2, mid_row)]
        self.direction = RIGHT
        self.grew      = False   # flag: did we eat food this step?

    def set_direction(self, new_dir):
        """
        Change direction, but prevent 180° reversal
        (you can't move directly backward into your own neck).
        """
        opposite = (-new_dir[0], -new_dir[1])
        if new_dir != opposite or len(self.body) == 1:
            self.direction = new_dir

    def move(self):
        """
        Advance the snake by one cell in the current direction.
        If the snake ate food (self.grew), keep the tail; otherwise remove it.
        """
        head = self.body[0]
        new_head = (head[0] + self.direction[0],
                    head[1] + self.direction[1])
        self.body.insert(0, new_head)

        if self.grew:
            self.grew = False   # consume the growth flag; tail stays
        else:
            self.body.pop()     # normal move: remove the last segment

    def head(self):
        """Return the (col, row) of the head."""
        return self.body[0]

    def body_set(self):
        """Return the body as a set for fast membership checks."""
        return set(self.body)

    def check_self_collision(self):
        """Return True if the head overlaps any body segment (excluding itself)."""
        return self.head() in set(self.body[1:])

    def grow(self):
        """Signal that the snake should grow on the next move."""
        self.grew = True

    def draw(self, surface):
        """Draw each segment; head is brighter than the body."""
        for i, (col, row) in enumerate(self.body):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            rect  = cell_rect(col, row)
            pygame.draw.rect(surface, color, rect, border_radius=4)
            # Inner highlight to give a slightly 3-D look
            inner = rect.inflate(-4, -4)
            lighter = tuple(min(255, c + 40) for c in color)
            pygame.draw.rect(surface, lighter, inner, border_radius=3)


# ── Food ───────────────────────────────────────────────────────────────────────
class Food:
    """A single food item placed randomly inside the playable area."""

    def __init__(self, occupied: set):
        self.col, self.row = random_free_cell(occupied)

    def position(self):
        return (self.col, self.row)

    def draw(self, surface):
        rect = cell_rect(self.col, self.row)
        # Draw as a circle inside the cell
        pygame.draw.ellipse(surface, FOOD_COLOR, rect)
        # Small shine dot
        shine_rect = pygame.Rect(rect.x + 4, rect.y + 4, 5, 5)
        pygame.draw.ellipse(surface, (255, 160, 160), shine_rect)


# ── Wall (border) ──────────────────────────────────────────────────────────────
def draw_walls(surface):
    """
    Draw the border wall cells around the grid.
    Any cell on column 0, column COLS-1, row 0, or row ROWS-1 is a wall.
    """
    for col in range(COLS):
        for row in range(ROWS):
            if col == 0 or col == COLS - 1 or row == 0 or row == ROWS - 1:
                rect = cell_rect(col, row)
                pygame.draw.rect(surface, WALL_COLOR, rect)
                # Slight border to distinguish individual blocks
                pygame.draw.rect(surface, (50, 50, 50), rect, 1)


def is_wall(col, row):
    """Return True if the given cell is a border wall."""
    return col <= 0 or col >= COLS - 1 or row <= 0 or row >= ROWS - 1


# ── HUD ────────────────────────────────────────────────────────────────────────
class HUD:
    """Draws the score and level strip at the top of the window."""

    def __init__(self):
        self.font = pygame.font.SysFont("Consolas", 22, bold=True)

    def draw(self, surface, score, level):
        # Background strip
        pygame.draw.rect(surface, HUD_BG, (0, 0, WIDTH, 50))
        pygame.draw.line(surface, WALL_COLOR, (0, 50), (WIDTH, 50), 2)

        # Score on the left
        score_surf = self.font.render("Score:", True, TEXT_COLOR)
        score_val  = self.font.render(str(score), True, SCORE_COLOR)
        surface.blit(score_surf, (10, 13))
        surface.blit(score_val,  (80, 13))

        # Level on the right
        level_surf = self.font.render(f"Level: ", True, TEXT_COLOR)
        level_val  = self.font.render(str(level), True, LEVEL_COLOR)
        lx = WIDTH - 130
        surface.blit(level_surf, (lx, 13))
        surface.blit(level_val,  (lx + 70, 13))


# ── Game ───────────────────────────────────────────────────────────────────────
class Game:
    """Top-level controller: game loop, state, level management."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake – Practice 10")
        self.clock  = pygame.time.Clock()

        self.snake  = Snake()
        self.hud    = HUD()

        self.score        = 0
        self.level        = 1
        self.foods_eaten  = 0    # foods eaten on the current level
        self.current_fps  = FPS  # will increase with each level

        # Place initial food, avoiding the snake body and walls
        occupied = self.snake.body_set()
        self.food = Food(occupied)

        self.game_over  = False
        self.paused     = False

        # Fonts for overlays
        self.font_big = pygame.font.SysFont("Consolas", 40, bold=True)
        self.font_med = pygame.font.SysFont("Consolas", 22)

    # ── Helpers ─────────────────────────────────────────────────────────────────
    def respawn_food(self):
        """Place new food avoiding the snake body and the border walls."""
        occupied = self.snake.body_set()
        self.food = Food(occupied)

    def advance_level(self):
        """
        Called when the snake eats enough food to level up.
        Increases the level counter and the game speed.
        """
        self.level       += 1
        self.foods_eaten  = 0
        # Increase speed by 2 FPS per level, up to MIN_FPS cap
        self.current_fps  = min(MIN_FPS, FPS + (self.level - 1) * 2)

    # ── Main loop ───────────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(self.current_fps)
            self.handle_events()

            if not self.game_over and not self.paused:
                self.update()

            self.draw()
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Restart after game over
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()
                    return

                # Pause / unpause
                if event.key == pygame.K_p:
                    self.paused = not self.paused

                # Direction keys – only meaningful when playing
                if not self.game_over:
                    if event.key in (pygame.K_UP,    pygame.K_w): self.snake.set_direction(UP)
                    if event.key in (pygame.K_DOWN,  pygame.K_s): self.snake.set_direction(DOWN)
                    if event.key in (pygame.K_LEFT,  pygame.K_a): self.snake.set_direction(LEFT)
                    if event.key in (pygame.K_RIGHT, pygame.K_d): self.snake.set_direction(RIGHT)

    def update(self):
        """Advance the game state by one tick."""
        self.snake.move()

        head = self.snake.head()

        # ── Border (wall) collision ──────────────────────────────────────────
        if is_wall(*head):
            self.game_over = True
            return

        # ── Self collision ───────────────────────────────────────────────────
        if self.snake.check_self_collision():
            self.game_over = True
            return

        # ── Food collection ──────────────────────────────────────────────────
        if head == self.food.position():
            self.snake.grow()          # snake grows next step
            self.score       += 10 * self.level   # higher levels = more points
            self.foods_eaten += 1

            # Level up when enough food has been collected
            if self.foods_eaten >= FOODS_PER_LEVEL:
                self.advance_level()

            self.respawn_food()        # place new food

    def draw(self):
        """Render all game objects."""
        self.screen.fill(BG_COLOR)

        # Subtle grid
        for col in range(COLS):
            for row in range(ROWS):
                r = cell_rect(col, row)
                pygame.draw.rect(self.screen, GRID_COLOR, r, 1)

        # Border walls
        draw_walls(self.screen)

        # Food and snake
        self.food.draw(self.screen)
        self.snake.draw(self.screen)

        # HUD
        self.hud.draw(self.screen, self.score, self.level)

        # Overlays
        if self.game_over:
            self._draw_game_over()
        elif self.paused:
            self._draw_paused()

    def _draw_game_over(self):
        """Translucent 'Game Over' overlay."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        go   = self.font_big.render("GAME OVER",           True, (220,  50,  50))
        info = self.font_med.render(
            f"Score: {self.score}   Level: {self.level}",  True, TEXT_COLOR)
        hint = self.font_med.render("Press R to restart",  True, LEVEL_COLOR)

        cx = WIDTH // 2
        cy = HEIGHT // 2
        self.screen.blit(go,   go.get_rect(center=(cx, cy - 40)))
        self.screen.blit(info, info.get_rect(center=(cx, cy + 10)))
        self.screen.blit(hint, hint.get_rect(center=(cx, cy + 45)))

    def _draw_paused(self):
        """Semi-transparent 'Paused' banner."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        paused = self.font_big.render("PAUSED", True, LEVEL_COLOR)
        self.screen.blit(paused, paused.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()