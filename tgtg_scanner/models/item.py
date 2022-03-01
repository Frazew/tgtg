"""This module implements the Item class
"""
import datetime


class Item():
    """The Item object describes the current state of one tgtg item

    Attributes:
        item_id (str):         unique item identifier
        items_available (int): available item count
        display_name (str):    display name as in tgtg app
        price (float):         price for one item
        currency (str):        currency for the price
        pickupdate (str):      human readable pickup date
    """

    ATTRS = ["item_id", "items_available", "display_name",
             "price", "currency", "pickupdate"]
    """List of available item attributes for notifications
    """

    def __init__(self, data: dict):
        """The Item object describes the current state of one tgtg item

        Args:
            data (dict): data for one item from tgtg API
        """
        self.item_id: str = data["item"]["item_id"]
        self.items_available: int = data["items_available"]
        self.display_name: str = data["display_name"]
        self.price: float = 0
        self.currency: str = ""
        if 'price_including_taxes' in data["item"]:
            self.price = data["item"]["price_including_taxes"]["minor_units"] / \
                (10**data["item"]["price_including_taxes"]["decimals"])
            self.currency = data["item"]["price_including_taxes"]["code"]
        if 'pickup_interval' in data:
            self.interval_start: datetime.datetime = self._datetimeparse(
                data['pickup_interval']['start'])
            self.interval_end: datetime.datetime = self._datetimeparse(
                data['pickup_interval']['end'])

    @staticmethod
    def _datetimeparse(datestr: str) -> datetime.datetime:
        """Parses datetime string from tgtg API to datetime object

        Args:
            datestr (str): datetime string in format '%Y-%m-%dT%H:%M:%SZ'

        Returns:
            datetime.datetime: datetime object
        """
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    @property
    def pickupdate(self) -> str:
        """Return the pickup date and time range in a human readable format

        Returns:
            str: human readable pickup date
        """
        if (hasattr(self, "interval_start") and hasattr(self, "interval_end")):
            now = datetime.datetime.now()
            pfrom = self.interval_start
            pto = self.interval_end
            prange = "%02d:%02d - %02d:%02d" % (pfrom.hour,
                                                pfrom.minute, pto.hour, pto.minute)
            if now.date() == pfrom.date():
                return "Today, %s" % prange
            if (pfrom.date() - now.date()).days == 1:
                return "Tomorrow, %s" % prange
            return "%d/%d, %s" % (pfrom.day, pfrom.month, prange)
        return "undefined"
