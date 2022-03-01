import random
from time import sleep
import telegram
from ..models import Item, TelegramConfigurationError, Notifier, TelegramConfig


class Telegram(Notifier):
    """Telegram notifier class
    """

    _config: TelegramConfig
    _bot: telegram.Bot

    def __init__(self, config: TelegramConfig):
        super().__init__(config)

    def _init(self):
        if not self._config.token:
            raise TelegramConfigurationError("Missing Telegram token")
        try:
            self._bot = telegram.Bot(token=self._config.token)
            self._bot.get_me(timeout=60)
        except Exception as err:
            raise TelegramConfigurationError() from err
        if not self._config.chat_id:
            self._get_chat_id()

    def __str__(self) -> str:
        return str(self._config.chat_id)

    def _send(self, item: Item):
        self._log.debug("Sending Telegram Notification")
        fmt = telegram.ParseMode.MARKDOWN
        message = "*%s*\n*Available*: %d\n*Price*: %.2f %s\n*Pickup*: %s" % (
            item.display_name,
            item.items_available,
            item.price,
            item.currency,
            item.pickupdate
        )
        self._bot.send_message(
            chat_id=self._config.chat_id,
            text=message,
            parse_mode=fmt,
            timeout=60
        )

    def _get_chat_id(self):
        """Initializes an interaction with the user to obtain the telegram chat id. \n
        On using the config.ini configuration the chat id will be stored in the config.ini.
        """
        self._log.warning(
            "You enabled the Telegram notifications without providing a chat id!")
        code = random.randint(1111, 9999)
        self._log.warning("Send %s to the bot in your desired chat.", code)
        self._log.warning("Waiting for code ...")
        while not self._config.chat_id:
            updates = self._bot.get_updates(timeout=60)
            for update in reversed(updates):
                if int(update.message.text) == code:
                    self._log.warning(
                        "Received code from %s %s on chat id %s",
                        update.message.from_user.first_name,
                        update.message.from_user.last_name,
                        update.message.chat_id
                    )
                    self._config.chat_id = update.message.chat_id
            sleep(1)
        if self._config.write("TELEGRAM", "chat_id", str(self._config.chat_id)):
            self._log.warning("Saved chat id in your config file")
        else:
            self._log.warning(
                "For persistence please set TELEGRAM_CHAT_ID=%s", self._config.chat_id
            )
