ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

ifndef PROJECT_DIR
$(error PROJECT_DIR is not set, please set it to the path of the search provider you would like to install. For example: make install PROJECT_DIR=./com.example.MySearchProvider)
endif

pip-install-base:
	/bin/bash -c "python -m venv --system-site-packages .venv && source ./.venv/bin/activate && python -m pip install -r ./requirements.txt"

install: ./* pip-install-base
    # Create our virtual env with dependencies for help with installing, \
	# and add our framework to our local venv for dev help \
	# Editable install settings via: https://stackoverflow.com/a/76897706/387851
	/bin/bash -c "source $(ROOT_DIR).venv/bin/activate \
		&& python -m pip install -e $(ROOT_DIR)/gnome_search_framework --config-settings editable_mode=strict \
		&& python $(ROOT_DIR)/install.py install $(ROOT_DIR)/gnome_search_framework $(PROJECT_DIR)"

uninstall: pip-install-base
	/bin/bash -c "source $(ROOT_DIR).venv/bin/activate && python $(ROOT_DIR)/install.py uninstall $(ROOT_DIR)/gnome_search_framework $(PROJECT_DIR)"

logs:
	@echo "WARNING: /var/log/syslog error messages may sometimes log slowly."
	PROJECT_ID=$(shell cat $(PROJECT_DIR)/meta.toml | grep 'id' | awk '{print $$3}' | tr -d '"')
	(journalctl -n 0 -f /usr/bin/dbus-daemon | GREP_COLORS='ms=01;33' grep --color=always -e '^.*$(PROJECT_ID).SearchProvider.*$$') &
	(journalctl -n 0 -f | GREP_COLORS='ms=01;34' grep --color=always -e '^.*$(PROJECT_ID).SearchProvider.*$$')
