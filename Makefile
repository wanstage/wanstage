.PHONY: fmt lint type test all
fmt:
	ruff check --fix .
	black .
lint:
	ruff check .
type:
	mypy
test:
	pytest -q -n auto
all: fmt lint type test
