# Road Racer Extended — TSIS 3

Extended arcade racer building on Practice 10 and Practice 11, using only Pygame's built-in capabilities.

## Repository Structure

```
TSIS3/
├── main.py          # Game loop + screen state machine
├── racer.py         # All game objects: car, traffic, obstacles, power-ups, road
├── ui.py            # All screen renderers (menu, settings, leaderboard, HUD, game-over)
├── persistence.py   # Load/save leaderboard.json and settings.json
├── settings.json    # Saved player preferences (auto-generated)
├── leaderboard.json # Persistent top-10 scores (auto-generated)
└── assets/          # Reserved for images/sounds if added
```

## Features Added (TSIS 3)

| Feature | Where |
|---|---|
| Lane hazards: oil, barriers, potholes, speed bumps, nitro strips | `racer.py → Obstacle` |
| Dynamic traffic cars with safe-spawn logic | `racer.py → TrafficCar` |
| Three power-ups: Nitro, Shield, Repair | `racer.py → PowerUp` |
| Difficulty scaling (intervals shrink as distance grows) | `racer.py → GameSession._scale_difficulty` |
| Distance meter with progress bar | `ui.py → draw_hud` |
| Persistent leaderboard (top 10) in `leaderboard.json` | `persistence.py` |
| Username entry screen | `ui.py → draw_username_entry` |
| Settings: sound toggle, car color, difficulty | `ui.py → draw_settings` |
| Save/load settings via `settings.json` | `persistence.py` |
| Main Menu, Game Over, Leaderboard, Settings screens | `ui.py`, `main.py` |
| Full state machine (menu→username→game→pause→gameover) | `main.py` |

> **Not re-implemented:** Player car movement, lane-based road scrolling, random coin spawning, coin counter, weighted coins, increasing enemy speed — all from Practice 10–11.

## Setup

```bash
pip install pygame
python main.py
```

Requires Python 3.10+ and Pygame 2.x.

## Controls

| Action | Key |
|---|---|
| Move left | `←` or `A` |
| Move right | `→` or `D` |
| Pause / Resume | `P` or `Esc` |
| Navigate menus | Mouse click |

## Power-Ups

| Power-Up | Icon | Effect | Duration |
|---|---|---|---|
| Nitro | ⚡ | 1.85× scroll speed | 4 seconds |
| Shield | 🛡 | Absorbs one collision | Until hit |
| Repair | 🔧 | Clears obstacles in player's lane | Instant |

## Scoring

Score = `(coins × 10) + (distance × 0.5)`

Higher difficulty multiplies spawn rates and traffic density. Finishing the 5,000 m course adds a completion bonus to the leaderboard entry.

## Architecture

### `racer.py`

- **`Road`** — scrolling road with animated kerb stripes, dashed lane markings, and grass shoulders
- **`PlayerCar`** — smooth lateral movement (lerps to target lane), nitro flame rendering, shield ring overlay
- **`TrafficCar`** — downward-scrolling enemy vehicles in random lanes, pruned when off-screen
- **`Obstacle`** — five types with distinct visuals and effects (`crash`, `slow`, `nitro`)
- **`Coin`** — weighted value selection from Practice 11; spinning ellipse animation
- **`PowerUp`** — BFS-safe spawning; bobbing glow animation; 8-second lifetime
- **`GameSession`** — master state: spawn timers, difficulty ramp, collision resolution, score/distance tracking

### `ui.py`

All rendering is pure Pygame. A shared `_panel()` helper draws translucent dark panels. `_btn()` handles hover/active states. `draw_hud()` renders a left info panel, right distance meter with progress bar, and a center power-up badge.

### `main.py`

Seven-state machine: `MENU → USERNAME → GAME → PAUSE → GAMEOVER → LEADERBOARD / SETTINGS`. Each state's draw function returns a `{key: Rect}` dict; `_hit()` maps mouse clicks back to action strings.
