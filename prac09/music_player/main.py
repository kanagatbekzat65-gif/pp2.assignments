"""
main.py - Music Player Application
Interactive music player with keyboard controls.

Controls:
  P - Play / Pause toggle
  S - Stop
  N - Next track
  B - Previous (Back) track
  Q - Quit
"""

import pygame
import sys
import os
import math
from player import MusicPlayer


SCREEN_WIDTH = 520
SCREEN_HEIGHT = 400
FPS = 60


BG_COLOR = (18, 18, 28)
PANEL_COLOR = (28, 28, 42)
ACCENT = (255, 80, 120)        
ACCENT2 = (80, 200, 255)       
TEXT_COLOR = (240, 235, 255)
DIM_TEXT = (120, 115, 140)
TRACK_BG = (38, 38, 55)
VIZ_COLOR = (255, 80, 120)


def draw_rounded_rect(surface, color, rect, radius=12):
    """Draw a rounded rectangle."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_progress_bar(surface, x, y, w, h, progress, bg_color, fg_color):
    """Draw a horizontal progress bar (0.0 to 1.0)."""
    pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=h // 2)
    fill_w = int(w * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        pygame.draw.rect(surface, fg_color, (x, y, fill_w, h), border_radius=h // 2)


def draw_visualizer(surface, x, y, w, h, tick, is_playing):
    """
    Draw a simple animated bar visualizer when music is playing.
    Uses sine waves with different frequencies per bar.
    """
    bar_count = 20
    bar_w = w // bar_count - 2
    for i in range(bar_count):
        if is_playing:
            
            phase = tick * 0.003 + i * 0.5
            bar_h = int((math.sin(phase) * 0.5 + 0.5) * h)
        else:
            bar_h = 4 
        bar_x = x + i * (bar_w + 2)
        bar_y = y + h - bar_h
        color_factor = i / bar_count
        r = int(ACCENT[0] * (1 - color_factor) + ACCENT2[0] * color_factor)
        g = int(ACCENT[1] * (1 - color_factor) + ACCENT2[1] * color_factor)
        b = int(ACCENT[2] * (1 - color_factor) + ACCENT2[2] * color_factor)
        pygame.draw.rect(surface, (r, g, b), (bar_x, bar_y, bar_w, bar_h), border_radius=2)


def truncate_text(text, font, max_width):
    """Truncate text with ellipsis if it exceeds max_width pixels."""
    if font.size(text)[0] <= max_width:
        return text
    while text and font.size(text + "…")[0] > max_width:
        text = text[:-1]
    return text + "…"


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("🎵 Music Player")
    clock = pygame.time.Clock()

    
    font_title = pygame.font.SysFont("monospace", 22, bold=True)
    font_track = pygame.font.SysFont("monospace", 17, bold=True)
    font_info  = pygame.font.SysFont("monospace", 13)
    font_keys  = pygame.font.SysFont("monospace", 12)

    
    music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
    player = MusicPlayer(music_dir)

    
    if not player.has_tracks():
        _create_sample_tracks(music_dir)
        player.load_playlist()

    tick = 0  

    running = True
    while running:
        tick += 1

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    player.toggle_play()           
                elif event.key == pygame.K_s:
                    player.stop()                  
                elif event.key == pygame.K_n:
                    player.next_track()            
                elif event.key == pygame.K_b:
                    player.prev_track()            

        
        player.check_auto_advance()

        
        screen.fill(BG_COLOR)

        
        draw_rounded_rect(screen, PANEL_COLOR, (20, 16, SCREEN_WIDTH - 40, 52), 10)
        title_surf = font_title.render("♫  MUSIC PLAYER", True, ACCENT)
        screen.blit(title_surf, (36, 30))

        
        viz_rect = (20, 82, SCREEN_WIDTH - 40, 70)
        draw_rounded_rect(screen, PANEL_COLOR, viz_rect, 10)
        draw_visualizer(screen, 28, 90, SCREEN_WIDTH - 56, 54, tick, player.is_playing)

        
        draw_rounded_rect(screen, PANEL_COLOR, (20, 166, SCREEN_WIDTH - 40, 90), 10)

        
        pos_surf = font_info.render(f"Track  {player.get_playlist_info()}", True, DIM_TEXT)
        screen.blit(pos_surf, (36, 180))

        
        status = "▶  PLAYING" if player.is_playing else "■  STOPPED"
        status_color = ACCENT if player.is_playing else DIM_TEXT
        status_surf = font_info.render(status, True, status_color)
        screen.blit(status_surf, (SCREEN_WIDTH - 36 - status_surf.get_width(), 180))

        
        track_name = player.get_current_track_name()
        track_name = truncate_text(track_name, font_track, SCREEN_WIDTH - 80)
        track_surf = font_track.render(track_name, True, TEXT_COLOR)
        screen.blit(track_surf, (36, 204))

       
        pos_s = player.get_position_seconds()
        
        demo_progress = (pos_s % 180) / 180 if player.is_playing else 0
        draw_progress_bar(screen, 36, 270, SCREEN_WIDTH - 72, 8,
                          demo_progress, TRACK_BG, ACCENT)

        
        mins = int(pos_s) // 60
        secs = int(pos_s) % 60
        pos_label = font_info.render(f"{mins:02d}:{secs:02d}", True, DIM_TEXT)
        screen.blit(pos_label, (36, 284))

        
        draw_rounded_rect(screen, PANEL_COLOR, (20, 304, SCREEN_WIDTH - 40, 76), 10)

        controls = [
            ("[P] Play/Stop", ACCENT),
            ("[S] Stop",      ACCENT2),
            ("[N] Next",      ACCENT),
            ("[B] Back",      ACCENT2),
            ("[Q] Quit",      DIM_TEXT),
        ]
        col_w = (SCREEN_WIDTH - 40) // len(controls)
        for i, (label, color) in enumerate(controls):
            surf = font_keys.render(label, True, color)
            x = 20 + i * col_w + (col_w - surf.get_width()) // 2
            screen.blit(surf, (x, 318))

        
        if not player.has_tracks():
            warn = font_info.render("⚠  No audio files found in /music folder", True, (255, 200, 80))
            screen.blit(warn, warn.get_rect(center=(SCREEN_WIDTH // 2, 350)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


def _create_sample_tracks(music_dir):
    """
    Generate two simple sine-wave WAV files as sample tracks
    so the player works out of the box without real audio files.
    """
    import struct
    import wave

    os.makedirs(music_dir, exist_ok=True)

    def write_wav(filename, frequency, duration_s=5, sample_rate=44100):
        path = os.path.join(music_dir, filename)
        n_samples = sample_rate * duration_s
        with wave.open(path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                
                envelope = min(t, 1.0, duration_s - t)
                sample = int(32767 * envelope * math.sin(2 * math.pi * frequency * t))
                wf.writeframes(struct.pack('<h', sample))

    write_wav("track1_440hz.wav", 440, duration_s=8)   
    write_wav("track2_528hz.wav", 528, duration_s=8)   


if __name__ == "__main__":
    main()
