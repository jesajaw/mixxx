.PHONY: install uninstall validate test scheme check upstream-diff mapping panel panel-dry
install:    ; bash install/install.sh
uninstall:  ; bash install/install.sh --uninstall
validate:   ; python3 tools/validate_skin.py
test:       ; python3 -m unittest discover -s tests -v
scheme:     ; python3 tools/make_scheme.py
upstream-diff: ; python3 tools/upstream_diff.py
mapping: ; python3 tools/make_panel.py
panel: ; python3 panel/server.py
panel-dry: ; python3 panel/server.py --dry-run --host 127.0.0.1
check: scheme mapping validate test
	@git diff --exit-code -- skins || (echo "Generated files differ: run 'make scheme' and commit" && exit 1)
