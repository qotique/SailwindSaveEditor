"""Sailwind save editor — core binary patching logic."""

import nrbf
import struct
import json
import sys
import os
import shutil

DEFAULT_SAVE = os.path.expanduser(
    "~/.local/share/Steam/steamapps/compatdata/1764530/pfx/"
    "drive_c/users/steamuser/AppData/LocalLow/Raw Lion Workshop/Sailwind/slot0.save"
)

PRIM_SIZES = {1: 1, 6: 8, 7: 2, 8: 4, 9: 8, 11: 4, 15: 4, 16: 8}
PRIM_FMTS = {6: 'd', 7: 'h', 8: 'i', 9: 'q', 11: 'f', 15: 'I', 16: 'Q'}
PRIM_NAMES = {1: 'Boolean', 7: 'Int16', 8: 'Int32', 9: 'Int64',
              11: 'Single', 15: 'UInt32', 16: 'UInt64'}


def find_all_prim_arrays(data):
    arrays = {}
    p = 0
    while p < len(data) - 10:
        if data[p] == 15:
            oid = struct.unpack_from('<i', data, p + 1)[0]
            cnt = struct.unpack_from('<i', data, p + 5)[0]
            pt = data[p + 9]
            if pt in PRIM_SIZES and 0 < cnt < 1000:
                vals_off = p + 10
                arrays[oid] = (p, pt, cnt, vals_off)
                p = vals_off + cnt * PRIM_SIZES[pt]
                continue
        p += 1
    return arrays


def read_lps(data, pos):
    length = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        length |= (b & 0x7F) << shift
        shift += 7
        pos += 1
        if b < 0x80:
            break
    return data[pos:pos + length].decode('utf-8', errors='replace'), pos + length


def skip_class_instance(data, pos):
    rt = data[pos]; pos += 1
    pos += 4
    _, pos = read_lps(data, pos)
    nm = struct.unpack_from('<i', data, pos)[0]; pos += 4
    for _ in range(nm):
        _, pos = read_lps(data, pos)
    btypes2 = []
    for _ in range(nm):
        btypes2.append(data[pos]); pos += 1
    for bt in btypes2:
        if bt in (0, 7):
            pos += 1
        elif bt == 3:
            _, pos = read_lps(data, pos)
        elif bt == 4:
            _, pos = read_lps(data, pos)
            pos += 4
    if rt == 5:
        pos += 4
    for bt in btypes2:
        if bt == 0:
            pos += 4
        elif bt == 7:
            rt2 = data[pos]
            if rt2 == 15:
                pos += 4; cnt = struct.unpack_from('<i', data, pos)[0]; pos += 4
                pt = data[pos]; pos += 1
                pos += cnt * PRIM_SIZES.get(pt, 0)
            elif rt2 == 9:
                pos += 5
        elif bt in (3, 4):
            rt2 = data[pos]
            if rt2 in (9, 10, 13, 14):
                pos += {9: 5, 10: 1, 13: 2, 14: 5}[rt2]
            elif rt2 in (4, 5):
                pos = skip_class_instance(data, pos)
        elif bt == 1:
            rt2 = data[pos]
            if rt2 == 6:
                pos += 4; _, pos = read_lps(data, pos)
            elif rt2 == 9:
                pos += 5
            elif rt2 == 10:
                pos += 1
        elif bt in (5, 6):
            rt2 = data[pos]
            if rt2 == 9:
                pos += 5
            elif rt2 in (16, 17):
                pos += 4; cnt = struct.unpack_from('<i', data, pos)[0]; pos += 4
    return pos


def find_save_container_fields(data):
    pos = 17
    while pos < len(data) and data[pos] == 12:
        pos += 1
        pos += 4
        _, pos = read_lps(data, pos)
    if data[pos] != 5:
        return None, None
    pos += 1
    class_id = struct.unpack_from('<i', data, pos)[0]; pos += 4
    class_name, pos = read_lps(data, pos)
    nmembers = struct.unpack_from('<i', data, pos)[0]; pos += 4
    member_names = []
    for _ in range(nmembers):
        name, pos = read_lps(data, pos)
        member_names.append(name)
    btypes = []
    for _ in range(nmembers):
        btypes.append(data[pos]); pos += 1
    addl = []
    for bt in btypes:
        if bt in (0, 7):
            addl.append(data[pos]); pos += 1
        elif bt == 3:
            _, pos = read_lps(data, pos)
            addl.append(None)
        elif bt == 4:
            _, pos = read_lps(data, pos)
            pos += 4
            addl.append(None)
        else:
            addl.append(None)
    pos += 4
    prim_arrays = find_all_prim_arrays(data)
    field_map = {}
    for i in range(nmembers):
        bt = btypes[i]
        ai = addl[i]
        if bt == 0:
            ptype = ai
            pname = PRIM_NAMES.get(ptype, f'Prim{ptype}')
            field_map[member_names[i]] = (pos, ptype, pname)
            pos += PRIM_SIZES.get(ptype, 0)
        elif bt == 7:
            rt = data[pos]
            if rt == 15:
                pos += 1  # record type
                pos += 4  # oid
                cnt = struct.unpack_from('<i', data, pos)[0]; pos += 4
                pt2 = data[pos]; pos += 1
                pname2 = PRIM_NAMES.get(pt2, f'Prim{pt2}')
                field_map[member_names[i]] = (pos, pt2, pname2, cnt)
                pos += cnt * PRIM_SIZES.get(pt2, 0)
            elif rt == 9:
                ref_id = struct.unpack_from('<i', data, pos + 1)[0]
                pos += 5
                if ref_id in prim_arrays:
                    arr_off, pt2, cnt, vals_off = prim_arrays[ref_id]
                    pname2 = PRIM_NAMES.get(pt2, f'Prim{pt2}')
                    field_map[member_names[i]] = (vals_off, pt2, pname2, cnt)
            else:
                break
        elif bt in (3, 4):
            rt = data[pos]
            if rt in (9, 10, 13, 14):
                pos += {9: 5, 10: 1, 13: 2, 14: 5}[rt]
            elif rt in (4, 5):
                pos = skip_class_instance(data, pos)
            else:
                break
        elif bt == 1:
            rt = data[pos]
            if rt == 6:
                pos += 4
                _, pos = read_lps(data, pos)
            elif rt == 9:
                pos += 5
            elif rt == 10:
                pos += 1
            else:
                break
        elif bt in (5, 6):
            rt = data[pos]
            if rt == 9:
                pos += 5
            elif rt == 10:
                pos += 1
            elif rt in (16, 17):
                pos += 4
                cnt = struct.unpack_from('<i', data, pos)[0]; pos += 4
            else:
                break
        else:
            break
    return field_map, member_names


