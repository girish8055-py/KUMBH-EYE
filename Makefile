.PHONY: install run run-laptop test lint typecheck clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run:
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

run-laptop:
	python backend/app.py

test:
	pytest tests/ -v

lint:
	ruff check backend/ ml_service/

typecheck:
	mypy backend/ ml_service/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
