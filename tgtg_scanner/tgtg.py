"""Copied from https://github.com/ahivert/tgtg-python

Modified by Der-Henning
"""
from __future__ import annotations
import datetime
import random
import logging
import time
from http import HTTPStatus
from urllib.parse import urljoin
import requests
from .models import TgtgAPIError, TgtgLoginError, \
    TgtgPollingError, TGTGConfigurationError

BASE_URL = "https://apptoogoodtogo.com/api/"
API_ITEM_ENDPOINT = "item/v7/"
AUTH_BY_EMAIL_ENDPOINT = "auth/v3/authByEmail"
AUTH_POLLING_ENDPOINT = "auth/v3/authByRequestPollingId"
SIGNUP_BY_EMAIL_ENDPOINT = "auth/v3/signUpByEmail"
REFRESH_ENDPOINT = "auth/v3/token/refresh"
USER_AGENTS = [
    "TGTG/21.12.1 Dalvik/2.1.0 (Linux; U; Android 6.0.1; Nexus 5 Build/M4B30Z)",
    "TGTG/21.12.1 Dalvik/2.1.0 (Linux; U; Android 7.0; SM-G935F Build/NRD90M)",
    "TGTG/21.12.1 Dalvik/2.1.0 (Linux; Android 6.0.1; SM-G920V Build/MMB29K)",
]
DEFAULT_ACCESS_TOKEN_LIFETIME = 3600 * 4  # 4 hours
DEFAULT_MAX_POLLING_TRIES = 24  # 24 * POLLING_WAIT_TIME = 2 minutes
DEFAULT_POLLING_WAIT_TIME = 5  # Seconds


