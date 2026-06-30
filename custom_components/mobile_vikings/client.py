"""Module containing the MobileVikingsClient class for interacting with the Mobile Vikings API."""

from datetime import datetime, timedelta, timezone
import logging

from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    BASE_URL,
    BASE_URL_JIMMOBILE,
    CLIENT_ID,
    CLIENT_ID_JIMMOBILE,
    CLIENT_SECRET,
    CLIENT_SECRET_TAG,
    CLIENT_SECRET_TAG_JIMMOBILE,
    CLIENT_SECRET_VALUE_JIMMOBILE,
    JIM_MOBILE,
    MOBILE_VIKINGS,
)

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""

    pass


class MobileVikingsClient:
    """Asynchronous client for interacting with the Mobile Vikings API."""

    def __init__(self, hass, username, password, mobile_platform, tokens=None):
        """Initialize the MobileVikingsClient.

        Parameters
        ----------
        hass : HomeAssistant
            The Home Assistant instance to use for handling API requests and coordination.
        username : str
            The username for authenticating with the Mobile Vikings API.
        password : str
            The password for authenticating with the Mobile Vikings API.
        mobile_platform : str
            The name of the mobile platform to connect to (Mobile Vikings or Jim Mobile).
        tokens : dict, optional
            A dictionary containing token information (refresh_token, access_token, expiry).

        """
        self.hass = hass
        self.username = username
        self.password = password
        self.mobile_platform = mobile_platform
        self.refresh_token = None
        self.access_token = None
        self.expires_in = None
        self.access_token_expiry = None
        self.client = get_async_client(self.hass)

        if tokens:
            self.refresh_token = tokens.get("refresh_token")
            self.access_token = tokens.get("access_token")
            self.expires_in = tokens.get("expires_in")
            if self.expires_in:
                self.access_token_expiry = datetime.fromisoformat(str(self.expires_in))

    async def close(self):
        """Set the client to none."""
        self.client = None

    async def authenticate(self):
        """Authenticate with the Mobile Vikings / JimMobile API."""
        actual_client_id = (
            CLIENT_ID_JIMMOBILE if self.mobile_platform == JIM_MOBILE else CLIENT_ID
        )
        actual_client_secret_tag = (
            CLIENT_SECRET_TAG_JIMMOBILE
            if self.mobile_platform == JIM_MOBILE
            else CLIENT_SECRET_TAG
        )
        actual_client_secret_value = (
            CLIENT_SECRET_VALUE_JIMMOBILE
            if self.mobile_platform == JIM_MOBILE
            else CLIENT_SECRET
        )
        if self._is_token_valid():
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"
        else:
            if self.refresh_token:
                _LOGGER.debug("Access token renewal with refresh token")
                await self._request_token(
                    {
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token",
                        "client_id": actual_client_id,
                        actual_client_secret_tag: actual_client_secret_value,
                    }
                )
            else:
                _LOGGER.debug("Requesting new access token")
                await self._request_token(
                    {
                        "username": self.username,
                        "password": self.password,
                        "grant_type": "password",
                        "client_id": actual_client_id,
                        actual_client_secret_tag: actual_client_secret_value,
                    }
                )

        if self._is_token_valid():
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"
            return {
                "refresh_token": self.refresh_token,
                "access_token": self.access_token,
                "expires_in": self.expires_in,
            }
        else:
            return False

    def _is_token_valid(self):
        """Check if the current access token is valid."""
        return (
            self.access_token
            and self.access_token_expiry
            and datetime.now() < self.access_token_expiry
        )

    async def _request_token(self, payload):
        """Request an access token with the given payload."""
        response = await self.handle_request(
            "/oauth2/token/", payload, "POST", True, True
        )

        data = response.json()
        if response.status_code == 200:
            self.access_token = data.get("access_token")
            self.expires_in = data.get("expires_in")
            self.access_token_expiry = datetime.now() + timedelta(
                seconds=self.expires_in
            )
            self.refresh_token = data.get("refresh_token")
        elif response.status_code == 400 and payload.get("grant_type") == "password":
            raise AuthenticationError(
                f"Invalid grant_type - {data.get('error_description')}"
            )
        elif (
            response.status_code == 401 and payload.get("grant_type") == "refresh_token"
        ):
            raise AuthenticationError(f"Unauthorized - {data.get('error_description')}")
        else:
            raise AuthenticationError("Failed to authenticate")

    async def handle_request(
        self,
        endpoint,
        payload=None,
        method="GET",
        return_raw_response=False,
        authenticate_request=False,
    ):
        """Handle the HTTP request by logging the request details and handling the response."""
        # Ensure access token is valid before making the request
        if authenticate_request is False:
            await self.authenticate()

        if self.mobile_platform == MOBILE_VIKINGS:
            url = BASE_URL + endpoint
        else:
            url = BASE_URL_JIMMOBILE + endpoint
        request_details = f"{method} request to: {url}"

        # Anonymize sensitive information like passwords
        if payload and ("password" in payload or "client_secret" in payload):
            anonymized_payload = {
                key: "********" if key in {"password", "client_secret"} else value
                for key, value in payload.items()
            }
            request_details += f", Payload: {anonymized_payload}"
        elif payload:
            request_details += f", Payload: {payload}"

        _LOGGER.debug(request_details)

        # Determine the appropriate method to call based on the HTTP method
        if method == "GET":
            response = await self.client.get(url)
        elif method == "POST":
            response = await self.client.post(url, data=payload)
        # Add support for other HTTP methods if needed
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if return_raw_response:
            _LOGGER.debug(f"Response data: {response.text}")
            return response

        if response.status_code == 200:
            data = response.json()
            _LOGGER.debug(f"Response data: {data}")
            return data
        elif response.status_code == 404:
            error_data = response.json()
            _LOGGER.debug(f"404 Error: {error_data}")
            return error_data
        elif str(response.status_code).startswith("4"):
            error_data = response.json()
            _LOGGER.debug(f"{response.status_code} Error: {error_data}")
            return False
        else:
            error_message = f"Request failed. Status code: {response.status_code}"
            try:
                error_data = response.json()
                error_message += f", Error: {error_data}"
            except Exception:
                pass
            raise Exception(error_message)

    async def get_customer_info(self):
        """Fetch customer information from the Mobile Vikings API.

        Returns
        -------
        dict or None: A dictionary containing customer information, or None if request fails.

        """
        return await self.handle_request("/customers/me")

    async def get_loyalty_points_balance(self):
        """Fetch loyalty points balance from the Mobile Vikings API.

        Returns
        -------
        dict or None: A dictionary containing loyalty points balance, or None if request fails.

        """
        if self.mobile_platform == JIM_MOBILE:
            # not existing for Jim Mobile
            return {"error": "not existing for Jim Mobile"}
        return await self.handle_request("/loyalty-points/balance")

    async def get_product_details(self, product_id):
        """Fetch product details from the Mobile Vikings API.

        Returns
        -------
        dict or None: A dictionary containing product details, or None if request fails.

        """
        return await self.handle_request(f"/products/{product_id}")

    def enrich_bundle(self, bundle, sim_info):
        """Add derived properties to a bundle for easy sensor creation."""
        now = datetime.now(timezone.utc)
        total = bundle.get("total", 0)
        used = bundle.get("used", 0)
        rlah_total = bundle.get("rlah_total", 0)
        rlah_used = bundle.get("rlah_used", 0)
        roam_row_total = bundle.get("roam_row_total", 0)
        roam_row_used = bundle.get("roam_row_used", 0)

        valid_from = datetime.strptime(bundle["valid_from"], "%Y-%m-%dT%H:%M:%S%z")
        valid_until = datetime.strptime(bundle["valid_until"], "%Y-%m-%dT%H:%M:%S%z")
        validity_seconds = (valid_until - valid_from).total_seconds()
        elapsed_seconds = (now - valid_from).total_seconds()

        bundle["used_percentage"] = round((used / total) * 100, 2) if total > 0 else 0
        bundle["period_percentage"] = round(
            max(0, min((elapsed_seconds / validity_seconds) * 100, 100)), 2
        )
        bundle["remaining_days"] = max((valid_until - now).days, 0)
        bundle["unlimited"] = total <= 0
        bundle["msisdn"] = sim_info.get("msisdn")
        bundle["alias"] = sim_info.get("alias")
        if bundle["type"] != "data":
            return bundle

        bundle["remaining_gb"] = round(max(total - used, 0) / (1024**3), 2)
        bundle["rlah_used_percentage"] = (
            round((rlah_used / rlah_total) * 100, 2) if rlah_total > 0 else 0
        )
        bundle["rlah_remaining_gb"] = round(
            max(rlah_total - rlah_used, 0) / (1024**3), 2
        )
        bundle["roam_row_used_percentage"] = (
            round((roam_row_used / roam_row_total) * 100, 2)
            if roam_row_total > 0
            else 0
        )
        bundle["roam_row_remaining_gb"] = round(
            max(roam_row_total - roam_row_used, 0) / (1024**3), 2
        )

        return bundle

    def build_bundle_key(self, bundle: dict) -> str:
        """Return a composite key for a bundle like data_default, sms_loyalty."""
        bundle_type = bundle.get("type", "unknown")
        bundle_category = bundle.get("category", "unknown")
        return f"{bundle_type}_{bundle_category}"

    async def get_subscriptions(self):
        """Fetch subscriptions and enrich each bundle individually."""
        subscriptions_raw = await self.handle_request("/subscriptions")
        subscriptions = {}

        for subscription in subscriptions_raw:
            subscription_id = subscription.get("id")

            # Fixed internet
            if subscription.get("type") == "fixed-internet":
                subscription["modem_settings"] = await self.handle_request(
                    f"/subscriptions/{subscription_id}/modem/settings"
                )
            else:
                sim_info = subscription.get("sim", {})
                if sim_info.get("msisdn"):
                    try:
                        balance = await self.handle_request(
                            f"/subscriptions/{subscription_id}/balance"
                        )
                        # usage = await self.handle_request(f"/subscriptions/{subscription_id}/usage-summary")
                        # subscription["usage"] = usage
                        bundles = balance.get("bundles", [])
                        subscription["balance"] = balance
                        # Remove "product" if present
                        subscription["balance"].pop("product", None)
                        subscription["balance"]["bundles"] = {
                            self.build_bundle_key(b): self.enrich_bundle(b, sim_info)
                            for b in bundles
                        }
                    except Exception as e:
                        _LOGGER.debug(
                            f"Failed to fetch balance for {subscription_id}: {e}"
                        )

            # Product details
            subscription["product"] = await self.get_product_details(
                subscription.get("product_id")
            )
            subscriptions[subscription_id] = subscription

        return subscriptions

    async def get_unpaid_invoices(self):
        """Fetch unpaid invoices from the Mobile Vikings API."""
        invoices = await self.handle_request(
            "/invoices?status=accepted,bad_dept,created,issued,partially_paid,pending_payment,review,unknown&per_page=20"
        )
        return invoices

    async def get_paid_invoices(self):
        """Fetch paid invoices from the Mobile Vikings API."""
        invoices = await self.handle_request("/invoices?status=paid")
        return invoices

    async def get_data(self):
        """Fetch customer info, loyalty points balance, invoices and subscriptions from the Mobile Vikings API.

        Returns
        -------
        dict
            A dictionary containing customer info, loyalty points balance, subscriptions, and unpaid invoices.

        Notes
        -----
            Errors in individual API calls will result in an error message being included in the respective section of the returned dictionary.

        """
        try:
            customer_info = await self.get_customer_info()
        except Exception as e:
            customer_info = {"error": str(e)}

        try:
            loyalty_points_balance = await self.get_loyalty_points_balance()
        except Exception as e:
            loyalty_points_balance = {"error": str(e)}

        try:
            subscriptions = await self.get_subscriptions()
        except Exception as e:
            subscriptions = {"error": str(e)}

        try:
            unpaid_invoices = await self.get_unpaid_invoices()
        except Exception as e:
            unpaid_invoices = {"error": str(e)}

        try:
            paid_invoices = await self.get_paid_invoices()
        except Exception as e:
            paid_invoices = {"error": str(e)}

        return {
            "timestamp": datetime.now().isoformat(),
            "customer_info": customer_info,
            "loyalty_points_balance": loyalty_points_balance,
            "subscriptions": subscriptions,
            "unpaid_invoices": unpaid_invoices,
            "paid_invoices": paid_invoices,
            "tokens": {
                "refresh_token": self.refresh_token,
                "access_token": self.access_token,
                "expires_in": self.expires_in,
            },
        }
