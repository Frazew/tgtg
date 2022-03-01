"""This module implements the main Scanner application
"""
import sys
import logging
from time import sleep
from random import random
from typing import NoReturn

from .models import Item, Config, Metrics, TgtgAPIError, Error, TGTGConfigurationError
from .notifiers import Notifiers
from .tgtg import TgtgClient


class Scanner():
    """Scanner class that implements the main application loop
    """

    _log = logging.getLogger('tgtg')

    def __init__(self, config_file: str = None, notifiers: bool = True):
        """Initializes the Scanner and loads the configuration.

        If no config_file is provided the configuration is loaded from environment variables.

        Initializes the TGTG API client and checks for configuration errors.

        Initializes the notifiers.

        Args:
            config_file (str, optional): full filename of config.ini
            notifiers (bool, optional): set False to disable all notifiers. Defaults to True.

        Raises:
            TGTGConfigurationError: Couldn't connect to TGTG API
        """
        self.config = Config(config_file) if config_file else Config()
        if self.config.debug:
            # pylint: disable=E1103
            loggers = [logging.getLogger(name)
                       for name in logging.root.manager.loggerDict]
            # pylint: enable=E1103
            for logger in loggers:
                logger.setLevel(logging.DEBUG)
            self._log.info("Debugging mode enabled")
        self.metrics = Metrics()
        if self.config.metrics:
            self.metrics.enable_metrics()
        self.item_ids = self.config.item_ids
        self.amounts = {}
        try:
            self.tgtg_client = TgtgClient(
                email=self.config.tgtg.username,
                timeout=self.config.tgtg.timeout,
                access_token_lifetime=self.config.tgtg.access_token_lifetime,
                max_polling_tries=self.config.tgtg.max_polling_tries,
                polling_wait_time=self.config.tgtg.polling_wait_time,
                access_token=self.config.tgtg.access_token,
                refresh_token=self.config.tgtg.refresh_token,
                user_id=self.config.tgtg.user_id
            )
            self.tgtg_client.login()
        except TgtgAPIError as err:
            raise
        except Error as err:
            self._log.error(err)
            raise TGTGConfigurationError() from err
        if notifiers:
            self.notifiers = Notifiers(self.config)

    def _job(self):
        """Gets called on every application loop by the run() function.

        Gathers all item information and runs the _check_item function for every item.

        Calls the save_token function.
        """
        for item_id in self.item_ids:
            try:
                if item_id != "":
                    data = self.tgtg_client.get_item(item_id)
                    self._check_item(Item(data))
            except Exception:
                self._log.error(
                    "itemID %s Error! - %s", item_id, sys.exc_info())
        for data in self._get_favorites():
            try:
                self._check_item(Item(data))
            except Exception:
                self._log.error("check item error! - %s", sys.exc_info())
        self._log.debug("new State: %s", self.amounts)
        self.config.save_tokens(
            self.tgtg_client.access_token,
            self.tgtg_client.refresh_token,
            self.tgtg_client.user_id
        )

    def _get_favorites(self) -> list[dict]:
        """Requests all favorites from the TGTG API and returns them as a list.

        Returns:
            list[dict]: List of items as dict
        """
        items = []
        page = 1
        page_size = 100
        error_count = 0
        while True and error_count < 5:
            try:
                new_items = self.tgtg_client.get_items(
                    favorites_only=True,
                    page_size=page_size,
                    page=page
                )
                items += new_items
                if len(new_items) < page_size:
                    break
                page += 1
            except Exception:
                self._log.error("get item error! - %s", sys.exc_info())
                error_count += 1
                self.metrics.get_favorites_errors.inc()
        return items

    def _check_item(self, item: Item):
        """Checks if the current item's items_available property rose from zero to something.

        If true it calls the _send_messages function to trigger the notifications.

        The function sets the new amount to the item count metric.

        Args:
            item (Item): current Item
        """
        try:
            if self.amounts[item.item_id] == 0 \
                    and item.items_available > self.amounts[item.item_id]:
                self._send_messages(item)
                self.metrics.send_notifications.labels(
                    item.item_id, item.display_name).inc()
            self.metrics.item_count.labels(
                item.item_id, item.display_name).set(item.items_available)
        except Exception:
            self.amounts[item.item_id] = item.items_available
        finally:
            if self.amounts[item.item_id] != item.items_available:
                self._log.info("%s - new amount: %s",
                               item.display_name, item.items_available)
                self.amounts[item.item_id] = item.items_available

    def _send_messages(self, item: Item):
        """Triggers all notifiers to send the provided Item information

        Args:
            item (Item): Item to be send
        """
        self._log.info("Sending notifications for %s - %s bags available",
                       item.display_name, item.items_available)
        self.notifiers.send(item)

    def run(self) -> NoReturn:
        """Main application loop.

        Sleeps for a random time between loops based on the provided sleep_time.
        """
        self._log.info("Scanner started ...")
        while True:
            try:
                self._job()
            except Exception as err:
                self._log.error("Job Error! - %s", err)
            finally:
                sleep(self.config.sleep_time * (0.9 + 0.2 * random()))
