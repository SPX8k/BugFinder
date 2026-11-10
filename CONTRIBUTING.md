# Contributing

- Create a branch for each change.
- Keep scanning local and read-only.
- Add tests for new rules and false-positive edge cases.
- Run `pytest -q` and `ruff check bugfinder tests`.
- Document limitations and confidence honestly.

Never execute scanned project files, silently upload source code, or modify source files during scanning.
