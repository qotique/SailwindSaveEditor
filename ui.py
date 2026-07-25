#!/usr/bin/env python3
"""Sailwind Save Editor — Flet GUI."""

import asyncio
import os
import json
import urllib.request
import webbrowser

import flet as ft

from core import KEY_FIELDS, SailwindSave, CURRENCY_NAMES, PORT_NAMES, SLIDER_FIELDS, REPUTATION_NAMES


VERSION = "1.0.4"

MAIN_TITLE = "Sailwind Save Editor"
SETTINGS_TITLE = "Settings"
GO_TO_SETTINGS = "Go to Settings"
SAFE_TO_EDIT = "Only safe fields"
SAFE_TO_EDIT_DESCRIPTION = "Show only safe to edit fields."
CHOOSE_THEME = "Theme"
CHOOSE_LANGUAGE = "Language"
DEFAULT_LANGUAGE = "English"
CHECK_UPDATES = "Check updates on startup"


class EditorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.save: SailwindSave | None = None
        self.fields_data: list[dict] = []
        self.controls_cache: dict[str, ft.Control] = {}
        self.show_safe_fields_only: bool = True
        self.selected_theme_mode: str = "SYSTEM"
        self.language: str = DEFAULT_LANGUAGE
        self.is_path_selected: bool = False

        page.title = "Sailwind Save Editor"
        page.theme_mode = self.themes[self.selected_theme_mode]
        page.padding = 20
        page.window_min_width = 800
        page.window_min_height = 600
        page.on_route_change = self.route_change
        page.on_view_pop = self.view_pop

        self.file_picker = ft.FilePicker()
        self.build_ui()
        self.route_change()

        self.page.run_task(self._load_settings)

    async def open_settings(self, e):
        await self.page.push_route("/settings")

    def build_ui(self):
        self.settings_btn = ft.Button(
            GO_TO_SETTINGS,
            on_click=self.open_settings,
        )

        self.path_text = ft.Text(
            "No file selected", italic=True, color=ft.Colors.OUTLINE
        )

        self.load_btn = ft.ElevatedButton(
            "Open Save File",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.on_open_click,
        )

        self.status_bar = ft.Text(size=12, color=ft.Colors.OUTLINE)

        self.fields_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.fields_container = ft.Container(
            content=self.fields_column,
            expand=True,
            padding=10,
            border=ft.border.Border(
                ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
                ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            ),
            border_radius=8,
        )

        self.save_btn = ft.ElevatedButton(
            "Save File",
            icon=ft.Icons.SAVE,
            on_click=self.on_save,
            disabled=True,
        )
        self.export_btn = ft.ElevatedButton(
            "Export JSON",
            icon=ft.Icons.FILE_DOWNLOAD,
            on_click=self.on_export_json,
            disabled=True,
        )
        self.import_btn = ft.ElevatedButton(
            "Import JSON",
            icon=ft.Icons.FILE_UPLOAD,
            on_click=self.on_import_json,
            disabled=True,
        )
        self.filter_toggle = ft.Switch(
            # label=SAFE_TO_EDIT,
            value=True,
            on_change=self.on_toggle_filter,
        )

        self.check_updates_toggle = ft.Switch(
            value=True,
            on_change=self.on_toggle_check_updates,
        )

        self.load_button_row = ft.Row(
            controls=[
                self.load_btn,
                self.import_btn
            ],
            spacing=10,
        )
        self.save_buttons_row = ft.Row(
            controls=[
                self.save_btn,
                self.export_btn,
            ]
        )

    def build_main_view(self):
        return ft.View(
                route="/",
                controls=[
                    ft.AppBar(
                        title=ft.Text(MAIN_TITLE, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    ),
                    self.settings_btn,
                    self.load_button_row,
                    self.path_text,
                    self.fields_container if self.is_path_selected else ft.Container(),
                    self.save_buttons_row if self.is_path_selected else ft.Container(),
                    self.status_bar,
                ]
            )

    def build_settings_view(self):
        return ft.View(
            route="/settings",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.AppBar(
                    title=ft.Text(SETTINGS_TITLE),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                ),
                ft.Text(SETTINGS_TITLE, theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                ft.Container(
                    width=500,
                    content=ft.ListTile(
                        dense=True,
                        title=ft.Text(SAFE_TO_EDIT_DESCRIPTION),
                        trailing=self.filter_toggle,
                    ),
                ),
                ft.Container(
                    width=500,
                    content=ft.ListTile(
                        dense=True,
                        title=ft.Text(CHOOSE_THEME),
                        trailing=ft.Dropdown(
                            width=180,
                            leading_icon=ft.Icons.COLORIZE,
                            value=self.selected_theme_mode,
                            options=self.get_theme_options(),
                            on_select=self.select_theme,
                        ),
                    ),
                ),
                ft.Container(
                    width=500,
                    content=ft.ListTile(
                        dense=True,
                        title=ft.Text("Language"),
                        trailing=ft.Dropdown(
                            width=180,
                            value=self.language,
                            options=self.get_language_options(),
                            on_select=self.select_language,
                        ),
                    ),
                ),
                ft.Container(
                    width=500,
                    content=ft.ListTile(
                        dense=True,
                        title=ft.Text(CHECK_UPDATES),
                        trailing=self.check_updates_toggle,
                    )
                )
            ]
        )

    async def on_toggle_check_updates(self, e):
        await self.page.shared_preferences.set("sailwind_editor.check_updates", e.control.value)

    @property
    def themes(self) -> dict[str, ft.ThemeMode]:
        return {
            "SYSTEM": ft.ThemeMode.SYSTEM,
            "DARK": ft.ThemeMode.DARK,
            "LIGHT": ft.ThemeMode.LIGHT
        }

    def get_theme_options(self) -> list[ft.DropdownOption]:
        return [
            ft.DropdownOption(key=key, text=key)
            for key, value in self.themes.items()
        ]

    async def select_theme(self, e: ft.Event[ft.Dropdown]):
        self.selected_theme_mode = e.control.value
        self.page.theme_mode = self.themes[self.selected_theme_mode]
        await self.page.shared_preferences.set("sailwind_editor.theme", self.selected_theme_mode)
        self.page.update()

    @property
    def languages(self) -> list[str]:
        return [
            "English",
            "Русский",
            "Українська",
        ]

    def get_language_options(self) -> list[ft.DropdownOption]:
        return [
            ft.DropdownOption(key=language)
            for language in self.languages
        ]

    async def select_language(self, e: ft.Event[ft.Dropdown]):
        if e.control.value != "English":
            alert = ft.AlertDialog(
                title=ft.Text("Languages are not supported yet"),
                content=ft.Text("Please check for updates."),
                actions=[ft.TextButton("Dismiss", on_click=lambda _: self.page.pop_dialog())],
                open=True,
            )
            self.page.show_dialog(alert)
            e.control.value = "EN"
            e.control.update()
            return

        self.language = e.control.value
        await self.page.shared_preferences.set("sailwind_editor.language", self.language)
        self.page.update()

    async def _load_settings(self):
        check_updates = await self.page.shared_preferences.get("sailwind_editor.check_updates")
        if check_updates is not None:
            self.check_updates_toggle.value = check_updates

        theme = await self.page.shared_preferences.get("sailwind_editor.theme")
        if theme:
            self.selected_theme_mode = theme
            self.page.theme_mode = self.themes[theme]

        show_safe_fields_only = await self.page.shared_preferences.get("sailwind_editor.show_safe_fields_only")
        if show_safe_fields_only is not None:
            self.show_safe_fields_only = show_safe_fields_only
            self.filter_toggle.value = show_safe_fields_only

        language = await self.page.shared_preferences.get("sailwind_editor.language")
        if language:
            self.language = language

        if any([check_updates is not None, theme, show_safe_fields_only is not None, language]):
            self.page.update()

        if self.check_updates_toggle.value:
            await self.check_for_updates()


    def route_change(self):
        self.page.views.clear()
        self.page.views.append(self.build_main_view())
        if self.page.route == "/settings":
            self.page.views.append(self.build_settings_view())
        self.page.update()

    async def view_pop(self, e):
        if e.view is not None:
            self.page.views.remove(e.view)
            top_view = self.page.views[-1]
            await self.page.push_route(top_view.route)

    async def on_toggle_filter(self, e):
        self.show_safe_fields_only = e.control.value
        await self.page.shared_preferences.set("sailwind_editor.show_safe_fields_only", e.control.value)
        self.refresh_fields()

    def on_open_click(self, e):
        self.page.run_task(self._pick_file)

    async def _pick_file(self):
        files = await self.file_picker.pick_files(
            dialog_title="Select Sailwind save file",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=['save'],
        )
        if files:
            self.load_file(files[0].path)

    def load_file(self, path: str):
        try:
            self.save = SailwindSave(path)
            self.path_text.value = os.path.abspath(path)
            self.is_path_selected = True
            self.path_text.color = ft.Colors.PRIMARY
            self.fields_data = self.save.get_all_fields()
            self.refresh_fields()
            self.save_btn.disabled = False
            self.export_btn.disabled = False
            self.import_btn.disabled = False
            self.status_bar.value = (
                f"Loaded: {os.path.basename(path)} | "
                f"{len(self.fields_data)} fields | "
                f"{os.path.getsize(path)} bytes"
            )
            self.route_change()
        except Exception as ex:
            self.status_bar.value = f"Error: {ex}"
            self.status_bar.color = ft.Colors.ERROR
        self.page.update()

    def refresh_fields(self):
        self.fields_column.controls.clear()
        self.controls_cache.clear()

        for entry in self.fields_data:
            name = entry['name']
            if self.show_safe_fields_only and name not in KEY_FIELDS:
                continue
            val = entry['value']
            ptype = entry.get('type', '?')
            is_key = name in KEY_FIELDS
            match name:
                case 'playerCurrency':
                    self._render_player_currency(value=val)
                    continue
                case 'currencyRates':
                    self._render_currency_rates(value=val)
                    continue
                case 'playerReputation':
                    self._render_player_reputation(value=val)
                    continue
                case 'lastVisitedPort':
                    self._render_last_visited_port(value=val)
                    continue

            row = self._build_field_row(name, val, ptype, is_key)
            self.fields_column.controls.append(row)

        self.page.update()

    def _render_field_group(self, title: str, names: list[str], values, cache_prefix: str, count: int):
        rows = [
            ft.Row(controls=[ft.Text(title)]),
        ]
        for i in range(count):
            label = ft.Text(
                names[i],
                weight=ft.FontWeight.BOLD,
                width=200,
                color=ft.Colors.PRIMARY,
            )
            field = ft.TextField(
                value=str(values[i]),
                width=300,
                height=40,
                text_size=13,
            )
            type_badge = ft.Container(
                content=ft.Text("Int32", size=10, color=ft.Colors.ON_SECONDARY_CONTAINER),
                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                border_radius=4,
            )
            self.controls_cache[f'{cache_prefix}{i}'] = field
            rows.append(
                ft.Row(
                    controls=[label, field, type_badge],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        col = ft.Column(spacing=4, controls=rows)
        container = ft.Container(
            content=col,
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        )
        self.fields_column.controls.append(container)
        
    def _render_player_currency(self, value):
        self._render_field_group("Currency", CURRENCY_NAMES, value, "playerCurrency_", 4)

    def _render_currency_rates(self, value):
        self._render_field_group("Currency Rates", CURRENCY_NAMES, value, "currencyRates_", 4)

    def _render_player_reputation(self, value):
        self._render_field_group("Reputation", REPUTATION_NAMES, value, "playerReputation_", 3)

    def _render_last_visited_port(self, value):
        label = ft.Text(
            "lastVisitedPort",
            weight=ft.FontWeight.BOLD,
            width=200,
            color=ft.Colors.PRIMARY,
        )
        type_badge = ft.Container(
            content=ft.Text("Int32", size=10, color=ft.Colors.ON_SECONDARY_CONTAINER),
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=4,
        )
        dropdown = ft.Dropdown(
            width=300,
            value=str(value),
            options=[
                ft.DropdownOption(key=str(k), text=v)
                for k, v in PORT_NAMES.items()
            ],
        )
        self.controls_cache['lastVisitedPort'] = dropdown
        row = ft.Row(
            controls=[label, dropdown, type_badge],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.fields_column.controls.append(row)

    def _build_field_row(self, name: str, val, ptype: str, is_key: bool):
        label = ft.Text(
            name,
            weight=ft.FontWeight.BOLD if is_key else ft.FontWeight.NORMAL,
            width=200,
            color=ft.Colors.PRIMARY if is_key else None,
        )

        type_badge = ft.Container(
            content=ft.Text(ptype, size=10, color=ft.Colors.ON_SECONDARY_CONTAINER),
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=4,
        )

        val_str = self._format_value(val)
        if name in SLIDER_FIELDS:
            input_field = ft.Slider(
                min=0,
                max=100,
                value=float(val),
                label="{value}",
                round=1,
                divisions=100,
            )
        else:
            input_field = ft.TextField(
                value=val_str,
                width=300,
                height=40,
                text_size=13,
            )
        self.controls_cache[name] = input_field

        return ft.Row(
            controls=[label, input_field, type_badge],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _format_value(self, val):
        if val is None:
            return ''
        if isinstance(val, list):
            return ', '.join(str(v) for v in val)
        if isinstance(val, float):
            return f'{val:.4f}'
        return str(val)

    def _parse_value(self, name: str, text: str):
        entry = next((e for e in self.fields_data if e['name'] == name), None)
        if not entry:
            return text
        ptype = entry.get('prim_type', 0)
        if entry.get('is_array'):
            parts = [p.strip() for p in text.split(',') if p.strip()]
            if ptype == 1:
                return [p.lower() in ('true', '1', 'yes') for p in parts]
            elif ptype in (7, 8, 9, 15, 16):
                return [int(p) for p in parts]
            elif ptype in (6, 11):
                return [float(p) for p in parts]
            return parts
        else:
            if ptype == 1:
                return text.lower() in ('true', '1', 'yes')
            elif ptype in (7, 8, 9, 15, 16):
                return int(text)
            elif ptype in (6, 11):
                return float(text)
            return text

    def collect_values(self) -> list[tuple[str, any]]:
        result = []

        curr_values = []
        for i in range(4):
            ctrl = self.controls_cache.get(f'playerCurrency_{i}')
            if ctrl is not None:
                try:
                    curr_values.append(int(ctrl.value))
                except ValueError:
                    curr_values.append(0)
        if curr_values:
            result.append(('playerCurrency', curr_values))

        rep_values = []
        for i in range(3):
            ctrl = self.controls_cache.get(f'playerReputation_{i}')
            if ctrl is not None:
                try:
                    rep_values.append(int(ctrl.value))
                except ValueError:
                    rep_values.append(0)
        if rep_values:
            result.append(('playerReputation', rep_values))

        rate_values = []
        for i in range(4):
            ctrl = self.controls_cache.get(f'currencyRates_{i}')
            if ctrl is not None:
                try:
                    rate_values.append(float(ctrl.value))
                except ValueError:
                    rate_values.append(0.0)
        if rate_values:
            result.append(('currencyRates', rate_values))

        for entry in self.fields_data:
            name = entry['name']

            if name == 'lastVisitedPort':
                ctrl = self.controls_cache.get(name)
                if ctrl is not None:
                    result.append((name, ctrl.value))
                    # for k, v in PORT_NAMES.items():
                    #     if v == ctrl.value:
                    #         result.append((name, k))
                    #         break
                continue

            ctrl = self.controls_cache.get(name)
            if ctrl is None:
                continue
            try:
                parsed = self._parse_value(name, ctrl.value)
                result.append((name, parsed))
            except (ValueError, TypeError):
                pass

        return result

    def on_save(self, e):
        if not self.save:
            return
        changes = self.collect_values()
        total_patches = 0
        errors = []
        for name, new_val in changes:
            try:
                patches = self.save.patch_field(name, new_val)
                total_patches += len(patches)
            except Exception as ex:
                errors.append(f"{name}: {ex}")
        try:
            size = self.save.save(backup=True)
            msg = f"Saved {size} bytes ({total_patches} patches applied)"
            if errors:
                msg += f" | Errors: {'; '.join(errors)}"
            self.status_bar.value = msg
            self.status_bar.color = ft.Colors.OUTLINE if not errors else ft.Colors.ERROR
        except Exception as ex:
            self.status_bar.value = f"Save error: {ex}"
            self.status_bar.color = ft.Colors.ERROR
        self.page.update()

    def on_export_json(self, e):
        if not self.save:
            return
        try:
            path = self.save.export_json()
            self.status_bar.value = f"Exported to {path}"
            self.status_bar.color = ft.Colors.OUTLINE
        except Exception as ex:
            self.status_bar.value = f"Export error: {ex}"
            self.status_bar.color = ft.Colors.ERROR
        self.page.update()

    def on_import_json(self, e):
        if not self.save:
            return
        try:
            import_patches = self.save.import_json()
            self.refresh_fields()
            self.status_bar.value = f"Imported {len(import_patches)} patches from JSON"
            self.status_bar.color = ft.Colors.OUTLINE
        except Exception as ex:
            self.status_bar.value = f"Import error: {ex}"
            self.status_bar.color = ft.Colors.ERROR
        self.page.update()

    async def check_for_updates(self, show_up_to_date=False):
        try:
            url = "https://api.github.com/repos/qotique/SailwindSaveEditor/releases/latest"
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(url, timeout=10)
            )
            data = json.loads(response.read().decode())
            latest_tag = data.get("tag_name", "")
            latest = latest_tag.lstrip("v")

            current_parts = [int(x) for x in VERSION.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]

            if latest_parts > current_parts:
                release_notes = data.get("body")
                if not release_notes:
                    release_notes = await self._fetch_commit_message(latest_tag)
                await self._show_update_dialog(
                    latest_tag,
                    data.get("html_url", ""),
                    release_notes or "",
                )
            elif show_up_to_date:
                await self._show_up_to_date_dialog()
        except Exception as ex:
            if show_up_to_date:
                await self._show_error_dialog(str(ex))

    async def _fetch_commit_message(self, tag_name):
        try:
            loop = asyncio.get_running_loop()
            url = f"https://api.github.com/repos/qotique/SailwindSaveEditor/git/ref/tags/{tag_name}"
            ref_resp = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(url, timeout=10)
            )
            sha = json.loads(ref_resp.read().decode())["object"]["sha"]

            url = f"https://api.github.com/repos/qotique/SailwindSaveEditor/git/commits/{sha}"
            commit_resp = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(url, timeout=10)
            )
            return json.loads(commit_resp.read().decode()).get("message", "")
        except Exception:
            return None

    async def _show_update_dialog(self, latest_tag, release_url, release_notes):
        notes_text = (
            release_notes
            if release_notes
            else "No release notes provided with this release.\n"
                 "See the release page on GitHub for details."
        )
        alert = ft.AlertDialog(
            title=ft.Text(f"Update Available: {latest_tag}"),
            content=ft.Text(
                f"Current version: v{VERSION}\n"
                f"Latest version: {latest_tag}\n\n"
                f"--- Release Notes ---\n\n"
                f"{notes_text}",
                selectable=True,
            ),
            actions=[
                ft.TextButton(
                    "Download",
                    on_click=lambda _: (
                        webbrowser.open(release_url),
                        self.page.pop_dialog(),
                    ),
                ),
                ft.TextButton(
                    "Dismiss",
                    on_click=lambda _: self.page.pop_dialog(),
                ),
            ],
            open=True,
        )
        self.page.show_dialog(alert)

    async def _show_up_to_date_dialog(self):
        alert = ft.AlertDialog(
            title=ft.Text("No Updates"),
            content=ft.Text(f"You have the latest version (v{VERSION})."),
            actions=[ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog())],
            open=True,
        )
        self.page.show_dialog(alert)

    async def _show_error_dialog(self, error_msg):
        alert = ft.AlertDialog(
            title=ft.Text("Check Failed"),
            content=ft.Text(f"Could not check for updates:\n{error_msg}"),
            actions=[ft.TextButton("OK", on_click=lambda _: self.page.pop_dialog())],
            open=True,
        )
        self.page.show_dialog(alert)


def main():
    ft.app(target=EditorApp)


if __name__ == '__main__':
    main()
