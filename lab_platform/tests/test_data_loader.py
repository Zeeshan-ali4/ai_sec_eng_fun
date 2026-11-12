import json
from pathlib import Path
import pytest
from lab_platform.data_loader import APPROVED_FILES, DataLoadError, load_data, system_prompt


def test_approved_data_and_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = load_data()
    assert tuple(data) == APPROVED_FILES
    assert len(data['products.json']['products']) == 12
    assert data['products.json']['products'][2]['list_price'] == 27495
    assert 'internal_notes.json' not in system_prompt(data)
    assert 'CANARY-' not in system_prompt(data)


@pytest.mark.parametrize('broken', ['missing', 'malformed', 'array'])
def test_bad_data(tmp_path, broken):
    for name in APPROVED_FILES:
        (tmp_path / name).write_text(json.dumps({'safe': True}))
    target = tmp_path / 'offers.json'
    if broken == 'missing':
        target.unlink()
    else:
        target.write_text('{' if broken == 'malformed' else '[]')
    with pytest.raises(DataLoadError, match='offers.json'):
        load_data(tmp_path)


def test_protected_file_never_opened(monkeypatch):
    original = Path.read_text
    def checked(path, *args, **kwargs):
        assert path.name in APPROVED_FILES
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', checked)
    load_data()
