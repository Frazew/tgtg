import re
import requests
from ..models import Item, WebHookConfigurationError, Notifier, WebHookConfig


class WebHook(Notifier):
    """WebHook notifier class
    """

    _config: WebHookConfig

    def __init__(self, config: WebHookConfig):
        super().__init__(config)

    def _init(self):
        if not self._config.method or not self._config.url:
            raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", self._config.body):
            if not match.group(1) in Item.ATTRS:
                raise WebHookConfigurationError()
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", self._config.url):
            if not match.group(1) in Item.ATTRS:
                raise WebHookConfigurationError()

    def __str__(self) -> str:
        return str(self._config.url)

    def _send(self, item: Item):
        self._log.debug("Sending WebHook Notification")
        url = self._config.url
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", url):
            if hasattr(item, match.group(1)):
                url = url.replace(
                    match.group(0),
                    str(getattr(item, match.group(1)))
                )
        self._log.debug("Webhook url: %s", url)
        body = None
        headers = {
            "Content-Type": self._config.type
        }
        self._log.debug("Webhook headers: %s", headers)
        if self._config.body:
            body = self._config.body
            for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", body):
                if hasattr(item, match.group(1)):
                    body = body.replace(
                        match.group(0), f"{getattr(item, match.group(1))}"
                    )
            headers["Content-Length"] = str(len(body))
            self._log.debug("Webhook body: %s", body)
        res = requests.request(
            method=self._config.method,
            url=url,
            timeout=self._config.timeout,
            data=body,
            headers=headers
        )
        res.raise_for_status()
