pip-install:
	/bin/bash -c "python -m venv --system-site-packages .venv && source ./.venv/bin/activate && python -m pip install -r ./requirements.txt"

install: ./*
	rm -rf /usr/local/bin/gnome-search-projects || true
	mkdir -p /usr/local/bin/gnome-search-projects
	python -m venv --system-site-packages /usr/local/bin/gnome-search-projects/.venv
	/bin/bash -c "source /usr/local/bin/gnome-search-projects/.venv/bin/activate && pip install -r requirements.txt"
	install -Dm 0644 gnome_search_projects/__main__.py /usr/local/bin/gnome-search-projects/gnome_search_projects/__main__.py

	install -Dm 0644 files/com.four43.Projects.SearchProvider.systemd.service /usr/lib/systemd/user/com.four43.Projects.SearchProvider.service
	install -Dm 0644  files/com.four43.Projects.SearchProvider.desktop /usr/share/applications/com.four43.Projects.SearchProvider.desktop
	install -Dm 0644 files/com.four43.Projects.SearchProvider.ini /usr/share/gnome-shell/search-providers/com.four43.Projects.SearchProvider.ini
	install -Dm 0644 files/com.four43.Projects.SearchProvider.dbus.service /usr/share/dbus-1/services/services/com.four43.Projects.SearchProvider.service

uninstall:
	rm -f /usr/lib/systemd/user/com.four43.Projects.SearchProvider.service
	rm -f /usr/share/applications/com.four43.Projects.SearchProvider.desktop
	rm -f /usr/share/gnome-shell/search-providers/com.four43.Projects.SearchProvider.ini
	rm -f /usr/share/dbus-1/services/services/com.four43.Projects.SearchProvider.service
	rm -rf ~/.local/bin/gnome-search-projects

dev: install
	rm -rf /usr/local/bin/gnome-search-projects
	ln -s $(shell pwd) /usr/local/bin/gnome-search-projects

restart:
	systemctl --user daemon-reload
	systemctl --user restart com.four43.Projects.SearchProvider.service
