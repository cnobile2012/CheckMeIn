#
# Development by Carl J. Nobile
#
include include.mk

PREFIX		= $(shell pwd)
BASE_DIR	= $(shell basename $(PREFIX))
PACKAGE_DIR	= $(BASE_DIR)-$(VERSION)$(TEST_TAG)
DOCS_DIR	= $(PREFIX)/docs
TODAY		= $(shell date +"%Y-%m-%dT%H:%M:%S.%N%:z")
RM_REGEX	= '(^.*.pyc$$)|(^.*.wsgic$$)|(^.*~$$)|(.*\#$$)|(^.*,cover$$)|(__pycache__)'
RM_CMD		= find $(PREFIX) -regextype posix-egrep -regex $(RM_REGEX) \
                  -exec rm {} \;
COVERAGE_FILE	= $(PREFIX)/.coveragerc
TEST_TAG	=
PIP_ARGS	= # Pass variables for pip install.
TEST_PATH	= # The path to run tests on.

#----------------------------------------------------------------------
all	: help

#---------------------------------------------------------------------
.PHONY	: help
help	:
	@LC_ALL=C $(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : \
                2>/dev/null | awk -v RS= \
                -F: '/(^|\n)# Files(\n|$$)/,/(^|\n)# Finished Make data \
                     base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep \
                -E -v -e '^[^[:alnum:]]' -e '^$@$$'

.PHONY	: tar
tar	: clobber
	@(cd ..; tar -cJvf $(PACKAGE_DIR).tar.xz --exclude=".git" \
          --exclude="__pycache__" --exclude=".pytest_cache" $(BASE_DIR))

#----------------------------------------------------------------------
.PHONY	: tests
tests	: clobber setup
	@mkdir -p docs
	@rm -rf $(DOCS_DIR)/htmlcov
	@coverage erase --rcfile=$(COVERAGE_FILE)
	@coverage run --rcfile=$(COVERAGE_FILE) -m pytest --capture=tee-sys \
         $(TEST_PATH)
	@coverage report -m --rcfile=$(COVERAGE_FILE)
	@coverage html --rcfile=$(COVERAGE_FILE)
	@echo $(TODAY)

.PHONY	: flake8
flake8	:
	# Error on syntax errors or undefined names.
	flake8 . --select=E9,F7,F63,F82 --show-source
	# Warn on everything else.
	flake8 . --exit-zero

#----------------------------------------------------------------------
.PHONY	: install-dev
install-dev:
	@python -m pip install --upgrade pip
	@pip install $(PIP_ARGS) -r requirements/development.txt

.PHONY	: install-prod
install-prod:
	@python -m pip install --upgrade pip
	@pip install $(PIP_ARGS) -r requirements/production.txt

#----------------------------------------------------------------------
.PHONY  : setup
setup	:
	@mkdir -p testData
	@echo "l1n5Be5G9GHFXTSMi6tb0O6o5AKmTC68OjF2UmaU55A=" > testData/checkmein.key
	@mkdir -p sessions

.PHONY	: run
run	: setup
	python src/checkMeIn.py development.conf

#----------------------------------------------------------------------
.PHONY	: clean clobber
clean	:
	$(shell $(RM_CMD))

clobber	: clean
	@rm -rf testData sessions
#	@(cd $(DOCS_DIR); make clobber)
#	@rm logs/*.log
