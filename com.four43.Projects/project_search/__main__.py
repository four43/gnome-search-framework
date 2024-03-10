#!/usr/bin/env python3
from gi.repository import GLib
from gi.repository import Gio

import pydbus
import pydbus.generic
from xdg_base_dirs import xdg_config_home, xdg_config_dirs

import argparse
import configparser
import logging
from pathlib import Path
import sys

log = logging.getLogger()

CONFIG_NAME = 'com.four43.Projects.SearchProvider.conf'

APP_DESKTOP_NAMES = [
  'code.desktop',
]


def argument_parser():
    parser = argparse.ArgumentParser(
        description="GNOME Search Provider for Joplin notes")
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help="Enable detailed logging to stderr")
    parser.add_argument('--timeout', metavar='SECONDS', default=10,
                        help="Shut down process after SECONDS inactivity. Default: 10)")
    return parser


def app_info():
    for desktop_name in APP_DESKTOP_NAMES:
        try:
            info = Gio.DesktopAppInfo.new(desktop_name)
            logging.debug("Loaded app info from %s", desktop_name)
            return info
        except TypeError as e:
            # This happens when the constructor returns NULL because the file
            # doesn't exist.
            log.debug("Failed to load app info from %s", desktop_name)


class SearchProvider2():
    """<node>
        <interface name="org.gnome.Shell.SearchProvider2">
            <method name="GetInitialResultSet">
                <arg type="as" name="terms" direction="in" />
                <arg type="as" name="results" direction="out" />
            </method>
            <method name="GetSubsearchResultSet">
                <arg type="as" name="previous_results" direction="in" />
                <arg type="as" name="terms" direction="in" />
                <arg type="as" name="results" direction="out" />
            </method>
            <method name="GetResultMetas">
                <arg type="as" name="identifiers" direction="in" />
                <arg type="aa{sv}" name="metas" direction="out" />
            </method>
            <method name="ActivateResult">
                <arg type="s" name="identifier" direction="in" />
                <arg type="as" name="terms" direction="in" />
                <arg type="u" name="timestamp" direction="in" />
            </method>
            <method name="LaunchSearch">
                <arg type="as" name="terms" direction="in" />
                <arg type="u" name="timestamp" direction="in" />
            </method>
        </interface>
    </node>"""

    def __init__(self, main_loop):
        self.main_loop = main_loop

        self.code_icon = Gio.ThemedIcon.new('application-xml')

        self.terms = []

    def GetInitialResultSet(self, terms):
        log.info("Initial search for %s", str(terms))
        self.main_loop.reset_active_timeout()
        self.terms = terms

        results = ["Project A", "Project B", "Project C"]

        return results

    def GetSubsearchResultSet(self, previous_results, terms):
        log.info("Subsearch for %s", str(terms))
        self.main_loop.reset_active_timeout()
        self.terms = terms

        # Lazy option. Search again on each keypress. Joplin is backed by
        # a local SQLite database so this should be fast enough.
        return self.GetInitialResultSet(terms)


    def GetResultMetas(self, results):
        log.info("Get result metas for %s", results)
        self.main_loop.reset_active_timeout()

        metas = []
        for result_id in results:
            metas.append({
                'id': GLib.Variant('s', result_id),
                'name': GLib.Variant('s', result_id),
                'gicon': GLib.Variant('s', self.code_icon.to_string()),
                'description': GLib.Variant('s', f"Description for {result_id}"),
            })
        return metas

    def ActivateResult(self, result, terms, timestamp):
        log.info("Activate %s", result)
        self.main_loop.reset_active_timeout()
        # FIXME: We can only activate the app, not the specific result.
        # See https://discourse.joplinapp.org/t/open-a-note-in-desktop-app-using-commandline/13433/6
        app_info().launch([], None)

    def LaunchSearch(self, terms, timestamp):
        log.info("Launch search %s", terms)
        self.main_loop.reset_active_timeout()
        # FIXME: We can only activate the app, not the specific result.
        # See https://discourse.joplinapp.org/t/open-a-note-in-desktop-app-using-commandline/13433/6
        app_info().launch([], None)


class MainLoop():
    """Wrapper around GLib main loop which adds an inactivity timeout."""
    def __init__(self):
        self.loop = GLib.MainLoop()

        self.timeout = None
        self.timeout_id = None

    def set_inactive_timeout(self, seconds=None):
        self.timeout = seconds
        self.reset_active_timeout()

    def reset_active_timeout(self):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        if self.timeout:
            GLib.timeout_add_seconds(self.timeout, lambda: self._inactive_timeout())

    def _inactive_timeout(self):
        log.info("Exiting due to %i seconds inactivity timer", self.timeout)
        self.loop.quit()
        return GLib.SOURCE_REMOVE

    def run(self):
        self.loop.run()


def load_config():
    parser = configparser.ConfigParser()
    for config_base in [xdg_config_home()] + xdg_config_dirs():
        config_path = Path(config_base / "gnome-shell", "search-providers", CONFIG_NAME)
        log.info("Loading config from %s", config_path)
        try:
            parser.read(config_path)
        except Exception as e:
            log.exception(e)
    try:
        api_token = parser['authentication']['api_token']
    except KeyError:
        raise RuntimeError("Did not find 'api_token' in config file. "
                           f"Check ~/.config/{CONFIG_NAME}")
    return api_token


def main():
    args = argument_parser().parse_args()

    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    # api_token = load_config()

    loop = MainLoop()

    bus = pydbus.SessionBus()
    dbusname = 'com.four43.Projects.SearchProvider'
    bus.publish(dbusname, SearchProvider2(loop))

    log.info("Waiting for requests on D-Bus name %s", dbusname)
    loop.set_inactive_timeout(int(args.timeout))
    loop.run()


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
