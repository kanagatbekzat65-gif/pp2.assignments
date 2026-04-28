"""
racer.py — Game objects and core game logic (TSIS 3)

Classes:
  Road            — scrolling lane road with markings
  PlayerCar       — player vehicle with movement, nitro, shield
  TrafficCar      — enemy vehicle scrolling down
  Obstacle        — static road hazard (oil, barrier, pothole, speedbump, nitrostrip)
  Coin            — collectible coin (extends Practice 10-11 weighted coins)
  PowerUp         — collectible power-up (nitro / shield / repair)
  GameSession     — master state: spawning, difficulty, scoring, distance
"""

import pygame
import random
import math

# ─────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────

def rect_overlap(a: pygame.Rect, b: pygame.Rect, margin=6) -> bool:
    return a.inflate(-margin, -margin).colliderect(b.inflate(-margin, -margin))


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

WIN_W, WIN_H = 700, 740
LANE_COUNT   = 5
ROAD_LEFT    = 120
ROAD_RIGHT   = 580
ROAD_W       = ROAD_RIGHT - ROAD_LEFT
LANE_W       = ROAD_W // LANE_COUNT

CAR_W, CAR_H          = 44, 72
TRAFFIC_W, TRAFFIC_H  = 44, 68

# Base speeds (pixels/sec); difficulty multiplier applied on top
BASE_SCROLL   = 280
BASE_PLAYER   = 260
NITRO_MULT    = 1.85

POWERUP_LIFETIME = 8.0   # seconds before a power-up disappears
COIN_LIFETIME    = 10.0

# Difficulty presets: (scroll_mult, spawn_mult, traffic_mult)
DIFFICULTY = {
    "easy":   (0.75, 0.6,  0.5),
    "normal": (1.0,  1.0,  1.0),
    "hard":   (1.35, 1.5,  1.5),
}

# Coin weights — carries over from Practice 11
COIN_WEIGHTS = [(1, 50), (3, 30), (5, 15), (10, 5)]   # (value, weight)

# ─────────────────────────────────────────────────────────────
# Color palette (no image assets — pure Pygame drawing)
# ─────────────────────────────────────────────────────────────

C_ROAD      = ( 55,  55,  65)
C_KERB_A    = (200,  40,  40)
C_KERB_B    = (240, 240, 240)
C_LANE_MARK = (230, 230, 160)
C_GRASS     = ( 60, 120,  50)
C_SKY       = ( 15,  15,  25)

CAR_PALETTE = {
    "red":    (220,  50,  50),
    "blue":   ( 50, 100, 220),
    "green":  ( 40, 180,  60),
    "yellow": (240, 200,   0),
    "purple": (160,  60, 220),
}
TRAFFIC_COLORS = [
    (200, 100,  40),
    (200, 200,  50),
    ( 50, 180, 180),
    (180,  50, 180),
    (100, 180,  80),
]

C_WHITE     = (240, 240, 240)
C_COIN_GOLD = (255, 200,  40)
C_OIL       = ( 30,  30,  80)
C_BARRIER   = (255, 140,   0)
C_POTHOLE   = ( 40,  40,  40)
C_SPEEDBUMP = (200, 200,  50)
C_NITROSTR  = (  0, 220, 255)
C_POWERUP   = {
    "nitro":  (  0, 220, 255),
    "shield": ( 80, 160, 255),
    "repair": ( 50, 210, 100),
}


def _lane_cx(lane: int) -> int:
    """Centre x of a lane (0-indexed)."""
    return ROAD_LEFT + lane * LANE_W + LANE_W // 2


# ─────────────────────────────────────────────────────────────
# Road
# ─────────────────────────────────────────────────────────────

