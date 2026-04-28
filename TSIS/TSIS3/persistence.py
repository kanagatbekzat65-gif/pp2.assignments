"""
persistence.py — Save / load leaderboard and settings (TSIS 3)
"""

import json
import os
from datetime import datetime

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"
MAX_ENTRIES      = 10

# ─────────────────────────────────────────────────────────────
# Default settings
# ─────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "sound":       True,
    "car_color":   "red",       # red | blue | green | yellow | purple
    "difficulty":  "normal",    # easy | normal | hard
    "username":    "",
}

# ─────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge so new keys from DEFAULT are always present
            merged = {**DEFAULT_SETTINGS, **data}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError as e:
        print(f"[persistence] Could not save settings: {e}")


# ─────────────────────────────────────────────────────────────
# Leaderboard
# ─────────────────────────────────────────────────────────────

def load_leaderboard() -> list[dict]:
    """Return list of entry dicts sorted by score desc."""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_leaderboard(entries: list[dict]):
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except OSError as e:
        print(f"[persistence] Could not save leaderboard: {e}")


def add_entry(username: str, score: int, distance: int, coins: int):
    """Add a new score entry and keep only the top MAX_ENTRIES."""
    entries = load_leaderboard()
    entries.append({
        "rank":     0,
        "name":     username or "Anonymous",
        "score":    score,
        "distance": distance,
        "coins":    coins,
        "date":     datetime.now().strftime("%Y-%m-%d"),
    })
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:MAX_ENTRIES]
    for i, e in enumerate(entries):
        e["rank"] = i + 1
    save_leaderboard(entries)
    return entries