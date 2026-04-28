"""
Racer – Practice 11, Task 1
Extends Practice 10 Racer with:
  1. Randomly generated coins with different weights
     (common $1 coins appear most often; rare $10 coins appear least)
  2. Enemy speed increases every N coins collected
  3. Full comments throughout
"""

import pygame
import random
import sys

# ── Constants ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
FPS           = 60

# Colors
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
RED    = (200,  30,  30)
BLUE   = (30,  30, 200)
GRAY   = (100, 100, 100)
YELLOW = (255, 220,   0)
GREEN  = (0,  180,   0)
ORANGE = (255, 140,   0)

# Road geometry
ROAD_LEFT  = 60
ROAD_RIGHT = 340
LANE_WIDTH = (ROAD_RIGHT - ROAD_LEFT) // 3

# Coin spawn timing (milliseconds)
COIN_MIN_INTERVAL = 1200
COIN_MAX_INTERVAL = 3500

# ── Weighted coin table ────────────────────────────────────────────────────────
# Each entry: (value, weight, display_color)
# Higher weight → appears more often.
# The weighted random pick is done in _pick_coin_value().
COIN_TYPES = [
    (1,  50, (255, 200,  40)),   # gold   – very common
    (3,  30, (200, 200, 200)),   # silver – common
    (5,  15, (180, 140, 255)),   # purple – uncommon
    (10,  5, (  0, 220, 255)),   # cyan   – rare
]

# Speed-up: enemy base speed increases after every SPEED_UP_COINS coins
SPEED_UP_COINS = 5   # threshold


def _pick_coin_value():
    """
    Weighted random selection from COIN_TYPES.
    Builds a cumulative-weight list and picks based on a random roll.
    Returns (value, color) for the chosen coin type.
    """
    total   = sum(w for _, w, _ in COIN_TYPES)
    roll    = random.randint(0, total - 1)
    cumul   = 0
    for value, weight, color in COIN_TYPES:
        cumul += weight
        if roll < cumul:
            return value, color
    return COIN_TYPES[0][0], COIN_TYPES[0][2]   # fallback


# ── Helper: draw a simple top-down car ────────────────────────────────────────
def draw_car(surface, color, x, y, w=40, h=60):
    """Draw a simplified top-down car with body, windows, and wheels."""
    pygame.draw.rect(surface, color, (x, y, w, h), border_radius=6)
    pygame.draw.rect(surface, (180, 230, 255), (x+5, y+6,  w-10, 12), border_radius=3)
    pygame.draw.rect(surface, (180, 230, 255), (x+5, y+h-18, w-10, 10), border_radius=3)
    wc = (30, 30, 30)
    pygame.draw.rect(surface, wc, (x-5,    y+8,    8, 14), border_radius=2)
    pygame.draw.rect(surface, wc, (x+w-3,  y+8,    8, 14), border_radius=2)
    pygame.draw.rect(surface, wc, (x-5,    y+h-22, 8, 14), border_radius=2)
    pygame.draw.rect(surface, wc, (x+w-3,  y+h-22, 8, 14), border_radius=2)


# ── Player ─────────────────────────────────────────────────────────────────────
class Player:
    """The player's car; moves left/right with arrow keys."""

    WIDTH  = 40
    HEIGHT = 60
    SPEED  = 5

    def __init__(self):
        self.x    = SCREEN_WIDTH // 2 - self.WIDTH // 2
        self.y    = SCREEN_HEIGHT - self.HEIGHT - 20
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    def update(self, keys):
        """Apply keyboard input and clamp position to road bounds."""
        if keys[pygame.K_LEFT]:
            self.x -= self.SPEED
        if keys[pygame.K_RIGHT]:
            self.x += self.SPEED
        self.x = max(ROAD_LEFT + 5,              self.x)
        self.x = min(ROAD_RIGHT - self.WIDTH - 5, self.x)
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        draw_car(surface, BLUE, self.x, self.y)


