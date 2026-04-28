"""
ball.py - Ball Entity
Encapsulates the red ball's position, size, and movement logic
with screen-boundary enforcement.
"""


class Ball:
    """
    Represents the red ball.

    Attributes:
        x, y   : center position (pixels)
        radius : ball radius (25 px → 50x50 total)
        color  : RGB tuple
        step   : pixels to move per key press
    """

    RADIUS = 25          
    COLOR = (220, 40, 40)
    OUTLINE_COLOR = (160, 20, 20)
    STEP = 20            

    def __init__(self, screen_width, screen_height):
        """Place the ball in the centre of the screen at startup."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.x = screen_width // 2
        self.y = screen_height // 2

    

    def move_up(self):
        """Move ball up by STEP pixels, if within screen bounds."""
        new_y = self.y - self.STEP
        if new_y - self.RADIUS >= 0:
            self.y = new_y
        

    def move_down(self):
        """Move ball down by STEP pixels, if within screen bounds."""
        new_y = self.y + self.STEP
        if new_y + self.RADIUS <= self.screen_height:   
            self.y = new_y

    def move_left(self):
        """Move ball left by STEP pixels, if within screen bounds."""
        new_x = self.x - self.STEP
        if new_x - self.RADIUS >= 0:          
            self.x = new_x

    def move_right(self):
        """Move ball right by STEP pixels, if within screen bounds."""
        new_x = self.x + self.STEP
        if new_x + self.RADIUS <= self.screen_width:    
            self.x = new_x

    

    def get_center(self):
        """Return (x, y) centre as a tuple."""
        return (self.x, self.y)

    def get_position_string(self):
        """Return formatted position for HUD display."""
        return f"({self.x}, {self.y})"
