#!/usr/bin/env python3
"""Minimal pygame widget toolkit for the Sailwind Save Editor.

Single-window form UI built directly on pygame: labels, buttons, text
fields, sliders, dropdowns, switches, a scrollable list and modal dialogs.
Theming is handled by an app-provided color palette (dict of hex colors).
"""

import os
import sys
import traceback

import pygame



class FontManager:
    """Cached fonts with automatic per-weight/per-size creation and
    a search order that prefers fonts with Cyrillic coverage."""

    CANDIDATE_NAMES = (
        "dejavusans",
        "liberationsans",
        "notosans",
        "arial",
        "segoeui",
        "tahoma",
        "freesansbold",
    )

    CANDIDATE_PATHS = (
        "assets/fonts/DejaVuSans.ttf",
        "assets/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/msyh.ttc",
    )

    def __init__(self):
        self._sizes: dict = {}
        self._paths = self._resolve_paths()
        self._fonts: dict = {}

    def _resolve_paths(self) -> dict[str, str]:
        paths = {"regular": None, "bold": None, "italic": None}
        env_font = os.environ.get("SAILWIND_FONT")
        for p in ([env_font] if env_font else []) + [p for p in self.CANDIDATE_PATHS if os.path.isfile(p)]:
            name = os.path.basename(p).lower()
            if "bold" in name and ("italic" in name or "oblique" in name):
                paths["italic"] = p
            elif "bold" in name:
                paths["bold"] = p
            elif "italic" in name or "oblique" in name:
                paths["italic"] = p
            elif paths["regular"] is None:
                paths["regular"] = p
            if not any(v is not None for v in paths.values()):
                continue
            if sum(v is not None for v in paths.values()) >= 2:
                break

        for weight in ("regular", "bold", "italic"):
            if paths[weight] is None:
                try:
                    paths[weight] = pygame.font.match_font(weight, bold=weight == "bold")
                except Exception:
                    paths[weight] = None
        if paths["italic"] is None and paths["regular"]:
            paths["italic"] = paths["regular"]
        if paths["bold"] is None:
            paths["bold"] = paths["regular"]
        return paths

    def get_font(self, size: int, bold: bool = False, italic: bool = False) -> pygame.font.Font:
        key = (round(size), bold, italic)
        font = self._fonts.get(key)
        if font is None:
            path = self._paths["bold" if bold else ("regular" if not italic else "italic")]
            if path:
                try:
                    font = pygame.font.Font(path, round(size))
                except Exception:
                    font = pygame.font.Font(None, round(size))
            else:
                font = pygame.font.Font(None, round(size))
            self._fonts[key] = font
        return font


class Fonts:
    """Convenience facade with fixed text sizes used across the app."""

    def __init__(self, fm: FontManager):
        self.fm = fm

    def regular(self, size=14):
        return self.fm.get_font(size)

    def bold(self, size=14):
        return self.fm.get_font(size, bold=True)

    def italic(self, size=14):
        return self.fm.get_font(size, bold=False, italic=True)


def wrap_text(font, text, max_width):
    """Wrap text into a list of lines fitted to max_width."""
    lines = []
    for paragraph in str(text).split("\n"):
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if font.size(trial)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def text_height(font, lines):
    return len(lines) * (font.get_height() + 2)



PALETTES = {
    "LIGHT": {
        "BACKGROUND": "#F7F8FA",
        "SURFACE": "#FFFFFF",
        "SURFACE_CONTAINER": "#F3F0F8",
        "APPBAR": "#E6E1E9",
        "PRIMARY": "#4A5FD0",
        "ON_PRIMARY": "#FFFFFF",
        "PRIMARY_HOVER": "#3A4CBE",
        "ON_SURFACE": "#1C1B1F",
        "OUTLINE": "#767680",
        "OUTLINE_VARIANT": "#C5C6CE",
        "SECONDARY_CONTAINER": "#E8DEF8",
        "ON_SECONDARY_CONTAINER": "#1D192B",
        "ERROR": "#B3261E",
        "FIELD": "#FFFFFF",
        "DISABLED": "#C7C5D0",
        "ON_DISABLED": "#666479",
    },
    "DARK": {
        "BACKGROUND": "#131313",
        "SURFACE": "#1F1F22",
        "SURFACE_CONTAINER": "#211F26",
        "APPBAR": "#2B2930",
        "PRIMARY": "#B0B8FF",
        "ON_PRIMARY": "#1B1D4B",
        "PRIMARY_HOVER": "#9FA7F0",
        "ON_SURFACE": "#E5E1E9",
        "OUTLINE": "#E5E1E9",
        "OUTLINE_VARIANT": "#46464F",
        "SECONDARY_CONTAINER": "#4A4458",
        "ON_SECONDARY_CONTAINER": "#E8DEF8",
        "ERROR": "#F2B8B5",
        "FIELD": "#19191C",
        "DISABLED": "#333240",
        "ON_DISABLED": "#8B8893",
    },
    "PIXEL": {
        "BACKGROUND": "#181A24",
        "SURFACE": "#232838",
        "SURFACE_CONTAINER": "#2D3346",
        "APPBAR": "#11131B",
        "PRIMARY": "#FFCE4B",
        "ON_PRIMARY": "#241D00",
        "PRIMARY_HOVER": "#FFE082",
        "ON_SURFACE": "#F4F0FF",
        "OUTLINE": "#8E94A8",
        "OUTLINE_VARIANT": "#4A5068",
        "SECONDARY_CONTAINER": "#5A3FB0",
        "ON_SECONDARY_CONTAINER": "#E8DCFF",
        "ERROR": "#FF5A5A",
        "FIELD": "#1B1E2B",
        "DISABLED": "#32374A",
        "ON_DISABLED": "#6E7385",
        "radius": 0,
        "antialias": False,
        "pixel_scale": 2,
    },
}


