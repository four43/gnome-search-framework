import logging
from gi.repository import GLib

log = logging.getLogger(__name__)

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
