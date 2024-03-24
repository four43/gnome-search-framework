ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

ifndef PROJECT_DIR
$(error PROJECT_DIR is not set, please set it to the path of the search provider you would like to install. For example: make install PROJECT_DIR=./com.example.MySearchProvider)
endif

pip-install-base:
	/bin/bash -c "python -m venv --system-site-packages .venv && source ./.venv/bin/activate && python -m pip install -r ./requirements.txt"

install: ./* pip-install-base
	/bin/bash -c "source $(ROOT_DIR).venv/bin/activate && python $(ROOT_DIR)/install.py install $(PROJECT_DIR)"

uninstall: pip-install-base
	/bin/bash -c "source $(ROOT_DIR).venv/bin/activate && python $(ROOT_DIR)/install.py uninstall $(PROJECT_DIR)"

logs:
	PROJECT_ID=$(shell cat $(PROJECT_DIR)/meta.toml | grep 'id' | awk '{print $$3}' | tr -d '"')
	(journalctl -f /usr/bin/dbus-daemon | GREP_COLORS='ms=01;33' grep --color=always -e '^.*$(PROJECT_ID).SearchProvider.*$$') &
	(tail -f /var/log/syslog | GREP_COLORS='ms=01;34' grep --color=always -e '^.*$(PROJECT_ID).SearchProvider.*$$')
