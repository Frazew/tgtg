"""
The config module implements a config class, that manages and serves all configuration options.
"""
from os import environ, path
import configparser
import logging
from typing import Callable


class TGTGconfig():
    """TGTG API configuration
    """

    username: str = None
    """TGTG username (mail)
    """

    access_token: str = None
    """API access token
    """

    refresh_token: str = None
    """API refresh token
    """

    user_id: str = None
    """API user id
    """

    timeout: int = 60
    """Timeout for TGTG API requests
    """

    access_token_lifetime: int = 3600 * 4
    """Lifetime of the access token
    """

    max_polling_tries: int = 24
    """Maximum retries to obtain access tokens after login via mail
    """

    polling_wait_time: int = 5
    """Waiting time between polling tries
    """

    def __str__(self) -> str:
        return str(self.__dict__)


class NotifierConfig():
    """Basic nofifier configuration class
    """

    enabled: bool = False
    """Enables the notifier
    """

    def __str__(self) -> str:
        return str(self.__dict__)


class TelegramConfig(NotifierConfig):
    """Telegram notifier configuration
    """

    token: str = None
    """Telegram bot token
    """

    chat_id: str = None
    """Telegram chat id
    """

    write: Callable[[str, str, str], bool]
    """Sets an option in the config.ini
    """


class SMTPConfig(NotifierConfig):
    """SMTP notifier configuration
    """

    debug: bool = False
    """Debugging for smtp communication
    """

    host: str = "smtp.gmail.com"
    """SMTP host
    """

    port: int = 465
    """SMTP port
    """

    tls: bool = True
    """Enable TLS
    """

    username: str = None
    """SMTP server login username
    """

    password: str = None
    """SMTP server login password
    """

    sender: str = None
    """Mail of sender
    """

    recipient: str = None
    """Mail of recipient
    """


class PushSaferConfig(NotifierConfig):
    """PushSafer notifier configuration
    """

    key: str = None
    """PushSafer key token
    """

    device_id: str = None
    """PushSafer deviceId
    """


class IFTTTConfig(NotifierConfig):
    """IFTTT notifier configuration
    """

    event: str = "tgtg_notification"
    """IFTTT Webhooks event
    """

    key: str = None
    """IFTTT Webhooks key
    """


class WebHookConfig(NotifierConfig):
    """Webhook notifier configuration
    """

    url: str = None
    """Webhook url
    """

    method: str = "GET"
    """Webhook request type
    """

    body: str = None
    """Webhook body
    """

    type: str = "text/plain"
    """Webhook body type
    """

    timeout: int = 60
    """Webhook request timeout
    """