def parse_color(value: str) -> tuple:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


class Theme:
    """Resolved palette with parsed RGB colors."""

    def __init__(self, palette: dict):
        self.palette = palette
        self.colors = {k: parse_color(v) for k, v in palette.items() if isinstance(v, str)}
        self.radius = palette.get("radius", 8)
        self.aa = palette.get("antialias", True)
        self.pixel_scale = palette.get("pixel_scale", 1)

    def c(self, name: str):
        return self.colors[name]

    def tone(self, color, amount):
        """Lighten (amount>0) or darken (amount<0) an RGB color toward white/black."""
        if amount >= 0:
            return tuple(min(255, int(c + (255 - c) * amount)) for c in color)
        amount = -amount
        return tuple(int(c * (1.0 - amount)) for c in color)

    @staticmethod
    def detect_system() -> str:
        if os.name == "nt":
            return "DARK"
        try:
            import subprocess
            out = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=2,
            )
            if "dark" in out.stdout.lower():
                return "DARK"
        except Exception:
            pass
        for var in ("GTK_THEME", "QT_QPA_PLATFORMTHEME"):
            if os.environ.get(var) and "dark" in os.environ[var].lower():
                return "DARK"
        return "DARK"




class Widget:
    def __init__(self, rect=None):
        self.rect = pygame.Rect(rect) if rect else pygame.Rect(0, 0, 0, 0)
        self.visible = True
        self.enabled = True

    def handle_event(self, event, app) -> bool:
        return False

    def screen_rect(self):
        return self.rect

    def draw(self, surface, theme, fonts) -> None:
        pass


class Panel(Widget):
    def __init__(self, rect):
        super().__init__(rect)

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        pygame.draw.rect(surface, theme.c("SURFACE"), self.rect, border_radius=theme.radius)
        draw_panel_frame(surface, theme, self.rect)


class Label(Widget):
    def __init__(self, rect, text="", color=None, fontsize=14, bold=False,
                 italic=False, align="left", wrap=False):
        super().__init__(rect)
        self.text = str(text)
        self.color_name = color
        self.fontsize = fontsize
        self.bold = bold
        self.italic = italic
        self.align = align
        self.wrap = wrap

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible or not self.text:
            return
        color = theme.c(self.color_name) if self.color_name else theme.c("ON_SURFACE")
        font = fonts.fm.get_font(self.fontsize, bold=self.bold, italic=self.italic)
        lines = wrap_text(font, self.text, self.rect.w) if self.wrap else [self.text]
        y = self.rect.y
        for line in lines:
            rendered = font.render(line, theme.aa, color)
            x = self.rect.x
            if self.align == "center":
                x = self.rect.centerx - rendered.get_width() // 2
            elif self.align == "right":
                x = self.rect.right - rendered.get_width()
            surface.blit(rendered, (x, y))
            y += font.get_height() + 2


