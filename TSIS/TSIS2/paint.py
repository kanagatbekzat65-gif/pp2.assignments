"""
paint.py — Paint Application Extended (TSIS 2)
===============================================
Run:  python paint.py

Requirements:
    pip install pygame

Controls
────────
  Tools (toolbar buttons or keyboard shortcuts):
    P  — Pencil (freehand)
    L  — Line (straight, with live preview)
    F  — Fill (flood-fill)
    T  — Text  (click canvas → type → Enter to commit, Esc to cancel)
    E  — Eraser
    R  — Rectangle
    C  — Circle
    S  — Square
    G  — Right Triangle
    Q  — Equilateral Triangle
    H  — Rhombus

  Brush size:
    1  — Small  (2 px)
    2  — Medium (5 px)
    3  — Large  (10 px)

  Color picker:
    Click any swatch in the palette row.

  Save:
    Ctrl+S  → saves canvas as  canvas_YYYYMMDD_HHMMSS.png

  Quit:
    Alt+F4 / close window
"""

import sys
import pygame
from datetime import datetime
from tools import build_tool_registry

# ─────────────────────────────────────────────────────────────
# Constants & Config
# ─────────────────────────────────────────────────────────────

WIN_W, WIN_H = 1100, 740
TOOLBAR_H    = 56          # top toolbar height
PALETTE_H    = 48          # bottom palette height
CANVAS_TOP   = TOOLBAR_H
CANVAS_BOT   = WIN_H - PALETTE_H
CANVAS_H     = CANVAS_BOT - CANVAS_TOP
CANVAS_W     = WIN_W

BG_COLOR      = (245, 245, 248)
TOOLBAR_BG    = (30,  30,  38)
PALETTE_BG    = (22,  22,  28)
ACTIVE_BORDER = (255, 200,  60)
BTN_HOVER     = (60,  62,  80)
BTN_NORMAL    = (42,  44,  58)
TEXT_COLOR    = (220, 220, 230)
CANVAS_WHITE  = (255, 255, 255)

BRUSH_SIZES   = [2, 5, 10]   # small, medium, large
SIZE_LABELS   = ["S", "M", "L"]

PALETTE_COLORS = [
    (0,   0,   0),    # Black
    (255, 255, 255),  # White
    (220,  30,  30),  # Red
    (255, 120,   0),  # Orange
    (255, 210,   0),  # Yellow
    ( 40, 180,  40),  # Green
    ( 30, 120, 220),  # Blue
    (130,  60, 200),  # Purple
    (255, 105, 180),  # Pink
    (  0, 200, 200),  # Cyan
    (160,  82,  45),  # Brown
    (128, 128, 128),  # Gray
    (200, 200, 200),  # Light gray
    ( 10,  40, 100),  # Navy
    ( 50, 200, 100),  # Mint
    (255, 180, 100),  # Peach
]

# Tool display order: (key, label, shortcut)
TOOL_DEFS = [
    ("pencil",               "✏ Pencil",    "P"),
    ("line",                 "╱ Line",      "L"),
    ("fill",                 "⬟ Fill",      "F"),
    ("text",                 "T Text",      "T"),
    ("eraser",               "◻ Eraser",    "E"),
    ("rectangle",            "▭ Rect",      "R"),
    ("circle",               "○ Circle",    "C"),
    ("square",               "■ Square",    "S"),
    ("right_triangle",       "◺ R.Tri",     "G"),
    ("equilateral_triangle", "△ Eq.Tri",    "Q"),
    ("rhombus",              "◈ Rhombus",   "H"),
]

SHORTCUT_MAP = {d[2]: d[0] for d in TOOL_DEFS}   # e.g. "P" -> "pencil"


# ─────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, tag=None):
        self.rect  = pygame.Rect(rect)
        self.label = label
        self.tag   = tag

    def draw(self, surface, font, active=False, hovered=False):
        color = ACTIVE_BORDER if active else (BTN_HOVER if hovered else BTN_NORMAL)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        if active:
            pygame.draw.rect(surface, ACTIVE_BORDER, self.rect, 2, border_radius=6)
        txt = font.render(self.label, True, TEXT_COLOR)
        r   = txt.get_rect(center=self.rect.center)
        surface.blit(txt, r)

    def hit(self, pos):
        return self.rect.collidepoint(pos)


