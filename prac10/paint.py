"""
Paint – Practice 10, Task 3
Extends the nerdparadise.com pygame paint tutorial (Part 6) with:
  - Freehand drawing (pencil)  ← from original tutorial
  - Rectangle tool
  - Circle (ellipse) tool
  - Eraser tool
  - Colour palette with interactive colour selection
  - Brush size selector
Full comments throughout.
"""

import pygame
import sys

# ── Constants ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 680

CANVAS_TOP    = 80    # y-pixel where the drawing canvas begins (below toolbar)
CANVAS_COLOR  = (255, 255, 255)
TOOLBAR_COLOR = (45,  45,  60)

# Preset colour palette (shown in the toolbar)
PALETTE = [
    (0,   0,   0),     # black
    (255, 255, 255),   # white
    (200,  30,  30),   # red
    (30,  200,  30),   # green
    (30,   80, 220),   # blue
    (220, 180,  30),   # yellow
    (180,  30, 180),   # purple
    (30,  200, 200),   # cyan
    (230, 100,  30),   # orange
    (139,  90,  43),   # brown
    (255, 150, 200),   # pink
    (100, 100, 100),   # grey
]

# Available brush sizes
BRUSH_SIZES = [2, 4, 8, 14, 22]

# Tool identifiers
TOOL_PENCIL    = "pencil"
TOOL_RECT      = "rect"
TOOL_CIRCLE    = "circle"
TOOL_ERASER    = "eraser"


# ── Toolbar button helper ──────────────────────────────────────────────────────
class Button:
    """A simple clickable rectangular button with a label."""

    def __init__(self, rect, label, font, fg=(230, 230, 230), bg=(70, 70, 90), active_bg=(100, 160, 255)):
        self.rect      = pygame.Rect(rect)
        self.label     = label
        self.font      = font
        self.fg        = fg
        self.bg        = bg
        self.active_bg = active_bg
        self.active    = False     # is this the currently selected tool?

    def draw(self, surface):
        color = self.active_bg if self.active else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (120, 120, 140), self.rect, 1, border_radius=6)
        text_surf = self.font.render(self.label, True, self.fg)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Colour swatch ──────────────────────────────────────────────────────────────
