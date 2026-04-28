"""
tools.py — Drawing tool implementations for the Paint app (TSIS 2)

Each tool is a class with a common interface:
    on_mouse_down(canvas, pos, color, size)
    on_mouse_move(canvas, pos, prev_pos, color, size)
    on_mouse_up(canvas, pos, color, size)
    draw_preview(surface, pos, color, size)   # live preview overlaid on screen

Tools implemented here (new in TSIS 2):
    PencilTool      — freehand drawing
    LineTool        — click-drag straight line with live preview
    FillTool        — BFS flood-fill
    TextTool        — click-to-place text, type, Enter to confirm

Shape tools that existed in Practice 10-11 are re-implemented with
brush-size support:
    RectTool, CircleTool, EraserTool
    SquareTool, RightTriangleTool, EquilateralTriangleTool, RhombusTool
"""

import math
import pygame
from collections import deque


# ─────────────────────────────────────────────────────────────────────────────
# Base
# ─────────────────────────────────────────────────────────────────────────────

class BaseTool:
    name = "base"
    cursor = pygame.SYSTEM_CURSOR_CROSSHAIR

    def on_mouse_down(self, canvas, pos, color, size): pass
    def on_mouse_move(self, canvas, pos, prev_pos, color, size): pass
    def on_mouse_up(self, canvas, pos, color, size): pass
    def draw_preview(self, surface, pos, color, size): pass


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  Pencil — freehand
# ─────────────────────────────────────────────────────────────────────────────

