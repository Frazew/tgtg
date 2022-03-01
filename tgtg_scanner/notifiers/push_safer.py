from pushsafer import Client
from ..models import Item, Notifier, PushSaferConfig, PushSaferConfigurationError


class PushSafer(Notifier):
    """PushSafer notifier class
    """

    _config: PushSaferConfig
    _client: Client = None

    def __init__(self, config: PushSaferConfig):
        super().__init__(config)

    def _init(self):
        if not self._config.key or not self._config.device_id:
            raise PushSaferConfigurationError()
        self._client = Client(self._config.key)

    def __str__(self) -> str:
        return self._config.key

    def _send(self, item: Item):
        self._log.debug("Sending PushSafer Notification")
        message = f"New Amount: {item.items_available}"
        self._client.send_message(message, item.display_name, self._config.device_id,
                                  "", "", "", "", "", "", "", "", "", "", "", "", "")
