import logging
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional

import pydbus
from gi.repository import GLib

from .main_loop import MainLoop

log = logging.getLogger(__name__)


class SearchProvider(metaclass=ABCMeta):
    dbus = """<node>
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

    def __init__(self, provider_id: str, timeout: int = 10) -> None:
        self._loop = MainLoop()
        self.provider_id = provider_id
        self.timeout = timeout

    def start(self) -> None:
        bus = pydbus.SessionBus()
        dbus_name = f"{self.provider_id}.SearchProvider"
        log.debug("Registering D-Bus name %s", dbus_name)
        bus.publish(dbus_name, self)

        log.debug("Waiting for requests on D-Bus name %s", dbus_name)
        self._loop.set_inactive_timeout(int(self.timeout))
        self._loop.run()

    def GetInitialResultSet(self, terms):
        log.debug("Initial search for %s", str(terms))
        self._loop.reset_active_timeout()

        return self.search(terms)

    def GetSubsearchResultSet(
        self, previous_results: List[str], terms: List[str]
    ) -> List[str]:
        log.debug("Subsearch for %s", str(terms))
        self._loop.reset_active_timeout()
        self.terms = terms

        return self.search(terms, previous_results)

    def ActivateResult(self, result: str, terms: List[str], timestamp: int):
        log.debug("Activate %s", result)
        self._loop.reset_active_timeout()
        self.select(result)

    def LaunchSearch(self, terms: List[str], timestamp: int):
        log.debug("Launch search %s, %d", terms, timestamp)
        self._loop.reset_active_timeout()

    def GetResultMetas(self, results) -> List[Dict]:
        log.debug("Get result metas for %s", results)
        self._loop.reset_active_timeout()

        metas = []
        for result_id in results:
            metas.append(self.get_meta(result_id))
        return metas

    @abstractmethod
    def search(self, terms, previous_results: Optional[list[str]] = None) -> list[str]:
        pass

    @abstractmethod
    def get_meta(self, result_id: str) -> dict:
        pass

    @abstractmethod
    def select(self, result_id: str) -> None:
        pass
