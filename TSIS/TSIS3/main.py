"""
main.py — Racer Game Extended (TSIS 3)
=======================================
Run:  python main.py

Requirements:
    pip install pygame

Controls (in-game):
    ← / A       — move left
    → / D       — move right
    P / Esc     — pause
    Ctrl+S      — (no-op placeholder; no save in-game needed)
"""

import sys
import pygame
from persistence import load_settings, save_settings, load_leaderboard, add_entry
from racer import GameSession, WIN_W, WIN_H
from ui import (
    draw_main_menu, draw_settings, draw_leaderboard,
    draw_game_over, draw_hud, draw_pause, draw_username_entry,
    CAR_COLORS,
)

# ─────────────────────────────────────────────────────────────
# Font cache
# ─────────────────────────────────────────────────────────────

def _make_fonts():
    return {
        "xl": pygame.font.SysFont("impact",    52, bold=False),
        "lg": pygame.font.SysFont("impact",    38, bold=False),
        "md": pygame.font.SysFont("segoeui",   22, bold=True),
        "sm": pygame.font.SysFont("segoeui",   16, bold=False),
    }


# ─────────────────────────────────────────────────────────────
# Screen states
# ─────────────────────────────────────────────────────────────

MENU        = "menu"
USERNAME    = "username"
GAME        = "game"
PAUSE       = "pause"
GAMEOVER    = "gameover"
LEADERBOARD = "leaderboard"
SETTINGS    = "settings"


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Road Racer — TSIS 3")
    screen  = pygame.display.set_mode((WIN_W, WIN_H))
    clock   = pygame.time.Clock()
    fonts   = _make_fonts()

    settings    = load_settings()
    leaderboard = load_leaderboard()

    state        = MENU
    session      = None
    hovered      = ""
    username_buf = settings.get("username", "")
    game_stats   = {}

    # Button rects returned by ui drawers each frame
    btn_rects = {}

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse = pygame.mouse.get_pos()

        # ── Events ──────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ── Username entry ──
            if state == USERNAME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if username_buf.strip():
                            settings["username"] = username_buf.strip()
                            save_settings(settings)
                            session = GameSession(settings)
                            state   = GAME
                    elif event.key == pygame.K_BACKSPACE:
                        username_buf = username_buf[:-1]
                    elif event.unicode and event.unicode.isprintable() and len(username_buf) < 20:
                        username_buf += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_rects.get("ok") and btn_rects["ok"].collidepoint(mouse):
                        if username_buf.strip():
                            settings["username"] = username_buf.strip()
                            save_settings(settings)
                            session = GameSession(settings)
                            state   = GAME

            # ── In-game ──
            elif state == GAME:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        state = PAUSE

            # ── Pause ──
            elif state == PAUSE:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        state = GAME

            # ── Settings key events ──
            elif state == SETTINGS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = MENU

            # ── Mouse clicks on buttons ──
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = _hit(btn_rects, mouse)

                if state == MENU:
                    if clicked == "play":
                        state = USERNAME
                    elif clicked == "leaderboard":
                        leaderboard = load_leaderboard()
                        state       = LEADERBOARD
                    elif clicked == "settings":
                        state = SETTINGS
                    elif clicked == "quit":
                        running = False

                elif state == LEADERBOARD:
                    if clicked == "back":
                        state = MENU

                elif state == SETTINGS:
                    if clicked == "sound_on":
                        settings["sound"] = True
                    elif clicked == "sound_off":
                        settings["sound"] = False
                    elif clicked and clicked.startswith("color_"):
                        settings["car_color"] = clicked[6:]
                    elif clicked and clicked.startswith("diff_"):
                        settings["difficulty"] = clicked[5:]
                    elif clicked == "save":
                        save_settings(settings)
                        state = MENU
                    elif clicked == "back":
                        state = MENU

                elif state == GAMEOVER:
                    if clicked == "retry":
                        session = GameSession(settings)
                        state   = GAME
                    elif clicked == "menu":
                        state = MENU

        # ── Update ──────────────────────────────────────────
        if state == GAME and session:
            keys = pygame.key.get_pressed()
            session.update(dt, keys)

            if session.game_over:
                # Record to leaderboard
                leaderboard = add_entry(
                    settings.get("username", "Anonymous"),
                    session.score,
                    int(session.distance),
                    session.coins_count,
                )
                game_stats = {
                    "score":    session.score,
                    "distance": int(session.distance),
                    "coins":    session.coins_count,
                    "username": settings.get("username", "?"),
                    "reason":   session.reason if not session.won else "🏁 Finished!",
                }
                state = GAMEOVER

        # ── Hover detection ──────────────────────────────────
        hovered = _hit(btn_rects, mouse)

        # ── Draw ────────────────────────────────────────────
        if state == MENU:
            btn_rects = draw_main_menu(screen, fonts, hovered)

        elif state == USERNAME:
            btn_rects = draw_username_entry(screen, fonts, username_buf)

        elif state == GAME and session:
            session.draw(screen)
            draw_hud(screen, fonts, session.hud_data())
            btn_rects = {}

        elif state == PAUSE and session:
            session.draw(screen)
            draw_hud(screen, fonts, session.hud_data())
            draw_pause(screen, fonts)
            btn_rects = {}

        elif state == GAMEOVER:
            # Draw last game frame underneath
            if session:
                session.draw(screen)
            btn_rects = draw_game_over(screen, fonts, game_stats, hovered)

        elif state == LEADERBOARD:
            btn_rects = draw_leaderboard(screen, fonts, leaderboard, hovered)

        elif state == SETTINGS:
            btn_rects = draw_settings(screen, fonts, settings, hovered)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def _hit(rects: dict, pos) -> str | None:
    for key, rect in rects.items():
        if rect.collidepoint(pos):
            return key
    return None


if __name__ == "__main__":
    main()