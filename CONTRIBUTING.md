# Contributing

Issues, code and pixel art are welcome. Discuss larger changes first.

- Get the maintainer's approval for every new or revised pixel-art asset before integration.
- Keep transparency, hard pixel edges, day counts and attack targets accurate.
- Include a preview for visual changes and tests for behavior changes.

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest -q
```
