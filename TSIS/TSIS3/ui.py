"""
ui.py — Screen renderers and UI helpers for the Racer game (TSIS 3)

Screens implemented:
  draw_main_menu(surface, font_lg, font_sm, hovered)
  draw_settings(surface, fonts, settings, hovered)
  draw_leaderboard(surface, fonts, entries, hovered)
  draw_game_over(surface, fonts, stats, hovered)
  draw_hud(surface, fonts, hud_data)
  draw_username_entry(surface, fonts, current_text)

All drawing is pure Pygame — no external UI libraries.
"""

import pygame

# ─────────────────────────────────────────────────────────────
# Palette
# ─────────────────────────────────────────────────────────────

C_BG       = (15,  15,  25)
C_PANEL    = (28,  28,  45)
C_ACCENT   = (255, 200,  40)
C_RED      = (220,  50,  50)
C_GREEN    = ( 50, 210,  90)
C_BLUE     = ( 60, 140, 255)
C_WHITE    = (240, 240, 250)
C_GREY     = (120, 120, 140)
C_DARK     = ( 10,  10,  18)
C_NITRO    = (  0, 220, 255)
C_SHIELD   = ( 80, 180, 255)
C_REPAIR   = ( 50, 220, 100)

CAR_COLORS = {
    "red":    (220,  50,  50),
    "blue":   ( 50, 100, 220),
    "green":  ( 40, 180,  60),
    "yellow": (240, 200,   0),
    "purple": (160,  60, 220),
}

# ─────────────────────────────────────────────────────────────
# Generic helpers
# ─────────────────────────────────────────────────────────────

def _panel(surface, rect, alpha=210, radius=12):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    s.fill((*C_PANEL, alpha))
    pygame.draw.rect(s, (*C_ACCENT, 80), s.get_rect(), 2, border_radius=radius)
    surface.blit(s, rect.topleft)


def _btn(surface, font, rect, label, active=False, hovered=False, color=None):
    bg = color or (C_ACCENT if active else (C_BLUE if hovered else C_PANEL))
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    border = C_ACCENT if active else (C_WHITE if hovered else C_GREY)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)
    txt = font.render(label, True, C_DARK if (active or hovered) else C_WHITE)
    surface.blit(txt, txt.get_rect(center=rect.center))
    return rect


