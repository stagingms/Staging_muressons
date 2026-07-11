# Manual diagnostic harnesses

Standalone e2e/diagnostic scripts (NOT part of the pytest suite in
`backend/tests/`). Most need a live server. Because Python puts the
script's own directory on sys.path, run them FROM `backend/` with the
repo on the path:

    cd backend
    PYTHONPATH=. python manual_tests/test_deep_audit.py

(or `python -m manual_tests.test_deep_audit` — both resolve
`from engine import ...` correctly.)

Moved here from backend/ root in the AR2 archive pass; behaviour unchanged.
