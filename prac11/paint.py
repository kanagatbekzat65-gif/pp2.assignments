"""
Paint – Practice 11, Task 3
Extends Practice 10 Paint with four new shape tools:
  1. Square        — equal-sided rectangle (locks width = height)
  2. Right Triangle
  3. Equilateral Triangle
  4. Rhombus
All tools have live ghost-preview while dragging, just like Rect/Circle.
Full comments throughout.
"""

import pygame
import sys
import math

# ── Constants ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 680
CANVAS_TOP    = 80
CANVAS_COLOR  = (255, 255, 255)
TOOLBAR_COLOR = (45,  45,  60)

PALETTE = [
    (0,   0,   0),
    (255, 255, 255),
    (200,  30,  30),
    (30,  200,  30),
    (30,   80, 220),
    (220, 180,  30),
    (180,  30, 180),
    (30,  200, 200),
    (230, 100,  30),
    (139,  90,  43),
    (255, 150, 200),
    (100, 100, 100),
]

BRUSH_SIZES = [2, 4, 8, 14, 22]

# Tool identifiers
TOOL_PENCIL   = "pencil"
TOOL_RECT     = "rect"
TOOL_SQUARE   = "square"       # NEW
TOOL_CIRCLE   = "circle"
TOOL_ERASER   = "eraser"
TOOL_RTRI     = "right_tri"    # NEW – right triangle
TOOL_EQTRI    = "eq_tri"       # NEW – equilateral triangle
TOOL_RHOMBUS  = "rhombus"      # NEW


# ── Button ─────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, label, font,
                 fg=(230, 230, 230), bg=(70, 70, 90), active_bg=(100, 160, 255)):
        self.rect      = pygame.Rect(rect)
        self.label     = label
        self.font      = font
        self.fg        = fg
        self.bg        = bg
        self.active_bg = active_bg
        self.active    = False

    def draw(self, surface):
        color = self.active_bg if self.active else self.bg
        pygame.draw.rect(surface, color,          self.rect, border_radius=6)
        pygame.draw.rect(surface, (120, 120, 140), self.rect, 1, border_radius=6)
        t = self.font.render(self.label, True, self.fg)
        surface.blit(t, t.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Colour swatch ──────────────────────────────────────────────────────────────
class ColourSwatch:
    SIZE = 28

    def __init__(self, x, y, color):
        self.rect  = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = color

    def draw(self, surface, selected=False):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)
        border_color = (255, 255, 255) if selected else (80, 80, 100)
        border_width = 3 if selected else 1
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=4)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── Brush size dot ─────────────────────────────────────────────────────────────
class BrushDot:
    def __init__(self, cx, cy, size):
        self.center = (cx, cy)
        self.size   = size
        self.radius = max(4, size // 2)

    def draw(self, surface, selected=False, color=(200, 200, 200)):
        c = (255, 255, 100) if selected else color
        pygame.draw.circle(surface, c, self.center, self.radius)

    def is_clicked(self, pos):
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        return dx * dx + dy * dy <= 16 * 16


# ── Shape helpers ──────────────────────────────────────────────────────────────

def _right_triangle_pts(start, end):
    """
    Returns three vertices of a right-angle triangle.
    Right angle is at the bottom-left corner.
      A = bottom-left  (right angle)
      B = top-left
      C = bottom-right
    """
    x0, y0 = start
    x1, y1 = end
    return [(x0, y1), (x0, y0), (x1, y1)]


def _equilateral_triangle_pts(start, end):
    """
    Returns three vertices of an equilateral triangle.
    Base runs from start to end; apex is above the midpoint.
    """
    x0, y0 = start
    x1, y1 = end
    mid_x  = (x0 + x1) / 2
    side   = math.hypot(x1 - x0, y1 - y0)
    height = side * math.sqrt(3) / 2
    # Apex direction: perpendicular, pointing upward (negative y)
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy) or 1
    # Perpendicular unit vector (rotated 90° CCW)
    px = -dy / length
    py =  dx / length
    apex_x = mid_x + px * height
    apex_y = (y0 + y1) / 2 + py * height
    return [(x0, y0), (x1, y1), (apex_x, apex_y)]


