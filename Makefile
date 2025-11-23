start:
	uv run fastapi dev --host 0.0.0.0 --port 8080

test:
	uv run pytest tests/

lint:
	uv run ruff check .

format:
	uv run ruff format .

install:
	uv sync