class Button(Widget):
    def __init__(self, rect, text, on_click=None, kind="primary",
                 enabled=True, fontsize=14):
        super().__init__(rect)
        self.text = str(text)
        self.on_click = on_click
        self.kind = kind
        self.enabled = enabled
        self.fontsize = fontsize
        self.hover = False
        self._pressed = False

    def handle_event(self, event, app) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self._pressed
            self._pressed = False
            if was and self.rect.collidepoint(event.pos) and self.enabled and self.on_click:
                self.on_click()
                return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        bg = theme.c("PRIMARY")
        fg = theme.c("ON_PRIMARY")
        border = None
        if not self.enabled:
            bg = theme.c("DISABLED")
            fg = theme.c("ON_DISABLED")
        elif self.kind == "outlined":
            bg = theme.c("SURFACE")
            fg = theme.c("PRIMARY")
            border = theme.c("PRIMARY")
            if self.hover:
                bg = theme.c("SECONDARY_CONTAINER")
        elif self.kind == "text":
            bg = None
            fg = theme.c("PRIMARY")
            if self.hover:
                bg = theme.c("SECONDARY_CONTAINER")
        elif self.hover:
            bg = theme.c("PRIMARY_HOVER")
        if bg:
            pygame.draw.rect(surface, bg, self.rect, border_radius=theme.radius)
        if border:
            pygame.draw.rect(surface, border, self.rect, width=1, border_radius=theme.radius)
        font = fonts.fm.get_font(self.fontsize, bold=True)
        rendered = font.render(self.text, theme.aa, fg)
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))


class TextField(Widget):
    def __init__(self, rect, initial="", on_change=None, fontsize=14):
        super().__init__(rect)
        self.text = str(initial)
        self.cursor = len(self.text)
        self.on_change = on_change
        self.focused = False
        self.fontsize = fontsize

    @property
    def value(self):
        return self.text

    def focus_point(self, x):
        font = getattr(self, "_font", None)
        if font is None:
            font = pygame.font.Font(None, self.fontsize)
        rel_x = max(0, x - (self.rect.x + 8))
        best = 0
        for i in range(len(self.text) + 1):
            if font.size(self.text[:i])[0] <= rel_x:
                best = i
        self.cursor = best

    def handle_event(self, event, app) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.focused = True
                app.focused_field = self
                self.focus_point(event.pos[0])
                return True
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                self.focused = False
                if getattr(app, "focused_field", None) is self:
                    app.focused_field = None
                return True
            if event.key == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor = min(len(self.text), self.cursor + 1)
            elif event.key == pygame.K_HOME:
                self.cursor = 0
            elif event.key == pygame.K_END:
                self.cursor = len(self.text)
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor > 0:
                    self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
                    self.cursor -= 1
            elif event.key == pygame.K_DELETE:
                if self.cursor < len(self.text):
                    self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
            elif event.key == pygame.K_a and (event.mod & pygame.KMOD_CTRL):
                self.cursor = len(self.text)
            elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                self.insert(app.clipboard_text())
            elif event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL):
                app.clipboard_copy(self.text)
            elif event.key == pygame.K_u and (event.mod & pygame.KMOD_CTRL):
                self.text = ""
                self.cursor = 0
            elif event.unicode and event.unicode.isprintable():
                self.text = self.text[:self.cursor] + event.unicode + self.text[self.cursor:]
                self.cursor += len(event.unicode)
            else:
                return False
            if self.on_change:
                self.on_change()
            return True
        return False

    def insert(self, text):
        if not text:
            return
        self.text = self.text[:self.cursor] + text + self.text[self.cursor:]
        self.cursor += len(text)

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        bg = theme.c("FIELD")
        border = theme.c("PRIMARY") if self.focused else theme.c("OUTLINE_VARIANT")
        pygame.draw.rect(surface, bg, self.rect, border_radius=theme.radius)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=theme.radius)
        font = fonts.fm.get_font(self.fontsize)
        self._font = font
        text_w = self.rect.w - 16
        txt = self.text
        shown, start = txt, 0
        if font.size(txt)[0] > text_w:
            if self.cursor > 0 and font.size(txt[:self.cursor])[0] >= text_w:
                start = index_to_fit(txt, self.cursor, font, text_w)
            shown = txt[start:]
            while font.size(shown)[0] > text_w and len(shown) > 1:
                shown = shown[:-1]
        color = theme.c("ON_SURFACE")
        rendered = font.render(shown, theme.aa, color)
        ty = self.rect.centery - rendered.get_height() // 2
        surface.blit(rendered, (self.rect.x + 8, ty))
        if self.focused:
            caret_local = font.size(shown[:max(0, self.cursor - start)])
            caret_x = self.rect.x + 8 + caret_local[0]
            stem = pygame.Rect(caret_x, ty + 1, 1, rendered.get_height() - 2)
            pygame.draw.rect(surface, color, stem)


def index_to_fit(text, cursor, font, max_w):
    """Return start index so text[start:cursor] fits within max_w."""
    start = cursor
    while start > 0:
        if font.size(text[start:cursor])[0] <= max_w:
            break
        start -= 1
    return start


