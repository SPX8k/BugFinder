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
