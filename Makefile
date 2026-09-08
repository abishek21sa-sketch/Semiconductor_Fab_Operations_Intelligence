.PHONY: install test validate api package clean
install:
	python -m pip install -e ".[dev]"
test:
	python -m pytest
validate:
	python scripts/run_validation.py
api:
	uvicorn fabops.api.app:app --reload
package:
	python scripts/build_release.py
clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage
