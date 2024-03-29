#!/usr/bin/env python3

import logging
import re
from pathlib import Path
from random import choices
import shutil
import subprocess
import toml

import click
from jinja2 import Environment, FileSystemLoader
from xdg_base_dirs import xdg_config_dirs, xdg_config_home

logger = logging.getLogger(__name__)
DIR = Path(__file__).parent


def camel_to_kebab(s):
    s = s.replace(".", "-")
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    return s.lower()


def dot_to_fw_slash(s):
    return s.replace(".", "/")


env = Environment(loader=FileSystemLoader(DIR / "templates"))
env.filters["camel_to_kebab"] = camel_to_kebab
env.filters["dot_to_fw_slash"] = dot_to_fw_slash


@click.command()
@click.argument(
    "action",
    type=click.Choice(["install", "uninstall"]),
    default="install",
    required=True,
)
@click.argument("framework-path", type=click.Path(exists=True), required=True)
@click.argument("project-path", type=click.Path(exists=True), required=True)
@click.option("--debug", is_flag=True, help="Enable detailed logging to stderr")
def main(
    action: str,
    framework_path: Path,
    project_path: Path,
    debug: bool,
):
    """
    Install or uninstall the search provider

    ACTION is either:

        install - Add the search provider files to the various system paths
        uninstall - Remove the search provider from the various system paths

    PROJECT_PATH is the path to the project directory
    """
    project_path = Path(project_path)
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    # Load the meta.toml from the project_path
    meta_path = project_path / "meta.toml"
    try:
        with open(meta_path, "r") as f:
            meta_data = toml.load(f)
    except FileNotFoundError:
        logger.error(f"meta.toml not found in {project_path}")
        return

    # Extract the required variables from meta_data
    print(meta_data)
    plugin_meta = {"provider": {**meta_data}}

    # fmt: off
    template_output_map = {
        "dbus.service.jinja2":        Path('/usr') / "share" / "dbus-1"       / "services" / f"{plugin_meta['provider']['id']}.SearchProvider.service",      # ex: org.gnome.Calculator.SearchProvider.service
        "search-provider.ini.jinja2": Path('/usr') / "share" / "gnome-shell"  / "search-providers" / f"{plugin_meta['provider']['id']}.search-provider.ini", # ex: org.gnome.Calendar.search-provider.ini
        "search.desktop.jinja2":      Path('/usr') / "share" / "applications" / f"{plugin_meta['provider']['id']}.SearchProvider.desktop",                   # ex: org.gnome.Calculator.desktop
    }
    # fmt: on

    if action == "install":
        # Install templates
        for template_file, output_path in template_output_map.items():
            logger.info(f"Writing {output_path}...")
            template = env.get_template(template_file)
            rendered_template = template.render(**plugin_meta)
            with open(output_path, "w") as f:
                f.write(rendered_template)

        # Install the project path

        import venv

        venv.create(project_path / ".venv", system_site_packages=True, with_pip=True)
        subprocess.run(
            [
                project_path / ".venv/bin/pip",
                "install",
                framework_path
            ]
        )
        subprocess.run(
            [
                project_path / ".venv/bin/pip",
                "install",
                "-r",
                project_path / "requirements.txt",
            ]
        )

        # fmt: off
        output_project_path = Path('/usr') / "libexec" / f"{camel_to_kebab(plugin_meta['provider']['id'])}-search-provider"
        # fmt: on
        output_project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Copying {project_path} to {output_project_path}...")
        shutil.copytree(src=project_path, dst=output_project_path, dirs_exist_ok=True)

    elif action == "uninstall":
        for _, output_path in template_output_map.items():
            logger.info(f"Removing {output_path}...")
            output_path.unlink()


if __name__ == "__main__":
    main()
