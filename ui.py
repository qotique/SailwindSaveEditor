#!/usr/bin/env python3
"""Sailwind Save Editor — pygame GUI.

Replaces the previous Flet interface with a lightweight custom pygame
widget toolkit (see widgets.py). All business logic lives in core.py and
is untouched by this migration.
"""

import json
import os
import queue
import threading
import urllib.request
import webbrowser

import pygame

from core import (
    KEY_FIELDS,
    SailwindSave,
    CURRENCY_NAMES,
    PORT_NAMES,
    SLIDER_FIELDS,
    REPUTATION_NAMES,
)
from translations import Strings
from widgets import (
    AppBase,
    Button,
    Dialog,
    Dropdown,
    GrassArea,
    Label,
    PALETTES,
    Panel,
    PlaceholderText,
    ScrollArea,
    Slider,
    Switch,
    TextField,
    Theme,
    Widget,
)

VERSION = "2.0.0"

DEFAULT_LANGUAGE = "English"

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".sailwind_editor.json")




class Config:
    """Very small JSON-backed key/value store (replaces page.shared_preferences)."""

    def __init__(self):
        self.data = self._load()

    def _load(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self._save()

    def _save(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass


def pick_save_file(title):
    """Native file dialog via tkinter (blocking, like the old flet FilePicker)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Sailwind saves", "*.save"), ("All files", "*.*")],
        )
        root.destroy()
        return path or None
    except Exception:
        return None



class _Row(Widget):
    """Absolute-positioned composite row (children get screen-space rects)."""

    def __init__(self, height):
        super().__init__()
        self.children = []
        self._height = height

    def height(self):
        return self._height

    def place(self, rect):
        self.rect = rect

    def handle_event(self, event, app):
        for child in reversed(self.children):
            if child.rect.collidepoint(event.pos):
                if child.handle_event(event, app):
                    return True
        return False

    def draw(self, surface, theme, fonts, dt=0.0):
        for child in self.children:
            child.draw(surface, theme, fonts, dt=dt)


class _Badge(Widget):
    def __init__(self, rect, text):
        super().__init__(rect)
        self.text = text

    def draw(self, surface, theme, fonts, dt=0.0):
        pygame.draw.rect(surface, theme.c("SECONDARY_CONTAINER"), self.rect, border_radius=theme.radius)
        font = fonts.fm.get_font(10)
        rendered = font.render(self.text, theme.aa, theme.c("ON_SECONDARY_CONTAINER"))
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))


class FieldRow(_Row):
    """label + editor control + type badge."""

    MAX_BADGE_W = 110
    MIN_BADGE_W = 54
    MIN_LABEL_W = 110
    MAX_LABEL_W = 220
    MIN_FIELD_W = 90

    def __init__(self, label_text, field, badge_text, label_key=False):
        super().__init__(52)
        self.label = Label(
            pygame.Rect(0, 0, 200, 22),
            label_text,
            color="PRIMARY" if label_key else "ON_SURFACE",
            bold=label_key,
            fontsize=14,
        )
        self.field = field
        self.badge = _Badge(pygame.Rect(0, 0, self.MAX_BADGE_W, 24), badge_text)
        self.children = [self.label, self.field, self.badge]

    def place(self, rect):
        self.rect = rect
        label_w = min(self.MAX_LABEL_W, max(self.MIN_LABEL_W, int(rect.w * 0.30)))
        badge_w = min(self.MAX_BADGE_W, max(self.MIN_BADGE_W, int(rect.w * 0.16)))
        field_w = max(self.MIN_FIELD_W, rect.w - label_w - 14 - 16 - badge_w)
        self.label.rect = pygame.Rect(rect.x, rect.y + (rect.h - 22) // 2, label_w, 22)
        self.field.rect = pygame.Rect(rect.x + label_w + 14, rect.y + (rect.h - 40) // 2, field_w, 40)
        self.badge.rect = pygame.Rect(self.field.rect.right + 16, rect.y + (rect.h - 24) // 2, badge_w, 24)


class HeaderRow(_Row):
    def __init__(self, title):
        super().__init__(30)
        self.label = Label(pygame.Rect(0, 0, 400, 22), title, color="PRIMARY", bold=True, fontsize=14)
        self.children = [self.label]

    def place(self, rect):
        self.rect = rect
        self.label.rect = pygame.Rect(rect.x, rect.y, rect.w, 22)

    def draw(self, surface, theme, fonts, dt=0.0):
        super().draw(surface, theme, fonts, dt)
        pygame.draw.rect(surface, theme.c("OUTLINE_VARIANT"), (self.rect.x, self.rect.bottom - 1, self.rect.w, 1))



class EditorApp(AppBase):
    def __init__(self):
        super().__init__(900, 700)
        self.config = Config()
        self.language = self.config.get("language", DEFAULT_LANGUAGE)
        self.check_updates = self.config.get("check_updates", True)
        self.selected_theme_mode = self.config.get("theme", "PIXEL")
        self.show_safe_fields_only = self.config.get("show_safe_fields_only", True)
        self.save = None
        self.fields_data = []
        self.widgets_cache = {}
        self.status_text = ""
        self.status_error = False
        self.path_text = ""
        self.path_selected = False
        self.route = "/"
        self.root_widgets = []
        self.grass = None
        self.water = None
        try:
            from watershader import WaterShader
            self.water = WaterShader()
        except Exception:
            self.water = None
        self._theme = self._resolve_theme()
        self._upd_queue = None
        self._rebuild()
        pygame.display.set_caption(Strings.MainTitle[self.language])
        if self.check_updates:
            self._start_updater()


    def _resolve_theme(self):
        if self.selected_theme_mode == "LIGHT":
            return Theme(PALETTES["LIGHT"])
        if self.selected_theme_mode == "DARK":
            return Theme(PALETTES["DARK"])
        if self.selected_theme_mode == "PIXEL":
            return Theme(PALETTES["PIXEL"])
        detected = Theme.detect_system()
        return Theme(PALETTES[detected if detected in PALETTES else "DARK"])

    def current_theme(self):
        return self._theme


    def _start_updater(self):
        self._upd_queue = queue.Queue()

        def worker():
            try:
                with urllib.request.urlopen(
                    "https://api.github.com/repos/qotique/SailwindSaveEditor/releases/latest",
                    timeout=10,
                ) as resp:
                    data = json.loads(resp.read().decode())
                latest_tag = data.get("tag_name", "")
                latest = latest_tag.lstrip("v")
                try:
                    current_parts = [int(x) for x in VERSION.split(".")]
                    latest_parts = [int(x) for x in latest.split(".")]
                    has_update = latest_parts > current_parts
                except ValueError:
                    has_update = False
                if not has_update:
                    return
                self._upd_queue.put({
                    "tag": latest_tag,
                    "url": data.get("html_url", ""),
                    "notes": data.get("body") or "",
                })
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def tick(self, dt):
        if self._upd_queue is not None:
            try:
                result = self._upd_queue.get_nowait()
            except queue.Empty:
                result = None
            if result:
                self._show_update_dialog(result)

    def _show_update_dialog(self, result):
        notes = result.get("notes") or Strings.NoReleaseNotesProvided[self.language]
        url = result.get("url", "")
        content = (
            f"{Strings.CurrentVersion[self.language]}: v{VERSION}\n"
            f"{Strings.LatestVersion[self.language]}: {result['tag']}\n\n"
            f"--- Release Notes ---\n\n{notes}"
        )
        self.dialog = Dialog(
            title=f"Update Available: {result['tag']}",
            content=content,
            buttons=[
                (Strings.Download[self.language], lambda: webbrowser.open(url) if url else None),
                (Strings.Dismiss[self.language], None),
            ],
            app=self,
        )
        self.dialog.layout()
        self.active_dropdown = None


    def _rebuild(self):
        self.root_widgets = []
        self.active_dropdown = None
        if self.route == "/settings":
            self.build_settings_view()
        else:
            self.build_main_view()
        self.layout()

    def on_escape(self):
        if self.route == "/settings":
            self.route = "/"
            self._rebuild()


    def build_main_view(self):
        self.settings_btn = Button(
            pygame.Rect(0, 0, 160, 34),
            Strings.OpenSettings[self.language],
            on_click=lambda: self._goto("/settings"),
            kind="outlined",
        )
        self.load_btn = Button(
            pygame.Rect(0, 0, 170, 36),
            Strings.OpenSaveFile[self.language],
            on_click=self.on_open_click,
        )
        self.import_btn = Button(
            pygame.Rect(0, 0, 150, 36),
            Strings.ImportJSON[self.language],
            on_click=self.on_import_json,
            kind="outlined",
        )
        self.save_btn = Button(
            pygame.Rect(0, 0, 130, 34),
            Strings.SaveFile[self.language],
            on_click=self.on_save,
        )
        self.export_btn = Button(
            pygame.Rect(0, 0, 160, 34),
            Strings.ExportJSON[self.language],
            on_click=self.on_export_json,
            kind="outlined",
        )
        self.title_label = Label(
            pygame.Rect(0, 0, 400, 24),
            Strings.MainTitle[self.language],
            color="PRIMARY",
            bold=True,
            fontsize=17,
        )
        self.path_label = Label(pygame.Rect(0, 0, 500, 20), "", fontsize=13, italic=True)
        self.status_label = Label(pygame.Rect(0, 0, 500, 18), "", fontsize=12)
        self.scroll = ScrollArea(pygame.Rect(0, 0, 100, 100))
        self.root_widgets = [
            self.title_label,
            self.settings_btn,
            self.load_btn,
            self.import_btn,
            self.path_label,
            self.scroll,
            self.save_btn,
            self.export_btn,
            self.status_label,
        ]
        self.refresh_fields()

    def _goto(self, route):
        self.route = route
        self._rebuild()


    def build_settings_view(self):
        self.settings_panel = Panel(pygame.Rect(0, 0, 100, 100))
        self.back_btn = Button(
            pygame.Rect(0, 0, 110, 36),
            "< " + Strings.SettingsTitle[self.language],
            on_click=lambda: self._goto("/"),
            kind="outlined",
        )
        self.title_label = Label(
            pygame.Rect(0, 0, 400, 24),
            Strings.SettingsTitle[self.language],
            color="PRIMARY",
            bold=True,
            fontsize=17,
        )
        self.safe_switch = Switch(
            pygame.Rect(0, 0, 32, 32),
            value=self.show_safe_fields_only,
            on_change=self.on_toggle_filter,
        )
        self.theme_dropdown = Dropdown(
            pygame.Rect(0, 0, 180, 36),
            options=[(k, k) for k in ("SYSTEM", "DARK", "LIGHT", "PIXEL")],
            value=self.selected_theme_mode,
            on_change=self.select_theme,
        )
        self.lang_dropdown = Dropdown(
            pygame.Rect(0, 0, 180, 36),
            options=[(k, k) for k in ("English", "Русский", "Українська")],
            value=self.language,
            on_change=self.select_language,
        )
        self.updates_switch = Switch(
            pygame.Rect(0, 0, 32, 32),
            value=self.check_updates,
            on_change=self.on_toggle_check_updates,
        )
        self.root_widgets = [
            self.settings_panel,
            self.back_btn,
            self.title_label,
            Label(pygame.Rect(0, 0, 380, 20), Strings.SafeToEditDescription[self.language], fontsize=14),
            self.safe_switch,
            Label(pygame.Rect(0, 0, 200, 20), Strings.ChooseTheme[self.language], fontsize=14),
            self.theme_dropdown,
            Label(pygame.Rect(0, 0, 200, 20), Strings.ChooseLanguage[self.language], fontsize=14),
            self.lang_dropdown,
            Label(pygame.Rect(0, 0, 300, 20), Strings.CheckUpdates[self.language], fontsize=14),
            self.updates_switch,
        ]


    def layout(self):
        w, h = self.logical_size()
        if self.route == "/settings":
            self._layout_settings(w, h)
        else:
            self._layout_main(w, h)

    def _layout_main(self, w, h):
        self.title_label.rect = pygame.Rect(20, 12, w - 280, 24)
        self.settings_btn.rect = pygame.Rect(w - 184, 10, 164, 34)
        self.load_btn.rect = pygame.Rect(20, 58, 170, 36)
        self.import_btn.rect = pygame.Rect(200, 58, 150, 36)
        self.path_label.rect = pygame.Rect(20, 102, w - 40, 20)
        self.path_label.text = self.path_text or Strings.NoFileSelected[self.language]
        self.path_label.color_name = "PRIMARY" if self.path_selected else "OUTLINE"
        self.save_btn.rect = pygame.Rect(20, h - 48, 130, 34)
        self.export_btn.rect = pygame.Rect(160, h - 48, 160, 34)
        self.status_label.rect = pygame.Rect(336, h - 44, w - 356, 18)
        self.status_label.text = self.status_text
        self.status_label.color_name = "ERROR" if self.status_error else "OUTLINE"
        self.scroll.rect = pygame.Rect(20, 132, w - 40, h - 132 - 62)
        self.scroll.layout()

    def _layout_settings(self, w, h):
        self.back_btn.rect = pygame.Rect(20, 12, 150, 36)
        self.title_label.rect = pygame.Rect(190, 16, 300, 24)
        panel_w = min(600, max(40, w - 40))
        x0 = (w - panel_w) // 2
        self.settings_panel.rect = pygame.Rect(x0 - 20, 80, panel_w + 40, 248)
        self.safe_switch.rect = pygame.Rect(x0 + panel_w - 60, 96, 32, 32)
        self.theme_dropdown.rect = pygame.Rect(x0 + panel_w - 200, 152, 180, 36)
        self.lang_dropdown.rect = pygame.Rect(x0 + panel_w - 200, 208, 180, 36)
        self.updates_switch.rect = pygame.Rect(x0 + panel_w - 60, 276, 32, 32)
        rows = [
            (0, Strings.SafeToEditDescription[self.language], (x0 + 60, 96, 380, 20)),
            (1, Strings.ChooseTheme[self.language], (x0 + 60, 156, 200, 20)),
            (2, Strings.ChooseLanguage[self.language], (x0 + 60, 212, 200, 20)),
            (3, Strings.CheckUpdates[self.language], (x0 + 60, 280, 300, 20)),
        ]
        for i, text, rect in rows:
            self.root_widgets[3 + i * 2].text = text
            self.root_widgets[3 + i * 2].rect = pygame.Rect(rect)


    def _snapshot_values(self):
        snap = {}
        for name, control in self.widgets_cache.items():
            try:
                snap[name] = control.value
            except Exception:
                continue
        return snap

    def refresh_fields(self, preserve=True):
        snap = self._snapshot_values() if preserve else {}
        self.widgets_cache.clear()
        self.grass = None
        self.scroll.clear()

        if not self.path_selected:
            if self.save is None:
                if self._theme.pixel_scale > 1:
                    self.grass = GrassArea(
                        pygame.Rect(0, 0, 300, 40),
                        f"{Strings.NoFileSelected[self.language]}. Touch grass",
                        app=self,
                    )
                    self.scroll.placeholder = self.grass
                else:
                    self.scroll.add(PlaceholderText(
                        pygame.Rect(0, 0, 300, 40), Strings.NoFileSelected[self.language]
                    ))
            return

        for entry in self.fields_data:
            name = entry["name"]
            if self.show_safe_fields_only and name not in KEY_FIELDS:
                continue
            val = entry["value"]
            ptype = entry.get("type", "?")
            is_key = name in KEY_FIELDS
            if name == "playerCurrency":
                self._render_group("Currency", CURRENCY_NAMES, val, "playerCurrency_", 4, snap)
            elif name == "currencyRates":
                self._render_group("Currency Rates", CURRENCY_NAMES, val, "currencyRates_", 4, snap)
            elif name == "playerReputation":
                self._render_group("Reputation", REPUTATION_NAMES, val, "playerReputation_", 3, snap)
            elif name == "lastVisitedPort":
                self._render_port_dropdown(val, snap)
            else:
                self._build_single_field_row(name, val, ptype, is_key, snap)

        self.scroll.layout()

    def _render_group(self, title, names, values, prefix, count, snap):
        self.scroll.add(HeaderRow(title))
        for i in range(count):
            key = f"{prefix}{i}"
            init = snap.get(key, values[i]) if len(values) > i else ""
            field = TextField(pygame.Rect(0, 0, 320, 40), initial=str(init))
            self.widgets_cache[key] = field
            self.scroll.add(FieldRow(names[i], field, "Int32"))

    def _render_port_dropdown(self, value, snap):
        name = "lastVisitedPort"
        options = [(str(k), v) for k, v in PORT_NAMES.items()]
        field = Dropdown(
            pygame.Rect(0, 0, 320, 40),
            options=options,
            value=str(snap.get(name, value)),
        )
        self.widgets_cache[name] = field
        self.scroll.add(FieldRow(name, field, "Int32", label_key=True))

    def _build_single_field_row(self, name, val, ptype, is_key, snap):
        init = snap.get(name, val)
        if name in SLIDER_FIELDS:
            try:
                fval = float(init)
            except (TypeError, ValueError):
                fval = 0.0
            field = Slider(
                pygame.Rect(0, 0, 320, 40),
                value=fval,
                min_val=0.0,
                max_val=100.0,
                divisions=100,
                roundto=1,
            )
        else:
            field = TextField(pygame.Rect(0, 0, 320, 40), initial=self._format_value(init))
        self.widgets_cache[name] = field
        self.scroll.add(FieldRow(name, field, ptype, label_key=is_key))


    def on_open_click(self):
        path = pick_save_file(Strings.SelectSaveFile[self.language])
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            self.save = SailwindSave(path)
            self.path_text = os.path.abspath(path)
            self.path_selected = True
            self.fields_data = self.save.get_all_fields()
            self.refresh_fields(preserve=False)
            self.status_text = (
                f"Loaded: {os.path.basename(path)} | "
                f"{len(self.fields_data)} fields | "
                f"{os.path.getsize(path)} bytes"
            )
            self.status_error = False
        except Exception as ex:
            self.status_text = f"Error: {ex}"
            self.status_error = True
        self.layout()

    def on_toggle_filter(self, value):
        self.show_safe_fields_only = bool(value)
        self.config.set("show_safe_fields_only", self.show_safe_fields_only)
        self.refresh_fields()

    def on_toggle_check_updates(self, value):
        self.check_updates = bool(value)
        self.config.set("check_updates", self.check_updates)

    def select_theme(self, key):
        self.selected_theme_mode = key
        self.config.set("theme", key)
        self._theme = self._resolve_theme()
        self._rebuild()

    def select_language(self, key):
        if key not in ("English", "Русский"):
            self.show_language_dialog(key)
            return
        self.language = key
        self.config.set("language", key)
        self._rebuild()
        if self.save:
            self.refresh_fields()
        pygame.display.set_caption(Strings.MainTitle[self.language])

    def show_language_dialog(self, key):
        self.dialog = Dialog(
            title=key + Strings.LanguageNotSupportedYetTitle[self.language],
            content=Strings.LanguageNotSupportedYetDescription[self.language],
            buttons=[(Strings.Dismiss[self.language], None)],
            app=self,
        )
        self.dialog.layout()


    def _format_value(self, val):
        if val is None:
            return ""
        if isinstance(val, list):
            return ", ".join(str(v) for v in val)
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    def _parse_value(self, name, text):
        entry = next((e for e in self.fields_data if e["name"] == name), None)
        if not entry:
            return text
        ptype = entry.get("prim_type", 0)
        if entry.get("is_array"):
            parts = [p.strip() for p in str(text).split(",") if p.strip()]
            if ptype == 1:
                return [p.lower() in ("true", "1", "yes") for p in parts]
            elif ptype in (7, 8, 9, 15, 16):
                return [int(p) for p in parts]
            elif ptype in (6, 11):
                return [float(p) for p in parts]
            return parts
        if ptype == 1:
            return str(text).lower() in ("true", "1", "yes")
        elif ptype in (7, 8, 9, 15, 16):
            return int(text)
        elif ptype in (6, 11):
            return float(text)
        return text

    def collect_values(self):
        result = []
        curr_values = []
        for i in range(4):
            ctrl = self.widgets_cache.get(f"playerCurrency_{i}")
            if ctrl is not None:
                try:
                    curr_values.append(int(ctrl.value))
                except ValueError:
                    curr_values.append(0)
        if curr_values:
            result.append(("playerCurrency", curr_values))

        rep_values = []
        for i in range(3):
            ctrl = self.widgets_cache.get(f"playerReputation_{i}")
            if ctrl is not None:
                try:
                    rep_values.append(int(ctrl.value))
                except ValueError:
                    rep_values.append(0)
        if rep_values:
            result.append(("playerReputation", rep_values))

        rate_values = []
        for i in range(4):
            ctrl = self.widgets_cache.get(f"currencyRates_{i}")
            if ctrl is not None:
                try:
                    rate_values.append(float(ctrl.value))
                except ValueError:
                    rate_values.append(0.0)
        if rate_values:
            result.append(("currencyRates", rate_values))

        for entry in self.fields_data:
            name = entry["name"]
            if name == "lastVisitedPort":
                ctrl = self.widgets_cache.get(name)
                if ctrl is not None:
                    result.append((name, ctrl.value))
                continue
            ctrl = self.widgets_cache.get(name)
            if ctrl is None:
                continue
            try:
                parsed = self._parse_value(name, ctrl.value)
                result.append((name, parsed))
            except (ValueError, TypeError):
                pass
        return result

    def on_save(self):
        if not self.save:
            return
        changes = self.collect_values()
        total_patches = 0
        errors = []
        for name, new_val in changes:
            try:
                total_patches += len(self.save.patch_field(name, new_val))
            except Exception as ex:
                errors.append(f"{name}: {ex}")
        try:
            size = self.save.save(backup=True)
            msg = f"Saved {size} bytes ({total_patches} patches applied)"
            if errors:
                msg += f" | Errors: {'; '.join(errors)}"
            self.status_text = msg
            self.status_error = bool(errors)
        except Exception as ex:
            self.status_text = f"Save error: {ex}"
            self.status_error = True
        self.layout()

    def on_export_json(self):
        if not self.save:
            return
        try:
            path = self.save.export_json()
            self.status_text = f"Exported to {path}"
            self.status_error = False
        except Exception as ex:
            self.status_text = f"Export error: {ex}"
            self.status_error = True
        self.layout()

    def on_import_json(self):
        if not self.save:
            return
        try:
            import_patches = self.save.import_json()
            self.refresh_fields()
            self.status_text = f"Imported {len(import_patches)} patches from JSON"
            self.status_error = False
        except Exception as ex:
            self.status_text = f"Import error: {ex}"
            self.status_error = True
        self.layout()


def main():
    app = EditorApp()
    app.run_loop()


if __name__ == "__main__":
    main()