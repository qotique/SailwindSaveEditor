import sys
import struct
import tempfile
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def _lps(s: str) -> bytes:
    data = s.encode('utf-8')
    length = len(data)
    result = bytearray()
    while length >= 0x80:
        result.append((length & 0x7F) | 0x80)
        length >>= 7
    result.append(length & 0x7F)
    result.extend(data)
    return bytes(result)


def make_mock_save(fields):
    buf = bytearray()

    # SerializationHeader (17 bytes)
    buf.extend(b'\x00')
    buf.extend(struct.pack('<I', 3))  # rootId
    buf.extend(struct.pack('<I', 1))  # headerId
    buf.extend(struct.pack('<I', 1))  # major
    buf.extend(struct.pack('<I', 0))  # minor

    lib_id = 2
    buf.extend(b'\x0c')
    buf.extend(struct.pack('<I', lib_id))
    buf.extend(_lps("mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089"))

    # ClassWithMembersAndTypes: SaveContainer
    buf.extend(b'\x05')
    buf.extend(struct.pack('<I', 3))
    buf.extend(_lps("SaveContainer"))
    buf.extend(struct.pack('<I', len(fields)))

    for name, bt, _, _ in fields:
        buf.extend(_lps(name))

    for _, bt, _, _ in fields:
        buf.extend(struct.pack('B', bt))

    for _, bt, ptype, _ in fields:
        if bt in (0, 7):
            buf.extend(struct.pack('B', ptype))

    buf.extend(struct.pack('<I', lib_id))

    next_oid = 100
    for _, bt, ptype, value in fields:
        if bt == 0:
            if isinstance(value, bytes):
                buf.extend(value)
            else:
                buf.extend(struct.pack('<' + {1: 'b', 8: 'i', 11: 'f'}[ptype], value))
        elif bt == 7:
            buf.extend(b'\x0f')
            buf.extend(struct.pack('<I', next_oid))
            next_oid += 1
            count = len(value) if isinstance(value, list) else 1
            buf.extend(struct.pack('<I', count))
            buf.extend(struct.pack('B', ptype))
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, bytes):
                        buf.extend(v)
                    else:
                        buf.extend(struct.pack('<' + {1: 'b', 8: 'i', 11: 'f'}[ptype], v))
            else:
                buf.extend(value)

    buf.extend(b'\x0b')
    return bytes(buf)


@pytest.fixture
def mock_save_int32():
    fields = [
        ("playerGold", 0, 8, 500),
    ]
    data = make_mock_save(fields)
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.save')
    f.write(data)
    f.close()
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_save_bool():
    fields = [
        ("compressed", 0, 1, False),
    ]
    data = make_mock_save(fields)
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.save')
    f.write(data)
    f.close()
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_save_full():
    fields = [
        ("playerGold", 0, 8, 1000),
        ("compressed", 0, 1, True),
        ("someArray", 7, 8, [10, 20]),
        ("boolArray", 7, 1, [True, False]),
    ]
    data = make_mock_save(fields)
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.save')
    f.write(data)
    f.close()
    yield f.name
    os.unlink(f.name)