# ── Enemy car ──────────────────────────────────────────────────────────────────
class Enemy:
    """An enemy car that scrolls down from the top at the current game speed."""

    WIDTH  = 40
    HEIGHT = 60

    def __init__(self, speed):
        lane      = random.randint(0, 2)
        self.x    = ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - self.WIDTH) // 2
        self.y    = -self.HEIGHT
        self.speed = speed
        self.rect  = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        self.color = random.choice([RED, ORANGE, GREEN])

    def update(self):
        """Move the enemy downward by its speed."""
        self.y    += self.speed
        self.rect.topleft = (self.x, self.y)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT

    def draw(self, surface):
        draw_car(surface, self.color, self.x, self.y)


# ── Weighted Coin ──────────────────────────────────────────────────────────────
class Coin:
    """
    A coin with a value determined by weighted random selection.
    Rarer coins are worth more and have a distinct colour.
    """

    RADIUS = 12

    def __init__(self, speed):
        lane        = random.randint(0, 2)
        cx          = ROAD_LEFT + lane * LANE_WIDTH + LANE_WIDTH // 2
        self.x      = cx
        self.y      = -self.RADIUS
        self.speed  = speed

        # Pick a value and colour based on the weight table
        self.value, self.color = _pick_coin_value()

        self.rect = pygame.Rect(cx - self.RADIUS, self.y - self.RADIUS,
                                self.RADIUS * 2,  self.RADIUS * 2)

    def update(self):
        """Scroll the coin downward."""
        self.y       += self.speed
        self.rect.center = (self.x, int(self.y))

    def is_off_screen(self):
        return self.y - self.RADIUS > SCREEN_HEIGHT

    def draw(self, surface):
        # Outer ring in the coin's colour
        pygame.draw.circle(surface, self.color,  (self.x, int(self.y)), self.RADIUS)
        # Darker inner ring for depth
        inner_color = tuple(max(0, c - 60) for c in self.color)
        pygame.draw.circle(surface, inner_color, (self.x, int(self.y)), self.RADIUS - 4)

        # Show the coin value as a number (e.g. "1", "3", "5", "10")
        font  = pygame.font.SysFont("Arial", 11, bold=True)
        label = font.render(str(self.value), True, (20, 20, 20))
        surface.blit(label, label.get_rect(center=(self.x, int(self.y))))


# ── Road ───────────────────────────────────────────────────────────────────────
class Road:
    """Scrolling road with dashed lane dividers."""

    DASH_HEIGHT = 40
    DASH_GAP    = 30
    DASH_SPEED  = 6

    def __init__(self):
        self.offset = 0

    def update(self):
        self.offset = (self.offset + self.DASH_SPEED) % (self.DASH_HEIGHT + self.DASH_GAP)

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY,  (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 6, 0, 6, SCREEN_HEIGHT))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT,    0, 6, SCREEN_HEIGHT))
        for lane in range(1, 3):
            x = ROAD_LEFT + lane * LANE_WIDTH
            y = -self.DASH_HEIGHT + self.offset
            while y < SCREEN_HEIGHT:
                pygame.draw.rect(surface, WHITE, (x - 2, y, 4, self.DASH_HEIGHT))
                y += self.DASH_HEIGHT + self.DASH_GAP


# ── HUD ────────────────────────────────────────────────────────────────────────
class HUD:
    """Displays score, coin count, and current enemy speed level."""

    def __init__(self):
        self.font_lg = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_sm = pygame.font.SysFont("Consolas", 14)

    def draw(self, surface, score, coins, speed_level):
        # Score – top left
        surface.blit(
            self.font_lg.render(f"Score: {score}", True, WHITE),
            (10, 10))

        # Coin count – top right
        coin_surf = self.font_lg.render(f"Coins: {coins}", True, YELLOW)
        surface.blit(coin_surf, (SCREEN_WIDTH - coin_surf.get_width() - 10, 10))

        # Speed level – below score
        spd_surf = self.font_sm.render(f"Speed lv: {speed_level}", True, (180, 220, 255))
        surface.blit(spd_surf, (10, 36))

        # Coin legend (shows all coin types and their values)
        lx = 10
        ly = SCREEN_HEIGHT - 26
        surface.blit(self.font_sm.render("Coins: ", True, GRAY), (lx, ly))
        lx += 60
        for value, _, color in COIN_TYPES:
            pygame.draw.circle(surface, color, (lx + 6, ly + 7), 7)
            lbl = self.font_sm.render(f"${value}", True, color)
            surface.blit(lbl, (lx + 16, ly))
            lx += 44