class Road:
    def __init__(self):
        self.offset = 0.0
        self.mark_h = 60
        self.mark_gap = 30

    def update(self, scroll_speed: float, dt: float):
        self.offset = (self.offset + scroll_speed * dt) % (self.mark_h + self.mark_gap)

    def draw(self, surface: pygame.Surface):
        W, H = surface.get_size()
        # Sky / grass
        surface.fill(C_SKY)
        pygame.draw.rect(surface, C_GRASS, (0, 0, ROAD_LEFT, H))
        pygame.draw.rect(surface, C_GRASS, (ROAD_RIGHT, 0, W - ROAD_RIGHT, H))
        # Road
        pygame.draw.rect(surface, C_ROAD, (ROAD_LEFT, 0, ROAD_W, H))

        # Kerb stripes (alternating red/white)
        stripe_h = 24
        stripes = H // stripe_h + 2
        for i in range(stripes):
            y = -stripe_h + int(self.offset) % (stripe_h * 2) + i * stripe_h
            col = C_KERB_A if i % 2 == 0 else C_KERB_B
            pygame.draw.rect(surface, col, (ROAD_LEFT - 12, y, 12, stripe_h))
            pygame.draw.rect(surface, col, (ROAD_RIGHT,     y, 12, stripe_h))

        # Dashed lane markings
        for lane in range(1, LANE_COUNT):
            x = ROAD_LEFT + lane * LANE_W
            y_start = -self.mark_h + int(self.offset)
            while y_start < H:
                pygame.draw.rect(surface, C_LANE_MARK, (x - 2, y_start, 4, self.mark_h))
                y_start += self.mark_h + self.mark_gap

        # Solid side lines
        pygame.draw.rect(surface, C_WHITE if True else C_LANE_MARK,
                         (ROAD_LEFT - 3, 0, 3, H))
        pygame.draw.rect(surface, (240, 240, 240), (ROAD_RIGHT, 0, 3, H))


# ─────────────────────────────────────────────────────────────
# Player Car
# ─────────────────────────────────────────────────────────────

