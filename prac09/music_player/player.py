"""
player.py - Music Player Logic
Handles playlist management and pygame.mixer playback control.
"""

import pygame
import os


class MusicPlayer:
    """
    Manages a playlist of audio tracks with play/stop/next/previous controls.
    Uses pygame.mixer for audio playback.
    """

    def __init__(self, music_dir="music"):
        """
        Initialize the player.

        Args:
            music_dir: path to folder containing audio files
        """
        pygame.mixer.init()
        self.music_dir = music_dir
        self.playlist = []          
        self.track_names = []       
        self.current_index = 0      
        self.is_playing = False
        self.load_playlist()

    def load_playlist(self):
        """Scan music_dir for supported audio files and build the playlist."""
        supported = (".mp3", ".wav", ".ogg", ".flac")
        if not os.path.isdir(self.music_dir):
            return

        for fname in sorted(os.listdir(self.music_dir)):
            if fname.lower().endswith(supported):
                full_path = os.path.join(self.music_dir, fname)
                self.playlist.append(full_path)
                
                name = os.path.splitext(fname)[0]
                self.track_names.append(name)

    def has_tracks(self):
        """Return True if the playlist contains at least one track."""
        return len(self.playlist) > 0

    def play(self):
        """Start playback of the current track."""
        if not self.has_tracks():
            return
        try:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play()
            self.is_playing = True
        except pygame.error as e:
            print(f"[MusicPlayer] Could not play track: {e}")
            self.is_playing = False

    def stop(self):
        """Stop playback."""
        pygame.mixer.music.stop()
        self.is_playing = False

    def next_track(self):
        """Advance to the next track (wraps around). Plays if currently playing."""
        if not self.has_tracks():
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        if self.is_playing:
            self.play()

    def prev_track(self):
        """Go to the previous track (wraps around). Plays if currently playing."""
        if not self.has_tracks():
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        if self.is_playing:
            self.play()

    def toggle_play(self):
        """Toggle between play and stop."""
        if self.is_playing:
            self.stop()
        else:
            self.play()

    def get_current_track_name(self):
        """Return the display name of the current track."""
        if not self.has_tracks():
            return "No tracks found"
        return self.track_names[self.current_index]

    def get_playlist_info(self):
        """Return a string like '2 / 5' showing track position."""
        if not self.has_tracks():
            return "0 / 0"
        return f"{self.current_index + 1} / {len(self.playlist)}"

    def get_position_seconds(self):
        """Return current playback position in seconds (0 if stopped)."""
        if self.is_playing:
            pos_ms = pygame.mixer.music.get_pos()
            return pos_ms / 1000.0 if pos_ms >= 0 else 0.0
        return 0.0

    def is_track_finished(self):
        """Return True if playback has ended (auto-advance trigger)."""
        return self.is_playing and not pygame.mixer.music.get_busy()

    def check_auto_advance(self):
        """Automatically advance to next track when current one finishes."""
        if self.is_track_finished():
            self.next_track()