class ColourSwatch:
    """A small square showing one colour from the palette."""

    SIZE = 28

    def __init__(self, x, y, color):
        self.rect  = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = color

    def draw(self, surface, selected=False):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        # White outline if this colour is selected
        border_color = (255, 255, 255) if selected else (80, 80, 100)
        border_width = 3 if selected else 1
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=4)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Brush size dot ─────────────────────────────────────────────────────────────
class BrushDot:
    """A clickable circle that represents a brush-size option."""

    def __init__(self, cx, cy, size):
        self.center = (cx, cy)
        self.size   = size   # the actual brush radius it represents
        self.radius = max(4, size // 2)   # display radius

    def draw(self, surface, selected=False, color=(200, 200, 200)):
        c = (255, 255, 100) if selected else color
        pygame.draw.circle(surface, c, self.center, self.radius)

    def is_clicked(self, pos):
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        # Generous hit area of 16 px radius regardless of display size
        return dx * dx + dy * dy <= 16 * 16


# ── Paint application ──────────────────────────────────────────────────────────
class PaintApp:
    """Main application controller."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Paint – Practice 10")
        self.clock  = pygame.time.Clock()

        self.font_sm = pygame.font.SysFont("Consolas", 13, bold=True)
        self.font_md = pygame.font.SysFont("Consolas", 14, bold=True)

        # ── Canvas surface (separate so we can blit shapes without flickering) ──
        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - CANVAS_TOP))
        self.canvas.fill(CANVAS_COLOR)

        # ── Tool state ───────────────────────────────────────────────────────────
        self.active_tool  = TOOL_PENCIL
        self.draw_color   = PALETTE[0]   # start with black
        self.brush_size   = BRUSH_SIZES[1]
        self.drawing      = False
        self.last_pos     = None          # last mouse position (for freehand)
        self.shape_start  = None          # anchor point for rect/circle tools

        # Preview surface: used to show the ghost outline while dragging shapes
        self.preview_surface = None

        # ── Build toolbar UI ─────────────────────────────────────────────────────
        self._build_toolbar()

    # ── Toolbar construction ────────────────────────────────────────────────────
    def _build_toolbar(self):
        """Create tool buttons, colour swatches, and brush-size dots."""
        # Tool buttons
        btn_w, btn_h = 72, 36
        y = (CANVAS_TOP - btn_h) // 2
        tools = [
            (TOOL_PENCIL, "Pencil"),
            (TOOL_RECT,   "Rect"),
            (TOOL_CIRCLE, "Circle"),
            (TOOL_ERASER, "Eraser"),
        ]
        self.tool_buttons = []
        for i, (tid, label) in enumerate(tools):
            x = 10 + i * (btn_w + 6)
            btn = Button((x, y, btn_w, btn_h), label, self.font_md)
            btn.active = (tid == self.active_tool)
            self.tool_buttons.append((tid, btn))

        # Colour swatches
        swatch_x0 = 340
        swatch_y0 = (CANVAS_TOP - ColourSwatch.SIZE) // 2
        self.swatches = []
        for i, color in enumerate(PALETTE):
            x = swatch_x0 + i * (ColourSwatch.SIZE + 4)
            self.swatches.append(ColourSwatch(x, swatch_y0, color))

        # Brush size dots
        dot_x0 = swatch_x0 + len(PALETTE) * (ColourSwatch.SIZE + 4) + 16
        dot_y0 = CANVAS_TOP // 2
        self.brush_dots = []
        for i, size in enumerate(BRUSH_SIZES):
            cx = dot_x0 + i * 36
            self.brush_dots.append(BrushDot(cx, dot_y0, size))

        # 'Clear' button (top-right)
        self.clear_btn = Button(
            (SCREEN_WIDTH - 80, y, 70, btn_h), "Clear", self.font_md,
            bg=(140, 40, 40), active_bg=(200, 60, 60))

    # ── Canvas-space coordinate ─────────────────────────────────────────────────
    def to_canvas(self, pos):
        """Convert a screen position to a position on the canvas surface."""
        return (pos[0], pos[1] - CANVAS_TOP)

    def on_canvas(self, pos):
        """Return True if the screen position is inside the drawing area."""
        return pos[1] >= CANVAS_TOP

    # ── Main loop ───────────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(60)
            self.handle_events()
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Mouse button pressed ─────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Check toolbar clicks first
                if not self.on_canvas(pos):
                    self._handle_toolbar_click(pos)
                    return

                # Begin drawing on canvas
                self.drawing   = True
                self.last_pos  = self.to_canvas(pos)

                if self.active_tool in (TOOL_RECT, TOOL_CIRCLE):
                    # Record shape anchor and snapshot canvas for preview
                    self.shape_start    = self.to_canvas(pos)
                    self.preview_surface = self.canvas.copy()

                elif self.active_tool == TOOL_PENCIL:
                    # Draw a single dot at click position
                    pygame.draw.circle(self.canvas, self.draw_color,
                                       self.to_canvas(pos), self.brush_size)

                elif self.active_tool == TOOL_ERASER:
                    # Erase: draw a white square (or circle)
                    self._erase(self.to_canvas(pos))

            # ── Mouse moved while button held ────────────────────────────────
            elif event.type == pygame.MOUSEMOTION and self.drawing:
                pos = event.pos
                if not self.on_canvas(pos):
                    return
                canvas_pos = self.to_canvas(pos)

                if self.active_tool == TOOL_PENCIL:
                    # Freehand: draw line segment from last position to current
                    if self.last_pos:
                        pygame.draw.line(self.canvas, self.draw_color,
                                         self.last_pos, canvas_pos, self.brush_size * 2)
                    self.last_pos = canvas_pos

                elif self.active_tool == TOOL_ERASER:
                    self._erase(canvas_pos)

                elif self.active_tool in (TOOL_RECT, TOOL_CIRCLE):
                    # Live preview: restore snapshot then draw ghost shape
                    self.canvas.blit(self.preview_surface, (0, 0))
                    self._draw_shape(self.canvas, self.shape_start, canvas_pos, ghost=True)

            # ── Mouse button released ────────────────────────────────────────
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.drawing:
                    pos = event.pos
                    if self.on_canvas(pos) and self.active_tool in (TOOL_RECT, TOOL_CIRCLE):
                        # Restore snapshot and commit the final shape
                        self.canvas.blit(self.preview_surface, (0, 0))
                        self._draw_shape(self.canvas,
                                         self.shape_start,
                                         self.to_canvas(pos),
                                         ghost=False)
                    self.drawing         = False
                    self.last_pos        = None
                    self.shape_start     = None
                    self.preview_surface = None

    # ── Toolbar click handler ────────────────────────────────────────────────────
    def _handle_toolbar_click(self, pos):
        # Tool buttons
        for (tid, btn) in self.tool_buttons:
            if btn.is_clicked(pos):
                self.active_tool = tid
                # Update active state for all buttons
                for (_, b) in self.tool_buttons:
                    b.active = False
                btn.active = True
                return

        # Colour swatches
        for swatch in self.swatches:
            if swatch.is_clicked(pos):
                self.draw_color = swatch.color
                return

        # Brush size dots
        for dot in self.brush_dots:
            if dot.is_clicked(pos):
                self.brush_size = dot.size
                return

        # Clear button
        if self.clear_btn.is_clicked(pos):
            self.canvas.fill(CANVAS_COLOR)

    # ── Drawing helpers ──────────────────────────────────────────────────────────
    def _erase(self, canvas_pos):
        """
        Erase by drawing a white filled rectangle centred on the cursor.
        Using a rect gives a blocky eraser which is intuitive.
        """
        size = self.brush_size * 3
        rect = pygame.Rect(
            canvas_pos[0] - size,
            canvas_pos[1] - size,
            size * 2, size * 2)
        pygame.draw.rect(self.canvas, CANVAS_COLOR, rect)

    def _draw_shape(self, surface, start, end, ghost=False):
        """
        Draw a rectangle or ellipse from start to end on the given surface.
        In ghost mode an alpha-blended preview outline is drawn.
        """
        x0, y0 = start
        x1, y1 = end

        # Normalise so rect is always top-left → bottom-right
        rect = pygame.Rect(min(x0, x1), min(y0, y1),
                           abs(x1 - x0), abs(y1 - y0))

        if ghost:
            # Draw a dotted / thin outline in the active colour for preview
            if self.active_tool == TOOL_RECT:
                pygame.draw.rect(surface, self.draw_color, rect, 2)
            else:
                pygame.draw.ellipse(surface, self.draw_color, rect, 2)
        else:
            # Solid filled shape with an outline
            if self.active_tool == TOOL_RECT:
                pygame.draw.rect(surface, self.draw_color, rect)
                pygame.draw.rect(surface, (0, 0, 0), rect, 2)
            else:
                pygame.draw.ellipse(surface, self.draw_color, rect)
                pygame.draw.ellipse(surface, (0, 0, 0), rect, 2)

    # ── Rendering ────────────────────────────────────────────────────────────────
    def draw(self):
        # Toolbar background
        self.screen.fill(TOOLBAR_COLOR)

        # Blit canvas below the toolbar
        self.screen.blit(self.canvas, (0, CANVAS_TOP))

        # Separator line
        pygame.draw.line(self.screen, (80, 80, 100),
                         (0, CANVAS_TOP), (SCREEN_WIDTH, CANVAS_TOP), 2)

        # Draw toolbar widgets
        for (_, btn) in self.tool_buttons:
            btn.draw(self.screen)
        self.clear_btn.draw(self.screen)

        for swatch in self.swatches:
            swatch.draw(self.screen, selected=(swatch.color == self.draw_color))

        for dot in self.brush_dots:
            dot.draw(self.screen,
                     selected=(dot.size == self.brush_size),
                     color=self.draw_color)

        # Current colour indicator (small labelled square, far left)
        indicator_rect = pygame.Rect(8, CANVAS_TOP + 4, 28, 28)
        pygame.draw.rect(self.screen, self.draw_color, indicator_rect, border_radius=4)
        pygame.draw.rect(self.screen, (200, 200, 200), indicator_rect, 1, border_radius=4)

        # Cursor: show crosshair while on canvas, default elsewhere
        mouse_pos = pygame.mouse.get_pos()
        if self.on_canvas(mouse_pos):
            # Draw a small crosshair cursor manually (no system cursor change needed)
            pygame.mouse.set_visible(True)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PaintApp().run()