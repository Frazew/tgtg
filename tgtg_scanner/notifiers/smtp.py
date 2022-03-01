import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ..models import Item, SMTPConfig, SMTPConfigurationError, Notifier


class SMTP(Notifier):
    """SMTP notifier class
    """

    _config: SMTPConfig
    _server: smtplib.SMTP = None
    _debug: int = 0

    def __init__(self, config: SMTPConfig):
        super().__init__(config)

    def _init(self):
        if self._config.debug:
            self._debug = 1
        if not self._config.host or not self._config.port:
            raise SMTPConfigurationError()
        try:
            self._connect()
        except Exception as err:
            raise SMTPConfigurationError() from err

    def __del__(self):
        """Cancels smtp server connection on destruction
        """
        if self._server:
            try:
                self._server.quit()
            except Exception:
                pass

    def _connect(self):
        """Connects to SMTP server
        """
        if self._config.tls:
            self._server = smtplib.SMTP_SSL(
                self._config.host, self._config.port)
        else:
            self._server = smtplib.SMTP(self._config.host, self._config.port)
        self._server.set_debuglevel(self._debug)
        self._server.ehlo()
        if self._config.username and self._config.password:
            self._server.login(self._config.username, self._config.password)

    def _stay_connected(self):
        """Reconnects to SMTP server if disconnected
        """
        try:
            _ = self._server.noop()[0]
        except Exception:
            self._connect()

    def _send_mail(self, subject: str, text: str):
        """Send mail via smtplib

        Args:
            subject (str): Mail subject
            text (str):    Mail body
        """
        message = MIMEMultipart('alternative')
        message['From'] = self._config.sender
        message['To'] = self._config.recipient
        message['Subject'] = subject
        message.attach(MIMEText(text, 'plain'))
        body = message.as_string()
        self._stay_connected()
        self._server.sendmail(self._config.sender,
                              self._config.recipient, body)

    def __str__(self) -> str:
        return str(self._config.recipient)

    def _send(self, item: Item):
        self._log.debug("Sending Mail Notification")
        self._send_mail(
            "New Magic Bags", f"{item.display_name} - New Amount: {item.items_available}")