class PencilTool(BaseTool):
    name = "pencil"

    def on_mouse_down(self, canvas, pos, color, size):
        pygame.draw.circle(canvas, color, pos, max(1, size // 2))

    def on_mouse_move(self, canvas, pos, prev_pos, color, size):
        if prev_pos:
            pygame.draw.line(canvas, color, prev_pos, pos, size)
            # Round caps
            pygame.draw.circle(canvas, color, pos, max(1, size // 2))
            pygame.draw.circle(canvas, color, prev_pos, max(1, size // 2))


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  Straight Line — live preview
# ─────────────────────────────────────────────────────────────────────────────

class LineTool(BaseTool):
    name = "line"

    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            pygame.draw.line(canvas, color, self._start, pos, size)
        self._start = None

    def draw_preview(self, surface, pos, color, size):
        if self._start:
            pygame.draw.line(surface, color, self._start, pos, size)


# ─────────────────────────────────────────────────────────────────────────────
# 3.3  Flood Fill — BFS over pixels
# ─────────────────────────────────────────────────────────────────────────────

class FillTool(BaseTool):
    name = "fill"
    cursor = pygame.SYSTEM_CURSOR_HAND

    def on_mouse_down(self, canvas, pos, color, size):
        _flood_fill(canvas, pos, color)


def _flood_fill(surface: pygame.Surface, start: tuple, fill_color):
    """BFS flood-fill using get_at / set_at. Exact color match tolerance."""
    x0, y0 = start
    w, h = surface.get_size()

    if not (0 <= x0 < w and 0 <= y0 < h):
        return

    target = surface.get_at((x0, y0))[:3]  # ignore alpha
    fill   = fill_color[:3] if len(fill_color) == 4 else fill_color[:3]

    if target == fill:
        return  # already the right color — nothing to do

    visited = set()
    queue   = deque()
    queue.append((x0, y0))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        if not (0 <= x < w and 0 <= y < h):
            continue
        if surface.get_at((x, y))[:3] != target:
            continue
        visited.add((x, y))
        surface.set_at((x, y), fill_color)
        queue.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])


# ─────────────────────────────────────────────────────────────────────────────
# 3.5  Text Tool
# ─────────────────────────────────────────────────────────────────────────────

class TextTool(BaseTool):
    name = "text"
    cursor = pygame.SYSTEM_CURSOR_IBEAM

    def __init__(self):
        self.active    = False
        self.pos       = (0, 0)
        self.buffer    = ""
        self._font     = None
        self.font_size = 24

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", self.font_size, bold=False)
        return self._font

    def on_mouse_down(self, canvas, pos, color, size):
        # Clicking while active commits what's already typed
        if self.active and self.buffer:
            self._commit(canvas, color)
        self.active = True
        self.pos    = pos
        self.buffer = ""

    def handle_key(self, canvas, event, color):
        """Call from the main event loop for KEYDOWN events."""
        if not self.active:
            return False
        if event.key == pygame.K_RETURN:
            self._commit(canvas, color)
            return True
        elif event.key == pygame.K_ESCAPE:
            self.active = False
            self.buffer = ""
            return True
        elif event.key == pygame.K_BACKSPACE:
            self.buffer = self.buffer[:-1]
            return True
        elif event.unicode and event.unicode.isprintable():
            self.buffer += event.unicode
            return True
        return False

    def _commit(self, canvas, color):
        if self.buffer:
            font  = self._get_font()
            surf  = font.render(self.buffer, True, color)
            canvas.blit(surf, self.pos)
        self.active = False
        self.buffer = ""

    def draw_preview(self, surface, pos, color, size):
        """Render the in-progress text + blinking cursor."""
        if not self.active:
            return
        font = self._get_font()
        text = self.buffer + ("|" if (pygame.time.get_ticks() // 500) % 2 == 0 else " ")
        surf = font.render(text, True, color)
        surface.blit(surf, self.pos)

    def cancel(self):
        self.active = False
        self.buffer = ""


# ─────────────────────────────────────────────────────────────────────────────
# Shape tools (from Practice 10-11, now with brush-size support)
# ─────────────────────────────────────────────────────────────────────────────

class _DragShapeTool(BaseTool):
    """Mixin for tools that record start on mouse-down, draw on mouse-up."""

    def __init__(self):
        self._start = None

    def on_mouse_down(self, canvas, pos, color, size):
        self._start = pos

    def on_mouse_up(self, canvas, pos, color, size):
        if self._start:
            self._draw(canvas, self._start, pos, color, size)
        self._start = None

    def draw_preview(self, surface, pos, color, size):
        if self._start:
            self._draw(surface, self._start, pos, color, size)

    def _draw(self, surface, start, end, color, size):
        raise NotImplementedError


class RectTool(_DragShapeTool):
    name = "rectangle"

    def _draw(self, surface, start, end, color, size):
        x = min(start[0], end[0])
        y = min(start[1], end[1])
        w = abs(end[0] - start[0])
        h = abs(end[1] - start[1])
        if w > 0 and h > 0:
            pygame.draw.rect(surface, color, (x, y, w, h), size)


class CircleTool(_DragShapeTool):
    name = "circle"

    def _draw(self, surface, start, end, color, size):
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        r  = int(math.hypot(end[0] - start[0], end[1] - start[1]) / 2)
        if r > 0:
            pygame.draw.circle(surface, color, (cx, cy), r, size)


class EraserTool(BaseTool):
    name = "eraser"
    cursor = pygame.SYSTEM_CURSOR_CROSSHAIR

    def on_mouse_down(self, canvas, pos, color, size):
        pygame.draw.circle(canvas, (255, 255, 255), pos, size * 3)

    def on_mouse_move(self, canvas, pos, prev_pos, color, size):
        if prev_pos:
            pygame.draw.line(canvas, (255, 255, 255), prev_pos, pos, size * 6)
            pygame.draw.circle(canvas, (255, 255, 255), pos, size * 3)

    def draw_preview(self, surface, pos, color, size):
        pygame.draw.circle(surface, (180, 180, 180), pos, size * 3, 1)


class SquareTool(_DragShapeTool):
    name = "square"

    def _draw(self, surface, start, end, color, size):
        side = min(abs(end[0] - start[0]), abs(end[1] - start[1]))
        sx   = start[0] + (1 if end[0] >= start[0] else -1) * side
        sy   = start[1] + (1 if end[1] >= start[1] else -1) * side
        x    = min(start[0], sx)
        y    = min(start[1], sy)
        if side > 0:
            pygame.draw.rect(surface, color, (x, y, side, side), size)


class RightTriangleTool(_DragShapeTool):
    name = "right_triangle"

    def _draw(self, surface, start, end, color, size):
        p1 = start
        p2 = (start[0], end[1])
        p3 = end
        pygame.draw.polygon(surface, color, [p1, p2, p3], size)


class EquilateralTriangleTool(_DragShapeTool):
    name = "equilateral_triangle"

    def _draw(self, surface, start, end, color, size):
        base  = abs(end[0] - start[0]) or 1
        h     = int(base * math.sqrt(3) / 2)
        cx    = (start[0] + end[0]) // 2
        direction = 1 if end[1] >= start[1] else -1
        p1 = (start[0], start[1])
        p2 = (end[0], start[1])
        p3 = (cx, start[1] + direction * h)
        pygame.draw.polygon(surface, color, [p1, p2, p3], size)


class RhombusTool(_DragShapeTool):
    name = "rhombus"

    def _draw(self, surface, start, end, color, size):
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        hw = abs(end[0] - start[0]) // 2
        hh = abs(end[1] - start[1]) // 2
        if hw > 0 and hh > 0:
            points = [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]
            pygame.draw.polygon(surface, color, points, size)


# ─────────────────────────────────────────────────────────────────────────────
# Registry — maps tool name → instance
# ─────────────────────────────────────────────────────────────────────────────

def build_tool_registry() -> dict:
    return {
        "pencil":               PencilTool(),
        "line":                 LineTool(),
        "fill":                 FillTool(),
        "text":                 TextTool(),
        "eraser":               EraserTool(),
        "rectangle":            RectTool(),
        "circle":               CircleTool(),
        "square":               SquareTool(),
        "right_triangle":       RightTriangleTool(),
        "equilateral_triangle": EquilateralTriangleTool(),
        "rhombus":              RhombusTool(),
    }