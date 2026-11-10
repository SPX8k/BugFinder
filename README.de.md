# BugFinder

BugFinder ist ein lokaler Code- und Sicherheitsanalysator. Er untersucht Projekte auf Programmierfehler, potenzielle Sicherheitsprobleme und problematische Code-Muster. Jede Fundstelle enthält Datei, Zeile, Regel-ID, Schweregrad, Konfidenz, Erklärung und Verbesserungsvorschlag.

## Download

[⬇️ **BugFinder für Windows herunterladen (Installer)**](https://github.com/SPX8k/BugFinder/releases)

[Alle Versionen und Releases anzeigen](https://github.com/SPX8k/BugFinder/releases)

*Öffne die Releases-Seite und lade dort `BugFinder-Setup.exe` herunter, sobald der erste Windows-Release veröffentlicht wurde.*

## Funktionen
- Desktop-Oberfläche mit PySide6 und Kommandozeile.
- Lokale, schreibgeschützte Analyse; untersuchter Code wird weder ausgeführt noch hochgeladen.
- Python-Syntax-/AST-Prüfungen und vorsichtige Musterprüfungen für Python, JavaScript, TypeScript, Java, C, C++, C#, PHP, Go, Rust, Ruby, HTML, CSS, SQL, JSON und YAML.
- SQLite-Analyseverlauf.
- Export als JSON, HTML, SARIF 2.1.0, TXT und CSV.
- Windows-Installer mit deutscher und englischer Sprachauswahl.

## Starten
Python 3.11 oder neuer:

```powershell
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python run_gui.py
```

CLI:

```powershell
python -m bugfinder scan . --format html --output bericht.html
```

## Windows-Build
```powershell
pip install -r requirements-build.txt
pyinstaller --noconfirm --clean packaging/bugfinder.spec
```

Anschließend `packaging/windows/BugFinder.iss` mit Inno Setup 6 kompilieren.

## Grenzen
Die tiefe AST-Analyse ist in dieser ersten Version für Python implementiert. Bei den übrigen Sprachen werden konservative Textmuster verwendet. Framework-spezifische Probleme und komplexe Datenflüsse können unentdeckt bleiben. Dependency-Onlineprüfungen und Linux-Binärpakete sind noch nicht enthalten.

## Datenschutz
BugFinder arbeitet lokal, führt den untersuchten Code nicht aus, verändert und löscht keine Quelldateien und lädt keinen Quellcode hoch.

## Lizenz
MIT. Siehe [LICENSE](LICENSE).
