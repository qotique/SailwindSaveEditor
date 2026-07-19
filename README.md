# Sailwind Save Editor

Cross-platform save file editor for the game **Sailwind** (Steam App ID 1764530). Built with Python and [Flet](https://flet.dev/) for native desktop UI (Windows, macOS, Linux) with future mobile/web support.

## Features

- **Open `.save` files** via native file picker
- **Edit all editable fields** (Int32, Boolean, Int64, Single, etc.) in a table UI
- **Key fields highlighted** (playerGold, water/food/sleep, time/day, etc.)
- **Auto-backup** creates `.bak` before saving
- **Export/Import JSON** for manual editing or version control
- **Cross-platform** — Flet compiles to Windows/macOS/Linux desktop, with future Android/iOS/Web support

## Installation

```bash
pip install flet nrbf
```

Or use `pip install -e .` if packaging as a module.

## Usage

### CLI (original functionality preserved)

```bash
# Show editable fields
python3 sailwind_editor.py info [save_file]

# Export to JSON for manual editing
python3 sailwind_editor.py dump [save_file]

# Import from JSON
python3 sailwind_editor.py pack [save_file]

# Launch GUI
python3 sailwind_editor.py ui [save_file]
```

Default save path (Steam Proton on Linux):
```
~/.local/share/Steam/steamapps/compatdata/1764530/pfx/drive_c/users/steamuser/AppData/LocalLow/Raw Lion Workshop/Sailwind/slot0.save
```

### GUI

```bash
python3 sailwind_editor.py ui
```

Opens a native window with:
- **Open Save File** button
- Table of all editable fields with inline editing
- **Save File** (auto-backup + diff)
- **Export JSON** / **Import JSON**

## Project Structure

```
sailwind_editor/
├── core.py              # Core binary patching logic (SailwindSave class)
├── ui.py                # Flet GUI application
├── sailwind_editor.py   # CLI entry point (dump/pack/info/ui)
├── tests/
│   ├── conftest.py      # Test fixtures (mock save generator)
│   └── test_core.py     # Unit tests (15 tests passing)
└── README.md
```

## Architecture

- **core.py** — Pure Python, no GUI dependencies. Parses .NET BinaryFormatter (NRBF) save files, finds field offsets, patches binary data in-place.
- **ui.py** — Flet-based GUI. Uses `FilePicker` for file selection, `TextField` for inline editing. Runs on desktop; future-proof for mobile/web.
- **sailwind_editor.py** — Thin CLI wrapper reusing core logic.

## Testing

```bash
cd /home/u/sailwind_editor
python3 -m pytest tests/ -v
```

All 15 tests pass, covering:
- Field discovery (scalar/array, Int32/Boolean)
- Patch operations (scalar/array, Boolean edge cases)
- JSON export/import round-trip
- Backup creation
- Error handling

## License

MIT License — see [LICENSE](LICENSE).

## Credits

- NRBF parsing via [`nrbf`](https://pypi.org/project/nrbf/) by @vickas
- UI via [Flet](https://flet.dev/) (Flutter-powered Python framework)