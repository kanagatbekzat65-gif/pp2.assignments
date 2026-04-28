import pygame
import sys
import math
import datetime
import os

WIDTH, HEIGHT = 600, 600
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 60


def get_time():
    now = datetime.datetime.now()
    return now.hour % 12, now.minute, now.second


def draw_arm(surface, angle_deg, length=160, color=(30, 30, 30), thickness=8):
    """Draw a clock hand from center at given angle."""
    a = math.radians(angle_deg - 90)
    ex = int(CENTER[0] + length * math.cos(a))
    ey = int(CENTER[1] + length * math.sin(a))
    
    pygame.draw.line(surface, (80, 80, 80),
                     (CENTER[0]+2, CENTER[1]+2), (ex+2, ey+2), thickness)
    
    pygame.draw.line(surface, color, CENTER, (ex, ey), thickness)
    
    pygame.draw.circle(surface, color, (ex, ey), thickness // 2 + 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mickey's Clock")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("monospace", 28, bold=True)

    
    img_path = os.path.join(os.path.dirname(__file__), "images", "mickey_clock.png")
    if os.path.exists(img_path):
        bg = pygame.image.load(img_path).convert_alpha()
        bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    else:
        # Fallback: plain white with message
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill((255, 255, 255))
        err_font = pygame.font.SysFont("monospace", 16)
        msg = err_font.render("Put mickey_clock.png in images/ folder", True, (200, 0, 0))
        bg.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2)))

    UPDATE = pygame.USEREVENT + 1
    pygame.time.set_timer(UPDATE, 1000)
    h, m, s = get_time()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
            elif event.type == UPDATE:
                h, m, s = get_time()

        screen.blit(bg, (0, 0))

        # Hour hand (short, dark)
        hour_angle = (h * 30) + (m * 0.5)
        draw_arm(screen, hour_angle, length=100, color=(40, 40, 40), thickness=10)

        # Minute hand = right arm (medium, dark)
        min_angle = m * 6 + s * 0.1
        draw_arm(screen, min_angle, length=150, color=(30, 30, 30), thickness=8)

        # Second hand = left arm (thin, red)
        sec_angle = s * 6
        draw_arm(screen, sec_angle, length=160, color=(200, 30, 30), thickness=4)

        # Center pin
        pygame.draw.circle(screen, (20, 20, 20), CENTER, 10)
        pygame.draw.circle(screen, (255, 255, 255), CENTER, 5)

        # Digital time
        t_surf = font.render(f"{h:02d}:{m:02d}:{s:02d}", True, (40, 20, 10))
        pygame.draw.rect(screen, (255, 240, 200),
                         t_surf.get_rect(center=(WIDTH//2, HEIGHT-30)).inflate(20, 10),
                         border_radius=8)
        screen.blit(t_surf, t_surf.get_rect(center=(WIDTH//2, HEIGHT-30)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
