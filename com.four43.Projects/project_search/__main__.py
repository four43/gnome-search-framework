import logging
import os
from pathlib import Path
from typing import Any, List, Optional

import toml
from gi.repository import Gio, GLib
from xdg_base_dirs import xdg_config_dirs, xdg_config_home

from gnome_search_framework import SearchProvider

DIR = Path(__file__).parent
config = toml.load(DIR.parent / "meta.toml")

log = logging.getLogger(__name__)

APP_DESKTOP_NAMES = [
  'code.desktop',
]

def app_info() -> Gio.DesktopAppInfo:
    for desktop_name in APP_DESKTOP_NAMES:
        try:
            info = Gio.DesktopAppInfo.new(desktop_name)
            logging.debug("Loaded app info from %s", desktop_name)
            return info
        except TypeError as e:
            # This happens when the constructor returns NULL because the file
            # doesn't exist.
            log.debug("Failed to load app info from %s", desktop_name)
    raise FileNotFoundError(f"No app info found for any listed apps: {APP_DESKTOP_NAMES}")

class ProjectSearch(SearchProvider):

    icon = Gio.ThemedIcon.new("code")

    def __init__(self) -> None:
        super().__init__(provider_id=config["id"])
        self.user_config = self._load_user_config(config["id"])
        self.project_paths = [Path(x) for x in self.user_config["project_paths"]]
        self.keep_parent = self.user_config.get("keep_parent", True)
        log.info(f"Project paths: {self.project_paths}")

    def _load_user_config(self, provider_id: str) -> dict[str, Any] | dict[str, list[Any]]:
        default_config = {"project_paths": []}
        log.debug(f"Loading user config from: {[xdg_config_home()] + xdg_config_dirs()}")

        def get_config_path(base):
            return (
                Path(base)
                / "gnome-shell"
                / "search-providers"
                / f"{provider_id}.SearchProvider.toml"
            )

        for config_base in [xdg_config_home()] + xdg_config_dirs():
            config_path = get_config_path(config_base)
            log.info("Loading config from %s", config_path)
            try:
                return toml.load(config_path)
            except FileNotFoundError as e:
                log.info(
                    f"Error loading config from {config_path}, trying other locations..."
                )
            except toml.TomlDecodeError as e:
                log.exception(
                    f"Error loading config from {config_path}, malformed toml file.", e
                )
                raise e

        config_path = get_config_path(xdg_config_home())
        config_path.parent.mkdir(parents=True, exist_ok=True)
        log.warning(f"Nmsg=o config found. Installing config template to {config_path}")
        with open(config_path, "w") as f:
            f.write(toml.dumps(default_config))
        return default_config


    def _path_to_searchable(self, project_path: Path) -> str:
        for project_dir in self.project_paths:
            if str(project_path).startswith(str(project_dir)):
                if self.keep_parent:
                    return str(project_path.relative_to(project_dir.parent))
                else:
                    return str(project_path.relative_to(project_dir))
        raise RuntimeError("Cannot find path in project paths")

    @staticmethod
    def _filter_project(project_dir: str, terms: list[str]) -> bool:
        for term in terms:
            if term in project_dir:
                return True
        return False

    def search(self, terms: List[str], previous_results: Optional[list[str]] = None) -> list[str]:
        project_dirs = []
        if previous_results is None:
            # Find projects via file search
            for project_dir in self.project_paths:
                log.debug("Searching for projects in %s", project_dir)
                for dir_entry in project_dir.iterdir():
                    if dir_entry.is_dir():
                        search_str = self._path_to_searchable(dir_entry)
                        log.debug("Filtering for project %s against %s", search_str, terms)
                        if self._filter_project(project_dir=search_str, terms=terms):
                            project_dirs.append(str(dir_entry))
        else:
            for result in previous_results:
                search_str = self._path_to_searchable(Path(result))
                if self._filter_project(project_dir=search_str, terms=terms):
                    project_dirs.append(result)
        return project_dirs

    def get_meta(self, result_id: str) -> dict:
        search_str = self._path_to_searchable(Path(result_id))
        return {
            "id": GLib.Variant("s", result_id),
            "name": GLib.Variant("s", search_str),
            "gicon": GLib.Variant("s", ProjectSearch.icon.to_string()),
            "description": GLib.Variant("s", f"Description for {result_id}"),
        }

    def select(self, result_id: str) -> None:
        # Find result_id's full path:
        project_path = Path(result_id)
        if not project_path.exists():
            raise RuntimeError(f"Path {result_id} does not exist")

        launch_context = Gio.AppLaunchContext()
        launch_context.setenv("GIO_LAUNCH_FLAGS", "G_APP_INFO_CREATE_NEEDS_TERMINAL")

        # TODO auto launch into dev container
        # devcontainer_path = project_path / ".devcontainer" / "devcontainer.json"
        # if devcontainer_path.exists():
        #     import urllib.parse
        #     encoded_project_path = urllib.parse.quote(str(devcontainer_path), safe='')
        #     launch_args = ["--folder-uri", f"vscode-remote://dev-container+{encoded_project_path}"]
        # else:
        #     pass

        launch_args = [project_path.as_uri()]

        try:
            log.debug(f"Launching {result_id}: {launch_args}")
            app_info().launch_uris_as_manager(launch_args, launch_context, GLib.SpawnFlags.DO_NOT_REAP_CHILD, None)
        except GLib.Error as e:
            log.error(f"Failed to launch {result_id}: {e.message}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # ps = ProjectSearch()
    # results = ps.search(terms=["gnome"])


    ProjectSearch().start()
