"""Module containing the MobileVikingsClient class for interacting with the Mobile Vikings API."""

from datetime import datetime, timedelta, timezone
import logging

from homeassistant.helpers.httpx_client import get_async_client

from .const import BASE_URL, CLIENT_ID, CLIENT_SECRET

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""

    pass


class MobileVikingsClient:
    """Asynchronous client for interacting with the Mobile Vikings API."""

    def __init__(self, hass, username, password, tokens=None):
        """Initialize the MobileVikingsClient.

        Parameters
        ----------
        hass : HomeAssistant
            The Home Assistant instance to use for handling API requests and coordination.
        username : str
            The username for authenticating with the Mobile Vikings API.
        password : str
            The password for authenticating with the Mobile Vikings API.
        tokens : dict, optional
            A dictionary containing token information (refresh_token, access_token, expiry).

        """
        self.hass = hass
        self.username = username
        self.password = password
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
        """Authenticate with the Mobile Vikings API."""
        if self._is_token_valid():
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"
        else:
            if self.refresh_token:
                _LOGGER.debug("Access token renewal with refresh token")
                await self._request_token(
                    {
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                    }
                )
            else:
                _LOGGER.debug("Requesting new access token")
                await self._request_token(
                    {
                        "username": self.username,
                        "password": self.password,
                        "grant_type": "password",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
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

        url = BASE_URL + endpoint
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
        return await self.handle_request("/loyalty-points/balance")

    async def get_subscriptions(self):
        """Fetch subscriptions from the Mobile Vikings API.

        Returns
        -------
        dict
            A dictionary containing subscription information.

        """
        subscriptions = await self.handle_request("/subscriptions?state=enabled")
        return_sub = {}
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if subscription.get("type") == "fixed-internet":
                subscription["modem_settings"] = await self.handle_request(
                    f"/subscriptions/{subscription_id}/modem/settings"
                )
            else:
                balance = await self.handle_request(
                    f"/subscriptions/{subscription_id}/balance"
                )
                subscription["balance"] = balance
                subscription["balance_aggregated"] = self.aggregate_bundles_by_type(
                    balance
                )
            return_sub[subscription_id] = subscription
        return return_sub

    def aggregate_bundles_by_type(self, balance):
        """Aggregate bundles by their type, summing up total, used, and remaining values.

        For each unique bundle type (data, voice, sms), a single structure is created.

        Args:
            balance (dict): A dictionary containing the balance information with a key `bundles`,
                            which is a list of dictionaries. Each bundle dictionary must have the following keys:
                            - `type` (str): The type of the bundle (e.g., 'data', 'sms', 'voice').
                            - `total` (float): The total amount of the bundle (in GB for data bundles).
                            - `used` (float): The amount of the bundle that has been used (in GB for data bundles).
                            - `remaining` (float): The amount remaining in the bundle (in GB for data bundles).
                            - `valid_from` (str): The start date of the bundle validity (ISO 8601 format).
                            - `valid_until` (str): The end date of the bundle validity (ISO 8601 format).

        Returns:
            dict: A dictionary with keys 'data', 'voice', 'sms', each containing the aggregated bundle for that type.

        Raises:
            KeyError: If required keys are missing in the input bundles.

        """
        # Parse the current time and make it timezone-aware
        current_time = datetime.now(timezone.utc)

        # Initialize the dictionary that will hold the aggregated bundles for each type
        aggregated_bundles = {"data": None, "voice": None, "sms": None}

        if "bundles" not in balance:
            raise KeyError("The 'balance' dictionary must contain a 'bundles' key")

        # Aggregate bundles by type
        for bundle in balance["bundles"]:
            bundle_type = bundle.get("type")
            if not bundle_type:
                raise KeyError("Each bundle must have a 'type' field.")

            # Only process data, voice, and sms bundles
            if bundle_type not in aggregated_bundles:
                continue

            # If this is the first bundle of this type, initialize the aggregated structure
            if aggregated_bundles[bundle_type] is None:
                aggregated_bundles[bundle_type] = {
                    "type": bundle_type,
                    "valid_from": bundle["valid_from"],
                    "valid_until": bundle["valid_until"],
                    "total": 0,
                    "used": 0,
                    "remaining": 0,
                    "unlimited": False,  # Default to False
                }

            # Check if the bundle is not "unlimited" and set the values accordingly
            if not aggregated_bundles[bundle_type]["unlimited"]:
                if bundle["total"] == 0:
                    # Mark as unlimited only if not already set
                    aggregated_bundles[bundle_type]["unlimited"] = True
                    aggregated_bundles[bundle_type]["total"] = 0
                    aggregated_bundles[bundle_type]["used"] = 0
                    aggregated_bundles[bundle_type]["remaining"] = 0
                else:
                    # Sum up values for this type
                    aggregated_bundles[bundle_type]["total"] += bundle["total"]
                    aggregated_bundles[bundle_type]["used"] += bundle["used"]
                    aggregated_bundles[bundle_type]["remaining"] += bundle["remaining"]

        # Calculate additional values for each aggregated bundle
        for bundle in aggregated_bundles.values():
            if bundle is not None:
                total = bundle["total"]
                used = bundle["used"]
                remaining = bundle["remaining"]

                # Calculate used percentage
                bundle["used_percentage"] = (used / total) * 100 if total > 0 else 0
                bundle["used_percentage"] = round(
                    bundle["used_percentage"], 2
                )  # Round to two decimal places

                # Only add total_gb, used_gb, and remaining_gb if the bundle type is 'data'
                if bundle["type"] == "data":
                    bundle["total_gb"] = round(
                        total / (1024**3), 2
                    )  # Convert from bytes to GB
                    bundle["used_gb"] = round(used / (1024**3), 2)
                    bundle["remaining_gb"] = round(remaining / (1024**3), 2)

                try:
                    valid_from = datetime.strptime(
                        bundle["valid_from"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                    valid_until = datetime.strptime(
                        bundle["valid_until"], "%Y-%m-%dT%H:%M:%S%z"
                    )
                except ValueError as e:
                    raise ValueError(f"Invalid date format in bundle: {e}")

                # Calculate validity percentage (period_percentage)
                validity_period = (valid_until - valid_from).total_seconds()
                elapsed_time = (current_time - valid_from).total_seconds()
                period_percentage = max(
                    0, min((elapsed_time / validity_period) * 100, 100)
                )  # Clamp between 0 and 100

                # Add period percentage to the bundle
                bundle["period_percentage"] = round(period_percentage, 2)

                # Calculate remaining days in the period
                remaining_days = (valid_until - current_time).days
                bundle["remaining_days"] = max(remaining_days, 0)  # Avoid negative days

                # Compare used_percentage with period_percentage and add usage_alert
                bundle["usage_alert"] = (
                    bundle["used_percentage"] > bundle["period_percentage"]
                )

        return aggregated_bundles

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
