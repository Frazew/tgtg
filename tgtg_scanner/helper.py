"""This module implements a helper CLI
"""
import logging
from .scanner import Scanner


class Helper(Scanner):
    """Helper class that implements the Scanner to provide some helpfull functions
    """

    _log = logging.getLogger('tgtg')
    _log.setLevel(logging.WARNING)

    @property
    def credentials(self) -> dict:
        """Access token, refresh token and user id

        Returns:
            dict: contains the credentials
        """
        return self.tgtg_client.credentials

    def get_items(self, lat: float, lng: float, radius: int) -> list[dict]:
        """Get items for a location

        Args:
            lat (float): latitude
            lng (float): longitude
            radius (int): radius

        Returns:
            list[Item]: List of items
        """
        return self.tgtg_client.get_items(
            favorites_only=False,
            latitude=lat,
            longitude=lng,
            radius=radius,
        )

    @property
    def favorites(self) -> list[dict]:
        """Get favorite items

        Returns:
            list[Item]: List of items
        """
        items = []
        page = 1
        page_size = 100
        while True:
            try:
                new_items = self.tgtg_client.get_items(
                    favorites_only=True,
                    page_size=page_size,
                    page=page
                )
                items += new_items
                if len(new_items) < page_size:
                    break
            except Exception as err:
                self._log.error("getItem Error! - %s", err)
            finally:
                page += 1
        return items

    def set_favorite(self, item_id: str):
        """Set a new favorite item

        Args:
            item_id (str): Item ID
        """
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=True)

    def unset_favorite(self, item_id: str):
        """Removes a favorite item

        Args:
            item_id (str): Item ID
        """
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=False)

    def remove_all_favorites(self):
        """Removes all favorites
        """
        item_ids = [item["item"]["item_id"] for item in self.favorites]
        for item_id in item_ids:
            self.unset_favorite(item_id)