class Slider(Widget):
    def __init__(self, rect, value=0.0, min_val=0.0, max_val=100.0,
                 divisions=100, roundto=1, on_change=None):
        super().__init__(rect)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.divisions = divisions
        self.roundto = roundto
        self.value = float(value)
        self.on_change = on_change
        self._dragging = False

    def _pos_to_value(self, x):
        track = self.rect.inflate(-14, 0)
        frac = (x - track.x) / max(track.w, 1)
        frac = max(0.0, min(1.0, frac))
        val = self.min_val + frac * (self.max_val - self.min_val)
        if self.divisions:
            val = round(val * self.divisions) / self.divisions
        val = round(val, self.roundto)
        self.value = max(self.min_val, min(self.max_val, val))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = float(v)

    def handle_event(self, event, app) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._pos_to_value(event.pos[0])
                if self.on_change:
                    self.on_change()
                return True
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._pos_to_value(event.pos[0])
            if self.on_change:
                self.on_change()
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        track = pygame.Rect(self.rect.x + 7, self.rect.centery - 2, self.rect.w - 14, 4)
        pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), track, border_radius=theme.radius)
        frac = 0.0
        if self.max_val != self.min_val:
            frac = (self.value - self.min_val) / (self.max_val - self.min_val)
        filled = pygame.Rect(track.x, track.y, int(track.w * frac) + 1, track.h)
        if filled.w > 1:
            pygame.draw.rect(surface, theme.c("PRIMARY"), filled, border_radius=theme.radius)
        knob_x = track.x + int(track.w * frac)
        if theme.radius == 0:
            pygame.draw.rect(surface, theme.c("PRIMARY"), (knob_x - 8, track.centery - 8, 16, 16))
        else:
            pygame.draw.circle(surface, theme.c("PRIMARY"), (knob_x, track.centery), 8)
        font = fonts.fm.get_font(11)
        rendered = font.render(f"{self.value:g}", theme.aa, theme.c("ON_SECONDARY_CONTAINER"))
        bubble = pygame.Rect(knob_x - rendered.get_width() // 2, self.rect.y - 4, rendered.get_width() + 8, rendered.get_height() + 4)
        pygame.draw.rect(surface, theme.c("SECONDARY_CONTAINER"), bubble, border_radius=theme.radius)
        surface.blit(rendered, (bubble.x + 4, bubble.y + 2))


class Switch(Widget):
    def __init__(self, rect, value=False, on_change=None):
        super().__init__(rect)
        self.value = bool(value)
        self.on_change = on_change

    def handle_event(self, event, app) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.value = not self.value
            if self.on_change:
                self.on_change(self.value)
            return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        track = pygame.Rect(self.rect.x, self.rect.centery - 8, 32, 16)
        if self.value:
            pygame.draw.rect(surface, theme.c("PRIMARY"), track, border_radius=theme.radius)
            knob_x = track.right - 12
        else:
            pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), track, border_radius=theme.radius)
            knob_x = track.x + 4
        if theme.radius == 0:
            knob = pygame.Rect(
                track.right - 18 if self.value else track.x + 4,
                track.y + 2, 14, 12,
            )
            pygame.draw.rect(surface, theme.c("SURFACE"), knob)
            pygame.draw.rect(surface, theme.c("ON_PRIMARY"), knob, width=1)
        else:
            pygame.draw.circle(surface, theme.c("SURFACE"), (knob_x + 4, track.centery), 7)


