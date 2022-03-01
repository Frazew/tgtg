"""This module implements a prometheus metrics http server.
"""
import logging
from prometheus_client import start_http_server, Gauge, Counter


class Metrics():
    """The Metrics object implements a prometheus metrics http server

    Attributes:
        item_count (Gauge):             currently available bags by item_id
        get_favorites_errors (Counter): error count fetching tgtg favorites
        send_notifications (Counter):   count of send notifications by item_id
    """

    _log = logging.getLogger('tgtg')

    def __init__(self, port: int = 8000):
        """The Metrics object implements a prometheus metrics http server

        Args:
            port (int, optional): port of the http server. Defaults to 8000.
        """
        self._port = port
        self.item_count: Gauge = Gauge(
            "tgtg_item_count", "Currently available bags", ['item_id', 'display_name'])
        self.get_favorites_errors: Counter = Counter(
            "tgtg_get_favorites_errors", "Count of request errors fetching tgtg favorites")
        self.send_notifications: Counter = Counter(
            "tgtg_send_notifications", "Count of send notifications", ['item_id', 'display_name'])

    def enable_metrics(self):
        """Starts the prometheus client http server
        """
        start_http_server(self._port)
        self._log.info("Metrics server startet on port %s", self._port)
