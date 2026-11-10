from pathlib import Path

from bugfinder.rules import scan_project, scan_text

def test_detects_dynamic_execution():
    results = scan_text(Path("demo.py"), "result = eval(user_input)\n")
    assert any(x.rule_id in {"BFSEC002", "BFPY002"} for x in results)

def test_detects_python_syntax_error():
    results = scan_text(Path("broken.py"), "def nope(:\n")
    assert any(x.rule_id == "BFPY001" for x in results)

def test_scans_project(tmp_path):
    (tmp_path / "main.py").write_text(
        "password = 'verylongsecretvalue'\n", encoding="utf-8"
    )
    results = scan_project(tmp_path)
    assert any(x.rule_id == "BFSEC001" for x in results)

def test_ignores_generated_folders(tmp_path):
    folder = tmp_path / "node_modules"
    folder.mkdir()
    (folder / "bad.py").write_text("eval(user_input)", encoding="utf-8")
    assert scan_project(tmp_path) == []


def test_detects_unsafe_pickle_deserialization():
    results = scan_text(Path("loader.py"), "value = pickle.loads(payload)\n")
    assert any(x.rule_id == "BFSEC007" for x in results)


def test_detects_unsafe_yaml_loader():
    results = scan_text(Path("config.py"), "config = yaml.load(stream)\n")
    assert any(x.rule_id == "BFSEC008" for x in results)


def test_detects_mutable_python_default():
    results = scan_text(Path("defaults.py"), "def add(value, items=[]):\n    items.append(value)\n")
    assert any(x.rule_id == "BFPY006" for x in results)


def test_detects_insecure_tempfile_name():
    results = scan_text(Path("temp.py"), "name = tempfile.mktemp()\n")
    assert any(x.rule_id == "BFPY004" for x in results)


def test_ignores_symlinked_directories(tmp_path):
    outside = tmp_path.parent / "bugfinder_outside"
    outside.mkdir(exist_ok=True)
    (outside / "unsafe.py").write_text("eval(user_input)\n", encoding="utf-8")
    link = tmp_path / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        return
    assert scan_project(tmp_path) == []
