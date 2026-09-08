# Local Runbook

1. Create a Python 3.11+ virtual environment.
2. Run `python -m pip install -e ".[dev]"`.
3. Run `python -m pytest`.
4. Run `python scripts/run_validation.py`.
5. Start `uvicorn fabops.api.app:app --reload`.
6. Open `frontend/index.html`.

Optional persistence location: copy `.env.example` semantics and set `FABOPS_DB` in the shell.
