#!/usr/bin/env python3
"""Sailwind Save Editor — Flet GUI."""

import os

import flet as ft

from core import KEY_FIELDS, SailwindSave


MAIN_TITLE = "Sailwind Save Editor"
SETTINGS_TITLE = "Settings"
GO_TO_SETTINGS = "Go to Settings"
SAFE_TO_EDIT = "Only safe fields"
SAFE_TO_EDIT_DESCRIPTION = "Show only safe to edit fields."
CHOOSE_THEME = "Theme"
CHOOSE_LANGUAGE = "Language"
DEFAULT_LANGUAGE = "English"


class EditorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.save: SailwindSave | None = None
        self.fields_data: list[dict] = []
        self.controls_cache: dict[str, ft.TextField] = {}
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

        self.save_buttons_row = ft.Row(
            controls=[
                self.load_btn,
                self.save_btn,
            ],
            spacing=10,
        )
        self.json_buttons_row = ft.Row(
            controls=[
                self.export_btn,
                self.import_btn,
            ]
        )
        # self.page.views.append(self.build_main_view())
        # self.page.update()

    def build_main_view(self):
        return ft.View(
                route="/",
                controls=[
                    ft.AppBar(
                        title=ft.Text(MAIN_TITLE, weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    ),
                    self.settings_btn,
                    self.save_buttons_row,
                    self.path_text,
                    self.fields_container if self.is_path_selected else ft.Container(),
                    self.json_buttons_row if self.is_path_selected else ft.Container(),
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
            ]
        )
    
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

        if any([theme, show_safe_fields_only is not None, language]):
            self.page.update()


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

            row = self._build_field_row(name, val, ptype, is_key)
            self.fields_column.controls.append(row)

        self.page.update()

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
        for entry in self.fields_data:
            name = entry['name']
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


def main():
    ft.app(target=EditorApp)


if __name__ == '__main__':
    main()