class Dropdown(Widget):
    def __init__(self, rect, options, value=None, on_change=None, fontsize=13):
        super().__init__(rect)
        self.options = options
        self.value = value
        self.on_change = on_change
        self.open = False
        self.fontsize = fontsize
        self.hover_option = 0

    @property
    def label(self):
        for key, label in self.options:
            if key == self.value:
                return label
        return str(self.value) if self.value is not None else ""

    def menu_rect(self):
        h = len(self.options) * (28 if self.options else 28)
        return pygame.Rect(self.rect.x, self.rect.bottom, self.rect.w, h)

    def option_rect(self, i):
        r = self.menu_rect()
        return pygame.Rect(r.x, r.y + i * 28, r.w, 28)

    def handle_event(self, event, app) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.open = True
                self.hover_option = 0
                app.active_dropdown = self
                return True
        if event.type == pygame.MOUSEMOTION and self.open and app.active_dropdown is self:
            for i, _ in enumerate(self.options):
                if self.option_rect(i).collidepoint(event.pos):
                    self.hover_option = i
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.open and app.active_dropdown is self:
            r = self.menu_rect()
            if r.collidepoint(event.pos):
                i = (event.pos[1] - r.y) // 28
                if 0 <= i < len(self.options):
                    key = self.options[i][0]
                    if key != self.value:
                        self.value = key
                        if self.on_change:
                            self.on_change(key)
            self.open = False
            app.active_dropdown = None
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.open:
            self.open = False
            app.active_dropdown = None
            return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        bg = theme.c("FIELD")
        border = theme.c("PRIMARY") if self.open else theme.c("OUTLINE_VARIANT")
        pygame.draw.rect(surface, bg, self.rect, border_radius=theme.radius)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=theme.radius)
        font = fonts.fm.get_font(self.fontsize)
        rendered = font.render(self.label, theme.aa, theme.c("ON_SURFACE"))
        surface.blit(rendered, (self.rect.x + 8, self.rect.centery - rendered.get_height() // 2))
        chev = font.render("▼" if False else "v", theme.aa, theme.c("OUTLINE"))
        surface.blit(chev, (self.rect.right - 18, self.rect.centery - chev.get_height() // 2))

    def draw_menu(self, surface, theme, fonts):
        if not self.open:
            return
        rect = self.menu_rect()
        bg = theme.c("SURFACE")
        pygame.draw.rect(surface, bg, rect, border_radius=theme.radius)
        pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), rect, width=1, border_radius=theme.radius)
        font = fonts.fm.get_font(self.fontsize)
        for i, (key, label) in enumerate(self.options):
            item = self.option_rect(i)
            if i == self.hover_option:
                pygame.draw.rect(surface, theme.c("SECONDARY_CONTAINER"), item, border_radius=theme.radius)
            selected = key == self.value
            color = theme.c("PRIMARY") if selected else theme.c("ON_SURFACE")
            rendered = font.render(("✓ " if selected else "  ") + label, theme.aa, color)
            surface.blit(rendered, (item.x + 6, item.y + 5))


class ScrollArea(Widget):
    def __init__(self, rect, spacing=8, padding=10):
        super().__init__(rect)
        self.rows = []
        self.spacing = spacing
        self.padding = padding
        self.offset = 0
        self.content_height = 0
        self.placeholder = None

    def clear(self):
        self.rows = []
        self.offset = 0
        self.content_height = 0
        self.placeholder = None

    def add(self, row):
        self.rows.append(row)

    def layout(self):
        if self.placeholder is not None:
            self.placeholder.rect = pygame.Rect(self.rect)
            return
        area_w = self.rect.w - 2 * self.padding
        y = self.rect.y + self.padding
        for row in self.rows:
            row.visible = True
            h = row.height()
            row.place(pygame.Rect(self.rect.x + self.padding, y - self.offset, area_w, h))
            y += h + self.spacing
        self.content_height = y - self.rect.y - self.spacing
        max_off = max(0, self.content_height - self.rect.h)
        self.offset = max(0, min(self.offset, max_off))

    def handle_event(self, event, app) -> bool:
        if not self.visible:
            return False
        if self.placeholder is not None:
            return self.placeholder.handle_event(event, app)
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(app.mouse_pos) and self.content_height > self.rect.h:
                self.offset -= round(event.y * 36)
                self.layout()
                return True
            return False
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEMOTION:
            for row in reversed(self.rows):
                if row.rect.collidepoint(event.pos) if isinstance(event.pos, tuple) else False:
                    if row.handle_event(event, app):
                        return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        if not self.visible:
            return
        pygame.draw.rect(surface, theme.c("SURFACE"), self.rect, border_radius=theme.radius)
        if self.placeholder is not None:
            surface.set_clip(self.rect)
            self.placeholder.draw(surface, theme, fonts, dt)
            surface.set_clip(None)
            self._draw_frame(surface, theme)
            return
        surface.set_clip(self.rect)
        for row in self.rows:
            if row.screen_rect().bottom < self.rect.y or row.screen_rect().y > self.rect.bottom:
                continue
            row.draw(surface, theme, fonts, dt)
        surface.set_clip(None)
        if self.content_height > self.rect.h:
            track = pygame.Rect(self.rect.right - 10, self.rect.y + 3, 4, self.rect.h - 6)
            pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), track, border_radius=theme.radius)
            max_off = max(self.content_height - self.rect.h, 1)
            thumb_h = max(28, int(track.h * self.rect.h / self.content_height))
            thumb_y = track.y + int((track.h - thumb_h) * (self.offset / max_off))
            thumb = pygame.Rect(track.x, thumb_y, 4, thumb_h)
            pygame.draw.rect(surface, theme.c("PRIMARY"), thumb, border_radius=theme.radius)
        self._draw_frame(surface, theme)

    def _draw_frame(self, surface, theme):
        draw_panel_frame(surface, theme, self.rect)


def draw_panel_frame(surface, theme, rect):
    if theme.pixel_scale > 1:
        light = theme.tone(theme.c("SURFACE"), 0.30)
        dark = theme.tone(theme.c("SURFACE"), -0.30)
        pygame.draw.rect(surface, light, (rect.x, rect.y, rect.w, 2))
        pygame.draw.rect(surface, light, (rect.x, rect.y, 2, rect.h))
        pygame.draw.rect(surface, dark, (rect.x, rect.bottom - 2, rect.w, 2))
        pygame.draw.rect(surface, dark, (rect.right - 2, rect.y, 2, rect.h))
    else:
        pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), rect, width=1, border_radius=theme.radius)


