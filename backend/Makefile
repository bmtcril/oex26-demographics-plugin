# Convenience targets for the backend plugin.
# Mirrors the sample-plugin's Makefile interface so participants can move
# between repos without re-learning commands.

.PHONY: help install test quality test-all clean migrate

help: ## Display this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the plugin (editable) with test and dev extras.
	uv pip install -e ".[test,dev]"

test: ## Run the test suite via pytest.
	pytest

quality: ## Run ruff (lint) and pyright (type check).
	ruff check src/ tests/
	pyright src/

test-all: ## Run all dev tests
	make clean
	make test
	make quality

migrate: ## Run plugin migrations against the LMS (use inside tutor dev shell).
	./manage.py lms migrate registration_demographics

clean: ## Remove build artifacts and caches.
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
