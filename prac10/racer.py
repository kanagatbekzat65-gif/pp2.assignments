"""
Racer Game - Practice 10, Task 1
Pygame racing game extended from coderslegacy.com tutorial.
Features: enemy cars, scrolling road, randomly appearing coins, coin counter.
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
LANE_WIDTH = (ROAD_RIGHT - ROAD_LEFT) // 3   # three lanes

# Coin spawn timing (milliseconds)
COIN_MIN_INTERVAL = 1500
COIN_MAX_INTERVAL = 4000

# ── Helper: draw a simple car with pygame primitives ───────────────────────────
def draw_car(surface, color, x, y, w=40, h=60):
    """Draw a simplified top-down car rectangle with windows and wheels."""
    # Body
    pygame.draw.rect(surface, color,   (x, y, w, h), border_radius=6)
    # Windshield
    pygame.draw.rect(surface, (180, 230, 255), (x+5, y+6,  w-10, 12), border_radius=3)
    # Rear window
    pygame.draw.rect(surface, (180, 230, 255), (x+5, y+h-18, w-10, 10), border_radius=3)
    # Wheels
    wheel_color = (30, 30, 30)
    pygame.draw.rect(surface, wheel_color, (x-5,    y+8,    8, 14), border_radius=2)
    pygame.draw.rect(surface, wheel_color, (x+w-3,  y+8,    8, 14), border_radius=2)
    pygame.draw.rect(surface, wheel_color, (x-5,    y+h-22, 8, 14), border_radius=2)
    pygame.draw.rect(surface, wheel_color, (x+w-3,  y+h-22, 8, 14), border_radius=2)


# ── Player ─────────────────────────────────────────────────────────────────────
class Player:
    """The car controlled by the player (keyboard)."""

    WIDTH  = 40
    HEIGHT = 60
    SPEED  = 5

    def __init__(self):
        # Start centered on the road
        self.x = SCREEN_WIDTH // 2 - self.WIDTH // 2
        self.y = SCREEN_HEIGHT - self.HEIGHT - 20
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    def update(self, keys):
        """Move left/right with arrow keys; clamp to road boundaries."""
        if keys[pygame.K_LEFT]:
            self.x -= self.SPEED
        if keys[pygame.K_RIGHT]:
            self.x += self.SPEED

        # Keep inside road
        self.x = max(ROAD_LEFT + 5,  self.x)
        self.x = min(ROAD_RIGHT - self.WIDTH - 5, self.x)

        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        draw_car(surface, BLUE, self.x, self.y)


# ── Enemy car ──────────────────────────────────────────────────────────────────
class Enemy:
    """An oncoming enemy car that scrolls down from the top."""

    WIDTH  = 40
    HEIGHT = 60

    def __init__(self, speed):
        # Pick a random lane
        lane = random.randint(0, 2)
        self.x = ROAD_LEFT + lane * LANE_WIDTH + (LANE_WIDTH - self.WIDTH) // 2
        self.y = -self.HEIGHT  # start above screen
        self.speed = speed
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        self.color = random.choice([RED, ORANGE, GREEN])

    def update(self):
        """Scroll the enemy car downward."""
        self.y += self.speed
        self.rect.topleft = (self.x, self.y)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT

    def draw(self, surface):
        draw_car(surface, self.color, self.x, self.y)


# ── Coin ───────────────────────────────────────────────────────────────────────
class Coin:
    """A golden coin that appears randomly on the road and scrolls down."""

    RADIUS = 12

    def __init__(self, speed):
        # Place coin in a random lane, centred horizontally
        lane = random.randint(0, 2)
        cx = ROAD_LEFT + lane * LANE_WIDTH + LANE_WIDTH // 2
        self.x = cx
        self.y = -self.RADIUS
        self.speed = speed
        # Rect for collision (square bounding box around circle)
        self.rect = pygame.Rect(cx - self.RADIUS, self.y - self.RADIUS,
                                self.RADIUS * 2,  self.RADIUS * 2)

    def update(self):
        """Scroll the coin down."""
        self.y += self.speed
        self.rect.center = (self.x, int(self.y))

    def is_off_screen(self):
        return self.y - self.RADIUS > SCREEN_HEIGHT

    def draw(self, surface):
        # Outer gold ring
        pygame.draw.circle(surface, (255, 180, 0), (self.x, int(self.y)), self.RADIUS)
        # Inner shine
        pygame.draw.circle(surface, YELLOW,        (self.x, int(self.y)), self.RADIUS - 4)
        # "$" symbol (tiny)
        font = pygame.font.SysFont("Arial", 14, bold=True)
        label = font.render("$", True, (180, 90, 0))
        surface.blit(label, label.get_rect(center=(self.x, int(self.y))))


# ── Road background ────────────────────────────────────────────────────────────
class Road:
    """Scrolling road with dashed lane dividers."""

    DASH_HEIGHT = 40
    DASH_GAP    = 30
    DASH_SPEED  = 6

    def __init__(self):
        self.offset = 0   # vertical scroll offset

    def update(self):
        """Advance the scroll offset."""
        self.offset = (self.offset + self.DASH_SPEED) % (self.DASH_HEIGHT + self.DASH_GAP)

    def draw(self, surface):
        # Road surface
        pygame.draw.rect(surface, GRAY, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, SCREEN_HEIGHT))
        # Solid road edges
        pygame.draw.rect(surface, WHITE, (ROAD_LEFT - 6,  0, 6, SCREEN_HEIGHT))
        pygame.draw.rect(surface, WHITE, (ROAD_RIGHT,     0, 6, SCREEN_HEIGHT))

        # Scrolling dashed lane dividers
        for lane in range(1, 3):
            x = ROAD_LEFT + lane * LANE_WIDTH
            y = -self.DASH_HEIGHT + self.offset
            while y < SCREEN_HEIGHT:
                pygame.draw.rect(surface, WHITE, (x - 2, y, 4, self.DASH_HEIGHT))
                y += self.DASH_HEIGHT + self.DASH_GAP


# ── HUD ────────────────────────────────────────────────────────────────────────
class HUD:
    """Heads-up display: score on the left, coin counter top-right."""

    def __init__(self):
        self.font_large = pygame.font.SysFont("Consolas", 22, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 18)

    def draw(self, surface, score, coins):
        # Score (top-left)
        score_surf = self.font_large.render(f"Score: {score}", True, WHITE)
        surface.blit(score_surf, (10, 10))

        # Coin counter (top-right) with a coin icon
        coin_text = self.font_large.render(f"Coins: {coins}", True, YELLOW)
        surface.blit(coin_text, (SCREEN_WIDTH - coin_text.get_width() - 10, 10))

        # Small coin icon next to the text
        pygame.draw.circle(surface,
                           (255, 180, 0),
                           (SCREEN_WIDTH - coin_text.get_width() - 26, 22),
                           10)


# ── Game ───────────────────────────────────────────────────────────────────────
class Game:
    """Main game controller."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Racer – Practice 10")
        self.clock  = pygame.time.Clock()

        self.road   = Road()
        self.player = Player()
        self.hud    = HUD()

        self.enemies: list[Enemy] = []
        self.coins:   list[Coin]  = []

        self.score      = 0
        self.coin_count = 0
        self.speed      = 5            # enemy/coin scroll speed

        # Enemy spawn timer
        self.enemy_timer    = 0
        self.enemy_interval = 1500     # ms between enemy spawns

        # Coin spawn timer (random interval)
        self.coin_timer    = 0
        self.coin_interval = random.randint(COIN_MIN_INTERVAL, COIN_MAX_INTERVAL)

        self.game_over = False
        self.font_big  = pygame.font.SysFont("Consolas", 42, bold=True)
        self.font_med  = pygame.font.SysFont("Consolas", 24)

    # ── Spawn helpers ───────────────────────────────────────────────────────────
    def spawn_enemy(self):
        self.enemies.append(Enemy(self.speed))

    def spawn_coin(self):
        self.coins.append(Coin(self.speed))
        # Randomise next coin interval
        self.coin_interval = random.randint(COIN_MIN_INTERVAL, COIN_MAX_INTERVAL)

    # ── Main loop ───────────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS)    # milliseconds since last frame
            self.handle_events()

            if not self.game_over:
                self.update(dt)
                self.draw()
            else:
                self.draw_game_over()

            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    # Restart
                    self.__init__()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.road.update()

        # ── Timers ──────────────────────────────────────────────────────────
        self.enemy_timer += dt
        self.coin_timer  += dt

        if self.enemy_timer >= self.enemy_interval:
            self.spawn_enemy()
            self.enemy_timer = 0

        if self.coin_timer >= self.coin_interval:
            self.spawn_coin()
            self.coin_timer = 0

        # ── Update enemies ───────────────────────────────────────────────────
        for enemy in self.enemies:
            enemy.update()
            # Collision with player → game over
            if self.player.rect.colliderect(enemy.rect):
                self.game_over = True

        # Remove off-screen enemies and add score
        for enemy in self.enemies[:]:
            if enemy.is_off_screen():
                self.enemies.remove(enemy)
                self.score += 1       # survived one car → +1 point

        # ── Update coins ─────────────────────────────────────────────────────
        for coin in self.coins[:]:
            coin.update()
            if self.player.rect.colliderect(coin.rect):
                # Player collected the coin
                self.coin_count += 1
                self.score      += 5   # bonus points per coin
                self.coins.remove(coin)
            elif coin.is_off_screen():
                self.coins.remove(coin)

        # ── Gradually increase difficulty ────────────────────────────────────
        # Every 10 score points, shorten the enemy interval (min 600 ms)
        self.enemy_interval = max(600, 1500 - self.score * 15)

    def draw(self):
        self.screen.fill(BLACK)          # grass / off-road
        self.road.draw(self.screen)

        # Draw coins behind player
        for coin in self.coins:
            coin.draw(self.screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw player on top
        self.player.draw(self.screen)

        # HUD last (always on top)
        self.hud.draw(self.screen, self.score, self.coin_count)

    def draw_game_over(self):
        """Overlay a 'Game Over' screen."""
        self.screen.fill((20, 0, 0))
        go   = self.font_big.render("GAME OVER", True, RED)
        sc   = self.font_med.render(f"Score: {self.score}   Coins: {self.coin_count}", True, WHITE)
        rest = self.font_med.render("Press R to restart", True, GRAY)

        cx = SCREEN_WIDTH // 2
        self.screen.blit(go,   go.get_rect(center=(cx, 220)))
        self.screen.blit(sc,   sc.get_rect(center=(cx, 290)))
        self.screen.blit(rest, rest.get_rect(center=(cx, 340)))


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()