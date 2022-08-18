all: build

.prep: venv/bin/activate ## Prepare
	pip3 install --user pre-commit
	pre-commit install
	pre-commit install-hooks
	touch .prep

venv/bin/activate: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/bin/activate

.PHONY: lint
lint: .prep ## Run python lint
	. venv/bin/activate; python3 -m black httpmq test scripts
	. venv/bin/activate; pylint httpmq test scripts --min-similarity-lines=30 --ignore-paths=httpmq/models,httpmq/typing_utils.py,httpmq/util.py

.PHONY: build
build: lint ## Build module
	. venv/bin/activate; python3 setup.py bdist_wheel

.PHONY: test
test: ## Run unit-tests
	. venv/bin/activate; pytest --verbose --junitxml=test-reports/test.xml test/

.PHONY: one-test
one-test: ## Run specific unit-tests
	. venv/bin/activate; pytest -s --verbose "$(FILTER)"

.PHONY: install
install: build ## Install module
	. venv/bin/activate; pip install dist/*.whl

.PHONY: uninstall
uninstall: ## Uninstall module
	. venv/bin/activate; pip uninstall -y httpmq

.PHONY: reinstall
reinstall: build ## Reinstall module
	. venv/bin/activate; pip uninstall -y httpmq && pip install dist/*.whl

.PHONY: cli
cli: .prep ## Run venv python CLI
	. venv/bin/activate; python3

.PHONY: compose
compose: ## Bring up development environment via docker-compose
	docker-compose -f docker-compose.yaml down --volume
	docker-compose -f docker-compose.yaml up -d

.PHONY: clean
clean: ## Clean up the python build artifacts
	rm -rf venv .prep build dist httpmq.egg-info

help: ## Display this help screen
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
