PYTHON_BIN ?= python3.14

VENV_DIR ?= .venv

PROJECT_DIR := pytetris
APP_DIR ?= apps
LIB_DIR ?= libs

ALL_DIR ?= $(APP_DIR)/ $(LIB_DIR)/

COVERAGE_PERCENT=75
COVERAGE_PERCENT_APP=60
COVERAGE_PERCENT_LIB=85

EXCL_DIRS := .vscode .github old build dist $(VENV_DIR)

# Define your apps (Folder:PackageName:Threshold)
# Format: path/to/dir:package_name:fail_under_percent
APPS ?= $(APP_DIR)/pytetris:pytetris:$(COVERAGE_PERCENT_APP)

# Define your libs (Folder:PackageName:Threshold)
# Format: path/to/dir:package_name:fail_under_percent
LIBS := $(LIB_DIR)/pytetris-core:pytetris_core:$(COVERAGE_PERCENT_LIB) \
		$(LIB_DIR)/pytetris-i18n:pytetris_i18n:$(COVERAGE_PERCENT_LIB) \
		$(LIB_DIR)/pytetris-qt:pytetris_qt:$(COVERAGE_PERCENT_LIB)

# Merge the raw strings first
DIRS ?= $(APPS) $(LIBS)

# Extract ONLY the directory paths (removing :package:threshold)
ALL_PATHS := $(foreach item,$(DIRS),$(firstword $(subst :, ,$(item))))

