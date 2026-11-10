# BugFinder

**Deutsch:** BugFinder ist ein lokaler Code- und Sicherheitsanalysator, der Programmierfehler, potenzielle Sicherheitsprobleme und problematische Code-Muster erkennt und verständliche Verbesserungsvorschläge liefert.

**English:** BugFinder is a local code and security analyzer that detects programming errors, potential security issues, and problematic code patterns while providing clear recommendations.

BugFinder is an assistive static-analysis tool. Findings are leads for human review, not proof of exploitability.

## Features

- PySide6 desktop interface and command-line interface.
- Local, read-only scanning. Scanned code is never executed or uploaded.
- Python syntax and AST checks, plus conservative pattern checks for Python, JavaScript, TypeScript, Java, C, C++, C#, PHP, Go, Rust, Ruby, HTML, CSS, SQL, JSON and YAML.
- Finding details: severity, confidence, file, line, explanation and recommendation.
- SQLite scan history.
- JSON, HTML, SARIF 2.1.0, TXT and CSV reports.
- Windows 10 22H2 / Windows 11 64-bit installer with German/English setup language.
- GitHub Actions for tests and Windows release builds.

## Run from source

Python 3.11+ is required.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_gui.py
```

CLI:

```powershell
python -m bugfinder scan . --format sarif --output report.sarif
```

## Build the Windows app

```powershell
pip install -r requirements-build.txt
pyinstaller --noconfirm --clean packaging/bugfinder.spec
```

Compile `packaging/windows/BugFinder.iss` with Inno Setup 6 to create `BugFinder-Setup.exe`.

## Current limitations

Deep AST analysis is currently implemented for Python. Other languages use conservative text-pattern checks. Framework-specific issues and complex data flows may not be detected. Dependency vulnerability lookups and Linux binary packages are not included in this first functional version.

## Privacy and safety

BugFinder runs locally, does not execute scanned code, does not modify or delete source files, and does not upload source code. Findings require human review.

## License

MIT. See [LICENSE](LICENSE).
