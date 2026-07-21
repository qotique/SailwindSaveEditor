import json
import os

import pytest

from core import SailwindSave, find_save_container_fields


class TestFindFields:
    def test_scalar_int32(self, mock_save_int32):
        with open(mock_save_int32, 'rb') as f:
            field_map, names = find_save_container_fields(f.read())
        assert field_map is not None
        assert 'playerGold' in field_map
        offset, ptype, pname = field_map['playerGold']
        assert ptype == 8
        assert pname == 'Int32'

    def test_scalar_bool(self, mock_save_bool):
        with open(mock_save_bool, 'rb') as f:
            field_map, names = find_save_container_fields(f.read())
        assert field_map is not None
        assert 'compressed' in field_map
        offset, ptype, pname = field_map['compressed']
        assert ptype == 1
        assert pname == 'Boolean'

    def test_full_mock(self, mock_save_full):
        with open(mock_save_full, 'rb') as f:
            field_map, names = find_save_container_fields(f.read())
        assert field_map is not None
        assert set(field_map.keys()) == {'playerGold', 'compressed', 'someArray', 'boolArray'}
        assert 'boolArray' in field_map
        offset, ptype, pname, count = field_map['boolArray']
        assert ptype == 1
        assert count == 2


class TestSailwindSave:
    def test_load(self, mock_save_int32):
        save = SailwindSave(mock_save_int32)
        assert save.path == mock_save_int32
        assert 'playerGold' in save.field_map
        assert save.get_field_value('playerGold') is not None

    def test_get_all_fields(self, mock_save_full):
        save = SailwindSave(mock_save_full)
        fields = save.get_all_fields()
        names = {f['name'] for f in fields}
        assert names == {'playerGold', 'compressed', 'someArray', 'boolArray'}

    def test_patch_int32_scalar(self, mock_save_int32):
        save = SailwindSave(mock_save_int32)
        patches = save.patch_field('playerGold', 999)
        assert len(patches) == 1
        name, idx, old, new = patches[0]
        assert name == 'playerGold'
        assert idx is None
        assert old == 500
        assert new == 999

    def test_patch_bool_scalar(self, mock_save_bool):
        save = SailwindSave(mock_save_bool)
        patches = save.patch_field('compressed', True)
        assert len(patches) == 1
        name, idx, old, new = patches[0]
        assert name == 'compressed'
        assert idx is None
        assert old == 0
        assert new is True

    def test_patch_bool_array(self, mock_save_full):
        save = SailwindSave(mock_save_full)
        patches = save.patch_field('boolArray', [False, True])
        assert len(patches) == 2
        assert patches[0][0] == 'boolArray'
        assert patches[0][1] == 0
        assert patches[0][2] == 1
        assert patches[0][3] is False

    def test_patch_int32_array(self, mock_save_full):
        save = SailwindSave(mock_save_full)
        patches = save.patch_field('someArray', [99, 199])
        assert len(patches) == 2
        assert patches[0][2] == 10
        assert patches[0][3] == 99

    def test_export_json(self, mock_save_full, tmp_path):
        save = SailwindSave(mock_save_full)
        json_path = os.path.join(tmp_path, 'save_data.json')
        result = save.export_json(json_path)
        assert result == json_path
        with open(json_path) as f:
            data = json.load(f)
        assert 'playerGold' in data
        assert data['playerGold']['value'] == 1000

    def test_import_json(self, mock_save_full, tmp_path):
        save = SailwindSave(mock_save_full)
        json_path = os.path.join(tmp_path, 'save_data.json')
        with open(json_path, 'w') as f:
            json.dump({
                'playerGold': {'offset': save.field_map['playerGold'][0],
                               'prim_type': 8, 'value': 777}
            }, f)
        patches = save.import_json(json_path)
        assert len(patches) == 1
        assert patches[0][3] == 777

    def test_save_creates_backup(self, mock_save_int32):
        save = SailwindSave(mock_save_int32)
        save.patch_field('playerGold', 123)
        size = save.save(backup=True)
        assert os.path.exists(mock_save_int32 + '.bak')
        assert size > 0

    def test_value_not_changed_no_patch(self, mock_save_int32):
        save = SailwindSave(mock_save_int32)
        patches = save.patch_field('playerGold', 500)
        assert len(patches) == 0


class TestParseEdgeCases:
    def test_bool_array_to_false(self, mock_save_full):
        save = SailwindSave(mock_save_full)
        patches = save.patch_field('boolArray', [False, False])
        assert len(patches) == 1
        assert patches[0][3] is False

    def test_float_conversion(self, mock_save_full):
        save = SailwindSave(mock_save_full)
        with pytest.raises(KeyError):
            save.patch_field('nonexistent', 0)