# Find the .po files using the cleaned paths
# Note: we add a / to the path to ensure wildcard looks inside the directory
PO_FILES := $(foreach path,$(ALL_PATHS),$(wildcard $(path)/locales/*/LC_MESSAGES/*.po))

# 4. Create the .mo mapping
MO_FILES := $(PO_FILES:.po=.mo)

PYTEST_ARG ?=
#PYTEST_ARG ?= --import-mode=importlib \
#			  --strict-markers \
#			  --tb=short \
#			  --disable-warnings \
#			  --capture=no \
#			  --log-cli-level=DEBUG \
#			  -ra \
#			  -v


empty :=
space := $(empty) $(empty)

## Colors for terminal output
BOLD            := $(shell tput -Txterm bold)
UNDER           := $(shell tput -Txterm smul)
FG_BLACK        := $(shell tput -Txterm setaf 0)
FG_RED          := $(shell tput -Txterm setaf 1)
FG_GREEN        := $(shell tput -Txterm setaf 2)
FG_YELLOW       := $(shell tput -Txterm setaf 3)
FG_LIGHTPURPLE  := $(shell tput -Txterm setaf 4)
FG_PURPLE       := $(shell tput -Txterm setaf 5)
FG_BLUE         := $(shell tput -Txterm setaf 6)
FG_WHITE        := $(shell tput -Txterm setaf 7)
BG_BLACK        := $(shell tput -Txterm setab 0)
BG_RED          := $(shell tput -Txterm setab 1)
BG_GREEN        := $(shell tput -Txterm setab 2)
BG_YELLOW       := $(shell tput -Txterm setab 3)
BG_LIGHTPURPLE  := $(shell tput -Txterm setab 4)
BG_PURPLE       := $(shell tput -Txterm setab 5)
BG_BLUE         := $(shell tput -Txterm setab 6)
BG_WHITE        := $(shell tput -Txterm setab 7)
RESET           := $(shell tput -Txterm sgr0)

##@ General

# The help target prints out all targets with their descriptions organized
# beneath their categories. The categories are represented by '##@' and the
# target descriptions by '##'. The awk command is responsible for reading the
# entire set of makefiles included in this invocation, looking for lines of the
# file as xyz: ## something, and then pretty-format the target and help. Then,
# if there's a line with ##@ something, that gets pretty-printed as a category.
# More info on the usage of ANSI control characters for terminal formatting:
# https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters
# More info on the awk command:
# http://linuxcommand.org/lc3_adv_awk.php

MAX_LINE_LENGTH ?= 78
# 20 for target name
TARGET_WIDTH ?= 22

# This is used to calculate the maximum length of the description
# part of the help text, based on the total max line length and the
# width allocated for the target name.
# The '-7' accounts for the spacing and formatting characters between
# the target and description.
#DESC_MAX_LEN := $(shell echo ${MAX_LINE_LENGTH}-${TARGET_WIDTH}-7 | bc)
DESC_MAX_LEN := $(shell echo $$(($(MAX_LINE_LENGTH)-$(TARGET_WIDTH)-2)))

# This is used to split long descriptions into multiple lines with proper
# indentation, without breaking words in half.
# It looks for the last space before the max line length to break the line.
# It's also very verbose written, since "printf" take colorcodes into
# account for string length, while "awk" does not, so we need to manually
# calculate the spacing for alignment.
.PHONY: help
help: ## Display this help.
	@echo ''
	@echo '$(BOLD)Usage:$(RESET)'
	@echo '  ${FG_YELLOW}make${RESET} ${FG_GREEN}<target>${RESET}'
	@echo ''
	@echo '$(BOLD)Targets:$(RESET)'
	@awk 'BEGIN {FS = ":.*##";} /^[a-zA-Z_0-9-]+:.*?##/ { \
		target = $$1; \
		sub(/^common-/, "", target); \
		desc = $$2; \
		printf "  "; \
		printf "$(FG_YELLOW)%s$(RESET)", target; \
		printf "%*s", $(TARGET_WIDTH) - length(target) - 5, ""; \
		\
		if (length(desc) > $(DESC_MAX_LEN)) { \
			while (length(desc) > $(DESC_MAX_LEN)) { \
				pos = $(DESC_MAX_LEN); \
				while (pos > 0 && substr(desc, pos, 1) != " ") pos--; \
				if (pos == 0) pos = $(DESC_MAX_LEN); \
				\
				printf "$(FG_GREEN)%s$(RESET)\n  ", substr(desc, 1, pos); \
				printf "%*s", $(TARGET_WIDTH), ""; \
				\
				desc = substr(desc, pos + 1); \
			} \
		} \
		printf "$(FG_GREEN)%s$(RESET)\n", desc \
	} \
	/^##@/ { \
		printf "\n$(BOLD)%s:$(RESET)\n", substr($$0, 5) \
	} ' $(MAKEFILE_LIST)
	@echo ''

##@ Internationalization

.PHONY: translations
translations: $(MO_FILES) ## Compile translation files (.mo) from .po files
	@# Generate .mo files from .po files

# Pattern rule: How to create a .mo from a .po
# % is a wildcard matching the filename
%.mo: %.po
	msgfmt -o $@ $<
	@echo "Compiled: $@"

##@ Virtual Environment Management
.PHONY: venv
venv: ## Create a virtual environment
	python3 -m venv $(VENV_DIR)
	@echo "Virtual environment created in $(VENV_DIR)"

.PHONY: clean-venv
clean-venv: ## Remove the virtual environment
	@rm -rf $(VENV_DIR)

.PHONY: activate
activate:
	@{ \
	if [[ "$${VIRTUAL_ENV}" == "" ]]; then \
		if [ ! -d "$(VENV_DIR)" ]; then \
			echo "Virtual environment not found. Creating one..."; \
			$(MAKE) venv; \
		fi; \
		source $(VENV_DIR)/bin/activate; \
	fi; \
	}
	@echo "Virtual environment activated. To deactivate, run: deactivate"

.PHONY: deactivate
deactivate:
	@{ \
	if [[ "$${VIRTUAL_ENV}" == "" ]]; then \
		deactivate; \
	fi; \
	}
	@echo "Virtual environment deactivated."

##@ Maintenance
.PHONY: clean
clean: clean-coverage clean-build clean-pyc ## Clean everything
	@# Clean everything

.PHONY: clean-coverage
clean-coverage: ## Remove coverage artifacts
	find . -name '.coverage.*' -exec rm -f {} +

.PHONY: clean-build
clean-build: ## Remove build artifacts
	rm -fr build/
	rm -fr htmlcov/
	rm -fr dist/
	find . -name '*.egg-info' -exec rm -rf {} +

.PHONY: clean-pyc
clean-pyc: ## Remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

##@ Health Checks
.PHONY: health
health: lint typecheck ## Alias for lint and typecheck
	@# Check that the code is linted and type-checked

.PHONY: lint
lint: activate ## Check style with ruff
	ruff check -v $(DIRS)/
	ruff format  -v --check $(DIRS)/

.PHONY: format
format: activate ## Format code with ruff
	ruff check -v --fix $(DIRS)/
	ruff format  -v $(DIRS)/

.PHONY: typecheck
typecheck: activate ## Check type hints with mypy
	{ \
		MYPYPATH=$(subst $(space),:,$(strip $(foreach item,$(LIBS),$(firstword $(subst :, ,$(item)))))) \
		mypy --namespace-packages --explicit-package-bases $(DIRS) \
	}

##@ Testing
.PHONY: test
test: activate ## Run tests quickly with the default Python
	@for item in $(DIRS); do \
		dir=$$(echo $$item | cut -d: -f1); \
		pkg=$$(echo $$item | cut -d: -f2); \
		min=$$(echo $$item | cut -d: -f3); \
		$(PYTHON_BIN) -m pytest $(PYTEST_ARG) $$dir/tests ; \
	done;

.PHONY: test-coverage
test-coverage: clean-coverage activate ## Run tests with coverage
	@for item in $(DIRS); do \
		dir=$$(echo $$item | cut -d: -f1); \
		pkg=$$(echo $$item | cut -d: -f2); \
		min=$$(echo $$item | cut -d: -f3); \
		COVERAGE_FILE=.coverage.$$pkg \
		$(PYTHON_BIN) -m pytest $(PYTEST_ARG) $$dir/tests --cov=$$pkg --quiet --cov-report=; \
	done

.PHONY: test-all
test-all: activate ## Run tests on every Python version with tox
	tox

##@ Coverage

.PHONY: coverage-gen
coverage-gen: activate ## Generate coverage reports for all packages
	@# Loop through the list
	@for item in $(DIRS); do \
		dir=$$(echo $$item | cut -d: -f1); \
		pkg=$$(echo $$item | cut -d: -f2); \
		min=$$(echo $$item | cut -d: -f3); \
		\
		echo "--- Testing $$pkg ---"; \
		COVERAGE_FILE=.coverage.$$pkg $(PYTHON_BIN) -m pytest $$dir/tests --cov=$$pkg --quiet --cov-report=; \
		\
		echo "--- Individual Report for $$pkg ---"; \
		coverage report --data-file=.coverage.$$pkg --fail-under=$$min -m; \
	done

	@echo "--- Final Combined Report ---"

.PHONY: coverage
coverage: clean-coverage activate test-coverage coverage-gen ## Check code coverage quickly with the default Python
	@echo "--- Final Combined Report ---"
	@coverage combine .coverage.*
	@coverage lcov -o .coverage.lcov
	coverage report --fail-under=$(COVERAGE_PERCENT) -m

##@ Setup and Installation

.PHONY: setup
setup: activate ## Install the project and its dependencies
	$(PYTHON_BIN) -m pip install .
	$(PYTHON_BIN) -m pip install pytest pytest-mock
	@for item in $(DIRS); do \
		dir=$$(echo $$item | cut -d: -f1); \
		\
		if [ -d "$$dir" ]; then \
			echo "--- Installing $$dir ---"; \
			$(PYTHON_BIN) -m pip install -e ./$$dir[dev]; \
		fi \
	done

##@ Documentation

.PHONY: docs
docs: ## Generate Sphinx HTML documentation
	rm -fr docs/_autosummary
	rm -fr docs/_build
	rm -f docs/$(PROJECT_DIR).rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ $(PROJECT_DIR)
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

##@ Release

.PHONY: release
release: clean ## Alias for clean-coverage, clean-build, and clean-pyc
	$(PYTHON_BIN) setup.py sdist upload

.PHONY: sdist
sdist: clean ## Package
	$(PYTHON_BIN) setup.py sdist
	ls -l dist
