# Flagship V2 Acceptance

The release gate requires: historical tests remain green; new RARE-FAB, bay-control, AMHS, equipment, yield and Factory Physics tests pass; the validation script produces a versioned evidence artifact; API smoke tests cover the new decision surfaces; source compiles; release packaging is reproducible.

External blockers remain: sustained MES/SECS-GEM/tool-event execution, full UCI SECOM row-level benchmark execution if not locally acquired, manufacturer/site AMHS semantics, and real operator shadow validation.


## V2.2 Windows runtime gate

The Windows gate now explicitly checks every native Python process exit code. API tests use HTTPX ASGI transport instead of Starlette TestClient to avoid the blocking-portal/thread crash observed on Microsoft Store CPython 3.13. The final gate starts a real Uvicorn process on a temporary local port, verifies `/health`, verifies that `/` serves the fab operator console, terminates the server, and only then emits `FLAGSHIP_V2_2_ACCEPTANCE=PASS`.