class Config():
    """The Config object manages and serves the configuration options

    Attributes:
        item_ids (list[str]):  List of item IDs
        sleep_time (int):      Sleep time between item update loops
        debug (bool):          True to activate debugging mode
        metrics (bool):        True to enable prometheus metrics http server
        metrics_port (int):    Port for the prometheus mettics http server
        tgtg (TGTGConfig):     Configuration for the TGTG API
        smtp (SMTPConfig):     Configuration for the SMTP notifier
        push_safer (PushSaferConfig): Configuration for the PushSafer notifier
        ifttt (IFTTTConfig):   Configuration for the IFTTT notifier
        telegram (TelegramConfig): Configuration for the Telegram notifier
    """

    _log = logging.getLogger('tgtg')

    debug: bool = False
    """Enables the debugging mode.
    """

    sleep_time: int = 60
    """Sleep time between item update loops.
    """

    disable_tests: bool = False
    """Disables test notifications on startup
    """

    item_ids: list[str] = []
    """List of item IDs to track in addition to favorites
    """

    metrics: bool = False
    """Enables the prometheus client http server
    """

    metrics_port: int = 8000
    """Port of the prometheus client http server
    """

    tgtg: TGTGconfig = None
    """TGTG API configuration options.
    """

    smtp: SMTPConfig = None
    """SMTP notifier options
    """

    push_safer: PushSaferConfig = None
    """PushSafer notifier options
    """

    ifttt: IFTTTConfig = None
    """IFTTT notifier options
    """

    telegram: TelegramConfig = None
    """Telegram notifier options
    """

    webhook: WebHookConfig = None
    """Webhook notifier options
    """

    def __init__(self, file: str = None):
        """The Config object manages and serves the configuration options

        Args:
            file (str, optional): provides the config.ini
        """
        self._file: str = file
        self._token_path: str = environ.get("TGTG_TOKEN_PATH", None)

        self.tgtg: TGTGconfig = TGTGconfig()

        self.telegram: TelegramConfig = TelegramConfig()
        self.ifttt: IFTTTConfig = IFTTTConfig()
        self.smtp: SMTPConfig = SMTPConfig()
        self.push_safer: PushSaferConfig = PushSaferConfig()
        self.webhook: WebHookConfig = WebHookConfig()

        if file:
            self._ini_reader(file)
            self._log.info("Loaded config from config.ini")
        else:
            self._env_reader()
            self._load_tokens()
            self._log.info("Loaded config from environment variables")

        self.telegram.write = self.set
        self.smtp.debug = self.debug

    def _load_tokens(self):
        """Reads saved tokens from token_path
        """
        if self._token_path:
            try:
                with open(path.join(self._token_path, 'accessToken'), 'r') as access_token_file:
                    self.tgtg.access_token = access_token_file.read()
                with open(path.join(self._token_path, 'refreshToken'), 'r') as refresh_token_file:
                    self.tgtg.refresh_token = refresh_token_file.read()
                with open(path.join(self._token_path, 'userID'), 'r') as user_id_file:
                    self.tgtg.user_id = user_id_file.read()
            except Exception:
                pass

    def _ini_reader(self, file: str):
        """Reads config from config.ini

        Args:
            file (str): File path of config.ini
        """
        config = configparser.ConfigParser()
        config.read(file)
        if "MAIN" in config.keys():
            self.debug = config["MAIN"].getboolean("Debug", self.debug)
            self.item_ids = config["MAIN"].get("ItemIDs").split(
                ',') if "ItemIDs" in config["MAIN"] else self.item_ids
            self.sleep_time = config["MAIN"].getint(
                "SleepTime", self.sleep_time)

            self.metrics = config["MAIN"].getboolean("Metrics", self.metrics)
            self.metrics_port = config["MAIN"].getint(
                "MetricsPort", self.metrics_port)

        if "TGTG" in config.keys():
            self.tgtg.username = config["TGTG"].get(
                "Username", self.tgtg.username)
            self.tgtg.access_token = config["TGTG"].get(
                "AccessToken", self.tgtg.access_token)
            self.tgtg.refresh_token = config["TGTG"].get(
                "RefreshToken", self.tgtg.refresh_token)
            self.tgtg.user_id = config["TGTG"].get("UserId", self.tgtg.user_id)
            self.tgtg.access_token_lifetime = config["TGTG"].getint(
                "AccessTokenLifetime", self.tgtg.access_token_lifetime)
            self.tgtg.max_polling_tries = config["TGTG"].getint(
                "MaxPollingTries", self.tgtg.max_polling_tries)
            self.tgtg.polling_wait_time = config["TGTG"].getint(
                "PollingWaitTime", self.tgtg.polling_wait_time)

        if "PUSHSAFER" in config.keys():
            self.push_safer.enabled = config["PUSHSAFER"].getboolean(
                "enabled", self.push_safer.enabled)
            self.push_safer.key = config["PUSHSAFER"].get(
                "Key", self.push_safer.key)
            self.push_safer.device_id = config["PUSHSAFER"].get(
                "DeviceID", self.push_safer.device_id)

        if "SMTP" in config.keys():
            self.smtp.enabled = config["SMTP"].getboolean(
                "enabled", self.smtp.enabled)
            self.smtp.host = config["SMTP"].get("Host", self.smtp.host)
            self.smtp.port = config["SMTP"].getint("Port", self.smtp.port)
            self.smtp.tls = config["SMTP"].getboolean("TLS", self.smtp.tls)
            self.smtp.username = config["SMTP"].get(
                "Username", self.smtp.username)
            self.smtp.password = config["SMTP"].get(
                "Password", self.smtp.password)
            self.smtp.sender = config["SMTP"].get("Sender", self.smtp.sender)
            self.smtp.recipient = config["SMTP"].get(
                "Recipient", self.smtp.recipient)

        if "IFTTT" in config.keys():
            self.ifttt.enabled = config["IFTTT"].getboolean(
                "enabled", self.ifttt.enabled)
            self.ifttt.event = config["IFTTT"].get("Event", self.ifttt.event)
            self.ifttt.key = config["IFTTT"].get("Key", self.ifttt.key)

        if "WEBHOOK" in config.keys():
            self.webhook.enabled = config["WEBHOOK"].getboolean(
                "enabled", self.webhook.enabled)
            self.webhook.url = config["WEBHOOK"].get("URL", self.webhook.url)
            self.webhook.method = config["WEBHOOK"].get(
                "Method", self.webhook.method)
            self.webhook.body = config["WEBHOOK"].get(
                "body", self.webhook.body)
            self.webhook.type = config["WEBHOOK"].get(
                "type", self.webhook.type)
            self.webhook.timeout = config["WEBHOOK"].getint(
                "timeout", self.webhook.timeout)

        if "TELEGRAM" in config.keys():
            self.telegram.enabled = config["TELEGRAM"].getboolean(
                "enabled", self.telegram.enabled)
            self.telegram.token = config["TELEGRAM"].get(
                "token", self.telegram.token)
            self.telegram.chat_id = config["TELEGRAM"].get(
                "chat_id", self.telegram.chat_id)

    def _env_reader(self):
        """Reads config from environment variables
        """
        self.item_ids = environ.get("ITEM_IDS").split(
            ",") if environ.get("ITEM_IDS") else self.item_ids
        self.sleep_time = int(environ.get("SLEEP_TIME", self.sleep_time))
        self.debug = environ.get(
            "DEBUG", "false").lower() in ('true', '1', 't')
        self.metrics = environ.get(
            "METRICS", "false").lower() in ('true', '1', 't')
        self.metrics_port = environ.get("METRICS_PORT", self.metrics_port)
        self.disable_tests = environ.get(
            "DISABLE_TESTS", "false").lower() in ('true', '1', 't')

        self.tgtg.username = environ.get("TGTG_USERNAME", self.tgtg.username)
        self.tgtg.access_token = environ.get(
            "TGTG_ACCESS_TOKEN", self.tgtg.access_token)
        self.tgtg.refresh_token = environ.get(
            "TGTG_REFRESH_TOKEN", self.tgtg.refresh_token)
        self.tgtg.user_id = environ.get("TGTG_USER_ID", self.tgtg.user_id)
        self.tgtg.timeout = int(environ.get("TGTG_TIMEOUT", self.tgtg.timeout))
        self.tgtg.access_token_lifetime = int(environ.get(
            "TGTG_ACCESS_TOKEN_LIFETIME", self.tgtg.access_token_lifetime))
        self.tgtg.max_polling_tries = int(environ.get(
            "TGTG_MAX_POLLING_TRIES", self.tgtg.max_polling_tries))
        self.tgtg.polling_wait_time = int(environ.get(
            "TGTG_POLLING_WAIT_TIME", self.tgtg.polling_wait_time))

        self.push_safer.enabled = environ.get(
            "PUSH_SAFER", "false").lower() in ('true', '1', 't')
        self.push_safer.key = environ.get(
            "PUSH_SAFER_KEY", self.push_safer.key)
        self.push_safer.device_id = environ.get(
            "PUSH_SAFER_DEVICE_ID", self.push_safer.device_id)

        self.smtp.enabled = environ.get(
            "SMTP", "false").lower() in ('true', '1', 't')
        self.smtp.host = environ.get("SMTP_HOST", self.smtp.host)
        self.smtp.port = int(environ.get("SMTP_PORT", self.smtp.port))
        self.smtp.tls = environ.get(
            "SMTP_TLS", "false").lower() in ('true', '1', 't')
        self.smtp.username = environ.get("SMTP_USERNAME", self.smtp.username)
        self.smtp.password = environ.get("SMTP_PASSWORD", self.smtp.password)
        self.smtp.sender = environ.get("SMTP_SENDER", self.smtp.sender)
        self.smtp.recipient = environ.get(
            "SMTP_RECIPIENT", self.smtp.recipient)

        self.ifttt.enabled = environ.get(
            "IFTTT", "false").lower() in ('true', '1', 't')
        self.ifttt.event = environ.get("IFTTT_EVENT", self.ifttt.event)
        self.ifttt.key = environ.get("IFTTT_KEY", self.ifttt.key)

        self.webhook.enabled = environ.get(
            "WEBHOOK", "false").lower() in ('true', '1', 't')
        self.webhook.url = environ.get("WEBHOOK_URL", self.webhook.url)
        self.webhook.method = environ.get(
            "WEBHOOK_METHOD", self.webhook.method)
        self.webhook.body = environ.get("WEBHOOK_BODY", self.webhook.body)
        self.webhook.type = environ.get("WEBHOOK_TYPE", self.webhook.type)
        self.webhook.timeout = int(environ.get(
            "WEBHOOK_TIMEOUT", self.webhook.timeout))

        self.telegram.enabled = environ.get(
            "TELEGRAM", "false").lower() in ('true', '1', 't')
        self.telegram.token = environ.get(
            "TELEGRAM_TOKEN", self.telegram.token)
        self.telegram.chat_id = environ.get(
            "TELEGRAM_CHAT_ID", self.telegram.chat_id)

    def set(self, section: str, option: str, value: str) -> bool:
        """Sets an option in the config.ini

        Args:
            section (str): Section name
            option (str):  Option name
            value (str):   New value

        Returns:
            bool: returns True on success
        """
        if self._file:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self._file)
                config.set(section, option, value)
                with open(self._file, 'w') as configfile:
                    config.write(configfile)
                return True
            except Exception as err:
                self._log.error("error writing config.ini! - %s", err)
        return False

    def save_tokens(self, access_token: str, refresh_token: str, user_id: str):
        """Saves tgtg credential tokens to token_path and config.ini

        Args:
            access_token (str):  Access token
            refresh_token (str): Refresh token
            user_id (str):       User ID
        """
        if self._file:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self._file)
                config.set("TGTG", "AccessToken", access_token)
                config.set("TGTG", "RefreshToken", refresh_token)
                config.set("TGTG", "UserId", user_id)
                with open(self._file, 'w') as configfile:
                    config.write(configfile)
            except Exception as err:
                self._log.error(
                    "error saving credentials to config.ini! - %s", err)
        if self._token_path:
            try:
                with open(path.join(self._token_path, 'accessToken'), 'w') as access_token_file:
                    access_token_file.write(access_token)
                with open(path.join(self._token_path, 'refreshToken'), 'w') as refresh_token_file:
                    refresh_token_file.write(refresh_token)
                with open(path.join(self._token_path, 'userID'), 'w') as user_id_file:
                    user_id_file.write(user_id)
            except Exception as err:
                self._log.error("error saving credentials! - %s", err)
