"""This module implements the basic Notifier and NotifierConfig classes
"""
import logging
from ..models import Item, NotifierConfig


class Notifier():
    """Basic notifier class

    To implement a new notifier as a minimum you have to overwrite the _send function.
    """

    _log: logging.Logger = logging.getLogger('tgtg')
    _enabled: bool = False

    def __init__(self, config: type[NotifierConfig]):
        """Initializes the notifier with the given config

        Args:
            config (NotifierConfig): notifier configuration
        """
        self._config = config
        self.enabled = self._config.enabled

    def _init(self):
        """This function will be called, when the notifier gets enabled.

        Implement this function for configuration checks and further initialization.

        Should raise configuration errors.
        """

    def __str__(self) -> str:
        """Override this function to identify the notifier in the console

        Returns:
            str: description of the notifier
        """

    @property
    def enabled(self):
        """Enables the notifier.
        Notifications will only be send if set to True.
        Setting this option to True will run the _init() function.
        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool):
        self._enabled = enabled
        if self.enabled:
            self._init()

    def _send(self, item: Item):
        """This funtcion implements the actual sending process for the notifier.
        This function needs to be implemented for every notifier.

        Args:
            item (Item): Provided item information
        """
        self._log.warning(
            "Send function for this notifier is not implemented!")

    def send(self, item: Item):
        """Sends notification if notifier is enabled

        Args:
            item (Item): Item to send
        """
        if self.enabled:
            try:
                self._send(item)
            except Exception as err:
                self._log.error(err)