class TgtgClient:

    _log = logging.getLogger('tgtg')

    def __init__(
        self,
        url: str = BASE_URL,
        email: str = None,
        access_token: str = None,
        refresh_token: str = None,
        user_id: str = None,
        user_agent: str = None,
        language: str = "en-UK",
        proxies: dict = None,
        timeout: int = None,
        access_token_lifetime: int = DEFAULT_ACCESS_TOKEN_LIFETIME,
        max_polling_tries: int = DEFAULT_MAX_POLLING_TRIES,
        polling_wait_time: int = DEFAULT_POLLING_WAIT_TIME,
        device_type: str = "ANDROID",
    ):
        self.base_url = url

        self.email = email

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_id = user_id

        self.last_time_token_refreshed = None
        self.access_token_lifetime = access_token_lifetime
        self.max_polling_tries = max_polling_tries
        self.polling_wait_time = polling_wait_time

        self.device_type = device_type

        self.user_agent = user_agent if user_agent else random.choice(
            USER_AGENTS)
        self.language = language
        self.proxies = proxies
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers = self._headers

    def __del__(self):
        self.session.close()

    def _get_url(self, path: str) -> str:
        return urljoin(self.base_url, path)

    @property
    def credentials(self) -> dict:
        self.login()
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id
        }

    @property
    def _headers(self) -> dict:
        headers = {
            "user-agent": self.user_agent,
            "accept-language": self.language,
            "Accept-Encoding": "gzip"
        }
        if self.access_token:
            headers["authorization"] = f"Bearer {self.access_token}"
        return headers

    @property
    def _already_logged(self) -> bool:
        return bool(self.access_token and self.refresh_token and self.user_id)

    def _request(self, url: str, json: dict) -> requests.Response:
        response = self.session.post(
            url,
            json=json,
            proxies=self.proxies,
            timeout=self.timeout
        )
        return response

    def _refresh_token(self):
        if (
            self.last_time_token_refreshed
            and (datetime.datetime.now() - self.last_time_token_refreshed).seconds
            <= self.access_token_lifetime
        ):
            return
        response = self._request(
            self._get_url(REFRESH_ENDPOINT),
            json={"refresh_token": self.refresh_token}
        )
        if response.status_code == HTTPStatus.OK:
            self.access_token = response.json()["access_token"]
            self.refresh_token = response.json()["refresh_token"]
            self.last_time_token_refreshed = datetime.datetime.now()
        else:
            raise TgtgAPIError(response.status_code, response.content)

    def login(self):
        if not (
            self.email or self.access_token and self.refresh_token and self.user_id
        ):
            raise TGTGConfigurationError(
                "You must provide at least email or access_token, refresh_token and user_id"
            )
        if self._already_logged:
            self._refresh_token()
        else:
            response = self._request(
                self._get_url(AUTH_BY_EMAIL_ENDPOINT),
                json={
                    "device_type": self.device_type,
                    "email": self.email,
                }
            )
            if response.status_code == HTTPStatus.OK:
                first_login_response = response.json()
                if first_login_response["state"] == "TERMS":
                    raise TgtgPollingError(
                        f"This email {self.email} is not linked to a tgtg account. "
                        "Please signup with this email first."
                    )
                if first_login_response["state"] == "WAIT":
                    self.start_polling(first_login_response["polling_id"])
                else:
                    raise TgtgLoginError(
                        response.status_code, response.content)
            else:
                if response.status_code == 429:
                    raise TgtgAPIError(
                        "429 - Too many requests. Try again later.")
                raise TgtgLoginError(
                    response.status_code, response.content)

    def start_polling(self, polling_id: str):
        for _ in range(self.max_polling_tries):
            response = self._request(
                self._get_url(AUTH_POLLING_ENDPOINT),
                json={
                    "device_type": self.device_type,
                    "email": self.email,
                    "request_polling_id": polling_id,
                }
            )
            if response.status_code == HTTPStatus.ACCEPTED:
                self._log.warning(
                    "Check your mailbox on PC to continue... "
                    "(Mailbox on mobile won't work, if you have installed tgtg app.)"
                )
                time.sleep(self.polling_wait_time)
                continue
            if response.status_code == HTTPStatus.OK:
                self._log.info("Logged in!")
                login_response = response.json()
                self.access_token = login_response["access_token"]
                self.refresh_token = login_response["refresh_token"]
                self.last_time_token_refreshed = datetime.datetime.now()
                self.user_id = login_response["startup_data"]["user"]["user_id"]
                return
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                raise TgtgAPIError(
                    "429 - Too many requests. Try again later.")
            raise TgtgLoginError(
                response.status_code, response.content)

        raise TgtgPollingError("Max retries ({} seconds) reached. Try again.".format(
            self.max_polling_tries * self.polling_wait_time
        ))

    def get_items(
        self,
        *,
        latitude: float = 0.0,
        longitude: float = 0.0,
        radius: int = 21,
        page_size: int = 20,
        page: int = 1,
        discover: bool = False,
        favorites_only: bool = True,
        item_categories: list[str] = None,
        diet_categories: list[str] = None,
        pickup_earliest: str = None,
        pickup_latest: str = None,
        search_phrase: str = None,
        with_stock_only: bool = False,
        hidden_only: bool = False,
        we_care_only: bool = False,
    ) -> list[dict]:
        self.login()

        # fields are sorted like in the app
        data = {
            "user_id": self.user_id,
            "origin": {"latitude": latitude, "longitude": longitude},
            "radius": radius,
            "page_size": page_size,
            "page": page,
            "discover": discover,
            "favorites_only": favorites_only,
            "item_categories": item_categories if item_categories else [],
            "diet_categories": diet_categories if diet_categories else [],
            "pickup_earliest": pickup_earliest,
            "pickup_latest": pickup_latest,
            "search_phrase": search_phrase,
            "with_stock_only": with_stock_only,
            "hidden_only": hidden_only,
            "we_care_only": we_care_only,
        }
        response = self._request(
            self._get_url(API_ITEM_ENDPOINT),
            json=data
        )
        if response.status_code == HTTPStatus.OK:
            return response.json()["items"]
        raise TgtgAPIError(response.status_code, response.content)

    def get_item(self, item_id: int | str) -> dict:
        self.login()
        response = self._request(
            urljoin(self._get_url(API_ITEM_ENDPOINT), str(item_id)),
            json={"user_id": self.user_id, "origin": None}
        )
        if response.status_code == HTTPStatus.OK:
            return response.json()
        raise TgtgAPIError(response.status_code, response.content)

    def set_favorite(self, item_id: int | str, is_favorite: bool):
        self.login()
        response = self._request(
            urljoin(self._get_url(API_ITEM_ENDPOINT),
                    f"{item_id}/setFavorite"),
            json={"is_favorite": is_favorite}
        )
        if response.status_code != HTTPStatus.OK:
            raise TgtgAPIError(response.status_code, response.content)

    def signup_by_email(
        self,
        *,
        email: str,
        name: str = "",
        country_id: str = "GB",
        newsletter_opt_in: bool = False,
        push_notification_opt_in: bool = True,
    ) -> TgtgClient:
        response = self._request(
            self._get_url(SIGNUP_BY_EMAIL_ENDPOINT),
            json={
                "country_id": country_id,
                "device_type": self.device_type,
                "email": email,
                "name": name,
                "newsletter_opt_in": newsletter_opt_in,
                "push_notification_opt_in": push_notification_opt_in,
            }
        )
        if response.status_code == HTTPStatus.OK:
            self.access_token = response.json(
            )["login_response"]["access_token"]
            self.refresh_token = response.json(
            )["login_response"]["refresh_token"]
            self.last_time_token_refreshed = datetime.datetime.now()
            self.user_id = response.json()["login_response"]["startup_data"]["user"][
                "user_id"
            ]
            return self
        raise TgtgAPIError(response.status_code, response.content)
