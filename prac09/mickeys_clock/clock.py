"""
clock.py - Mickey Mouse Clock Logic
Handles time calculation and hand rotation angles.
"""

import datetime
import math


class MickeyClock:
    """
    Manages the Mickey Mouse clock state.
    Calculates rotation angles for minute and second hands.
    """

    def __init__(self):
        self.minutes = 0
        self.seconds = 0

    def update(self):
        """Fetch current system time and update minutes/seconds."""
        now = datetime.datetime.now()
        self.minutes = now.minute
        self.seconds = now.second

    def get_minute_angle(self):
        """
        Calculate rotation angle for the minute hand (right hand).
        0 minutes = 0 degrees (pointing up), rotates clockwise.
        Returns angle in degrees for pygame.transform.rotate() (counter-clockwise positive).
        """
        
        angle_clockwise = self.minutes * 6
        
        return -angle_clockwise

    def get_second_angle(self):
        """
        Calculate rotation angle for the second hand (left hand).
        0 seconds = 0 degrees (pointing up), rotates clockwise.
        Returns angle in degrees for pygame.transform.rotate() (counter-clockwise positive).
        """
        
        angle_clockwise = self.seconds * 6
        return -angle_clockwise

    def get_time_string(self):
        """Return formatted time string MM:SS."""
        return f"{self.minutes:02d}:{self.seconds:02d}"
