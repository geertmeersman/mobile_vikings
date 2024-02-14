"""MobileVikings API Client."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import re

from requests import Session

from .const import (
    BASE_HEADERS,
    CONNECTION_RETRY,
    DATETIME_FORMAT,
    DEFAULT_MOBILEVIKINGS_ENVIRONMENT,
    REQUEST_TIMEOUT,
)
from .exceptions import BadCredentialsException, MobileVikingsServiceException
from .models import MobileVikingsEnvironment, MobileVikingsItem
from .utils import _LOGGER, format_entity_name, mask_fields, sizeof_fmt


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
            _LOGGER.debug(f"{caller} Calling GET {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        else:
            data_copy = copy.deepcopy(data)
            mask_fields(data_copy, ["password", "client_id", "client_secret"])
            _LOGGER.debug(f"{caller} Calling POST {url} with {data_copy}")
            response = self.session.post(url, data, timeout=REQUEST_TIMEOUT)
        _LOGGER.debug(
            f"{caller} http status code = {response.status_code} (expecting {expected})"
        )
        if "authenticate" not in caller:
            _LOGGER.debug(f"{caller} Response:\n{response.text}")
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
                if str(response.status_code).startswith("4"):
                    raise BadCredentialsException(
                        f"[{caller}] Response HTTP {response.status_code}, Response: {response.text}, Url: {response.url}"
                    )
                raise MobileVikingsServiceException(
                    f"[{caller}] Expecting HTTP {expected} | Response HTTP {response.status_code}, Response: {response.text}, Url: {response.url}"
                )
            _LOGGER.debug(
                f"[MobileVikingsClient|request] Received a HTTP {response.status_code}, nothing to worry about! We give it another try :-)"
            )
            self.login()
            response = self.request(
                url, caller, data, expected, log, True, connection_retry_left - 1
            )
        return response

    def login(self) -> dict:
        """Start a new MobileVikings session with a user & password."""

        _LOGGER.debug("[MobileVikingsClient|login|start]")
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
        )
        return response.json()

    def products(self):
        """Get products."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20230905/mv/products",
            "subscriptions",
            None,
            200,
        )
        return response.json()

    def find_product(self, products, product_id):
        """Find a product by it's id."""
        for product in products:
            if product["id"] == product_id:
                return product
        return None

    def me(self):
        """Get user info."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20210211/mv/customers/me",
            "me",
            None,
            200,
        )
        return response.json()

    def balance(self, subscription_id):
        """Get balance."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20200901/mv/subscriptions/{subscription_id}/balance",
            "balance",
            None,
            200,
        )
        return response.json()

    def invoice_address(self, subscription_id):
        """Get user info."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/mv/addresses?type=invoice&subscription_id={subscription_id}",
            "invoice_address",
            None,
            200,
        )
        return response.json()

    def modem_settings(self, subscription_id):
        """Get product settings."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/mv/subscriptions/{subscription_id}/modem/settings",
            "products",
            None,
            200,
        )
        return response.json()

    def loyalty_points(self):
        """Get loyalty point."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/mv/loyalty-points/balance",
            "loyalty_points",
            None,
            200,
        )
        return response.json()

    def claims(self):
        """Get claims."""
        response = self.request(
            f"{self.environment.deals_endpoint}/api/20210707/catalog/claims/",
            "claims",
            None,
            200,
        )
        return response.json()

    def open_invoices(self):
        """Get open invoices."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20220211/mv/invoices?status=created%2Cissued%2Cpending_payment%2Cpartially_paid",
            "open_invoices",
            None,
            200,
        )
        return response.json()

    def paid_invoices(self):
        """Get paid invoices."""
        response = self.request(
            f"{self.environment.uwa_endpoint}/20220211/mv/invoices?status=paid",
            "paid_invoices",
            None,
            200,
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
            _LOGGER.debug("[MobileVikingsClient|fetch_data] Logged out, renewing token")
            self.login()

        me = self.me()
        userid = me.get("id")
        self.language = me.get("language")
        loyalty_points = self.loyalty_points()
        claims = self.claims()

        device_key = format_entity_name(f"{userid} invoices")
        device_name = f"{me.get('first_name')} {me.get('last_name')} Invoices"
        device_model = "Invoices"
        open_invoices = self.open_invoices()
        open_invoice_amount = 0
        next_expiration_date = False
        if open_invoices.get("total_items") > 0:
            for invoice in open_invoices.get("results"):
                open_invoice_amount += invoice.get("amount_due")
                timestamp = datetime.strptime(
                    invoice.get("expiration_date"), "%Y-%m-%dT%H:%M:%S%z"
                ).timestamp()
                if next_expiration_date:
                    if timestamp < next_expiration_date:
                        next_expiration_date = timestamp
                else:
                    next_expiration_date = timestamp
        extra_attributes = {}
        state = False
        if next_expiration_date:
            next_expiration_date = datetime.fromtimestamp(next_expiration_date)
            state = next_expiration_date.strftime("%Y-%m-%d")
            extra_attributes = {
                "Remaining days": (next_expiration_date - datetime.now()).days
            }
        key = format_entity_name(f"{userid} upcoming expiration date")
        data[key] = MobileVikingsItem(
            name="Upcoming expiration date",
            key=key,
            type="date",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=state,
            extra_attributes=extra_attributes,
        )
        key = format_entity_name(f"{userid} open invoices")
        data[key] = MobileVikingsItem(
            name="Open invoices",
            key=key,
            type="euro",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=open_invoice_amount,
            extra_attributes={"Open invoices list": open_invoices.get("results")},
        )
        paid_invoices = self.paid_invoices()
        key = format_entity_name(f"{userid} paid invoices")
        data[key] = MobileVikingsItem(
            name="Paid invoices",
            key=key,
            type="invoices",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=paid_invoices.get("total_items"),
            extra_attributes={"paid_invoices_list": paid_invoices.get("results")},
        )

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
        device_key = format_entity_name(f"{userid} loyalty")
        device_name = f"{me.get('first_name')} {me.get('last_name')} Vikingpunten"
        device_model = "Vikingpunten"
        key = format_entity_name(f"{userid} loyalty points available")
        data[key] = MobileVikingsItem(
            name="Vikingpunten available",
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
            name="Vikingpunten pending",
            key=key,
            type="euro_pending",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=loyalty_points.get("pending"),
            extra_attributes=loyalty_points,
        )
        key = format_entity_name(f"{userid} loyalty points blocked")
        data[key] = MobileVikingsItem(
            name="Vikingpunten blocked",
            key=key,
            type="euro_blocked",
            device_key=device_key,
            device_name=device_name,
            device_model=device_model,
            state=loyalty_points.get("blocked"),
            extra_attributes=loyalty_points,
        )
        subscriptions = self.subscriptions()
        products = self.products()
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if subscription.get("sim") and len(subscription.get("sim")):
                balance = self.balance(subscription_id)
                product = balance.get("product")
                msisdn = subscription.get("sim").get("msisdn")
                if msisdn[0:2] == "32":
                    msisdn = f"0{msisdn[2:]}"
                device_key = format_entity_name(f"{product.get('type')} {msisdn}")
                device_name = f"{msisdn} | {subscription.get('sim').get('alias')}"
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
                    },
                )
                key = format_entity_name(f"{msisdn} credit")
                data[key] = MobileVikingsItem(
                    name="Credit",
                    key=key,
                    type="euro",
                    device_key=device_key,
                    device_name=device_name,
                    device_model=device_model,
                    state=balance.get("credit"),
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
                bundle_data = 0
                bundle_voice = 0
                bundle_sms = 0

                for bundle in balance.get("bundles"):
                    type = bundle.get("type")
                    days_remaining = (
                        datetime.strptime(bundle.get("valid_until"), DATETIME_FORMAT)
                        - now
                    ).days
                    days_in_period = (
                        datetime.strptime(bundle.get("valid_until"), DATETIME_FORMAT)
                        - datetime.strptime(bundle.get("valid_from"), DATETIME_FORMAT)
                    ).days
                    first_of_period = datetime.strptime(
                        bundle.get("valid_from"), DATETIME_FORMAT
                    )

                    seconds_in_month = days_in_period * 86400
                    seconds_completed = (now - first_of_period).total_seconds()
                    period_percentage_completed = round(
                        100 * seconds_completed / seconds_in_month, 1
                    )
                    period_percentage_remaining = 100 - period_percentage_completed

                    total = bundle.get("total")
                    used = bundle.get("used")
                    extra_attributes = {
                        "valid_from": bundle.get("valid_from"),
                        "valid_until": bundle.get("valid_until"),
                        "days_remaining": days_remaining,
                        "days_in_period": days_in_period,
                        "period_percentage_completed": period_percentage_completed,
                        "period_percentage_remaining": period_percentage_remaining,
                        "total": total,
                        "used": used,
                    }
                    key = format_entity_name(f"{msisdn} days remaining")
                    data[key] = MobileVikingsItem(
                        name="Remaining Days",
                        key=key,
                        type="remaining_days",
                        device_key=device_key,
                        device_name=device_name,
                        device_model=device_model,
                        state=days_remaining,
                        extra_attributes=extra_attributes,
                    )
                    if bundle.get("category") != "default":
                        suffix = f" {bundle.get('category')}"
                    else:
                        suffix = ""
                    if str(total) == "-1":
                        state = "∞"
                    else:
                        state = round(100 * used / total)
                    if type == "data":
                        if suffix == "" and bundle_data > 0:
                            suffix = f"{suffix} {bundle_data}"
                        if suffix == "":
                            bundle_data += 1
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
                        if suffix == "" and bundle_voice > 0:
                            suffix = f"{suffix} {bundle_voice}"
                        if suffix == "":
                            bundle_voice += 1
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
                        if suffix == "" and bundle_sms > 0:
                            suffix = f"{suffix} {bundle_sms}"
                        if suffix == "":
                            bundle_sms += 1
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
            elif subscription.get("type", "") == "fixed-internet":
                product_info = self.find_product(
                    products, subscription.get("product_id")
                )
                device_key = format_entity_name(
                    f"{product_info.get('type')} {subscription_id}"
                )
                device_name = product_info.get("descriptions").get("title")
                device_model = product_info.get("type", "").title()

                key = format_entity_name(f"{device_model} product")
                data[key] = MobileVikingsItem(
                    name=product_info.get("descriptions").get("title"),
                    key=key,
                    type="product_price",
                    device_key=device_key,
                    device_name=device_name,
                    device_model=device_model,
                    state=product_info.get("price"),
                    extra_attributes=product_info,
                )

                modem = self.modem_settings(subscription_id)
                key = format_entity_name(f"{device_model} modem")
                data[key] = MobileVikingsItem(
                    name="Internet Box",
                    key=key,
                    type="modem",
                    device_key=device_key,
                    device_name=device_name,
                    device_model=device_model,
                    state=modem.get("actual", "").get("gateway", "").get("mode", ""),
                    extra_attributes=modem,
                )
        return data