def _build_toolbar_buttons(font) -> list[Button]:
    """Create one button per tool, laid out horizontally in the toolbar."""
    buttons = []
    x = 8
    for key, label, shortcut in TOOL_DEFS:
        # measure label width
        w = font.size(label)[0] + 18
        btn = Button((x, 8, w, TOOLBAR_H - 16), label, tag=key)
        buttons.append(btn)
        x += w + 4
    return buttons


def _build_size_buttons() -> list[Button]:
    """Three brush-size buttons, right-aligned in the toolbar."""
    buttons = []
    x = WIN_W - 120
    for i, lbl in enumerate(SIZE_LABELS):
        btn = Button((x, 10, 34, TOOLBAR_H - 20), lbl, tag=i)
        buttons.append(btn)
        x += 38
    return buttons


def _build_palette_rects() -> list[tuple]:
    """Return (pygame.Rect, color) pairs for the bottom palette row."""
    result = []
    swatch_w = WIN_W // len(PALETTE_COLORS)
    for i, col in enumerate(PALETTE_COLORS):
        r = pygame.Rect(i * swatch_w, WIN_H - PALETTE_H + 4,
                        swatch_w - 2, PALETTE_H - 8)
        result.append((r, col))
    return result


# ─────────────────────────────────────────────────────────────
# Flood-fill lock (runs on canvas; needs pixel-level lock)
# ─────────────────────────────────────────────────────────────

def _safe_fill(canvas: pygame.Surface, pos, color):
    """Lock canvas, run fill, unlock."""
    canvas.lock()
    try:
        from tools import _flood_fill
        _flood_fill(canvas, pos, color)
    finally:
        canvas.unlock()


# ─────────────────────────────────────────────────────────────
# Save canvas
# ─────────────────────────────────────────────────────────────

