# DJ Studio (Linux): Mixxx + touch panel + skin. Everything goes through make:   make help
SHELL         := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:

PY     ?= python3
VENV   ?= .venv
VPY    := $(VENV)/bin/python
STUDIO := $(PY) tools/studio.py
# `make doctor` should work before the Python environment exists
DOCTOR_PY = $$([ -x $(VPY) ] && echo $(VPY) || echo $(PY))

.PHONY: help install deps deps-build mixxx venv skin configure run panel dry-run doctor midi-test uninstall clean \
        check test validate scheme mapping upstream-diff

help: ## this list
	@echo "DJ Studio - first time:  make install      then every day:  make run"; echo
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z_-]+:.*## /{printf "  make %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## ---- use -------------------------------------------------------------------------------------------------------
install: deps mixxx venv skin configure ## everything, once: system packages, Mixxx, Python env, skin, settings
	@echo; echo "Installed. Start it with:  make run      (problems?  make doctor)"

run: $(VENV)/.ready ## start the touch panel and Mixxx together (closing Mixxx stops the panel)
	$(VPY) panel/server.py --launch $(ARGS)

panel: $(VENV)/.ready ## only the touch panel server (open the printed address on the tablet)
	$(VPY) panel/server.py $(ARGS)

dry-run: ## the panel without MIDI: prints what it would send (no python-rtmidi needed)
	$(PY) panel/server.py --dry-run --host 127.0.0.1 $(ARGS)

doctor: ## check Mixxx, display, ALSA MIDI, skin, mapping - and say what to do
	@$(DOCTOR_PY) tools/studio.py doctor

midi-test: $(VENV)/.ready ## self-test of the virtual MIDI port (server <-> second MIDI client)
	$(VPY) tools/studio.py midi-test

## ---- install steps (make install runs them in this order) -------------------------------------------------------
deps: ## system packages for the Python side (venv, pip, ALSA tools; asks for sudo)
	$(STUDIO) deps

deps-build: ## compilers + ALSA headers for building python-rtmidi (make venv does this by itself when needed)
	$(STUDIO) deps --build

mixxx: ## Mixxx >= 2.5: official PPA on Ubuntu/Mint, otherwise Flatpak (skipped if already new enough)
	$(STUDIO) mixxx-install

venv: $(VENV)/.ready ## Python environment with python-rtmidi (in .venv; builds it from source if there is no prebuilt package)
$(VENV)/.ready: requirements.txt
	$(PY) -m venv $(VENV)
	@$(VPY) -m pip install --quiet --only-binary=:all: -r requirements.txt 2>/dev/null || { \
	  echo "No prebuilt python-rtmidi for Python $$($(VPY) -c 'import sys; print(sys.version.split()[0])') - building it from source (installs compilers + ALSA headers, asks for sudo) ..."; \
	  $(STUDIO) deps --build && $(VPY) -m pip install -r requirements.txt || { \
	    echo "Building python-rtmidi failed (see the messages above: they name the missing tool or header)."; rm -rf $(VENV); exit 1; }; }
	@touch $@

skin: ## skin, controller mapping and keyboard layout into Mixxx's settings folder
	bash install/install.sh --data-dir "$$($(STUDIO) data-dir)"

configure: ## select the StudioDeck skin in Mixxx (Mixxx must be closed; the old settings are kept as .bak)
	$(STUDIO) configure

uninstall: ## remove skin, mapping and keyboard layout again (Mixxx and .venv stay)
	bash install/install.sh --uninstall --data-dir "$$($(STUDIO) data-dir)"

clean: ## remove .venv and caches
	rm -rf $(VENV) .cache build dist .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

## ---- development --------------------------------------------------------------------------------------------------
check: scheme mapping validate test ## everything the CI runs
	@git diff --exit-code -- skins || (echo "Generated files differ: run 'make scheme' and commit" && exit 1)

test: ## unit tests (UI tests need playwright + chromium, otherwise they are skipped)
	$(PY) -m unittest discover -s tests -v

validate: ## check the skin's file references
	$(PY) tools/validate_skin.py

scheme: ## regenerate the colour scheme (qss + recoloured SVGs)
	$(PY) tools/make_scheme.py

mapping: ## regenerate the Mixxx mapping (xml + js) from panel/protocol.py
	$(PY) tools/make_panel.py

upstream-diff: ## what differs from Mixxx's own skin
	$(PY) tools/upstream_diff.py