# ── Game ───────────────────────────────────────────────────────────────────────
class Game:
    """Main controller: spawning, collision, scoring, difficulty."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Racer – Practice 11")
        self.clock  = pygame.time.Clock()

        self.road   = Road()
        self.player = Player()
        self.hud    = HUD()

        self.enemies : list[Enemy] = []
        self.coins   : list[Coin]  = []

        self.score       = 0
        self.coin_count  = 0   # total coins collected (all values)
        self.coin_value  = 0   # total $ value collected

        # Base enemy scroll speed; incremented every SPEED_UP_COINS coins
        self.base_speed  = 5
        self.speed_level = 1   # displayed in HUD

        # Enemy spawn timer
        self.enemy_timer    = 0
        self.enemy_interval = 1500   # ms

        # Coin spawn timer
        self.coin_timer    = 0
        self.coin_interval = random.randint(COIN_MIN_INTERVAL, COIN_MAX_INTERVAL)

        self.game_over = False
        self.font_big  = pygame.font.SysFont("Consolas", 42, bold=True)
        self.font_med  = pygame.font.SysFont("Consolas", 24)

    # ── Spawn helpers ───────────────────────────────────────────────────────────
    def _spawn_enemy(self):
        self.enemies.append(Enemy(self.base_speed))

    def _spawn_coin(self):
        self.coins.append(Coin(self.base_speed))
        self.coin_interval = random.randint(COIN_MIN_INTERVAL, COIN_MAX_INTERVAL)

    # ── Speed-up logic ─────────────────────────────────────────────────────────
    def _check_speedup(self):
        """
        Increase base_speed by 1 for every SPEED_UP_COINS coins collected.
        This makes all newly spawned enemies and coins faster.
        """
        new_level = 1 + self.coin_count // SPEED_UP_COINS
        if new_level > self.speed_level:
            self.speed_level = new_level
            self.base_speed  = 4 + self.speed_level   # 5, 6, 7 …

    # ── Main loop ───────────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self._handle_events()
            if not self.game_over:
                self._update(dt)
                self._draw()
            else:
                self._draw_game_over()
            pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()

    def _update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.road.update()

        # ── Timers ──────────────────────────────────────────────────────────
        self.enemy_timer += dt
        self.coin_timer  += dt

        if self.enemy_timer >= self.enemy_interval:
            self._spawn_enemy()
            self.enemy_timer    = 0
            # Shrink spawn interval slightly as score rises (min 600 ms)
            self.enemy_interval = max(600, 1500 - self.score * 12)

        if self.coin_timer >= self.coin_interval:
            self._spawn_coin()
            self.coin_timer = 0

        # ── Enemies ─────────────────────────────────────────────────────────
        for enemy in self.enemies[:]:
            enemy.update()
            if self.player.rect.colliderect(enemy.rect):
                self.game_over = True
                return
            if enemy.is_off_screen():
                self.enemies.remove(enemy)
                self.score += 1   # survived one enemy car → +1

        # ── Coins ───────────────────────────────────────────────────────────
        for coin in self.coins[:]:
            coin.update()
            if self.player.rect.colliderect(coin.rect):
                # Award points equal to the coin's value × 10
                self.score      += coin.value * 10
                self.coin_count += 1
                self.coin_value += coin.value
                self.coins.remove(coin)
                # Check whether we should speed up enemies
                self._check_speedup()
            elif coin.is_off_screen():
                self.coins.remove(coin)

    def _draw(self):
        self.screen.fill(BLACK)
        self.road.draw(self.screen)
        for coin in self.coins:
            coin.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        self.hud.draw(self.screen, self.score, self.coin_count, self.speed_level)

    def _draw_game_over(self):
        self.screen.fill((20, 0, 0))
        lines = [
            self.font_big.render("GAME OVER", True, RED),
            self.font_med.render(f"Score: {self.score}   Coins: {self.coin_count}   Value: ${self.coin_value}", True, WHITE),
            self.font_med.render(f"Speed level reached: {self.speed_level}", True, (180, 220, 255)),
            self.font_med.render("Press R to restart", True, GRAY),
        ]
        cx = SCREEN_WIDTH // 2
        y  = 200
        for surf in lines:
            self.screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 50


if __name__ == "__main__":
    Game().run()