import requests
from ..models import Item, IFTTTConfigurationError, Notifier, IFTTTConfig


class IFTTT(Notifier):
    """IFTTT notifier class
    """

    _config: IFTTTConfig
    _url: str = None

    def __init__(self, config: IFTTTConfig):
        super().__init__(config)

    def _init(self):
        """Checks IFTTT notifier configuration and builds webhook url

        Raises:
            IFTTTConfigurationError: on missing Webhooks event or key
        """
        if not self._config.event or not self._config.key:
            raise IFTTTConfigurationError()
        self._url = "https://maker.ifttt.com/trigger/{0}/with/key/{1}".format(
            self._config.event,
            self._config.key
        )

    def __str__(self) -> str:
        return self._config.key

    def _send(self, item: Item):
        self._log.debug("Sending IFTTT Notification")
        res = requests.post(
            self._url,
            json={
                "value1": item.display_name,
                "value2": item.items_available
            },
            timeout=60)
        res.raise_for_status()