class PlayerCar:
    def __init__(self, color_key="red"):
        self.lane    = LANE_COUNT // 2     # start in the middle lane
        self.x       = float(_lane_cx(self.lane))
        self.y       = float(WIN_H - 140)
        self.color   = CAR_PALETTE.get(color_key, CAR_PALETTE["red"])
        self.speed   = BASE_PLAYER
        self.nitro   = False
        self.nitro_t = 0.0
        self.shield  = False
        self.rect    = pygame.Rect(0, 0, CAR_W, CAR_H)
        self._update_rect()
        self._lane_target = float(self.x)
        self._move_speed  = 600.0   # lateral px/sec

    def _update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery  = int(self.y)

    def set_lane(self, lane: int):
        lane = max(0, min(LANE_COUNT - 1, lane))
        self.lane = lane
        self._lane_target = float(_lane_cx(lane))

    def move_left(self):  self.set_lane(self.lane - 1)
    def move_right(self): self.set_lane(self.lane + 1)

    def activate_nitro(self, duration=4.0):
        self.nitro   = True
        self.nitro_t = duration

    def activate_shield(self):
        self.shield = True

    def hit(self) -> bool:
        """Returns True if collision is fatal (no shield absorbs it)."""
        if self.shield:
            self.shield = False
            return False
        return True

    def update(self, dt: float):
        # Smooth lateral movement
        dx = self._lane_target - self.x
        if abs(dx) < 2:
            self.x = self._lane_target
        else:
            self.x += math.copysign(min(abs(dx), self._move_speed * dt), dx)

        # Nitro countdown
        if self.nitro:
            self.nitro_t -= dt
            if self.nitro_t <= 0:
                self.nitro   = False
                self.nitro_t = 0.0

        self._update_rect()

    def effective_scroll(self, base_scroll: float) -> float:
        return base_scroll * (NITRO_MULT if self.nitro else 1.0)

    def draw(self, surface: pygame.Surface):
        cx, cy = int(self.x), int(self.y)
        col = self.color
        hw, hh = CAR_W // 2, CAR_H // 2

        # Body
        pygame.draw.rect(surface, col, (cx - hw + 6, cy - hh, CAR_W - 12, CAR_H), border_radius=8)
        # Roof
        pygame.draw.rect(surface, _darken(col, 0.6), (cx - hw + 12, cy - hh + 14, CAR_W - 24, CAR_H - 36), border_radius=5)
        # Windshield
        pygame.draw.rect(surface, (160, 210, 255, 180), (cx - hw + 12, cy - hh + 14, CAR_W - 24, 18), border_radius=3)
        # Headlights
        pygame.draw.circle(surface, (255, 255, 180), (cx - hw + 8,  cy - hh + 5), 5)
        pygame.draw.circle(surface, (255, 255, 180), (cx + hw - 8,  cy - hh + 5), 5)
        # Taillights
        pygame.draw.circle(surface, (220, 50, 50), (cx - hw + 8,  cy + hh - 5), 5)
        pygame.draw.circle(surface, (220, 50, 50), (cx + hw - 8,  cy + hh - 5), 5)

        # Nitro flame
        if self.nitro:
            for i in range(3):
                fx = cx - 8 + i * 8
                fy = cy + hh
                fl = random.randint(12, 28)
                pygame.draw.polygon(surface, (0, 200, 255), [
                    (fx - 4, fy), (fx + 4, fy), (fx, fy + fl)
                ])
        # Shield ring
        if self.shield:
            pygame.draw.circle(surface, (80, 160, 255), (cx, cy), max(CAR_W, CAR_H) // 2 + 8, 3)


def _darken(color, factor):
    return tuple(int(c * factor) for c in color)


# ─────────────────────────────────────────────────────────────
# Traffic Car
# ─────────────────────────────────────────────────────────────

class TrafficCar:
    def __init__(self, lane: int, y_start: float = -80):
        self.lane  = lane
        self.x     = float(_lane_cx(lane))
        self.y     = y_start
        self.color = random.choice(TRAFFIC_COLORS)
        self.rect  = pygame.Rect(0, 0, TRAFFIC_W, TRAFFIC_H)
        self._update_rect()
        self.alive = True

    def _update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery  = int(self.y)

    def update(self, scroll_speed: float, dt: float):
        self.y += scroll_speed * dt
        self._update_rect()
        if self.y > WIN_H + 100:
            self.alive = False

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        col = self.color
        hw, hh = TRAFFIC_W // 2, TRAFFIC_H // 2
        pygame.draw.rect(surface, col, (cx - hw + 5, cy - hh, TRAFFIC_W - 10, TRAFFIC_H), border_radius=7)
        pygame.draw.rect(surface, _darken(col, 0.5), (cx - hw + 11, cy - hh + 12, TRAFFIC_W - 22, TRAFFIC_H - 30), border_radius=4)
        pygame.draw.rect(surface, (160, 210, 255), (cx - hw + 11, cy + hh - 26, TRAFFIC_W - 22, 14), border_radius=3)
        pygame.draw.circle(surface, (240, 100, 100), (cx - hw + 7, cy + hh - 5), 4)
        pygame.draw.circle(surface, (240, 100, 100), (cx + hw - 7, cy + hh - 5), 4)


# ─────────────────────────────────────────────────────────────
# Obstacle
# ─────────────────────────────────────────────────────────────

OBS_TYPES = {
    "oil":       {"w": 52, "h": 34, "color": C_OIL,      "effect": "slow",  "score": 0},
    "barrier":   {"w": 48, "h": 22, "color": C_BARRIER,  "effect": "crash", "score": 0},
    "pothole":   {"w": 36, "h": 28, "color": C_POTHOLE,  "effect": "crash", "score": 0},
    "speedbump": {"w": LANE_W, "h": 16, "color": C_SPEEDBUMP, "effect": "slow", "score": 0},
    "nitrostrip":{"w": LANE_W, "h": 18, "color": C_NITROSTR,  "effect": "nitro", "score": 20},
}

class Obstacle:
    def __init__(self, obs_type: str, lane: int, y_start: float = -50):
        self.obs_type = obs_type
        self.lane     = lane
        self.x        = float(_lane_cx(lane))
        self.y        = y_start
        meta          = OBS_TYPES[obs_type]
        self.effect   = meta["effect"]
        self.bonus    = meta["score"]
        self.color    = meta["color"]
        self.w        = meta["w"]
        self.h        = meta["h"]
        self.rect     = pygame.Rect(0, 0, self.w, self.h)
        self.alive    = True
        self._update_rect()
        self._anim    = 0.0

    def _update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery  = int(self.y)

    def update(self, scroll_speed: float, dt: float):
        self.y    += scroll_speed * dt
        self._anim = (self._anim + dt * 3) % (2 * math.pi)
        self._update_rect()
        if self.y > WIN_H + 60:
            self.alive = False

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        hw, hh = self.w // 2, self.h // 2

        if self.obs_type == "oil":
            # Elliptical oil spill
            pulse = int(4 * math.sin(self._anim))
            pygame.draw.ellipse(surface, C_OIL, (cx - hw - pulse, cy - hh, self.w + pulse*2, self.h))
            pygame.draw.ellipse(surface, (60, 60, 140), (cx - hw // 2, cy - hh // 2, hw, hh // 2))

        elif self.obs_type == "barrier":
            pygame.draw.rect(surface, C_BARRIER, (cx - hw, cy - hh, self.w, self.h), border_radius=4)
            # Stripes
            for i in range(3):
                sx = cx - hw + 4 + i * 14
                pygame.draw.rect(surface, (0, 0, 0), (sx, cy - hh + 2, 8, self.h - 4))

        elif self.obs_type == "pothole":
            pygame.draw.ellipse(surface, C_POTHOLE, (cx - hw, cy - hh, self.w, self.h))
            pygame.draw.ellipse(surface, (25, 25, 25), (cx - hw + 4, cy - hh + 4, self.w - 8, self.h - 8))

        elif self.obs_type == "speedbump":
            pygame.draw.rect(surface, C_SPEEDBUMP, (cx - hw, cy - hh, self.w, self.h), border_radius=6)
            pygame.draw.rect(surface, (180, 180, 30), (cx - hw, cy - hh, self.w, self.h), 2, border_radius=6)

        elif self.obs_type == "nitrostrip":
            pygame.draw.rect(surface, C_NITROSTR, (cx - hw, cy - hh, self.w, self.h), border_radius=4)
            # Arrows
            for ax in range(cx - hw + 8, cx + hw - 8, 18):
                pygame.draw.polygon(surface, (255, 255, 255), [
                    (ax, cy + 4), (ax + 8, cy + 4), (ax + 4, cy - 5)
                ])


# ─────────────────────────────────────────────────────────────
# Coin
# ─────────────────────────────────────────────────────────────

def _weighted_coin_value():
    total = sum(w for _, w in COIN_WEIGHTS)
    r = random.randint(0, total - 1)
    for val, weight in COIN_WEIGHTS:
        if r < weight:
            return val
        r -= weight
    return 1


class Coin:
    def __init__(self, lane: int, y_start: float = -30):
        self.lane    = lane
        self.x       = float(_lane_cx(lane))
        self.y       = y_start
        self.value   = _weighted_coin_value()
        self.alive   = True
        self.rect    = pygame.Rect(0, 0, 24, 24)
        self._anim   = random.uniform(0, math.pi * 2)
        self._update_rect()

    def _update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery  = int(self.y)

    def update(self, scroll_speed: float, dt: float):
        self.y    += scroll_speed * dt
        self._anim = (self._anim + dt * 4) % (2 * math.pi)
        self._update_rect()
        if self.y > WIN_H + 40:
            self.alive = False

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        r   = 10 + self.value   # bigger for higher value
        r   = min(r, 16)
        col_map = {1: C_COIN_GOLD, 3: (200, 200, 200), 5: (200, 180, 255), 10: (0, 220, 255)}
        col = col_map.get(self.value, C_COIN_GOLD)
        squeeze = int(3 * abs(math.sin(self._anim)))
        pygame.draw.ellipse(surface, col, (cx - r + squeeze, cy - r, (r - squeeze) * 2, r * 2))
        val_font = pygame.font.SysFont("monospace", 10, bold=True)
        t = val_font.render(str(self.value), True, (20, 20, 20))
        surface.blit(t, t.get_rect(center=(cx, cy)))


# ─────────────────────────────────────────────────────────────
# Power-Up
# ─────────────────────────────────────────────────────────────

class PowerUp:
    TYPES = ["nitro", "shield", "repair"]

    def __init__(self, lane: int, y_start: float = -40):
        self.lane   = lane
        self.x      = float(_lane_cx(lane))
        self.y      = y_start
        self.kind   = random.choice(self.TYPES)
        self.alive  = True
        self.age    = 0.0
        self.rect   = pygame.Rect(0, 0, 34, 34)
        self._anim  = random.uniform(0, math.pi * 2)
        self._update_rect()

    def _update_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery  = int(self.y)

    def update(self, scroll_speed: float, dt: float):
        self.y    += scroll_speed * dt
        self.age  += dt
        self._anim = (self._anim + dt * 2) % (2 * math.pi)
        self._update_rect()
        if self.y > WIN_H + 60 or self.age > POWERUP_LIFETIME:
            self.alive = False

    def draw(self, surface):
        cx, cy  = int(self.x), int(self.y)
        col     = C_POWERUP[self.kind]
        bob     = int(5 * math.sin(self._anim))
        # Glow
        for r in range(22, 12, -3):
            alpha_col = tuple(max(0, c - 80) for c in col)
            pygame.draw.circle(surface, alpha_col, (cx, cy + bob), r)
        # Body
        pygame.draw.circle(surface, col, (cx, cy + bob), 15)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy + bob), 15, 2)
        # Icon char
        icon = {"nitro": "⚡", "shield": "🛡", "repair": "🔧"}[self.kind]
        fnt = pygame.font.SysFont("segoeui", 14)
        t   = fnt.render(icon, True, (20, 20, 20))
        surface.blit(t, t.get_rect(center=(cx, cy + bob)))


# ─────────────────────────────────────────────────────────────
# Game Session
# ─────────────────────────────────────────────────────────────

class GameSession:
    """
    Manages all spawn timers, difficulty scaling, score, and
    distance tracking.  The main loop calls update() each frame.
    """

    TOTAL_DISTANCE = 5000   # metres to "finish"

    def __init__(self, settings: dict):
        diff_key       = settings.get("difficulty", "normal")
        dm             = DIFFICULTY.get(diff_key, DIFFICULTY["normal"])
        self.diff_key  = diff_key
        self.scroll_m  = dm[0]
        self.spawn_m   = dm[1]
        self.traffic_m = dm[2]

        # Scrolling road speed
        self.scroll_speed = BASE_SCROLL * self.scroll_m

        # Player
        self.player    = PlayerCar(settings.get("car_color", "red"))

        # Entities
        self.road       = Road()
        self.traffic    : list[TrafficCar] = []
        self.obstacles  : list[Obstacle]   = []
        self.coins      : list[Coin]       = []
        self.powerups   : list[PowerUp]    = []

        # Scoring
        self.score      = 0
        self.coins_count= 0
        self.distance   = 0.0    # metres

        # Power-up state
        self.active_pu  = None   # "nitro" | "shield" | "repair" | None
        self.pu_timer   = 0.0

        # Spawn timers (seconds)
        self._coin_t    = 0.0
        self._obs_t     = 0.0
        self._traffic_t = 0.0
        self._pu_t      = 0.0

        self._coin_int    = 1.4 / self.spawn_m
        self._obs_int     = 3.0 / self.spawn_m
        self._traffic_int = 2.2 / self.traffic_m
        self._pu_int      = 12.0

        self.game_over = False
        self.won       = False
        self.reason    = ""

    # ── Update ──────────────────────────────────────────────

    def update(self, dt: float, keys):
        if self.game_over:
            return

        # Input
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.player.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move_right()

        self.player.update(dt)

        # Effective scroll (nitro may boost it)
        scroll = self.player.effective_scroll(self.scroll_speed)

        # Distance (approximate: 1 pixel/sec ≈ 0.1 m)
        self.distance += scroll * dt * 0.1
        if self.distance >= self.TOTAL_DISTANCE:
            self.won = True
            self.game_over = True
            return

        # Road
        self.road.update(scroll, dt)

        # Difficulty scaling
        self._scale_difficulty()

        # Power-up timer
        if self.active_pu and self.active_pu not in ("shield",):
            self.pu_timer -= dt
            if self.pu_timer <= 0:
                self.active_pu = None
                self.pu_timer  = 0.0

        # ── Spawn ──
        self._coin_t    -= dt
        self._obs_t     -= dt
        self._traffic_t -= dt
        self._pu_t      -= dt

        if self._coin_t <= 0:
            self._spawn_coin()
            self._coin_t = self._coin_int

        if self._obs_t <= 0:
            self._spawn_obstacle()
            self._obs_t = self._obs_int

        if self._traffic_t <= 0:
            self._spawn_traffic()
            self._traffic_t = self._traffic_int

        if self._pu_t <= 0:
            self._spawn_powerup()
            self._pu_t = self._pu_int

        # ── Entity updates ──
        for e in self.traffic:  e.update(scroll, dt)
        for e in self.obstacles: e.update(scroll, dt)
        for e in self.coins:     e.update(scroll, dt)
        for e in self.powerups:  e.update(scroll, dt)

        # ── Collisions ──
        pr = self.player.rect

        # Coins
        for c in self.coins:
            if c.alive and rect_overlap(pr, c.rect, margin=4):
                c.alive = False
                self.coins_count += 1
                self.score += c.value * 10
                # Practice 11: increase scroll speed per coin collect
                self.scroll_speed = min(
                    self.scroll_speed + 2 * self.scroll_m,
                    BASE_SCROLL * self.scroll_m * 2.0
                )

        # Power-ups
        for p in self.powerups:
            if p.alive and rect_overlap(pr, p.rect, margin=4):
                p.alive = False
                self._apply_powerup(p.kind)

        # Obstacles
        for o in self.obstacles:
            if o.alive and rect_overlap(pr, o.rect, margin=8):
                o.alive = False
                if o.effect == "crash":
                    if self.player.hit():
                        self.game_over = True
                        self.reason    = f"Crashed into a {o.obs_type}!"
                        return
                elif o.effect == "slow":
                    self.scroll_speed = max(
                        BASE_SCROLL * self.scroll_m * 0.5,
                        self.scroll_speed * 0.7
                    )
                elif o.effect == "nitro":
                    self.player.activate_nitro(2.0)
                self.score += o.bonus

        # Traffic
        for t in self.traffic:
            if t.alive and rect_overlap(pr, t.rect, margin=8):
                t.alive = False
                if self.player.hit():
                    self.game_over = True
                    self.reason    = "Crashed into traffic!"
                    return

        # Prune dead entities
        self.traffic   = [e for e in self.traffic   if e.alive]
        self.obstacles = [e for e in self.obstacles if e.alive]
        self.coins     = [e for e in self.coins     if e.alive]
        self.powerups  = [e for e in self.powerups  if e.alive]

        # Score from distance
        self.score = int(
            self.coins_count * 10 +
            self.distance * 0.5
        )

    # ── Spawning ────────────────────────────────────────────

    def _safe_lane(self, exclude: set = None) -> int:
        """Pick a lane that is not the player's and not in exclude."""
        exclude = exclude or set()
        exclude.add(self.player.lane)
        options = [l for l in range(LANE_COUNT) if l not in exclude]
        return random.choice(options) if options else random.randint(0, LANE_COUNT - 1)

    def _spawn_coin(self):
        lane = random.randint(0, LANE_COUNT - 1)
        self.coins.append(Coin(lane))

    def _spawn_obstacle(self):
        # Lane hazards: pick 1-2 lanes to block, leave others safe
        blocked_lanes = random.sample(range(LANE_COUNT),
                                      k=min(2, LANE_COUNT - 1))
        # Exclude player's current lane for fairness
        if self.player.lane in blocked_lanes and len(blocked_lanes) > 1:
            blocked_lanes.remove(self.player.lane)

        weights = ["barrier"] * 2 + ["oil"] * 3 + ["pothole"] * 2 + \
                  ["speedbump"] * 2 + ["nitrostrip"] * 1
        obs_type = random.choice(weights)

        for lane in blocked_lanes[:1]:   # one obstacle per spawn event
            self.obstacles.append(Obstacle(obs_type, lane))

    def _spawn_traffic(self):
        lane = self._safe_lane()
        # Safe spawn: no other traffic within 200 px in that lane
        for t in self.traffic:
            if t.lane == lane and t.y < 200:
                return
        self.traffic.append(TrafficCar(lane))

    def _spawn_powerup(self):
        if len(self.powerups) >= 2:
            return
        lane = random.randint(0, LANE_COUNT - 1)
        self.powerups.append(PowerUp(lane))

    # ── Power-up application ────────────────────────────────

    def _apply_powerup(self, kind: str):
        if kind == "nitro":
            self.player.activate_nitro(4.0)
            self.active_pu = "nitro"
            self.pu_timer  = 4.0
        elif kind == "shield":
            self.player.activate_shield()
            self.active_pu = "shield"
            self.pu_timer  = 0.0   # no countdown; lasts until hit
        elif kind == "repair":
            # Clears the nearest obstacle ahead of the player
            self.obstacles = [o for o in self.obstacles
                               if not (o.lane == self.player.lane and o.y < self.player.y)]
            self.active_pu = None  # instant effect, no display needed

    # ── Difficulty scaling ───────────────────────────────────

    def _scale_difficulty(self):
        progress = self.distance / self.TOTAL_DISTANCE
        # Ramp intervals tighter as the track progresses
        self._traffic_int = max(0.8, (2.2 - progress * 1.2) / self.traffic_m)
        self._obs_int     = max(1.2, (3.0 - progress * 1.5) / self.spawn_m)

    # ── Draw ────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        self.road.draw(surface)
        for e in self.coins:     e.draw(surface)
        for e in self.powerups:  e.draw(surface)
        for e in self.obstacles: e.draw(surface)
        for e in self.traffic:   e.draw(surface)
        self.player.draw(surface)

    # ── HUD data dict ────────────────────────────────────────

    def hud_data(self) -> dict:
        pu_timer = self.pu_timer if self.active_pu == "nitro" else 0
        return {
            "score":        self.score,
            "coins":        self.coins_count,
            "distance":     int(self.distance),
            "total_dist":   self.TOTAL_DISTANCE,
            "speed":        int(self.scroll_speed * 0.36),  # rough km/h
            "powerup_name": self.active_pu,
            "powerup_timer":pu_timer,
            "shield_active":self.player.shield,
            "nitro_active": self.player.nitro,
            "difficulty":   self.diff_key,
        }