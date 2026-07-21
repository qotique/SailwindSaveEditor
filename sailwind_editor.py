#!/usr/bin/env python3
"""Sailwind save file editor — CLI.

Usage:
    python3 sailwind_editor.py dump [save_file]      - Export to save_data.json
    python3 sailwind_editor.py pack [save_file]      - Import from save_data.json
    python3 sailwind_editor.py info [save_file]      - Show editable fields
    python3 sailwind_editor.py ui   [save_file]      - Launch GUI
"""

import os
import sys

from core import DEFAULT_SAVE, KEY_FIELDS, SailwindSave


def cmd_dump(save_path):
    save = SailwindSave(save_path)
    path = save.export_json()
    print(f"Exported {len(save.field_map)} fields to {path}")
    print("\nKey fields:")
    for n in KEY_FIELDS:
        if n in save.field_map:
            val = save.get_field_value(n)
            print(f"  {n:22s}: {val}")


def cmd_pack(save_path):
    save = SailwindSave(save_path)
    patches = save.import_json()
    size = save.save(backup=True)
    for name, idx, old, new in patches:
        idx_str = f"[{idx}]" if idx is not None else ""
        print(f"  {name:22s}{idx_str}: {old} -> {new}")
    print(f"\nPatched {len(patches)} fields, wrote {size} bytes to {save_path}")


def cmd_info(save_path):
    save = SailwindSave(save_path)
    print("=== Editable fields ===\n")
    print(f"{'Name':22s} {'Value':>14s}  {'Type':8s}  {'Offset':>7s}")
    print("-" * 60)
    for entry in save.get_all_fields():
        if entry['name'] not in KEY_FIELDS:
            continue
        val = entry['value']
        val_s = str(val)
        if isinstance(val, float):
            val_s = f"{val:.4f}"
        off = entry['offset']
        print(f"{entry['name']:22s} {val_s:>30s}  {entry['type']:8s}  0x{off:05x}")
    print(f"\nTotal: {len(save.field_map)} patchable fields")
    print(f"File size: {os.path.getsize(save_path)} bytes")


def main():
    args = sys.argv[1:]
    if not args:
        from ui import main as ui_main
        ui_main()
        return
    cmd = args[0]
    if cmd in ('dump', 'pack', 'info'):
        save = args[1] if len(args) > 1 else DEFAULT_SAVE
        if not os.path.exists(save):
            print(f"Save file not found: {save}")
            sys.exit(1)
        if cmd == 'dump':
            cmd_dump(save)
        elif cmd == 'pack':
            cmd_pack(save)
        elif cmd == 'info':
            cmd_info(save)
    elif cmd == 'ui':
        from ui import main as ui_main
        ui_main()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
