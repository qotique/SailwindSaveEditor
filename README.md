# Sailwind Save Editor

Cross-platform save file editor for the game **Sailwind** (Steam App ID 1764530). Built with Python and [pygame](https://www.pygame.org/) for native desktop UI (Windows, Linux).

---

# Редактор сохранений Sailwind

Кроссплатформенный редактор файлов сохранений для игры **Sailwind** (Steam App ID 1764530). Написан на Python с использованием [pygame](https://www.pygame.org/) для нативного интерфейса на Windows и Linux.

## Features

- **Open `.save` files** via native file picker
- **Edit all editable fields** (Int32, Boolean, Int64, Single, etc.) in a table UI
- **Key fields highlighted** (playerGold, water/food/sleep, time/day, etc.)
- **Auto-backup** creates `.bak` before saving
- **Export/Import JSON** for manual editing or version control
- **Cross-platform** — native desktop builds for Windows and Linux

## Возможности

- **Открытие `.save` файлов** через нативный файловый диалог
- **Редактирование всех полей** (Int32, Boolean, Int64, Single и др.) в табличном интерфейсе
- **Ключевые поля выделены** (playerGold, вода/еда/сон, время/день и др.)
- **Автобэкап** создаёт `.bak` перед сохранением
- **Экспорт/импорт JSON** для ручного редактирования или версионирования
- **Кроссплатформенность** — нативные сборки для Windows и Linux

## Installation

### From Releases (Recommended)

Download the latest binary for your OS from the [Releases](https://github.com/qotique/SailwindSaveEditor/releases) page:

- **Linux**: `sailwind_editor_linux`
- **Windows**: `sailwind_editor_windows.exe`

Make executable and run (Linux):

```bash
chmod +x sailwind_editor_linux
./sailwind_editor_linux ui
```

### From Source

```bash
pip install pygame-ce nrbf
python3 sailwind_editor.py ui
```

## Установка

### Из релизов (Рекомендуется)

Скачайте готовый бинарник для вашей ОС со страницы [Releases](https://github.com/qotique/SailwindSaveEditor/releases):

- **Linux**: `sailwind_editor_linux`
- **Windows**: `sailwind_editor_windows.exe`

Сделайте исполняемым и запустите (Linux):

```bash
chmod +x sailwind_editor_linux
./sailwind_editor_linux ui
```

### Из исходников

```bash
pip install pygame nrbf
python3 sailwind_editor.py ui
```

## Usage

### GUI (default)

```bash
# Linux
./sailwind_editor_linux

# Windows
sailwind_editor_windows.exe
```

Opens native window with:
- **Open Save File** button
- Table of all editable fields with inline editing
- **Save File** (auto-backup + diff)
- **Export JSON** / **Import JSON**

### CLI

```bash
# Show editable fields
./sailwind_editor_linux info [save_file]

# Export to JSON for manual editing
./sailwind_editor_linux dump [save_file]

# Import from JSON
./sailwind_editor_linux pack [save_file]
```

Default save path (Steam Proton on Linux):
```
~/.local/share/Steam/steamapps/compatdata/1764530/pfx/drive_c/users/steamuser/AppData/LocalLow/Raw Lion Workshop/Sailwind/slot0.save
```

## Использование

### GUI (по умолчанию)

```bash
# Linux
./sailwind_editor_linux

# Windows
sailwind_editor_windows.exe
```

Открывается нативное окно с:
- Кнопка открытия файла сохранения
- Таблица всех редактируемых полей с inline-редактированием
- **Сохранение файла** (автобэкап + дифф)
- **Экспорт/импорт JSON**

### CLI

```bash
# Показать редактируемые поля
./sailwind_editor_linux info [файл_сохранения]

# Экспорт в JSON для ручного редактирования
./sailwind_editor_linux dump [файл_сохранения]

# Импорт из JSON
./sailwind_editor_linux pack [файл_сохранения]
```

Путь к сохранению по умолчанию (Steam Proton на Linux):
```
~/.local/share/Steam/steamapps/compatdata/1764530/pfx/drive_c/users/steamuser/AppData/LocalLow/Raw Lion Workshop/Sailwind/slot0.save
```

## Project Structure

```
sailwind_editor/
├── core.py              # Core binary patching logic (SailwindSave class)
├── widgets.py           # Custom pygame widget toolkit (labels, fields, sliders...)
├── ui.py                # pygame GUI application
├── sailwind_editor.py   # CLI entry point (dump/pack/info/ui)
├── tests/
│   ├── conftest.py      # Test fixtures (mock save generator)
│   └── test_core.py     # Unit tests (15 tests passing)
└── README.md
```

## Структура проекта

```
sailwind_editor/
├── core.py              # Ядро: бинарный патчинг (класс SailwindSave)
├── widgets.py           # Тулкит виджетов на pygame (лейблы, поля, слайдеры...)
├── ui.py                # GUI на pygame
├── sailwind_editor.py   # CLI точка входа (dump/pack/info/ui)
├── tests/
│   ├── conftest.py      # Фикстуры тестов (генератор мок-сохранений)
│   └── test_core.py     # Юнит-тесты (15 тестов проходят)
└── README.md
```

## Architecture

- **core.py** — Pure Python, no GUI dependencies. Parses .NET BinaryFormatter (NRBF) save files, finds field offsets, patches binary data in-place.
- **widgets.py** — Custom pygame widget toolkit: buttons, text fields, sliders, dropdowns, switches, scroll area and modal dialogs. Includes a font manager with Cyrillic support and light/dark palettes.
- **ui.py** — pygame GUI. Uses a native file dialog via tkinter for file selection, inline editing widgets. Runs on desktop.
- **sailwind_editor.py** — Thin CLI wrapper reusing core logic.

## Архитектура

- **core.py** — Чистый Python, без GUI-зависимостей. Парсит .NET BinaryFormatter (NRBF), находит смещения полей, патчит бинарные данные inplace.
- **widgets.py** — Собственный тулкит виджетов на pygame: кнопки, текстовые поля, слайдеры, выпадающие списки, переключатели, скролл-область и модальные диалоги. Включает менеджер шрифтов с поддержкой кириллицы и светлую/тёмную палитру.
- **ui.py** — GUI на pygame. Использует нативный файловый диалог (tkinter) для выбора файла и виджеты inline-редактирования. Работает на десктопе.
- **sailwind_editor.py** — Тонкая CLI-обёртка, переиспользующая логику core.

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

## Тестирование

```bash
cd /home/u/sailwind_editor
python3 -m pytest tests/ -v
```

Все 15 тестов проходят, покрывают:
- Обнаружение полей (скалярные/массивы, Int32/Boolean)
- Операции патчинга (скалярные/массивы, граничные случаи Boolean)
- JSON экспорт/импорт туда-обратно
- Создание бэкапов
- Обработку ошибок

## License

MIT License — see [LICENSE](LICENSE).

## Лицензия

MIT License — см. [LICENSE](LICENSE).

## Credits

- NRBF parsing via [`nrbf`](https://pypi.org/project/nrbf/) by @vickas
- UI via [pygame](https://www.pygame.org/) (custom widget toolkit in `widgets.py`)
- Grass easter egg via [pygame-grass](https://github.com/DaFluffyPotato/pygame-grass) by DaFluffyPotato (embedded in `grass.py` + `grass_assets/`)

## Благодарности

- Парсинг NRBF через [`nrbf`](https://pypi.org/project/nrbf/) от @vickas
- UI через [pygame](https://www.pygame.org/) (собственный тулкит виджетов в `widgets.py`)
- Пасхалка с травой на основе [pygame-grass](https://github.com/DaFluffyPotato/pygame-grass) от DaFluffyPotato (встроено в `grass.py` + `grass_assets/`)