class SailwindSave:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Save file not found: {path}")
        self.raw = bytearray(open(path, 'rb').read())
        self.parsed = nrbf.load(open(path, 'rb'))
        self.field_map, self.member_names = find_save_container_fields(bytes(self.raw))
        if not self.field_map:
            raise ValueError("Could not find SaveContainer fields in save file")

    def get_field_value(self, name: str):
        return self.parsed.get(name)

    def get_field_info(self, name: str):
        return self.field_map.get(name)

    def get_all_fields(self):
        result = []
        for name in self.member_names:
            if name in self.field_map:
                fdata = self.field_map[name]
                val = self.parsed.get(name, '?')
                is_array = len(fdata) == 4
                if is_array:
                    offset, ptype, pname, count = fdata
                    entry = {'name': name, 'value': val, 'type': f'{pname}[{count}]',
                             'offset': offset, 'prim_type': ptype, 'count': count,
                             'is_array': True}
                else:
                    offset, ptype, pname = fdata
                    entry = {'name': name, 'value': val, 'type': pname,
                             'offset': offset, 'prim_type': ptype,
                             'is_array': False}
                result.append(entry)
        return result

    def patch_field(self, name: str, new_value):
        if name not in self.field_map:
            raise KeyError(f"Field '{name}' not found")
        fdata = self.field_map[name]
        offset = fdata[0]
        ptype = fdata[1]
        count = fdata[3] if len(fdata) == 4 else None
        fmt = PRIM_FMTS.get(ptype)

        patches = []
        if count and isinstance(new_value, list):
            for j in range(min(count, len(new_value))):
                elem_off = offset + j * PRIM_SIZES[ptype]
                if ptype == 1:
                    old_elem = self.raw[elem_off]
                    new_bin = b'\x01' if new_value[j] else b'\x00'
                else:
                    if not fmt:
                        raise ValueError(f"Unsupported prim type {ptype}")
                    old_elem = struct.unpack_from('<' + fmt, self.raw, elem_off)[0]
                    new_elem = type(old_elem)(new_value[j])
                    new_bin = struct.pack('<' + fmt, new_elem)
                if new_bin != bytes(self.raw[elem_off:elem_off + len(new_bin)]):
                    self.raw[elem_off:elem_off + len(new_bin)] = new_bin
                    patches.append((name, j, old_elem, new_value[j]))
        else:
            if ptype == 1:
                old_val = self.raw[offset]
                new_bin = b'\x01' if new_value else b'\x00'
            else:
                if not fmt:
                    raise ValueError(f"Unsupported prim type {ptype}")
                old_val = struct.unpack_from('<' + fmt, self.raw, offset)[0]
                new_bin = struct.pack('<' + fmt, type(old_val)(new_value))
            if new_bin != bytes(self.raw[offset:offset + len(new_bin)]):
                self.raw[offset:offset + len(new_bin)] = new_bin
                patches.append((name, None, old_val, new_value))

        return patches

    def save(self, backup: bool = True):
        if backup:
            shutil.copy2(self.path, self.path + '.bak')
        with open(self.path, 'wb') as f:
            f.write(bytes(self.raw))
        return os.path.getsize(self.path)

    def export_json(self, output_path: str = 'save_data.json'):
        editable = {}
        for name, fdata in self.field_map.items():
            val = self.parsed.get(name)
            if val is not None:
                if len(fdata) == 4:
                    offset, ptype, pname, count = fdata
                    editable[name] = {
                        'value': val, 'type': f'{pname}[{count}]',
                        'offset': offset, 'prim_type': ptype, 'count': count,
                    }
                else:
                    offset, ptype, pname = fdata
                    editable[name] = {
                        'value': val, 'type': pname,
                        'offset': offset, 'prim_type': ptype,
                    }
        for name in ['wind', 'wavesRotation']:
            if name in self.parsed:
                editable[name] = {'value': self.parsed[name], 'type': 'class_ref'}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(editable, f, indent=2, ensure_ascii=False, default=str)
        return output_path

    def import_json(self, input_path: str = 'save_data.json'):
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"{input_path} not found")
        with open(input_path, 'r', encoding='utf-8') as f:
            edited = json.load(f)
        all_patches = []
        for name, info in edited.items():
            if 'offset' not in info or 'prim_type' not in info:
                continue
            if name not in self.field_map:
                continue
            try:
                patches = self.patch_field(name, info['value'])
                all_patches.extend(patches)
            except (KeyError, ValueError, struct.error):
                continue
        return all_patches