class Row(Widget):
    """Composite horizontal row."""

    def __init__(self, left, width):
        super().__init__(pygame.Rect(left, 0, width, 0))
        self.children = []

    def height(self):
        return max(c.height if hasattr(c, "height") else c.rect.h for c in self.children)

    def place(self, rect):
        self.rect = rect

    def to_screen(self, local_rect, origin):
        return pygame.Rect(local_rect.x + origin[0], local_rect.y + origin[1], local_rect.w, local_rect.h)

    def handle_event(self, event, app) -> bool:
        for child in reversed(self.children):
            if child.rect.collidepoint(event.pos):
                if child.handle_event(event, app):
                    return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        for child in self.children:
            child.draw(surface, theme, fonts, dt=dt)


class PlaceholderText(Widget):
    def __init__(self, rect, text):
        super().__init__(rect)
        self.text = text

    def height(self):
        return 40

    def place(self, rect):
        self.rect = rect

    def handle_event(self, event, app):
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        font = fonts.italic(13)
        rendered = font.render(self.text, theme.aa, theme.c("OUTLINE"))
        surface.blit(rendered, (self.rect.x + 8, self.rect.centery - rendered.get_height() // 2))


class GrassArea(Widget):
    """Easter egg: animated grass (from /home/u/pygame-grass by DaFluffyPotato).

    Faithful to the original demo: a dense green lawn that bends away from the
    mouse (apply_force hover-repel), gently sways in the wind, and lets the
    player plant purple grass with the left mouse button.
    """

    GREEN_BG = (27, 66, 52)
    BRUSH_RADIUS = 10
    BRUSH_DROPOFF = 25
    TILE_SIZE = 10

    def __init__(self, rect, text, app=None):
        super().__init__(rect)
        self.text = str(text)
        self._app = app
        self._gm = None
        self._t = 0.0
        self._last_size = None
        self._clicking = False
        self._init_grass()

    def _init_grass(self):
        try:
            import grass as grass_mod
            assets_dir = os.path.join(os.path.dirname(os.path.abspath(grass_mod.__file__)), "grass_assets")
            mgr = grass_mod.GrassManager(
                assets_dir, tile_size=self.TILE_SIZE, stiffness=600,
                max_unique=5, place_range=[0, 1], padding=13,
            )
            mgr.enable_ground_shadows(shadow_radius=4, shadow_color=(0, 0, 1), shadow_shift=(1, 2))
            self._gm = mgr
        except Exception:
            self._gm = None

    def _seed(self, w, h):
        """Dense green lawn in the CENTER of the container only (like the demo's
        square patch: about 2/3 of the area, empty margins around it to draw in)."""
        if self._gm is None:
            return
        import random
        ts = self.TILE_SIZE
        pw = (self.rect.w * 2) // 3
        ph = (self.rect.h * 2) // 3
        offx = (self.rect.w - pw) // 2
        offy = (self.rect.h - ph) // 2
        x0 = (self.rect.x + offx) // ts
        y0 = (self.rect.y + offy) // ts
        x1 = (self.rect.x + offx + pw) // ts
        y1 = (self.rect.y + offy + ph) // ts
        for gy in range(y0, y1 + 1):
            for gx in range(x0, x1 + 1):
                v = random.random()
                if v > 0.1:
                    self._gm.place_tile((gx, gy), int(v * 12), [0, 1, 2, 3, 4])

    def _plant_purple(self, gx, gy):
        if self._gm is None:
            return
        import random
        self._gm.place_tile((gx, gy), int(random.random() * 12 + 1), [0, 1, 2, 3, 5])
        for ox, oy in ((-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)):
            self._gm.place_tile((gx + ox, gy + oy), int(random.random() * 14 + 3), [0, 1, 2, 3, 5])

    def height(self):
        return 0

    def place(self, rect):
        self.rect = rect

    def handle_event(self, event, app):
        if self._gm is None:
            return False
        if app is None or not hasattr(app, "mouse_pos"):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(app.mouse_pos):
                self._clicking = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._clicking = False
            return True
        return False

    def _brush_circle(self, surf, center, clicking):
        pygame.draw.circle(surf, (255, 255, 255), center,
                           self.BRUSH_RADIUS - int(clicking) * 2,
                           width=0 if clicking else 2)

    def draw(self, surface, theme, fonts, dt=0.0):
        if self._gm is None:
            return
        import math
        app = self._app
        rect = self.rect
        if rect.w <= 0 or rect.h <= 0:
            return
        if (rect.w, rect.h) != self._last_size:
            if self._last_size is not None:
                self._gm.clear()
            self._seed(rect.w, rect.h)
            self._last_size = (rect.w, rect.h)
        mouse = None
        if app is not None and hasattr(app, "mouse_pos"):
            mouse = app.mouse_pos
        inside = mouse is not None and rect.collidepoint(mouse)
        surface.set_clip(rect)
        pygame.draw.rect(surface, self.GREEN_BG, rect)
        self._t += dt
        ts = self.TILE_SIZE
        if inside and mouse is not None:
            if self._clicking:
                self._plant_purple(int(mouse[0] // ts), int(mouse[1] // ts))
            self._gm.apply_force(mouse, self.BRUSH_RADIUS, self.BRUSH_DROPOFF)
        self._gm.update_render(
            surface, dt, offset=(0, 0),
            rot_function=lambda x, y: int(math.sin(self._t / 60 + x * 0.011 + y * 0.017) * 15),
        )
        if inside and mouse is not None:
            self._brush_circle(surface, (int(mouse[0]), int(mouse[1])), self._clicking)
        surface.set_clip(None)
        font = fonts.italic(13)
        rendered = font.render(self.text, theme.aa, theme.c("ON_SURFACE"))
        surface.blit(rendered, (rect.x + 10, rect.y + 10))




class Dialog:
    def __init__(self, title, content, buttons, app, fontsize_title=17, fontsize_body=13):
        self.title = title
        self.content = content
        self.buttons = buttons
        self.app = app
        self.fontsize_title = fontsize_title
        self.fontsize_body = fontsize_body

    def layout(self):
        screen_w, screen_h = self.app.logical_size()
        box_w = min(520, screen_w - 60)
        title_font = self.app.fonts.fm.get_font(self.fontsize_title, bold=True)
        body_font = self.app.fonts.fm.get_font(self.fontsize_body)
        body_lines = wrap_text(body_font, self.content, box_w - 40)
        body_h = text_height(body_font, body_lines)
        btn_h = 34
        box_h = 40 + 80 + body_h + btn_h
        box_h = max(180, box_h)
        x = (screen_w - box_w) // 2
        y = (screen_h - box_h) // 2
        self.rect = pygame.Rect(x, y, box_w, box_h)
        y_cursor = y + 20
        self.title_rect = pygame.Rect(x + 20, y_cursor, box_w - 40, 26)
        y_cursor += 26
        self.body_rect = pygame.Rect(x + 20, y_cursor, box_w - 40, body_h)
        y_cursor += body_h + 8
        steps = (box_w - 40 - (len(self.buttons) - 1) * 8) // max(len(self.buttons), 1)
        self.button_rects = []
        bx = x + 20
        for i in range(len(self.buttons)):
            w = steps if i < len(self.buttons) - 1 or (box_w - 40) % max(len(self.buttons), 1) == 0 else steps + ((box_w - 40) - steps * len(self.buttons))
            self.button_rects.append(pygame.Rect(bx, y_cursor, w, btn_h))
            bx += w + 8
        self.body_lines = body_lines

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.close_dialog()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, brect in enumerate(self.button_rects):
                if brect.collidepoint(event.pos):
                    label, cb = self.buttons[i]
                    self.app.close_dialog()
                    if cb:
                        cb()
                    return True
        return False

    def draw(self, surface, theme, fonts):
        dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        surface.blit(dim, (0, 0))
        pygame.draw.rect(surface, theme.c("SURFACE"), self.rect, border_radius=theme.radius)
        pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), self.rect, width=1, border_radius=theme.radius)
        title_font = fonts.fm.get_font(self.fontsize_title, bold=True)
        t = title_font.render(self.title, theme.aa, theme.c("ON_SURFACE"))
        surface.blit(t, (self.title_rect.x, self.title_rect.y))
        body_font = fonts.fm.get_font(self.fontsize_body)
        y = self.body_rect.y
        for line in self.body_lines:
            r = body_font.render(line, theme.aa, theme.c("ON_SURFACE"))
            surface.blit(r, (self.body_rect.x, y))
            y += body_font.get_height() + 2
        for (label, _cb), brect in zip(self.buttons, self.button_rects):
            pygame.draw.rect(surface, theme.c("PRIMARY"), brect, border_radius=theme.radius)
            ft = fonts.fm.get_font(13, bold=True)
            btxt = ft.render(label, theme.aa, theme.c("ON_PRIMARY"))
            surface.blit(btxt, btxt.get_rect(center=brect.center))




class AppBase:
    """Wires widgets to the pygame event loop, handles overlays (dropdown
    menus and modal dialogs) and clipboard helpers."""

    TARGET_FPS = 60

    def __init__(self, width=900, height=700):
        pygame.init()
        pygame.display.set_caption("Sailwind Save Editor")
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.mouse_pos = (0, 0)
        self.fonts = Fonts(FontManager())
        self.fm = self.fonts.fm
        self.active_dropdown = None
        self.dialog = None
        self.focused_field = None
        self._work = None
        self.running = True
        self._clipboard_ready = self._init_clipboard()

    def _init_clipboard(self):
        try:
            pygame.scrap.init()
            pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)
            return True
        except Exception:
            return False

    def clipboard_text(self):
        if not self._clipboard_ready:
            return ""
        try:
            if pygame.scrap.contains(pygame.SCRAP_TEXT):
                data = pygame.scrap.get(pygame.SCRAP_TEXT)
                if isinstance(data, bytes):
                    return data.decode("utf-8", errors="replace")
                return str(data)
        except Exception:
            pass
        return ""

    def clipboard_copy(self, text):
        if not self._clipboard_ready:
            return
        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
        except Exception:
            pass

    def close_dialog(self):
        self.dialog = None

    def build_view(self):
        raise NotImplementedError

    def on_escape(self):
        pass

    def handle_dropdown_overlay(self, event):
        d = self.active_dropdown
        if d is not None and d.open:
            if d.handle_event(event, self):
                return True
        return False

    @property
    def scale(self):
        return getattr(self.current_theme(), "pixel_scale", 1)

    def logical_size(self):
        s = self.scale
        w, h = self.screen.get_size()
        return (max(1, w // s), max(1, h // s))

    def to_logical(self, pos):
        s = self.scale
        if s <= 1 or pos is None:
            return pos
        return (int(pos[0] / s), int(pos[1] / s))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.mouse_pos = self.to_logical(event.pos)
        if self.scale > 1 and hasattr(event, "pos"):
            event = pygame.event.Event(event.type, dict(event.dict, pos=self.to_logical(event.pos)))
        if self.dialog is not None:
            return self.dialog.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.active_dropdown and self.active_dropdown.open:
                    self.active_dropdown.open = False
                    self.active_dropdown = None
                    return True
                if self.focused_field is not None:
                    self.focused_field.focused = False
                    self.focused_field = None
                    return True
                self.on_escape()
                return True
            if self.focused_field is not None:
                self.focused_field.handle_event(event, self)
                return True
            return False
        if self.handle_dropdown_overlay(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            ff = self.focused_field
            if ff is not None and not ff.rect.collidepoint(event.pos):
                ff.focused = False
                self.focused_field = None
        for w in self.root_widgets:
            if w.handle_event(event, self):
                return True
        return False

    def render(self, dt):
        theme = self.current_theme()
        scale = getattr(theme, "pixel_scale", 1)
        target = self.screen
        if scale > 1:
            w, h = self.screen.get_size()
            logical = (max(1, w // scale), max(1, h // scale))
            if self._work is None or self._work.get_size() != logical:
                self._work = pygame.Surface(logical)
            target = self._work
        target.fill(theme.c("BACKGROUND"))
        water = getattr(self, "water", None)
        if scale > 1 and water is not None:
            bg = water.render(
                *logical, dt, base=theme.c("BACKGROUND"), line=theme.c("ON_SURFACE")
            )
            if bg is not None:
                target.blit(bg, (0, 0))
        for w in self.root_widgets:
            w.draw(target, theme, self.fonts, dt)
        if self.active_dropdown and self.active_dropdown.open:
            self.active_dropdown.draw_menu(target, theme, self.fonts)
        if self.dialog:
            self.dialog.draw(target, theme, self.fonts)
        if scale > 1:
            self.screen.blit(pygame.transform.scale(target, self.screen.get_size()), (0, 0))
        pygame.display.flip()

    def run_loop(self):
        while self.running:
            dt = self.clock.tick(self.TARGET_FPS) / 1000.0
            for event in pygame.event.get():
                try:
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        event_w = max(640, event.size[0])
                        event_h = max(480, event.size[1])
                        if (event_w, event_h) != self.screen.get_size():
                            try:
                                self.screen = pygame.display.set_mode((event_w, event_h), pygame.RESIZABLE)
                            except pygame.error:
                                pass
                        if hasattr(self, "layout"):
                            self.layout()
                    elif event.type == pygame.MOUSEMOTION:
                        self.handle_event(event)
                        continue
                    else:
                        self.handle_event(event)
                except Exception:
                    traceback.print_exc()
            try:
                self.tick(dt)
                self.render(dt)
            except Exception:
                traceback.print_exc()
        pygame.quit()
        sys.exit(0)