def save_canvas(canvas: pygame.Surface):
    stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{stamp}.png"
    pygame.image.save(canvas, filename)
    return filename


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Paint — TSIS 2")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock  = pygame.time.Clock()

    # Fonts
    ui_font   = pygame.font.SysFont("segoeui",  13, bold=False)
    msg_font  = pygame.font.SysFont("segoeui",  15, bold=True)

    # Canvas
    canvas = pygame.Surface((CANVAS_W, CANVAS_H))
    canvas.fill(CANVAS_WHITE)

    # Tools
    tools        = build_tool_registry()
    active_tool  = "pencil"
    active_color = (0, 0, 0)
    size_idx     = 1            # 0=small, 1=medium, 2=large

    # UI elements
    tool_buttons  = _build_toolbar_buttons(ui_font)
    size_buttons  = _build_size_buttons()
    palette_swatches = _build_palette_rects()

    # Drawing state
    drawing   = False
    prev_pos  = None

    # Status message
    status_msg  = ""
    status_time = 0

    def set_status(msg):
        nonlocal status_msg, status_time
        status_msg  = msg
        status_time = pygame.time.get_ticks()

    def canvas_pos(screen_pos):
        """Map screen coordinates to canvas coordinates."""
        return (screen_pos[0], screen_pos[1] - CANVAS_TOP)

    def in_canvas(screen_pos):
        return CANVAS_TOP <= screen_pos[1] < CANVAS_BOT

    # ── Event loop ──────────────────────────────────────────
    running = True
    while running:
        mouse_screen = pygame.mouse.get_pos()
        mouse_canvas = canvas_pos(mouse_screen)
        tool         = tools[active_tool]
        brush_size   = BRUSH_SIZES[size_idx]

        for event in pygame.event.get():

            # ── Quit ──
            if event.type == pygame.QUIT:
                running = False

            # ── Keyboard ──
            elif event.type == pygame.KEYDOWN:

                # Text tool intercepts all keys when active
                text_tool = tools["text"]
                if active_tool == "text" and text_tool.active:
                    text_tool.handle_key(canvas, event, active_color)
                    continue  # don't process as shortcut

                # Ctrl+S → save
                mods = pygame.key.get_mods()
                if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    fname = save_canvas(canvas)
                    set_status(f"✓ Saved: {fname}")
                    continue

                # Brush size shortcuts
                if event.key == pygame.K_1:
                    size_idx = 0
                elif event.key == pygame.K_2:
                    size_idx = 1
                elif event.key == pygame.K_3:
                    size_idx = 2

                # Tool shortcuts (uppercase letters)
                key_name = pygame.key.name(event.key).upper()
                if key_name in SHORTCUT_MAP:
                    active_tool = SHORTCUT_MAP[key_name]
                    tools["text"].cancel()   # cancel any in-progress text

            # ── Mouse button down ──
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Toolbar tool buttons
                for btn in tool_buttons:
                    if btn.hit(pos):
                        tools["text"].cancel()
                        active_tool = btn.tag
                        break
                else:
                    # Toolbar size buttons
                    for btn in size_buttons:
                        if btn.hit(pos):
                            size_idx = btn.tag
                            break
                    else:
                        # Palette swatches (bottom bar)
                        if pos[1] >= CANVAS_BOT:
                            for rect, col in palette_swatches:
                                if rect.collidepoint(pos):
                                    active_color = col
                                    break
                        # Canvas area
                        elif in_canvas(pos):
                            drawing  = True
                            prev_pos = None
                            cp = canvas_pos(pos)
                            tool.on_mouse_down(canvas, cp, active_color, brush_size)
                            prev_pos = cp

            # ── Mouse motion ──
            elif event.type == pygame.MOUSEMOTION:
                if drawing and in_canvas(mouse_screen):
                    cp = mouse_canvas
                    tool.on_mouse_move(canvas, cp, prev_pos, active_color, brush_size)
                    prev_pos = cp

            # ── Mouse button up ──
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    cp = canvas_pos(event.pos)
                    tool.on_mouse_up(canvas, cp, active_color, brush_size)
                drawing  = False
                prev_pos = None

        # ── Render ──────────────────────────────────────────

        # 1. Toolbar background
        screen.fill(TOOLBAR_BG, (0, 0, WIN_W, TOOLBAR_H))

        # 2. Tool buttons
        for btn in tool_buttons:
            btn.draw(screen, ui_font,
                     active=(btn.tag == active_tool),
                     hovered=btn.hit(mouse_screen))

        # 3. Size buttons
        for i, btn in enumerate(size_buttons):
            btn.draw(screen, ui_font,
                     active=(i == size_idx),
                     hovered=btn.hit(mouse_screen))

        # 4. Active color swatch (in toolbar, right of size buttons)
        swatch_rect = pygame.Rect(WIN_W - 46, 10, 36, TOOLBAR_H - 20)
        pygame.draw.rect(screen, active_color, swatch_rect, border_radius=4)
        pygame.draw.rect(screen, TEXT_COLOR, swatch_rect, 1, border_radius=4)

        # 5. Canvas
        screen.blit(canvas, (0, CANVAS_TOP))

        # 6. Live preview overlay (shapes/line preview — drawn on screen, not canvas)
        preview_surf = screen.copy()   # draw preview on a copy so canvas stays clean
        if in_canvas(mouse_screen) or (active_tool == "line" and tools["line"]._start):
            tool.draw_preview(screen, mouse_canvas, active_color, brush_size)

        # 7. Status bar (drawn over canvas top-left if active)
        if status_msg and pygame.time.get_ticks() - status_time < 3000:
            label = msg_font.render(status_msg, True, (30, 30, 30))
            bg    = pygame.Surface((label.get_width() + 16, label.get_height() + 8))
            bg.fill((255, 255, 220))
            bg.set_alpha(230)
            screen.blit(bg, (8, CANVAS_TOP + 6))
            screen.blit(label, (16, CANVAS_TOP + 10))

        # 8. Palette bar
        screen.fill(PALETTE_BG, (0, CANVAS_BOT, WIN_W, PALETTE_H))
        for rect, col in palette_swatches:
            pygame.draw.rect(screen, col, rect, border_radius=3)
            if col == active_color:
                pygame.draw.rect(screen, ACTIVE_BORDER, rect, 2, border_radius=3)

        # 9. Tooltip line at bottom of toolbar
        tip_parts = [
            f"Tool: {active_tool.replace('_', ' ').title()}",
            f"Size: {SIZE_LABELS[size_idx]} ({BRUSH_SIZES[size_idx]}px)",
            "1/2/3=size  Ctrl+S=save  P/L/F/T/E/R/C/S/G/Q/H=tools",
        ]
        tip = ui_font.render("   |   ".join(tip_parts), True, (140, 140, 160))
        screen.blit(tip, (8, TOOLBAR_H - 16))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()