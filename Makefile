all: build

.prep: ## Prepare
	pip3 install --user pre-commit
	pre-commit install
	pre-commit install-hooks
	poetry install --no-root
	touch .prep

.PHONY: lint
lint: .prep ## Run python lint
	poetry install --no-root
	poetry run black httpmq test scripts examples
	poetry run pylint httpmq test scripts examples --min-similarity-lines=30 --ignore-paths=httpmq/models,httpmq/typing_utils.py,httpmq/util.py

.PHONY: build
build: lint ## Build module
	poetry build

.PHONY: test
test: ## Run unit-tests
	poetry run pytest --verbose --junitxml=test-reports/test.xml test/

.PHONY: one-test
one-test: ## Run specific unit-tests
	poetry run pytest -s --verbose "$(FILTER)"

.PHONY: install
install: lint ## Install module
	poetry install

.PHONY: uninstall
uninstall: ## Uninstall module
	poetry run pip uninstall -y httpmq

.PHONY: reinstall
reinstall: lint ## Reinstall module
	poetry run pip uninstall -y httpmq
	poetry install

.PHONY: cli
cli: .prep ## Run venv python CLI
	poetry run python3

.PHONY: compose
compose: ## Bring up development environment via docker-compose
	docker-compose -f docker-compose.yaml down --volume
	docker-compose -f docker-compose.yaml up -d

.PHONY: clean
clean: ## Clean up the python build artifacts
	rm -rf venv .venv .prep build dist httpmq.egg-info .pytest_cache test-reports

help: ## Display this help screen
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
