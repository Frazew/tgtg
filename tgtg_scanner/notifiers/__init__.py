import logging
from datetime import datetime
from ..models import Config, Item
from .push_safer import PushSafer
from .smtp import SMTP
from .ifttt import IFTTT
from .webhook import WebHook
from .telegram import Telegram

class Notifiers():
    """Notifiers class initializes all configured notifiers
    """

    _log = logging.getLogger('tgtg')

    def __init__(self, config: Config):
        """Notifiers class initializes all configured notifiers

        Args:
            config (Config): app configuration
        """
        self.push_safer = PushSafer(config.push_safer)
        self.smtp = SMTP(config.smtp)
        self.ifttt = IFTTT(config.ifttt)
        self.webhook = WebHook(config.webhook)
        self.telegram = Telegram(config.telegram)

        self._log.info("Activated notifiers:")
        if self.smtp.enabled:
            self._log.info("- SMTP: %s", self.smtp)
        if self.ifttt.enabled:
            self._log.info("- IFTTT: %s", self.ifttt)
        if self.push_safer.enabled:
            self._log.info("- PushSafer: %s", self.push_safer)
        if self.webhook.enabled:
            self._log.info("- WebHook: %s", self.webhook)
        if self.telegram.enabled:
            self._log.info("- Telegram: %s", self.telegram)

        now = datetime.now()
        if not config.disable_tests:
            test_item = Item({
                "item": {
                    "item_id": "12345",
                    "price_including_taxes": {
                        "code": "EUR",
                        "minor_units": 1099,
                        "decimals": 2
                    }
                },
                "display_name": "test_item",
                "pickup_interval": {
                    "start": f"{now.year}-{now.month}-{now.day}T20:00:00Z",
                    "end": f"{now.year}-{now.month}-{now.day}T21:00:00Z"},
                "items_available": 1})
            self._log.info("Sending test notifications ...")
            self.send(test_item)

    def send(self, item: Item):
        """Sends notification on all configured and enabled notifiers

        Args:
            item (Item): Item to send
        """
        self.push_safer.send(item)
        self.smtp.send(item)
        self.ifttt.send(item)
        self.webhook.send(item)
        self.telegram.send(item)