def _rhombus_pts(start, end):
    """
    Returns four vertices of a rhombus (diamond shape).
    start/end define the bounding box; the rhombus touches the midpoints of each side.
    """
    x0, y0 = start
    x1, y1 = end
    mx = (x0 + x1) / 2
    my = (y0 + y1) / 2
    return [(mx, y0), (x1, my), (mx, y1), (x0, my)]


# ── Paint application ──────────────────────────────────────────────────────────
class PaintApp:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Paint – Practice 11")
        self.clock   = pygame.time.Clock()

        self.font_sm = pygame.font.SysFont("Consolas", 12, bold=True)
        self.font_md = pygame.font.SysFont("Consolas", 13, bold=True)

        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - CANVAS_TOP))
        self.canvas.fill(CANVAS_COLOR)

        self.active_tool  = TOOL_PENCIL
        self.draw_color   = PALETTE[0]
        self.brush_size   = BRUSH_SIZES[1]
        self.drawing      = False
        self.last_pos     = None
        self.shape_start  = None
        self.preview_surface = None

        self._build_toolbar()

    # ── Toolbar ────────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        # Two rows of tool buttons to fit all 8 tools
        btn_w, btn_h = 66, 30
        row1_y = 6
        row2_y = 40

        # Row 1: Pencil, Rect, Square, Circle
        # Row 2: Eraser, RightTri, EqTri, Rhombus
        row1_tools = [
            (TOOL_PENCIL, "Pencil"),
            (TOOL_RECT,   "Rect"),
            (TOOL_SQUARE, "Square"),
            (TOOL_CIRCLE, "Circle"),
        ]
        row2_tools = [
            (TOOL_ERASER,  "Eraser"),
            (TOOL_RTRI,    "R-Tri"),
            (TOOL_EQTRI,   "EqTri"),
            (TOOL_RHOMBUS, "Rhombus"),
        ]

        self.tool_buttons = []
        for i, (tid, label) in enumerate(row1_tools):
            x   = 10 + i * (btn_w + 4)
            btn = Button((x, row1_y, btn_w, btn_h), label, self.font_md)
            btn.active = (tid == self.active_tool)
            self.tool_buttons.append((tid, btn))

        for i, (tid, label) in enumerate(row2_tools):
            x   = 10 + i * (btn_w + 4)
            btn = Button((x, row2_y, btn_w, btn_h), label, self.font_md)
            btn.active = (tid == self.active_tool)
            self.tool_buttons.append((tid, btn))

        # Colour swatches
        swatch_x0 = 310
        swatch_y0 = (CANVAS_TOP - ColourSwatch.SIZE) // 2
        self.swatches = []
        for i, color in enumerate(PALETTE):
            x = swatch_x0 + i * (ColourSwatch.SIZE + 3)
            self.swatches.append(ColourSwatch(x, swatch_y0, color))

        # Brush dots
        dot_x0 = swatch_x0 + len(PALETTE) * (ColourSwatch.SIZE + 3) + 14
        dot_y0 = CANVAS_TOP // 2
        self.brush_dots = []
        for i, size in enumerate(BRUSH_SIZES):
            cx = dot_x0 + i * 34
            self.brush_dots.append(BrushDot(cx, dot_y0, size))

        # Clear button
        self.clear_btn = Button(
            (SCREEN_WIDTH - 78, (CANVAS_TOP - 30) // 2, 68, 30),
            "Clear", self.font_md, bg=(140, 40, 40), active_bg=(200, 60, 60))

    # ── Coordinate helpers ─────────────────────────────────────────────────────
    def to_canvas(self, pos):
        return (pos[0], pos[1] - CANVAS_TOP)

    def on_canvas(self, pos):
        return pos[1] >= CANVAS_TOP

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(60)
            self._handle_events()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if not self.on_canvas(pos):
                    self._handle_toolbar_click(pos)
                    return
                self.drawing  = True
                self.last_pos = self.to_canvas(pos)
                if self.active_tool in (TOOL_RECT, TOOL_SQUARE, TOOL_CIRCLE,
                                        TOOL_RTRI, TOOL_EQTRI, TOOL_RHOMBUS):
                    self.shape_start     = self.to_canvas(pos)
                    self.preview_surface = self.canvas.copy()
                elif self.active_tool == TOOL_PENCIL:
                    pygame.draw.circle(self.canvas, self.draw_color,
                                       self.to_canvas(pos), self.brush_size)
                elif self.active_tool == TOOL_ERASER:
                    self._erase(self.to_canvas(pos))

            elif event.type == pygame.MOUSEMOTION and self.drawing:
                pos        = event.pos
                if not self.on_canvas(pos):
                    return
                canvas_pos = self.to_canvas(pos)
                if self.active_tool == TOOL_PENCIL:
                    if self.last_pos:
                        pygame.draw.line(self.canvas, self.draw_color,
                                         self.last_pos, canvas_pos, self.brush_size * 2)
                    self.last_pos = canvas_pos
                elif self.active_tool == TOOL_ERASER:
                    self._erase(canvas_pos)
                elif self.active_tool in (TOOL_RECT, TOOL_SQUARE, TOOL_CIRCLE,
                                          TOOL_RTRI, TOOL_EQTRI, TOOL_RHOMBUS):
                    self.canvas.blit(self.preview_surface, (0, 0))
                    self._draw_shape(self.canvas, self.shape_start, canvas_pos, ghost=True)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.drawing:
                    pos = event.pos
                    if self.on_canvas(pos) and self.active_tool in (
                            TOOL_RECT, TOOL_SQUARE, TOOL_CIRCLE,
                            TOOL_RTRI, TOOL_EQTRI, TOOL_RHOMBUS):
                        self.canvas.blit(self.preview_surface, (0, 0))
                        self._draw_shape(self.canvas,
                                         self.shape_start,
                                         self.to_canvas(pos), ghost=False)
                    self.drawing         = False
                    self.last_pos        = None
                    self.shape_start     = None
                    self.preview_surface = None

    # ── Toolbar click ──────────────────────────────────────────────────────────
    def _handle_toolbar_click(self, pos):
        for (tid, btn) in self.tool_buttons:
            if btn.is_clicked(pos):
                self.active_tool = tid
                for (_, b) in self.tool_buttons:
                    b.active = False
                btn.active = True
                return
        for swatch in self.swatches:
            if swatch.is_clicked(pos):
                self.draw_color = swatch.color
                return
        for dot in self.brush_dots:
            if dot.is_clicked(pos):
                self.brush_size = dot.size
                return
        if self.clear_btn.is_clicked(pos):
            self.canvas.fill(CANVAS_COLOR)

    # ── Erase helper ──────────────────────────────────────────────────────────
    def _erase(self, canvas_pos):
        size = self.brush_size * 3
        rect = pygame.Rect(canvas_pos[0] - size, canvas_pos[1] - size,
                           size * 2, size * 2)
        pygame.draw.rect(self.canvas, CANVAS_COLOR, rect)

    # ── Shape drawing ──────────────────────────────────────────────────────────
    def _draw_shape(self, surface, start, end, ghost=False):
        """
        Dispatch to the correct drawing routine for the active tool.
        ghost=True → thin outline preview; ghost=False → filled + outline.
        """
        tool = self.active_tool
        col  = self.draw_color
        lw   = 2   # line width for ghost / outline

        # ── Rectangle ───────────────────────────────────────────────────────
        if tool == TOOL_RECT:
            rect = _normalise_rect(start, end)
            if ghost:
                pygame.draw.rect(surface, col, rect, lw)
            else:
                pygame.draw.rect(surface, col, rect)
                pygame.draw.rect(surface, (0, 0, 0), rect, lw)

        # ── Square (lock width = height) ─────────────────────────────────────
        elif tool == TOOL_SQUARE:
            side = min(abs(end[0] - start[0]), abs(end[1] - start[1]))
            sx   = start[0] + (side if end[0] >= start[0] else -side)
            sy   = start[1] + (side if end[1] >= start[1] else -side)
            rect = _normalise_rect(start, (sx, sy))
            if ghost:
                pygame.draw.rect(surface, col, rect, lw)
            else:
                pygame.draw.rect(surface, col, rect)
                pygame.draw.rect(surface, (0, 0, 0), rect, lw)

        # ── Circle / Ellipse ─────────────────────────────────────────────────
        elif tool == TOOL_CIRCLE:
            rect = _normalise_rect(start, end)
            if rect.width < 2 or rect.height < 2:
                return
            if ghost:
                pygame.draw.ellipse(surface, col, rect, lw)
            else:
                pygame.draw.ellipse(surface, col, rect)
                pygame.draw.ellipse(surface, (0, 0, 0), rect, lw)

        # ── Right Triangle ───────────────────────────────────────────────────
        elif tool == TOOL_RTRI:
            pts = _right_triangle_pts(start, end)
            if ghost:
                pygame.draw.polygon(surface, col, pts, lw)
            else:
                pygame.draw.polygon(surface, col, pts)
                pygame.draw.polygon(surface, (0, 0, 0), pts, lw)

        # ── Equilateral Triangle ─────────────────────────────────────────────
        elif tool == TOOL_EQTRI:
            pts = _equilateral_triangle_pts(start, end)
            if ghost:
                pygame.draw.polygon(surface, col, pts, lw)
            else:
                pygame.draw.polygon(surface, col, pts)
                pygame.draw.polygon(surface, (0, 0, 0), pts, lw)

        # ── Rhombus ──────────────────────────────────────────────────────────
        elif tool == TOOL_RHOMBUS:
            pts = _rhombus_pts(start, end)
            if ghost:
                pygame.draw.polygon(surface, col, pts, lw)
            else:
                pygame.draw.polygon(surface, col, pts)
                pygame.draw.polygon(surface, (0, 0, 0), pts, lw)

    # ── Render ────────────────────────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(TOOLBAR_COLOR)
        self.screen.blit(self.canvas, (0, CANVAS_TOP))
        pygame.draw.line(self.screen, (80, 80, 100),
                         (0, CANVAS_TOP), (SCREEN_WIDTH, CANVAS_TOP), 2)

        for (_, btn) in self.tool_buttons:
            btn.draw(self.screen)
        self.clear_btn.draw(self.screen)
        for swatch in self.swatches:
            swatch.draw(self.screen, selected=(swatch.color == self.draw_color))
        for dot in self.brush_dots:
            dot.draw(self.screen,
                     selected=(dot.size == self.brush_size),
                     color=self.draw_color)

        # Active colour indicator
        indicator = pygame.Rect(SCREEN_WIDTH - 78 - 38, (CANVAS_TOP - 28) // 2, 28, 28)
        pygame.draw.rect(self.screen, self.draw_color, indicator, border_radius=4)
        pygame.draw.rect(self.screen, (200, 200, 200), indicator, 1, border_radius=4)

        pygame.mouse.set_visible(True)


# ── Utility ────────────────────────────────────────────────────────────────────

def _normalise_rect(start, end):
    """Return a pygame.Rect from two arbitrary corner points."""
    x0, y0 = start
    x1, y1 = end
    return pygame.Rect(min(x0, x1), min(y0, y1),
                       abs(x1 - x0), abs(y1 - y0))


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PaintApp().run()