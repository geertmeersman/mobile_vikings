"""MobileVikings API Client."""
from __future__ import annotations

import json
import re
from datetime import datetime
from datetime import timezone

from requests import (
    Session,
)

from .const import BASE_HEADERS
from .const import CONNECTION_RETRY
from .const import DATETIME_FORMAT
from .const import DEFAULT_MOBILEVIKINGS_ENVIRONMENT
from .const import REQUEST_TIMEOUT
from .exceptions import MobileVikingsServiceException
from .models import MobileVikingsEnvironment
from .models import MobileVikingsItem
from .utils import format_entity_name
from .utils import log_debug
from .utils import sizeof_fmt


class MobileVikingsClient:
    """MobileVikings client."""

    session: Session
    environment: MobileVikingsEnvironment

    def __init__(
        self,
        session: Session | None = None,
        username: str | None = None,
        password: str | None = None,
        headers: dict | None = BASE_HEADERS,
        environment: MobileVikingsEnvironment = DEFAULT_MOBILEVIKINGS_ENVIRONMENT,
    ) -> None:
        """Initialize MobileVikingsClient."""
        self.session = session if session else Session()
        self.username = username
        self.password = password
        self.environment = environment
        self.session.headers = headers
        self.language = "nl"
        self.request_error = {}

    def request(
        self,
        url,
        caller="Not set",
        data=None,
        expected="200",
        log=False,
        retrying=False,
        connection_retry_left=CONNECTION_RETRY,
    ) -> dict:
        """Send a request to MobileVikings."""
        if data is None:
            log_debug(f"{caller} Calling GET {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        else:
            log_debug(f"{caller} Calling POST {url} with {data}")
            response = self.session.post(url, data, timeout=REQUEST_TIMEOUT)
        log_debug(
            f"{caller} http status code = {response.status_code} (expecting {expected})"
        )
        if log:
            log_debug(f"{caller} Response:\n{response.text}")
        if expected is not None and response.status_code != expected:
            if response.status_code == 404:
                self.request_error = response.json()
                return False
            if (
                response.status_code != 403
                and response.status_code != 401
                and response.status_code != 500
                and connection_retry_left > 0
                and not retrying
            ):
                raise MobileVikingsServiceException(
                    f"[{caller}] Expecting HTTP {expected} | Response HTTP {response.status_code}, Response: {response.text}, Url: {response.url}"
                )
            log_debug(
                f"[MobileVikingsClient|request] Received a HTTP {response.status_code}, nothing to worry about! We give it another try :-)"
            )
            self.login()
            response = self.request(
                url, caller, data, expected, log, True, connection_retry_left - 1
            )
        return response

    def login(self) -> dict:
        """Start a new MobileVikings session with a user & password."""

        log_debug("[MobileVikingsClient|login|start]")
        """Login process"""
        if self.username is None or self.password is None:
            return False
        response = self.request(
            f"{self.environment.api_endpoint}/login",
            "[MobileVikingsClient|login|authenticate]",
            {"username": self.username, "password": self.password},
            200,
        )
        z = re.findall(r"{\"baseUrl\".*}", response.text)
        if z:
            j = json.loads(z[0])
            self.session.headers.update(
                {
                    "authority": self.environment.authority,
                    "accept": "application/json",
                    "content-type": "application/x-www-form-urlencoded",
                }
            )
            data = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
                "client_id": j["uwa"]["oauthClientId"],
                "client_secret": j["uwa"]["oauthClientSecret"],
            }
            response = self.request(
                f"{self.environment.uwa_endpoint}/mv/oauth2/token/", "login", data, 200
            )
            j = response.json()
            self.session.headers.update(
                {"authorization": "Bearer " + j.get("access_token")}
            )
            return True
        return False

    def logged_in(self):
        """Check if anonymous."""
        response = self.request(self.environment.logincheck, "logged_in", None, 200)
        if response.json().get("customer_code") != "anonymous":
            return True
        return False

    def subscriptions(self):
        """Get subscriptions."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20220211/mv/subscriptions",
            "subscriptions",
            None,
            200,
            True,
        )
        return response.json()

    def me(self):
        """Get user info."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20210211/mv/customers/me",
            "me",
            None,
            200,
            True,
        )
        return response.json()

    def balance(self, subscription_id):
        """Get balance."""
        response = self.request(
            f"https://uwa.mobilevikings.be/20200901/mv/subscriptions/{subscription_id}/balance",
            "balance",
            None,
            200,
            True,
        )
        return response.json()

    def invoice_address(self, subscription_id):
        """Get user info."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/mv/addresses?type=invoice&subscription_id={subscription_id}",
            "invoice_address",
            None,
            200,
            True,
        )
        return response.json()

    def products(self):
        """Get products."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20220211/mv/products?",
            "products",
            None,
            200,
            True,
        )
        return response.json()

    def loyalty_points(self):
        """Get loyalty point."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/mv/loyalty-points/balance",
            "loyalty_points",
            None,
            200,
            True,
        )
        return response.json()

    def claims(self):
        """Get claims."""
        response = self.request(
            "https://vikingdeals.be/api/20210707/catalog/claims/",
            "claims",
            None,
            200,
            True,
        )
        return response.json()

    def fetch_data(self):
        """Fetch MobileVikings data."""
        data = {}

        now = datetime.now(timezone.utc)
        if not self.login():
            return False
        logged_in = self.logged_in()
        if not logged_in:
            log_debug("[MobileVikingsClient|fetch_data] Logged out, renewing token")
            self.login()

        me = self.me()
        userid = me.get("id")
        self.language = me.get("language")
        loyalty_points = self.loyalty_points()
        claims = self.claims()

        device_key = format_entity_name(f"{userid} user")
        device_name = f"{me.get('first_name')} {me.get('last_name')}"
        device_model = "Useraccount"
        key = format_entity_name(f"{userid} user")
        data[key] = MobileVikingsItem(
            name=f"{me.get('first_name')} {me.get('last_name')}",
            key=key,
            type="profile",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=me.get("email"),
            extra_attributes=me,
        )
        key = format_entity_name(f"{userid} loyalty points available")
        data[key] = MobileVikingsItem(
            name="Vikings deals available",
            key=key,
            type="euro",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=loyalty_points.get("available"),
            extra_attributes=loyalty_points | {"claims": claims},
        )
        key = format_entity_name(f"{userid} loyalty points pending")
        data[key] = MobileVikingsItem(
            name="Vikings deals pending",
            key=key,
            type="euro",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=loyalty_points.get("pending"),
            extra_attributes=loyalty_points,
        )
        key = format_entity_name(f"{userid} loyalty points blocked")
        data[key] = MobileVikingsItem(
            name="Vikings deals blocked",
            key=key,
            type="euro",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=loyalty_points.get("blocked"),
            extra_attributes=loyalty_points,
        )
        subscriptions = self.subscriptions()
        for subscription in subscriptions:
            if subscription.get("sim") and len(subscription.get("sim")):
                subscription_id = subscription.get("id")
                balance = self.balance(subscription_id)
                product = balance.get("product")
                msisdn = subscription.get("sim").get("msisdn")
                if msisdn[0:2] == "32":
                    log_debug(f"32 GEVONDEN: {msisdn}")
                    msisdn = f"0{msisdn[2:]}"
                device_key = format_entity_name(f"{product.get('type')} {msisdn}")
                device_name = f"{msisdn} | {product.get('descriptions').get('title')}"
                device_model = product.get("type").title()
                address = self.invoice_address(subscription_id)
                if len(address):
                    address = address[0]
                    key = format_entity_name(f"{msisdn} invoice address")
                    data[key] = MobileVikingsItem(
                        name="Invoice Address",
                        key=key,
                        type="address",
                        device_key=device_key,
                        device_name=device_name,
                        device_model=device_model,
                        state=address.get("address").get("city"),
                        extra_attributes=address,
                    )
                key = format_entity_name(f"{msisdn} product")
                data[key] = MobileVikingsItem(
                    name=product.get("descriptions").get("title"),
                    key=key,
                    type="euro",
                    device_key=device_key,
                    device_name=device_name,
                    device_model=device_model,
                    state=product.get("price"),
                    extra_attributes=product,
                )
                key = format_entity_name(f"{msisdn} out of bundle")
                data[key] = MobileVikingsItem(
                    name="Out of bundle",
                    key=key,
                    type="euro",
                    device_key=device_key,
                    device_name=device_name,
                    device_model=device_model,
                    state=balance.get("out_of_bundle_cost"),
                    extra_attributes={
                        "Out of bundle cost threshold": balance.get(
                            "out_of_bundle_cost_threshold"
                        ),
                        "Credit": balance.get("credit"),
                    },
                )
                key = format_entity_name(f"{msisdn} subscription")
                data[key] = MobileVikingsItem(
                    name="Subscription",
                    key=key,
                    type="subscription",
                    device_key=device_key,
                    device_name=device_name,
                    device_model=device_model,
                    state=subscription.get("sim").get("alias"),
                    extra_attributes=subscription,
                )

                for bundle in balance.get("bundles"):
                    type = bundle.get("type")
                    days_remaining = (
                        datetime.strptime(bundle.get("valid_until"), DATETIME_FORMAT)
                        - now
                    ).days
                    period_length = (
                        datetime.strptime(bundle.get("valid_until"), DATETIME_FORMAT)
                        - datetime.strptime(bundle.get("valid_from"), DATETIME_FORMAT)
                    ).days
                    period_percentage = round(
                        100 * (period_length - days_remaining) / period_length
                    )
                    total = bundle.get("total")
                    used = bundle.get("used")
                    extra_attributes = {
                        "period_length": period_length,
                        "period_percentage": period_percentage,
                        "total": total,
                        "used": used,
                    }
                    if bundle.get("category") != "default":
                        suffix = f" {bundle.get('category')}"
                    else:
                        suffix = ""
                    if str(total) == "-1":
                        state = "∞"
                    else:
                        state = round(100 * used / total)
                    if type == "data":
                        if state == "∞":
                            used_human = sizeof_fmt(used)
                            extra_attributes |= {
                                "total_human": "∞",
                                "used_human": used_human,
                                "remaining_human": "∞",
                                "usage_human": f"{used_human} verbruikt",
                            }
                        else:
                            total_human = sizeof_fmt(total)
                            extra_attributes |= {
                                "total_human": total_human,
                                "used_human": sizeof_fmt(used),
                                "remaining_human": sizeof_fmt(total - used),
                                "usage_human": f"van de {total_human} over",
                            }
                        key = format_entity_name(f"{msisdn} data{suffix}")
                        data[key] = MobileVikingsItem(
                            name=f"Data{suffix}",
                            key=key,
                            type="usage_percentage_mobile",
                            device_key=device_key,
                            device_name=device_name,
                            device_model=device_model,
                            state=state,
                            extra_attributes=extra_attributes,
                        )
                    elif type == "voice":
                        used_human = f"{str(round(used/60))} min"
                        if state == "∞":
                            extra_attributes |= {
                                "total_human": "∞",
                                "used_human": used_human,
                                "remaining_human": "∞",
                                "usage_human": f"{used_human} verbruikt",
                            }
                        else:
                            total_human = f"{str(round(total/60))} min"
                            extra_attributes |= {
                                "total_human": total_human,
                                "used_human": used_human,
                                "remaining_human": f"{str(round((total-used)/60))} min",
                                "usage_human": f"van de {total_human} over",
                            }
                        key = format_entity_name(f"{msisdn} voice{suffix}")
                        data[key] = MobileVikingsItem(
                            name=f"Voice{suffix}",
                            key=key,
                            type="voice",
                            device_key=device_key,
                            device_name=device_name,
                            device_model=device_model,
                            state=state,
                            extra_attributes=extra_attributes,
                        )
                    elif type == "sms":
                        used_human = str(round(used)) + " sms'en"
                        if state == "∞":
                            extra_attributes |= {
                                "total_human": "∞",
                                "used_human": used_human,
                                "remaining_human": "∞",
                                "usage_human": f"{used_human} verstuurd",
                            }
                        else:
                            total_human = str(round(total)) + " sms'en"
                            extra_attributes |= {
                                "total_human": total_human,
                                "used_human": used_human,
                                "remaining_human": f"{str(round(total-used))} sms'en",
                                "usage_human": f"van de {total_human} over",
                            }
                        key = format_entity_name(f"{msisdn} sms{suffix}")
                        data[key] = MobileVikingsItem(
                            name=f"SMS{suffix}",
                            key=key,
                            type="sms",
                            device_key=device_key,
                            device_name=device_name,
                            device_model=device_model,
                            state=state,
                            extra_attributes=extra_attributes,
                        )
        return data
