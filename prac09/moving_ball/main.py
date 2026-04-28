"""
main.py - Moving Ball Game
Control a red ball with arrow keys.
The ball cannot leave the screen boundaries.

Controls:
  ↑ ↓ ← →  — Move ball (20 pixels per press)
  ESC / Q   — Quit
"""

import pygame
import sys
from ball import Ball


SCREEN_WIDTH = 600
SCREEN_HEIGHT = 500
FPS = 60


BG_COLOR = (255, 255, 255)          
GRID_COLOR = (235, 235, 235)        
SHADOW_COLOR = (200, 30, 30, 80)    
BORDER_COLOR = (200, 200, 200)
HUD_BG = (245, 245, 245)
HUD_TEXT = (60, 60, 60)
ARROW_COLOR = (180, 180, 180)
ARROW_ACTIVE = (220, 40, 40)


def draw_grid(surface, cell_size=20):
    """Draw a light grid to make movement more visible."""
    for x in range(0, SCREEN_WIDTH, cell_size):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, cell_size):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))


def draw_boundary(surface):
    """Draw a visible boundary rectangle."""
    pygame.draw.rect(surface, BORDER_COLOR, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)


def draw_arrow_hud(surface, font, keys_pressed):
    """
    Draw on-screen arrow key indicators showing which keys are pressed.
    Gives visual feedback for the control scheme.
    """
    cx, cy = SCREEN_WIDTH - 70, SCREEN_HEIGHT - 70
    arrows = [
        ("↑", (cx,      cy - 22), pygame.K_UP),
        ("↓", (cx,      cy + 22), pygame.K_DOWN),
        ("←", (cx - 22, cy),      pygame.K_LEFT),
        ("→", (cx + 22, cy),      pygame.K_RIGHT),
    ]
    for symbol, (ax, ay), key in arrows:
        color = ARROW_ACTIVE if keys_pressed[key] else ARROW_COLOR
        text = font.render(symbol, True, color)
        surface.blit(text, text.get_rect(center=(ax, ay)))


def draw_hud(surface, ball, font_small):
    """Draw position info at the top of the screen."""
    pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_WIDTH, 28))
    pygame.draw.line(surface, BORDER_COLOR, (0, 28), (SCREEN_WIDTH, 28))
    info = f"Position: {ball.get_position_string()}   |   Use Arrow Keys to move   |   ESC to quit"
    text = font_small.render(info, True, HUD_TEXT)
    surface.blit(text, (10, 7))


def draw_ball(surface, ball):
    """Draw the ball with a subtle shadow for depth."""
    cx, cy = ball.get_center()
    r = Ball.RADIUS

    
    shadow_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (180, 30, 30, 60), (r + 3, r + 3), r)
    surface.blit(shadow_surf, (cx - r - 3 + 4, cy - r - 3 + 4))

    
    pygame.draw.circle(surface, Ball.COLOR, (cx, cy), r)

    
    pygame.draw.circle(surface, Ball.OUTLINE_COLOR, (cx, cy), r, 2)

    
    highlight_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(highlight_surf, (255, 255, 255, 60),
                       (int(r * 0.65), int(r * 0.6)), int(r * 0.35))
    surface.blit(highlight_surf, (cx - r, cy - r))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("🔴 Moving Ball Game")
    clock = pygame.time.Clock()

    font_small = pygame.font.SysFont("monospace", 13)
    font_arrow = pygame.font.SysFont("monospace", 20, bold=True)

    ball = Ball(SCREEN_WIDTH, SCREEN_HEIGHT - 28)  
    ball.y += 28 

    running = True
    while running:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                
                elif event.key == pygame.K_UP:
                    ball.move_up()
                elif event.key == pygame.K_DOWN:
                    ball.move_down()
                elif event.key == pygame.K_LEFT:
                    ball.move_left()
                elif event.key == pygame.K_RIGHT:
                    ball.move_right()

        
        screen.fill(BG_COLOR)
        draw_grid(screen)
        draw_boundary(screen)
        draw_ball(screen, ball)
        draw_hud(screen, ball, font_small)

        
        keys = pygame.key.get_pressed()
        draw_arrow_hud(screen, font_arrow, keys)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
