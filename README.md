# Sailwind Save Editor / Редактор сохранений Sailwind

Cross-platform save file editor for the game **Sailwind** (Steam App ID 1764530). Built with Python and [Flet](https://flet.dev/) for native desktop UI (Windows, Linux).
Кроссплатформенный редактор файлов сохранений для игры **Sailwind** (Steam App ID 1764530). Написан на Python с использованием [Flet](https://flet.dev/) для нативного интерфейса на Windows и Linux.

## Features / Возможности

- **Open `.save` files** via native file picker / Открытие `.save` файлов через нативный файловый диалог
- **Edit all editable fields** (Int32, Boolean, Int64, Single, etc.) in a table UI / Редактирование всех полей (Int32, Boolean, Int64, Single и др.) в табличном интерфейсе
- **Key fields highlighted** (playerGold, water/food/sleep, time/day, etc.) / Ключевые поля выделены (playerGold, вода/еда/сон, время/день и др.)
- **Auto-backup** creates `.bak` before saving / Автобэкап создаёт `.bak` перед сохранением
- **Export/Import JSON** for manual editing or version control / Экспорт/импорт JSON для ручного редактирования или версионирования
- **Cross-platform** — native desktop builds for Windows and Linux / Кроссплатформенность — нативные сборки для Windows и Linux

## Installation / Установка

### From Releases / Из релизов (Recommended / Рекомендуется)

Download the latest binary for your OS from the [Releases](https://github.com/qotique/SailwindSaveEditor/releases) page:
Скачайте готовый бинарник для вашей ОС со страницы [Releases](https://github.com/qotique/SailwindSaveEditor/releases):

- **Linux**: `sailwind_editor_linux`
- **Windows**: `sailwind_editor_windows.exe`

Make executable and run (Linux):
Сделайте исполняемым и запустите (Linux):

```bash
chmod +x sailwind_editor_linux
./sailwind_editor_linux ui
```

### From Source / Из исходников

```bash
pip install flet nrbf
python3 sailwind_editor.py ui
```

## Usage / Использование

### GUI

```bash
# Linux
./sailwind_editor_linux ui

# Windows
sailwind_editor_windows.exe ui
```

Opens a native window with:
Открывается нативное окно с:

- **Open Save File** button / Кнопка открытия файла сохранения
- Table of all editable fields with inline editing / Таблица всех редактируемых полей с inline-редактированием
- **Save File** (auto-backup + diff) / Сохранение файла (автобэкап + дифф)
- **Export JSON** / **Import JSON** / Экспорт/импорт JSON

### Default save path / Путь к сохранению по умолчанию (Steam Proton на Linux)

```
~/.local/share/Steam/steamapps/compatdata/1764530/pfx/drive_c/users/steamuser/AppData/LocalLow/Raw Lion Workshop/Sailwind/slot0.save
```

## Project Structure / Структура проекта

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

## Architecture / Архитектура

- **core.py** — Pure Python, no GUI dependencies. Parses .NET BinaryFormatter (NRBF) save files, finds field offsets, patches binary data in-place.
  Чистый Python, без GUI-зависимостей. Парсит .NET BinaryFormatter (NRBF), находит смещения полей, патчит бинарные данные inplace.
- **ui.py** — Flet-based GUI. Uses `FilePicker` for file selection, `TextField` for inline editing. Runs on desktop.
  GUI на Flet. Использует `FilePicker` для выбора файла, `TextField` для inline-редактирования. Работает на десктопе.
- **sailwind_editor.py** — Thin CLI wrapper reusing core logic.
  Тонкая CLI-обёртка, переиспользующая логику core.

## Testing / Тестирование

```bash
cd /home/u/sailwind_editor
python3 -m pytest tests/ -v
```

All 15 tests pass, covering:
Все 15 тестов проходят, покрывают:

- Field discovery (scalar/array, Int32/Boolean) / Обнаружение полей (скалярные/массивы, Int32/Boolean)
- Patch operations (scalar/array, Boolean edge cases) / Операции патчинга (скалярные/массивы, граничные случаи Boolean)
- JSON export/import round-trip / JSON экспорт/импорт туда-обратно
- Backup creation / Создание бэкапов
- Error handling / Обработка ошибок

## License / Лицензия

MIT License — see [LICENSE](LICENSE).

## Credits / Благодарности

- NRBF parsing via [`nrbf`](https://pypi.org/project/nrbf/) by @vickas
- UI via [Flet](https://flet.dev/) (Flutter-powered Python framework)