def _title(surface, font, text, y, color=C_ACCENT):
    t = font.render(text, True, color)
    surface.blit(t, t.get_rect(centerx=surface.get_width() // 2, y=y))


def _text(surface, font, text, pos, color=C_WHITE, center=False):
    t = font.render(text, True, color)
    r = t.get_rect(center=pos) if center else (pos[0], pos[1])
    surface.blit(t, r)


# ─────────────────────────────────────────────────────────────
# Username entry
# ─────────────────────────────────────────────────────────────

def draw_username_entry(surface, fonts, current_text):
    """Returns dict of button rects: {'ok': rect}"""
    W, H = surface.get_size()
    surface.fill(C_BG)
    _title(surface, fonts["lg"], "ENTER YOUR NAME", H // 2 - 100)

    box = pygame.Rect(W // 2 - 200, H // 2 - 30, 400, 56)
    pygame.draw.rect(surface, C_PANEL, box, border_radius=8)
    pygame.draw.rect(surface, C_ACCENT, box, 2, border_radius=8)
    display = current_text + ("|" if (pygame.time.get_ticks() // 500) % 2 == 0 else " ")
    _text(surface, fonts["md"], display, (box.x + 12, box.y + 12))

    ok_rect = pygame.Rect(W // 2 - 80, H // 2 + 50, 160, 44)
    _btn(surface, fonts["sm"], ok_rect, "START  ▶", hovered=True)
    _text(surface, fonts["sm"], "Press Enter or click START", (W // 2, H // 2 + 115), C_GREY, center=True)
    return {"ok": ok_rect}


# ─────────────────────────────────────────────────────────────
# Main Menu
# ─────────────────────────────────────────────────────────────

def draw_main_menu(surface, fonts, hovered=""):
    """Returns dict of button rects."""
    W, H = surface.get_size()
    surface.fill(C_BG)

    # Road decoration
    for i in range(6):
        x = W // 2 - 160 + i * 64
        pygame.draw.rect(surface, (40, 40, 60), (x, 0, 40, H))

    # Title
    shadow = fonts["xl"].render("ROAD  RACER", True, (0, 0, 0))
    surface.blit(shadow, shadow.get_rect(centerx=W // 2 + 3, y=83))
    _title(surface, fonts["xl"], "ROAD  RACER", 80, C_ACCENT)
    _title(surface, fonts["sm"], "TSIS 3  —  Extended Edition", 148, C_GREY)

    labels = ["▶  PLAY", "🏆  LEADERBOARD", "⚙  SETTINGS", "✕  QUIT"]
    keys   = ["play", "leaderboard", "settings", "quit"]
    rects  = {}
    y0     = 220
    for key, label in zip(keys, labels):
        r = pygame.Rect(W // 2 - 160, y0, 320, 52)
        _btn(surface, fonts["md"], r, label, hovered=(hovered == key))
        rects[key] = r
        y0 += 66

    _text(surface, fonts["sm"], "Use arrow keys or mouse to navigate",
          (W // 2, H - 30), C_GREY, center=True)
    return rects


# ─────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────

def draw_settings(surface, fonts, settings, hovered=""):
    """Returns dict of clickable rects."""
    W, H = surface.get_size()
    surface.fill(C_BG)
    _title(surface, fonts["lg"], "⚙  SETTINGS", 40)

    rects = {}
    panel = pygame.Rect(W // 2 - 260, 100, 520, 420)
    _panel(surface, panel)

    y = 120

    # Sound toggle
    _text(surface, fonts["md"], "Sound", (panel.x + 30, y))
    for i, (val, lbl) in enumerate([("on", "ON"), ("off", "OFF")]):
        r = pygame.Rect(panel.x + 260 + i * 90, y - 4, 80, 36)
        active = (settings.get("sound") is True and val == "on") or \
                 (settings.get("sound") is False and val == "off")
        _btn(surface, fonts["sm"], r, lbl, active=active, hovered=(hovered == f"sound_{val}"))
        rects[f"sound_{val}"] = r
    y += 70

    # Car color
    _text(surface, fonts["md"], "Car Color", (panel.x + 30, y))
    for i, col_key in enumerate(CAR_COLORS):
        r = pygame.Rect(panel.x + 240 + i * 52, y - 6, 44, 44)
        active = settings.get("car_color") == col_key
        pygame.draw.rect(surface, CAR_COLORS[col_key], r, border_radius=6)
        if active:
            pygame.draw.rect(surface, C_ACCENT, r, 3, border_radius=6)
        else:
            pygame.draw.rect(surface, C_GREY, r, 1, border_radius=6)
        rects[f"color_{col_key}"] = r
    y += 70

    # Difficulty
    _text(surface, fonts["md"], "Difficulty", (panel.x + 30, y))
    for i, diff in enumerate(["easy", "normal", "hard"]):
        r = pygame.Rect(panel.x + 240 + i * 96, y - 4, 86, 36)
        active = settings.get("difficulty") == diff
        col = C_GREEN if diff == "easy" else (C_ACCENT if diff == "normal" else C_RED)
        _btn(surface, fonts["sm"], r, diff.capitalize(), active=active,
             hovered=(hovered == f"diff_{diff}"), color=col if active else None)
        rects[f"diff_{diff}"] = r
    y += 90

    # Save / Back
    save_r = pygame.Rect(W // 2 - 180, y + 20, 160, 46)
    back_r = pygame.Rect(W // 2 + 20,  y + 20, 160, 46)
    _btn(surface, fonts["md"], save_r, "💾  Save", hovered=(hovered == "save"))
    _btn(surface, fonts["md"], back_r, "←  Back",  hovered=(hovered == "back"))
    rects["save"] = save_r
    rects["back"] = back_r

    return rects


# ─────────────────────────────────────────────────────────────
# Leaderboard
# ─────────────────────────────────────────────────────────────

def draw_leaderboard(surface, fonts, entries, hovered=""):
    W, H = surface.get_size()
    surface.fill(C_BG)
    _title(surface, fonts["lg"], "🏆  LEADERBOARD", 30)

    panel = pygame.Rect(W // 2 - 340, 90, 680, 440)
    _panel(surface, panel, radius=10)

    # Header
    hx = panel.x + 20
    hy = panel.y + 14
    for label, xoff in [("#", 0), ("Name", 50), ("Score", 270), ("Distance", 380), ("Date", 510)]:
        _text(surface, fonts["sm"], label, (hx + xoff, hy), C_ACCENT)

    pygame.draw.line(surface, C_ACCENT, (panel.x + 10, hy + 26), (panel.right - 10, hy + 26), 1)

    if not entries:
        _text(surface, fonts["md"], "No scores yet — be the first!", (W // 2, panel.centery), C_GREY, center=True)
    else:
        for i, e in enumerate(entries[:10]):
            ry   = hy + 42 + i * 36
            row_col = C_ACCENT if i == 0 else (C_WHITE if i < 3 else C_GREY)
            medal = ["🥇", "🥈", "🥉"]
            rank_str = medal[i] if i < 3 else str(e.get("rank", i + 1))
            _text(surface, fonts["sm"], rank_str,                          (hx,       ry), row_col)
            _text(surface, fonts["sm"], e.get("name","?")[:18],            (hx + 50,  ry), row_col)
            _text(surface, fonts["sm"], f"{e.get('score',0):,}",           (hx + 270, ry), row_col)
            _text(surface, fonts["sm"], f"{e.get('distance',0):,} m",      (hx + 380, ry), row_col)
            _text(surface, fonts["sm"], e.get("date",""),                  (hx + 510, ry), C_GREY)

    back_r = pygame.Rect(W // 2 - 80, panel.bottom + 24, 160, 46)
    _btn(surface, fonts["md"], back_r, "←  Back", hovered=(hovered == "back"))
    return {"back": back_r}


# ─────────────────────────────────────────────────────────────
# Game Over
# ─────────────────────────────────────────────────────────────

def draw_game_over(surface, fonts, stats, hovered=""):
    """
    stats: {score, distance, coins, username, reason}
    Returns dict of rects: retry, menu
    """
    W, H = surface.get_size()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((10, 10, 20, 200))
    surface.blit(overlay, (0, 0))

    panel = pygame.Rect(W // 2 - 240, H // 2 - 200, 480, 400)
    _panel(surface, panel, alpha=240)

    _title(surface, fonts["lg"], "GAME  OVER", panel.y + 20, C_RED)
    _text(surface, fonts["sm"], f"Driver: {stats.get('username','?')}",
          (W // 2, panel.y + 76), C_GREY, center=True)

    reason = stats.get("reason", "")
    if reason:
        _text(surface, fonts["sm"], reason, (W // 2, panel.y + 104), C_RED, center=True)

    rows = [
        ("Score",    f"{stats.get('score',0):,}",     C_ACCENT),
        ("Distance", f"{stats.get('distance',0):,} m", C_WHITE),
        ("Coins",    str(stats.get('coins', 0)),        C_ACCENT),
    ]
    y = panel.y + 140
    for label, val, col in rows:
        _text(surface, fonts["md"], label, (W // 2 - 140, y), C_GREY)
        _text(surface, fonts["md"], val,   (W // 2 + 60,  y), col)
        y += 48

    retry_r = pygame.Rect(W // 2 - 210, panel.bottom - 72, 190, 46)
    menu_r  = pygame.Rect(W // 2 + 20,  panel.bottom - 72, 190, 46)
    _btn(surface, fonts["md"], retry_r, "↺  Retry",     hovered=(hovered == "retry"))
    _btn(surface, fonts["md"], menu_r,  "⌂  Main Menu", hovered=(hovered == "menu"))
    return {"retry": retry_r, "menu": menu_r}


# ─────────────────────────────────────────────────────────────
# HUD (in-game overlay)
# ─────────────────────────────────────────────────────────────

def draw_hud(surface, fonts, hud):
    """
    hud keys:
      score, coins, distance, total_dist, speed,
      powerup_name, powerup_timer,
      shield_active, nitro_active,
      lives, difficulty
    """
    W, H = surface.get_size()
    sm    = fonts["sm"]
    md    = fonts["md"]

    # Top-left panel
    panel = pygame.Rect(8, 8, 200, 116)
    _panel(surface, panel, alpha=180, radius=8)
    _text(surface, sm, f"Score    {hud.get('score',0):>8,}", (panel.x + 10, panel.y + 8),  C_ACCENT)
    _text(surface, sm, f"Coins    {hud.get('coins',0):>8}",  (panel.x + 10, panel.y + 34), C_WHITE)
    _text(surface, sm, f"Speed    {hud.get('speed',0):>6} km/h", (panel.x + 10, panel.y + 60), C_WHITE)
    diff_col = {
        "easy": C_GREEN, "normal": C_ACCENT, "hard": C_RED
    }.get(hud.get("difficulty", "normal"), C_WHITE)
    _text(surface, sm, hud.get("difficulty","").upper(), (panel.x + 10, panel.y + 88), diff_col)

    # Top-right: distance meter
    dist     = hud.get("distance", 0)
    total    = hud.get("total_dist", 5000)
    dist_str = f"{dist:,} / {total:,} m"
    dp = pygame.Rect(W - 218, 8, 210, 50)
    _panel(surface, dp, alpha=180, radius=8)
    _text(surface, sm, "Distance", (dp.x + 10, dp.y + 6), C_GREY)
    _text(surface, sm, dist_str,   (dp.x + 10, dp.y + 28), C_WHITE)

    # Progress bar
    bar_r = pygame.Rect(W - 218, 62, 210, 10)
    pygame.draw.rect(surface, C_DARK, bar_r, border_radius=5)
    fill_w = int(bar_r.width * min(dist / max(total, 1), 1.0))
    pygame.draw.rect(surface, C_GREEN, (*bar_r.topleft, fill_w, bar_r.height), border_radius=5)

    # Active power-up badge
    pname = hud.get("powerup_name")
    ptimer = hud.get("powerup_timer", 0)
    if pname:
        pcol = {"nitro": C_NITRO, "shield": C_SHIELD, "repair": C_REPAIR}.get(pname, C_ACCENT)
        pu_panel = pygame.Rect(W // 2 - 100, 8, 200, 52)
        _panel(surface, pu_panel, alpha=200, radius=8)
        pygame.draw.rect(surface, pcol, pu_panel, 2, border_radius=8)
        icon = {"nitro": "⚡", "shield": "🛡", "repair": "🔧"}.get(pname, "★")
        _text(surface, md, f"{icon} {pname.upper()}", (W // 2, pu_panel.y + 8),  pcol, center=True)
        if ptimer > 0:
            _text(surface, sm, f"{ptimer:.1f}s", (W // 2, pu_panel.y + 32), C_WHITE, center=True)

    # Shield icon (persistent)
    if hud.get("shield_active"):
        _text(surface, md, "🛡 SHIELD", (W - 218, 82), C_SHIELD)


# ─────────────────────────────────────────────────────────────
# Pause overlay
# ─────────────────────────────────────────────────────────────

def draw_pause(surface, fonts):
    W, H = surface.get_size()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))
    _title(surface, fonts["xl"], "PAUSED", H // 2 - 40)
    _text(surface, fonts["sm"], "Press P or Esc to resume",
          (W // 2, H // 2 + 30), C_GREY, center=True)